#!/usr/bin/env python3
"""
Real-time Example for OKX Trade Simulator

This script demonstrates how to use the OKX Trade Simulator in real-time mode
with live market data.
"""

import sys
import os
import json
import asyncio
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import signal

# Add the parent directory to the path so we can import the src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.simulation_engine import SimulationEngine
from src.data.orderbook import OrderBook
from src.models.fee_model import FeeModel
from src.models.slippage_model import SlippageModel
from src.models.market_impact_model import AlmgrenChrissModel
from src.models.maker_taker_model import MakerTakerModel
from src.utils.performance import PerformanceMonitor
from src.websocket.connector import WebSocketConnector
from src.utils.config import Config


class RealTimeSimulator:
    """Real-time simulator that connects to live market data."""
    
    def __init__(self, config_path='config.json'):
        """
        Initialize the real-time simulator.
        
        Args:
            config_path (str): Path to the configuration file
        """
        # Load configuration
        self.config = Config()
        self.config.load(config_path)
        
        # Initialize components
        self.order_book = OrderBook()
        self.fee_model = FeeModel()
        self.slippage_model = SlippageModel()
        self.market_impact_model = AlmgrenChrissModel()
        self.maker_taker_model = MakerTakerModel()
        self.performance_monitor = PerformanceMonitor()
        
        # Initialize simulation engine
        self.simulation_engine = SimulationEngine(
            self.order_book,
            self.fee_model,
            self.slippage_model,
            self.market_impact_model,
            self.maker_taker_model,
            self.performance_monitor
        )
        
        # Initialize WebSocket connector
        self.websocket_connector = WebSocketConnector()
        self.websocket_connector.on_message = self.on_websocket_message
        self.websocket_connector.on_error = self.on_websocket_error
        self.websocket_connector.on_close = self.on_websocket_close
        self.websocket_connector.on_open = self.on_websocket_open
        
        # Initialize result storage
        self.results = []
        self.running = False
        
        # Set up event loop
        self.loop = asyncio.get_event_loop()
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, sig, frame):
        """Handle termination signals."""
        print("\nShutting down gracefully...")
        self.stop()
        
        # Save results if available
        if self.results:
            self.save_results('simulation_results.csv')
            self.analyze_results()
        
        sys.exit(0)
    
    def set_parameters(self, params):
        """
        Set simulation parameters.
        
        Args:
            params (dict): Simulation parameters
        """
        self.simulation_engine.set_parameters(params)
    
    async def start(self, instrument):
        """
        Start the real-time simulation.
        
        Args:
            instrument (str): Instrument to simulate, e.g., 'BTC-USDT-SWAP'
        """
        self.running = True
        print(f"Starting real-time simulation for {instrument}...")
        
        # Connect to WebSocket
        await self.websocket_connector.connect()
        
        # Subscribe to order book channel
        await self.websocket_connector.subscribe("books", instrument)
        
        # Keep the connection alive
        while self.running:
            await asyncio.sleep(1)
    
    def stop(self):
        """Stop the real-time simulation."""
        self.running = False
        asyncio.run_coroutine_threadsafe(self.websocket_connector.disconnect(), self.loop)
        print("Real-time simulation stopped.")
    
    def on_websocket_message(self, message):
        """
        Handle WebSocket messages.
        
        Args:
            message (dict): WebSocket message
        """
        # Record tick received for performance monitoring
        self.performance_monitor.record_tick_received()
        
        # Process the message
        if 'data' in message:
            # Extract order book data
            order_book_data = {
                'timestamp': message.get('ts', ''),
                'exchange': 'OKX',
                'symbol': message.get('arg', {}).get('instId', ''),
                'asks': message.get('data', [{}])[0].get('asks', []),
                'bids': message.get('data', [{}])[0].get('bids', [])
            }
            
            # Update the order book
            update_time = self.order_book.update(order_book_data)
            
            # Record order book update time for performance monitoring
            self.performance_monitor.record_orderbook_updated(update_time)
            
            # Process the tick in the simulation engine
            self.simulation_engine.process_tick(order_book_data)
            
            # Get simulation results
            result = self.simulation_engine.get_current_results()
            self.results.append(result)
            
            # Print current results
            self.print_current_results(result)
    
    def on_websocket_error(self, error):
        """
        Handle WebSocket errors.
        
        Args:
            error (Exception): WebSocket error
        """
        print(f"WebSocket error: {error}")
    
    def on_websocket_close(self):
        """Handle WebSocket close events."""
        print("WebSocket connection closed")
    
    def on_websocket_open(self):
        """Handle WebSocket open events."""
        print("WebSocket connection opened")
    
    def print_current_results(self, result):
        """
        Print current simulation results.
        
        Args:
            result (dict): Simulation result
        """
        # Clear the console
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Print header
        print("=" * 80)
        print(f"OKX Trade Simulator - Real-time Mode")
        print("=" * 80)
        
        # Print current time
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Current Time: {current_time}")
        
        # Print market data
        print(f"\nMarket Data:")
        print(f"  Mid Price: ${result['mid_price']:.2f}")
        print(f"  Execution Price: ${result['execution_price']:.2f}")
        
        # Print simulation parameters
        print(f"\nSimulation Parameters:")
        print(f"  Order Type: {self.simulation_engine.order_type}")
        print(f"  Quantity: ${self.simulation_engine.quantity_usd:.2f}")
        print(f"  Direction: {'Buy' if self.simulation_engine.is_buy else 'Sell'}")
        
        # Print simulation results
        print(f"\nSimulation Results:")
        print(f"  Slippage: {result['slippage_percentage'] * 100:.4f}%")
        print(f"  Market Impact: {result['market_impact_percentage'] * 100:.4f}%")
        print(f"  Maker Proportion: {result['maker_proportion'] * 100:.2f}%")
        print(f"  Fees: ${result['fees']:.2f}")
        print(f"  Total Cost: ${result['total_cost']:.2f} ({result['total_cost_percentage']:.4f}%)")
        
        # Print performance metrics
        print(f"\nPerformance Metrics:")
        latency = self.performance_monitor.get_average_latency()
        throughput = self.performance_monitor.get_throughput()
        print(f"  Average Latency: {latency:.2f} ms")
        print(f"  Throughput: {throughput:.2f} messages/sec")
        
        # Print instructions
        print("\nPress Ctrl+C to stop the simulation and save results")
    
    def save_results(self, file_path):
        """
        Save simulation results to a CSV file.
        
        Args:
            file_path (str): Path to save the results
        """
        # Convert results to DataFrame
        df = pd.DataFrame(self.results)
        
        # Save to CSV
        df.to_csv(file_path, index=False)
        print(f"Results saved to {file_path}")
    
    def analyze_results(self):
        """Analyze and visualize simulation results."""
        if not self.results:
            print("No results to analyze.")
            return
        
        # Convert results to DataFrame
        df = pd.DataFrame(self.results)
        
        # Calculate statistics
        avg_slippage = df['slippage_percentage'].mean() * 100
        avg_market_impact = df['market_impact_percentage'].mean() * 100
        avg_maker_proportion = df['maker_proportion'].mean() * 100
        avg_total_cost = df['total_cost_percentage'].mean()
        
        # Print statistics
        print("\nSimulation Results Summary:")
        print(f"Average Slippage: {avg_slippage:.4f}%")
        print(f"Average Market Impact: {avg_market_impact:.4f}%")
        print(f"Average Maker Proportion: {avg_maker_proportion:.2f}%")
        print(f"Average Total Cost: {avg_total_cost:.4f}%")
        
        # Plot results
        plt.figure(figsize=(12, 8))
        
        # Plot execution price
        plt.subplot(2, 2, 1)
        plt.plot(df['execution_price'])
        plt.title('Execution Price')
        plt.xlabel('Time')
        plt.ylabel('Price')
        
        # Plot slippage and market impact
        plt.subplot(2, 2, 2)
        plt.plot(df['slippage_percentage'] * 100, label='Slippage (%)')
        plt.plot(df['market_impact_percentage'] * 100, label='Market Impact (%)')
        plt.title('Slippage and Market Impact')
        plt.xlabel('Time')
        plt.ylabel('Percentage (%)')
        plt.legend()
        
        # Plot maker proportion
        plt.subplot(2, 2, 3)
        plt.plot(df['maker_proportion'] * 100)
        plt.title('Maker Proportion')
        plt.xlabel('Time')
        plt.ylabel('Percentage (%)')
        
        # Plot total cost
        plt.subplot(2, 2, 4)
        plt.plot(df['total_cost_percentage'])
        plt.title('Total Cost')
        plt.xlabel('Time')
        plt.ylabel('Percentage (%)')
        
        plt.tight_layout()
        plt.savefig('realtime_results.png')
        print("Results visualization saved to realtime_results.png")


def main():
    """Main entry point for the real-time example."""
    # Create real-time simulator
    simulator = RealTimeSimulator()
    
    # Define simulation parameters
    simulation_params = {
        'exchange': 'OKX',
        'fee_tier': 0,
        'order_type': 'limit',
        'quantity_usd': 10000.0,
        'is_buy': True,
        'avg_daily_volume': 1000000.0,
        'volatility': 0.02
    }
    
    # Set simulation parameters
    simulator.set_parameters(simulation_params)
    
    # Define instrument to simulate
    instrument = "BTC-USDT-SWAP"
    
    # Run the simulation
    try:
        simulator.loop.run_until_complete(simulator.start(instrument))
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user.")
    finally:
        simulator.stop()
        simulator.loop.close()


if __name__ == "__main__":
    main()
