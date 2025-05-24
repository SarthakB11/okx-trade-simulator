import asyncio
import json
import logging
import ssl
import time
from typing import Callable, Dict, Any, Optional, List, Union

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

# Set up logging
logger = logging.getLogger('websocket_connector')
logger.setLevel(logging.INFO)

# Create file handler
file_handler = logging.FileHandler('websocket.log')
file_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)


class WebSocketConnector:
    """
    WebSocket connector for OKX market data API.
    """
    
    def __init__(self, uri: str, on_message_callback: Callable[[Any], None]):
        """
        Initialize the WebSocket connector.
        
        Args:
            uri: WebSocket URI to connect to (e.g., wss://ws.okx.com:8443/ws/v5/public)
            on_message_callback: Callback function for received messages
        """
        self.uri = uri
        self.on_message_callback = on_message_callback
        self.websocket = None
        self.connection_task = None
        self.should_run = False
        self.last_ping_time = 0
        self.last_pong_time = 0
        self.ping_interval = 20  # OKX recommends 20 seconds
        self.reconnect_interval = 5  # seconds
        self.max_reconnect_attempts = 5
        self.reconnect_attempts = 0
        self.subscriptions = []  # Track active subscriptions
    
    async def connect(self) -> bool:
        """
        Establish connection to the WebSocket endpoint.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        self.should_run = True
        self.reconnect_attempts = 0
        self.connection_task = asyncio.create_task(self._maintain_connection())
        
        # Wait for the connection to be established
        for _ in range(10):  # Try for 5 seconds (10 * 0.5s)
            if self.websocket is not None and self.websocket.open:
                logger.info("Successfully connected to WebSocket endpoint")
                return True
            await asyncio.sleep(0.5)
        
        logger.error("Failed to connect to WebSocket endpoint")
        return False
    
    async def disconnect(self):
        """
        Disconnect from the WebSocket endpoint.
        """
        self.should_run = False
        
        # Clear subscriptions
        self.subscriptions = []
        
        if self.connection_task:
            self.connection_task.cancel()
            try:
                await self.connection_task
            except asyncio.CancelledError:
                pass
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        logger.info("Disconnected from WebSocket endpoint")
    
    async def send(self, message) -> bool:
        """
        Send a message to the WebSocket endpoint.
        
        Args:
            message: Message to send (will be converted to JSON)
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if not self.websocket or not self.websocket.open:
            logger.error("Cannot send message: not connected")
            return False
        
        try:
            if isinstance(message, dict):
                message = json.dumps(message)
            
            logger.info(f"Sending message: {message}")
            await self.websocket.send(message)
            return True
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False
    
    async def subscribe(self, channel: str, instrument_id: str) -> bool:
        """
        Subscribe to a specific channel for an instrument.
        
        Args:
            channel: Channel name (e.g., 'books', 'tickers')
            instrument_id: Instrument ID (e.g., 'BTC-USDT-SWAP')
            
        Returns:
            bool: True if subscription was successful, False otherwise
        """
        # Create subscription message according to OKX API format
        subscription = {
            "channel": channel,
            "instId": instrument_id
        }
        
        # Check if already subscribed
        if subscription in self.subscriptions:
            logger.info(f"Already subscribed to {channel} for {instrument_id}")
            return True
        
        # Create subscription message
        message = {
            "op": "subscribe",
            "args": [subscription]
        }
        
        # Send subscription request
        success = await self.send(message)
        
        if success:
            # Add to subscriptions list
            self.subscriptions.append(subscription)
            logger.info(f"Sent subscription request for {channel} on {instrument_id}")
            
            # Wait for confirmation (up to 3 seconds)
            for _ in range(6):
                await asyncio.sleep(0.5)
                # We assume success if we're still connected after sending
                if self.websocket and self.websocket.open:
                    return True
            
            # If we get here, we didn't receive confirmation in time
            logger.warning(f"No explicit confirmation for {channel} subscription on {instrument_id}, but continuing")
            return True
        else:
            logger.error(f"Failed to send subscription for {channel} on {instrument_id}")
            return False
    
    async def unsubscribe(self, channel: str, instrument_id: str) -> bool:
        """
        Unsubscribe from a specific channel for an instrument.
        
        Args:
            channel: Channel name (e.g., 'books', 'tickers')
            instrument_id: Instrument ID (e.g., 'BTC-USDT-SWAP')
            
        Returns:
            bool: True if unsubscription was successful, False otherwise
        """
        subscription = {
            "channel": channel,
            "instId": instrument_id
        }
        
        # Check if subscribed
        if subscription not in self.subscriptions:
            logger.info(f"Not subscribed to {channel} for {instrument_id}")
            return True
        
        # Create unsubscription message
        message = {
            "op": "unsubscribe",
            "args": [subscription]
        }
        
        # Send unsubscription request
        success = await self.send(message)
        
        if success:
            # Remove from subscriptions list
            if subscription in self.subscriptions:
                self.subscriptions.remove(subscription)
            logger.info(f"Unsubscribed from {channel} on {instrument_id}")
            return True
        else:
            logger.error(f"Failed to unsubscribe from {channel} on {instrument_id}")
            return False
    
    async def _maintain_connection(self):
        """
        Maintain the WebSocket connection, reconnecting as needed.
        """
        while self.should_run:
            try:
                logger.info(f"Connecting to {self.uri}")
                
                # Create SSL context for secure connections
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                # Connect to the WebSocket endpoint
                async with websockets.connect(self.uri, ssl=ssl_context) as websocket:
                    self.websocket = websocket
                    self.reconnect_attempts = 0  # Reset reconnect attempts on successful connection
                    logger.info("Connected to WebSocket endpoint")
                    
                    # Start ping task
                    ping_task = asyncio.create_task(self._ping_loop())
                    
                    # Resubscribe to channels if we have any
                    if self.subscriptions:
                        await self._resubscribe()
                    
                    try:
                        # Process messages
                        async for message in websocket:
                            try:
                                # Update pong time when we receive any message
                                self.last_pong_time = time.time()
                                
                                # Process the message
                                if len(message) > 200:
                                    logger.debug(f"Received message: {message[:200]}...")
                                else:
                                    logger.debug(f"Received message: {message}")
                                
                                # Parse and process the message
                                self.on_message_callback(message)
                            except Exception as e:
                                logger.error(f"Error processing message: {str(e)}")
                    finally:
                        # Clean up ping task
                        ping_task.cancel()
                        try:
                            await ping_task
                        except asyncio.CancelledError:
                            pass
            
            except (ConnectionClosed, WebSocketException) as e:
                self.websocket = None
                logger.error(f"WebSocket connection closed: {str(e)}")
                
                # Check if we should reconnect
                if self.should_run:
                    self.reconnect_attempts += 1
                    if self.reconnect_attempts > self.max_reconnect_attempts:
                        logger.error(f"Max reconnect attempts ({self.max_reconnect_attempts}) reached, giving up")
                        break
                    
                    wait_time = self.reconnect_interval * min(self.reconnect_attempts, 5)  # Exponential backoff, capped at 5x
                    logger.info(f"Reconnecting in {wait_time} seconds (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
                    await asyncio.sleep(wait_time)
                else:
                    break
            
            except Exception as e:
                self.websocket = None
                logger.error(f"Unexpected error: {str(e)}")
                
                # Check if we should reconnect
                if self.should_run:
                    self.reconnect_attempts += 1
                    if self.reconnect_attempts > self.max_reconnect_attempts:
                        logger.error(f"Max reconnect attempts ({self.max_reconnect_attempts}) reached, giving up")
                        break
                    
                    wait_time = self.reconnect_interval * min(self.reconnect_attempts, 5)  # Exponential backoff, capped at 5x
                    logger.info(f"Reconnecting in {wait_time} seconds (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
                    await asyncio.sleep(wait_time)
                else:
                    break
        
        logger.info("Connection maintenance loop exited")
    
    async def _resubscribe(self):
        """
        Resubscribe to all previously subscribed channels after reconnection.
        """
        if not self.subscriptions:
            return
        
        logger.info(f"Resubscribing to {len(self.subscriptions)} channels")
        
        # Group subscriptions into batches of 10 (OKX recommendation)
        subscription_batches = [self.subscriptions[i:i+10] for i in range(0, len(self.subscriptions), 10)]
        
        for batch in subscription_batches:
            message = {
                "op": "subscribe",
                "args": batch
            }
            
            success = await self.send(message)
            if not success:
                logger.error("Failed to resubscribe to some channels")
            
            # Small delay between batches
            await asyncio.sleep(1)
    
    async def _ping_loop(self):
        """
        Send periodic pings to keep the connection alive.
        
        OKX requires a ping message every 30 seconds.
        """
        while True:
            try:
                current_time = time.time()
                
                # Check if we need to send a ping
                if current_time - self.last_ping_time >= self.ping_interval:
                    if self.websocket and self.websocket.open:
                        # For OKX, we need to send a specific ping message
                        ping_message = {"op": "ping"}
                        logger.info("Sending ping message")
                        await self.send(ping_message)
                        self.last_ping_time = current_time
                    else:
                        logger.warning("Cannot send ping: WebSocket not connected")
                
                # Check for ping timeout (no message received in 2x ping interval)
                if self.last_pong_time > 0 and current_time - self.last_pong_time > 2 * self.ping_interval:
                    logger.error(f"Ping timeout: no response for {current_time - self.last_pong_time:.1f} seconds")
                    # Force close the connection, which will trigger a reconnect
                    if self.websocket:
                        await self.websocket.close()
                    break
                
                await asyncio.sleep(1)  # Check every second
            
            except Exception as e:
                logger.error(f"Error in ping loop: {str(e)}")
                await asyncio.sleep(5)  # Wait a bit longer on error
