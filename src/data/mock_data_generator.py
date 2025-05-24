"""
Mock Data Generator for OKX Trade Simulator

This module provides mock order book data for testing when
the real WebSocket endpoint is not available.
"""

import time
import random
import json
import asyncio
import logging
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime, timezone

# Configure logging
logger = logging.getLogger("mock_data_generator")

class MockDataGenerator:
    """
    Generates mock order book data for testing the OKX Trade Simulator.
    """
    
    def __init__(self, callback: Callable[[Dict[str, Any]], None], symbol: str = "BTC-USDT-SWAP"):
        """
        Initialize the mock data generator.
        
        Args:
            callback: Function to call with generated data
            symbol: Trading symbol to generate data for
        """
        self.callback = callback
        self.symbol = symbol
        self.is_running = False
        self.task = None
        
        # Initial price and parameters
        self.current_price = 65000.0  # Starting price for BTC
        self.volatility = 0.001  # Price movement per tick
        self.spread_percentage = 0.01  # 0.01% spread
        self.depth_decay = 0.2  # How quickly liquidity decays from best price
        self.tick_interval = 0.5  # Seconds between ticks
        
        logger.info(f"Mock data generator initialized for {symbol}")
    
    async def start(self):
        """Start generating mock data."""
        if self.is_running:
            logger.warning("Mock data generator is already running")
            return
            
        self.is_running = True
        self.task = asyncio.create_task(self._generate_data())
        logger.info("Mock data generator started")
    
    async def stop(self):
        """Stop generating mock data."""
        self.is_running = False
        
        if self.task:
            try:
                self.task.cancel()
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                pass
            
        logger.info("Mock data generator stopped")
    
    async def _generate_data(self):
        """Generate mock order book data at regular intervals."""
        while self.is_running:
            try:
                # Update the current price with random walk
                price_change = random.normalvariate(0, self.volatility) * self.current_price
                self.current_price += price_change
                
                # Generate order book data
                data = self._generate_order_book()
                
                # Call the callback with the generated data
                self.callback(data)
                
                # Wait for the next tick
                await asyncio.sleep(self.tick_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error generating mock data: {str(e)}")
                await asyncio.sleep(1)  # Wait a bit longer on error
    
    def _generate_order_book(self) -> Dict[str, Any]:
        """
        Generate a mock order book.
        
        Returns:
            Dict with order book data
        """
        # Calculate spread
        spread = self.current_price * self.spread_percentage / 100
        
        # Calculate best bid and ask prices
        best_bid = self.current_price - spread / 2
        best_ask = self.current_price + spread / 2
        
        # Generate bids (buy orders)
        bids = []
        current_bid = best_bid
        for i in range(20):  # Generate 20 price levels
            price = round(current_bid, 2)
            
            # Size increases for better prices (lower index)
            base_size = random.uniform(5.0, 50.0) if i < 5 else random.uniform(0.5, 10.0)
            size = round(base_size * (1 - i * self.depth_decay / 20), 8)
            
            if size <= 0:
                size = 0.01
                
            bids.append([str(price), str(size)])
            
            # Price gaps increase as we move away from the best price
            price_gap = random.uniform(0.1, 0.5) if i < 5 else random.uniform(0.5, 2.0)
            current_bid -= price_gap
        
        # Generate asks (sell orders)
        asks = []
        current_ask = best_ask
        for i in range(20):  # Generate 20 price levels
            price = round(current_ask, 2)
            
            # Size increases for better prices (lower index)
            base_size = random.uniform(5.0, 50.0) if i < 5 else random.uniform(0.5, 10.0)
            size = round(base_size * (1 - i * self.depth_decay / 20), 8)
            
            if size <= 0:
                size = 0.01
                
            asks.append([str(price), str(size)])
            
            # Price gaps increase as we move away from the best price
            price_gap = random.uniform(0.1, 0.5) if i < 5 else random.uniform(0.5, 2.0)
            current_ask += price_gap
        
        # Create timestamp in ISO format with UTC timezone
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Create order book data
        order_book = {
            "timestamp": timestamp,
            "exchange": "OKX",
            "symbol": self.symbol,
            "asks": asks,
            "bids": bids
        }
        
        # Log sample of the generated data
        logger.info(f"Generated mock order book with {len(bids)} bids and {len(asks)} asks")
        logger.info(f"Best bid: {bids[0][0]} @ {bids[0][1]}, Best ask: {asks[0][0]} @ {asks[0][1]}")
        
        return order_book
