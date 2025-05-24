#!/usr/bin/env python3
"""
Comprehensive Example for OKX Trade Simulator

This script demonstrates how to use the OKX Trade Simulator with both
real WebSocket data and mock data. It provides a command-line interface
to control the simulation parameters and view the results.
"""

import sys
import os
import json
import asyncio
import logging
import argparse
from datetime import datetime
import signal
import time

# Add the parent directory to the path so we can import the src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.simulation_engine import SimulationEngine
from src.websocket.connector import WebSocketConnector
from src.data.mock_data_generator import MockDataGenerator
from src.utils.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('comprehensive_example.log')
    ]
)

logger = logging.getLogger(__name__)

class SimulatorExample:
    """
    Example application for the OKX Trade Simulator.
    Demonstrates how to use the simulator with both real and mock data.
    """
    
    def __init__(self, use_mock_data: bool = False):
        """
        Initialize the simulator example.
        
        Args:
            use_mock_data: Whether to use mock data instead of real WebSocket data
        """
        # Load configuration
        self.config = Config()
        
        # Set up simulation parameters
        self.simulation_params = {
            'exchange': 'OKX',
            'spotAsset': 'BTC-USDT',
            'orderType': 'market',
            'quantityUSD': 100.0,
            'volatility': 0.02,
            'feeTier': 'Tier 1'
        }
        
        # Initialize simulation engine
        self.simulation_engine = SimulationEngine(
            simulation_id="example-simulation",
            parameters=self.simulation_params,
            output_callback=self.on_simulation_output
        )
        
        # Flag to control the simulation
        self.is_running = False
        self.use_mock_data = use_mock_data
        
        # Store results
        self.results = []
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info(f"Simulator example initialized with {'mock' if use_mock_data else 'real'} data")
    
    def signal_handler(self, sig, frame):
        """Handle signals for graceful shutdown."""
        logger.info(f"Received signal {sig}, shutting down...")
        self.stop()
        sys.exit(0)
    
    async def start(self):
        """Start the simulation."""
        if self.is_running:
            logger.warning("Simulation is already running")
            return
        
        self.is_running = True
        logger.info(f"Starting simulation with parameters: {self.simulation_params}")
        
        # Get the instrument from parameters
        instrument = self.simulation_params.get('spotAsset', 'BTC-USDT')
        if self.simulation_params.get('exchange') == 'OKX':
            instrument += '-SWAP'
        
        try:
            if self.use_mock_data:
                # Use mock data generator
                logger.info("Using mock data generator")
                self.data_source = MockDataGenerator(
                    callback=self.on_data_received,
                    symbol=instrument
                )
                await self.data_source.start()
            else:
                # Use real WebSocket connection
                logger.info(f"Connecting to WebSocket for {instrument}")
                websocket_uri = "wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP"
                
                self.data_source = WebSocketConnector(
                    uri=websocket_uri,
                    on_message_callback=self.on_data_received
                )
                
                await self.data_source.connect()
                
                # Try to send a subscription message
                try:
                    subscription_message = {
                        "op": "subscribe",
                        "args": [{
                            "channel": "books",
                            "instId": instrument
                        }]
                    }
                    await self.data_source.send(subscription_message)
                    logger.info(f"Sent subscription message for {instrument}")
                except Exception as e:
                    logger.warning(f"Failed to send subscription message: {str(e)}")
            
            logger.info("Simulation started successfully")
            
            # Keep the simulation running until stopped
            while self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error starting simulation: {str(e)}")
            self.is_running = False
    
    async def stop(self):
        """Stop the simulation."""
        if not self.is_running:
            logger.warning("Simulation is not running")
            return
        
        self.is_running = False
        logger.info("Stopping simulation...")
        
        try:
            if self.use_mock_data:
                await self.data_source.stop()
            else:
                await self.data_source.disconnect()
                
            logger.info("Simulation stopped successfully")
            
            # Print summary
            self.print_summary()
            
        except Exception as e:
            logger.error(f"Error stopping simulation: {str(e)}")
    
    def on_data_received(self, message):
        """
        Handle data received from WebSocket or mock data generator.
        
        Args:
            message: The data message
        """
        try:
            # Parse the message if it's a string
            if isinstance(message, str):
                try:
                    message = json.loads(message)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse message: {message}")
                    return
            
            # Handle different message formats
            order_book_data = None
            
            # Format 1: Direct order book data (expected from the project endpoint or mock generator)
            if all(key in message for key in ['timestamp', 'exchange', 'symbol', 'asks', 'bids']):
                order_book_data = message
                logger.debug(f"Received direct order book data format")
            
            # Format 2: OKX WebSocket API format
            elif 'data' in message:
                # Extract order book data from OKX format
                order_book_data = {
                    'timestamp': message.get('ts', ''),
                    'exchange': 'OKX',
                    'symbol': message.get('arg', {}).get('instId', ''),
                    'asks': message.get('data', [{}])[0].get('asks', []),
                    'bids': message.get('data', [{}])[0].get('bids', [])
                }
                logger.debug(f"Extracted order book data from OKX format")
            
            # If we have valid order book data, process it
            if order_book_data and order_book_data.get('asks') and order_book_data.get('bids'):
                # Process the tick in the simulation engine
                self.simulation_engine.process_tick(order_book_data)
            else:
                # This might be a control message or other type of message
                logger.debug(f"Received non-order book message: {message}")
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
    def on_simulation_output(self, output):
        """
        Handle simulation output.
        
        Args:
            output: The simulation output
        """
        # Store the result
        self.results.append(output)
        
        # Print the result
        self.print_result(output)
    
    def print_result(self, result):
        """
        Print a simulation result.
        
        Args:
            result: The simulation result
        """
        # Clear the console
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Print header
        print("=" * 80)
        print(f"OKX Trade Simulator - Comprehensive Example")
        print("=" * 80)
        
        # Print current time
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Current Time: {current_time}")
        
        # Print simulation parameters
        print(f"\nSimulation Parameters:")
        for key, value in self.simulation_params.items():
            print(f"  {key}: {value}")
        
        # Print simulation results
        print(f"\nSimulation Results:")
        if 'expectedSlippageUSD' in result:
            print(f"  Expected Slippage: ${result['expectedSlippageUSD']:.2f}")
        if 'expectedFeesUSD' in result:
            print(f"  Expected Fees: ${result['expectedFeesUSD']:.2f}")
        if 'expectedMarketImpactUSD' in result:
            print(f"  Expected Market Impact: ${result['expectedMarketImpactUSD']:.2f}")
        if 'netCostUSD' in result:
            print(f"  Net Cost: ${result['netCostUSD']:.2f}")
        
        # Print maker/taker proportion
        if 'makerTakerProportion' in result:
            maker = result['makerTakerProportion'].get('maker', 0)
            taker = result['makerTakerProportion'].get('taker', 0)
            print(f"  Maker/Taker Proportion: {maker*100:.1f}% / {taker*100:.1f}%")
        
        # Print performance metrics
        if 'performance' in result:
            perf = result['performance']
            print(f"\nPerformance Metrics:")
            if 'averageLatencyMs' in perf:
                print(f"  Average Latency: {perf['averageLatencyMs']:.2f} ms")
            if 'tickCount' in perf:
                print(f"  Tick Count: {perf['tickCount']}")
        
        # Print instructions
        print("\nPress Ctrl+C to stop the simulation")
    
    def print_summary(self):
        """Print a summary of the simulation results."""
        if not self.results:
            logger.info("No results to summarize")
            return
        
        # Calculate averages
        total_slippage = 0
        total_fees = 0
        total_impact = 0
        total_cost = 0
        count = 0
        
        for result in self.results:
            if 'expectedSlippageUSD' in result:
                total_slippage += result['expectedSlippageUSD']
            if 'expectedFeesUSD' in result:
                total_fees += result['expectedFeesUSD']
            if 'expectedMarketImpactUSD' in result:
                total_impact += result['expectedMarketImpactUSD']
            if 'netCostUSD' in result:
                total_cost += result['netCostUSD']
            count += 1
        
        if count > 0:
            avg_slippage = total_slippage / count
            avg_fees = total_fees / count
            avg_impact = total_impact / count
            avg_cost = total_cost / count
            
            print("\n" + "=" * 80)
            print("Simulation Summary:")
            print("=" * 80)
            print(f"  Total Ticks: {count}")
            print(f"  Average Slippage: ${avg_slippage:.2f}")
            print(f"  Average Fees: ${avg_fees:.2f}")
            print(f"  Average Market Impact: ${avg_impact:.2f}")
            print(f"  Average Net Cost: ${avg_cost:.2f}")
            print("=" * 80)


async def main():
    """Main entry point for the example."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='OKX Trade Simulator Example')
    parser.add_argument('--mock', action='store_true', help='Use mock data instead of real WebSocket data')
    parser.add_argument('--quantity', type=float, default=100.0, help='Order quantity in USD')
    parser.add_argument('--volatility', type=float, default=0.02, help='Market volatility parameter')
    parser.add_argument('--fee-tier', type=str, default='Tier 1', help='Fee tier (e.g., Tier 1, Tier 2)')
    args = parser.parse_args()
    
    # Create simulator example
    simulator = SimulatorExample(use_mock_data=args.mock)
    
    # Update parameters from command line
    simulator.simulation_params['quantityUSD'] = args.quantity
    simulator.simulation_params['volatility'] = args.volatility
    simulator.simulation_params['feeTier'] = args.fee_tier
    
    try:
        # Start the simulation
        await simulator.start()
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
    finally:
        # Stop the simulation
        await simulator.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
