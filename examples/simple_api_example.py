#!/usr/bin/env python3
"""
Simple API Example for OKX Trade Simulator

This script demonstrates how to use the OKX Trade Simulator API
without the GUI for programmatic integration.
"""

import sys
import os
import json
import asyncio
import logging
from datetime import datetime

# Add the parent directory to the path so we can import the src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.simulation_engine import SimulationEngine
from src.websocket.connector import WebSocketConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api_example.log')
    ]
)

logger = logging.getLogger(__name__)


class SimpleSimulator:
    """Simple simulator that uses the OKX Trade Simulator API."""
    
    def __init__(self):
        """Initialize the simulator."""
        # Simulation parameters
        self.simulation_id = "api-example"
        self.simulation_params = {
            'exchange': 'OKX',
            'spotAsset': 'BTC-USDT',
            'orderType': 'limit',
            'quantityUSD': 10000.0,
            'volatility': 0.02,
            'feeTier': 'Tier 1'
        }
        
        # Initialize simulation engine
        self.simulation_engine = SimulationEngine(
            simulation_id=self.simulation_id,
            parameters=self.simulation_params,
            output_callback=self.on_simulation_output
        )
        
        # Initialize WebSocket connector
        self.websocket_uri = "wss://ws.okx.com:8443/ws/v5/public"
        self.websocket_connector = WebSocketConnector(
            uri=self.websocket_uri,
            on_message_callback=self.on_websocket_message
        )
        
        # Track results
        self.results = []
        self.running = False
        
    async def start(self, instrument="BTC-USDT-SWAP"):
        """
        Start the simulator.
        
        Args:
            instrument (str): The instrument to simulate
        """
        self.running = True
        logger.info(f"Starting simulation for {instrument}")
        
        try:
            # Connect to WebSocket
            await self.websocket_connector.connect()
            logger.info("Connected to WebSocket")
            
            # Send subscription message
            subscription_message = json.dumps({
                "op": "subscribe",
                "args": [{
                    "channel": "books",
                    "instId": instrument
                }]
            })
            
            logger.info(f"Sending subscription message: {subscription_message}")
            
            # Keep the connection alive
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in simulator: {str(e)}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the simulator."""
        self.running = False
        logger.info("Stopping simulator")
        
        # Disconnect from WebSocket
        await self.websocket_connector.disconnect()
        
        # Print summary of results
        self.print_summary()
    
    def on_websocket_message(self, message):
        """
        Handle WebSocket messages.
        
        Args:
            message: The WebSocket message
        """
        try:
            # Parse the message if it's a string
            if isinstance(message, str):
                try:
                    message = json.loads(message)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse WebSocket message: {message}")
                    return
            
            # Process the message if it contains data
            if 'data' in message:
                # Extract order book data
                order_book_data = {
                    'timestamp': message.get('ts', ''),
                    'exchange': 'OKX',
                    'symbol': message.get('arg', {}).get('instId', ''),
                    'asks': message.get('data', [{}])[0].get('asks', []),
                    'bids': message.get('data', [{}])[0].get('bids', [])
                }
                
                # Process the tick in the simulation engine
                self.simulation_engine.process_tick(order_book_data)
                
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}")
    
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
        print(f"OKX Trade Simulator - API Example")
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
            
            logger.info(f"Simulation Summary:")
            logger.info(f"  Total Ticks: {count}")
            logger.info(f"  Average Slippage: ${avg_slippage:.2f}")
            logger.info(f"  Average Fees: ${avg_fees:.2f}")
            logger.info(f"  Average Market Impact: ${avg_impact:.2f}")
            logger.info(f"  Average Net Cost: ${avg_cost:.2f}")


async def main():
    """Main entry point for the example."""
    # Create simulator
    simulator = SimpleSimulator()
    
    try:
        # Start simulator
        await simulator.start()
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
    finally:
        # Stop simulator
        await simulator.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
