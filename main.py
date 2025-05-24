#!/usr/bin/env python3
"""
OKX Trade Simulator - Main Application

This script launches the OKX Trade Simulator application, which provides
real-time market data analysis and trade cost estimation.
"""

import sys
import asyncio
import logging
import json
from PyQt6.QtWidgets import QApplication

from src.ui.main_window import MainWindow
from src.websocket.connector import WebSocketConnector
from src.data.orderbook import OrderBook
from src.models.simulation_engine import SimulationEngine
from src.models.fee_model import FeeModel
from src.models.slippage_model import SlippageModel
from src.models.market_impact_model import AlmgrenChrissModel
from src.models.maker_taker_model import MakerTakerModel
from src.utils.performance import PerformanceMonitor
from src.utils.config import Config
from src.data.mock_data_generator import MockDataGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('okx_simulator.log')
    ]
)

logger = logging.getLogger(__name__)


class Application:
    """Main application class for the OKX Trade Simulator."""

    def __init__(self):
        """Initialize the application."""
        self.app = QApplication(sys.argv)
        self.config = Config()
        self.config.load()
        
        # Initialize components
        self.order_book = OrderBook()
        self.fee_model = FeeModel()
        self.slippage_model = SlippageModel()
        self.market_impact_model = AlmgrenChrissModel()
        self.maker_taker_model = MakerTakerModel()
        self.performance_monitor = PerformanceMonitor()
        
        # Initialize simulation engine
        self.simulation_id = "main-simulation"
        self.simulation_params = {
            'exchange': 'OKX',
            'spotAsset': 'BTC-USDT',
            'orderType': 'limit',
            'quantityUSD': 10000.0,
            'volatility': 0.02,
            'feeTier': 'Tier 1'
        }
        
        # Create callback function for simulation results
        def simulation_output_callback(output):
            # This will be called when the simulation produces output
            if hasattr(self.simulation_engine, 'simulation_result'):
                self.simulation_engine.simulation_result.emit(output)
        
        self.simulation_engine = SimulationEngine(
            simulation_id=self.simulation_id,
            parameters=self.simulation_params,
            output_callback=simulation_output_callback
        )
        
        # Initialize WebSocket connector for OKX API
        # Use the endpoint from the project requirements
        websocket_uri = "wss://ws.okx.com:8443/ws/v5/public"
        
        # Create a callback function for WebSocket messages
        def websocket_message_callback(message):
            self.on_websocket_message(message)
        
        self.websocket_connector = WebSocketConnector(
            uri=websocket_uri,
            on_message_callback=websocket_message_callback
        )
        
        # Connection status
        self.is_connected = False
        
        # Initialize main window
        self.main_window = MainWindow()
        
        # Connect our callbacks to the main window
        self.main_window.on_simulation_start = self.start_simulation
        self.main_window.on_simulation_stop = self.stop_simulation
        
        # Connect signals and slots
        self.connect_signals()
        
        # Set up event loop for asyncio
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def connect_signals(self):
        """Connect signals and slots."""
        # We've already connected the main callbacks in __init__
        # No need for signal/slot connections since we're using direct function calls
        pass

    def start_simulation(self, params):
        """Start the simulation with the given parameters."""
        logger.info(f"Starting simulation with parameters: {params}")
        
        # Update simulation parameters
        self.simulation_engine.parameters = params
        
        # Get the instrument from parameters
        instrument = params.get('spotAsset', 'BTC-USDT')
        if params.get('exchange') == 'OKX':
            # For OKX, we use the SWAP contract as specified in the requirements
            instrument += '-SWAP'
        
        # Update the mock data generator with the correct symbol
        self.mock_data_generator.symbol = instrument
        
        # Connect to WebSocket or start mock data generator
        asyncio.run_coroutine_threadsafe(self.connect_websocket(instrument), self.loop)

    def stop_simulation(self):
        """Stop the simulation."""
        logger.info("Stopping simulation")
        
        # Disconnect from WebSocket
        asyncio.run_coroutine_threadsafe(self.websocket_connector.disconnect(), self.loop)
        
        # Reset connection status
        self.is_connected = False
        
        # Update UI
        self.main_window.update_connection_status(False)
        self.main_window.status_bar.showMessage("Simulation stopped")

    def change_instrument(self, instrument):
        """Change the instrument being simulated."""
        logger.info(f"Changing instrument to {instrument}")
        
        # Disconnect current WebSocket
        asyncio.run_coroutine_threadsafe(self.websocket_connector.disconnect(), self.loop)
        
        # Connect to new instrument
        asyncio.run_coroutine_threadsafe(self.connect_websocket(instrument), self.loop)

    async def connect_websocket(self, instrument):
        """Connect to the WebSocket for order book data."""
        try:
            logger.info(f"Connecting to WebSocket for instrument: {instrument}")
            
            # Connect to the WebSocket
            connection_success = await self.websocket_connector.connect()
            
            if not connection_success:
                logger.error(f"Failed to connect to WebSocket endpoint")
                self.main_window.update_connection_status(False)
                self.main_window.status_bar.showMessage(f"Failed to connect to WebSocket")
                return
            
            # Subscribe to the books channel for the specified instrument
            logger.info(f"Subscribing to books channel for {instrument}")
            
            # Create subscription message for OKX API
            subscription_success = await self.websocket_connector.subscribe("books", instrument)
            
            if subscription_success:
                logger.info(f"Successfully subscribed to {instrument}")
                self.is_connected = True
                
                # Update the UI to show we're connected
                self.main_window.update_connection_status(True)
                self.main_window.status_bar.showMessage(f"Connected to order book stream for {instrument}")
            else:
                logger.error(f"Failed to subscribe to {instrument}")
                self.main_window.update_connection_status(False)
                self.main_window.status_bar.showMessage(f"Failed to subscribe to {instrument}")
                
                # Disconnect since subscription failed
                await self.websocket_connector.disconnect()
            
        except Exception as e:
            logger.error(f"Error connecting to WebSocket: {str(e)}")
            self.main_window.update_connection_status(False)
            self.main_window.status_bar.showMessage(f"Connection error: {str(e)}")

    def on_websocket_message(self, message):
        """Handle WebSocket messages."""
        # Process the message
        try:
            # Parse the message if it's a string
            if isinstance(message, str):
                try:
                    message = json.loads(message)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse WebSocket message: {message}")
                    return
            
            # Check for OKX API specific messages
            if isinstance(message, dict):
                # Handle subscription confirmation
                if message.get('event') == 'subscribe':
                    logger.info(f"Subscription confirmed: {message}")
                    return
                
                # Handle error messages
                if message.get('event') == 'error':
                    logger.error(f"WebSocket error: {message}")
                    self.main_window.status_bar.showMessage(f"WebSocket error: {message.get('msg', 'Unknown error')}")
                    return
                
                # Handle OKX API data format
                if 'data' in message and 'arg' in message:
                    # Extract data from OKX format
                    arg = message.get('arg', {})
                    channel = arg.get('channel')
                    instrument = arg.get('instId')
                    
                    if channel == 'books':
                        # Extract order book data
                        data_items = message.get('data', [])
                        if data_items and len(data_items) > 0:
                            data = data_items[0]  # Get the first data item
                            
                            # Create order book data structure
                            order_book_data = {
                                'timestamp': message.get('ts', time.time() * 1000),  # OKX uses milliseconds
                                'exchange': 'OKX',
                                'symbol': instrument,
                                'asks': data.get('asks', []),
                                'bids': data.get('bids', [])
                            }
                            
                            # Log the data structure
                            ask_count = len(order_book_data.get('asks', []))
                            bid_count = len(order_book_data.get('bids', []))
                            logger.info(f"Processing order book with {ask_count} asks and {bid_count} bids")
                            
                            if ask_count > 0 and bid_count > 0:
                                # Process the tick in the simulation engine
                                result = self.simulation_engine.process_tick(order_book_data)
                                
                                # Update the UI with the result
                                self.main_window.update_simulation_output(result)
                            else:
                                logger.warning(f"Received empty order book data")
                    else:
                        logger.debug(f"Received data for channel: {channel}")
                else:
                    logger.debug(f"Received message: {message}")
            else:
                logger.warning(f"Received non-dict message: {type(message)}")
                
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}")
            self.main_window.status_bar.showMessage(f"Error: {str(e)}")
            # Don't update connection status for processing errors
            # self.main_window.update_connection_status(False)

    def on_websocket_error(self, error):
        """Handle WebSocket errors."""
        logger.error(f"WebSocket error: {error}")
        # Update the UI to show the error
        self.main_window.status_bar.showMessage(f"WebSocket error: {error}")
        self.main_window.update_connection_status(False)

    def on_websocket_close(self):
        """Handle WebSocket close events."""
        logger.info("WebSocket connection closed")
        # Update the UI to show we're disconnected
        self.main_window.status_bar.showMessage("WebSocket connection closed")
        self.main_window.update_connection_status(False)

    def on_websocket_open(self):
        """Handle WebSocket open events."""
        logger.info("WebSocket connection opened")
        # Update the UI to show we're connected
        self.main_window.status_bar.showMessage("WebSocket connection opened")
        self.main_window.update_connection_status(True)

    def run(self):
        """Run the application."""
        # Show the main window
        self.main_window.show()
        
        # Start the asyncio event loop in a separate thread
        import threading
        threading.Thread(target=self._run_event_loop, daemon=True).start()
        
        # Start the Qt event loop
        return self.app.exec()

    def _run_event_loop(self):
        """Run the asyncio event loop."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()


def main():
    """Main entry point for the application."""
    try:
        app = Application()
        sys.exit(app.run())
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
