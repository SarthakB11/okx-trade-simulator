#!/usr/bin/env python3
"""
Backtest Example for OKX Trade Simulator

This script demonstrates how to use the OKX Trade Simulator for backtesting
with historical market data.
"""

import sys
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.simulation_engine import SimulationEngine
from src.data.orderbook import OrderBook
from src.models.fee_model import FeeModel
from src.models.slippage_model import SlippageModel
from src.models.market_impact_model import AlmgrenChrissModel
from src.models.maker_taker_model import MakerTakerModel
from src.utils.performance import PerformanceMonitor


def load_historical_data(file_path):
    """
    Load historical order book data from a CSV file.
    
    Args:
        file_path (str): Path to the CSV file containing historical data
        
    Returns:
        list: List of order book snapshots
    """
    # Load data from CSV
    df = pd.read_csv(file_path)
    
    # Convert data to order book snapshots
    snapshots = []
    for _, row in df.iterrows():
        # Parse asks and bids from the CSV
        asks = json.loads(row['asks'])
        bids = json.loads(row['bids'])
        
        # Create order book snapshot
        snapshot = {
            'timestamp': row['timestamp'],
            'exchange': 'OKX',
            'symbol': row['symbol'],
            'asks': asks,
            'bids': bids
        }
        
        snapshots.append(snapshot)
    
    return snapshots


def run_backtest(historical_data, simulation_params):
    """
    Run a backtest using historical data and simulation parameters.
    
    Args:
        historical_data (list): List of order book snapshots
        simulation_params (dict): Simulation parameters
        
    Returns:
        list: List of simulation results
    """
    # Initialize components
    order_book = OrderBook()
    fee_model = FeeModel()
    slippage_model = SlippageModel()
    market_impact_model = AlmgrenChrissModel()
    maker_taker_model = MakerTakerModel()
    performance_monitor = PerformanceMonitor()
    
    # Initialize simulation engine
    simulation_engine = SimulationEngine(
        order_book,
        fee_model,
        slippage_model,
        market_impact_model,
        maker_taker_model,
        performance_monitor
    )
    
    # Set simulation parameters
    simulation_engine.set_parameters(simulation_params)
    
    # Run simulation on historical data
    results = []
    for snapshot in historical_data:
        # Process each order book snapshot
        simulation_engine.process_tick(snapshot)
        
        # Get simulation results
        result = simulation_engine.get_current_results()
        results.append(result)
    
    return results


def analyze_results(results):
    """
    Analyze and visualize backtest results.
    
    Args:
        results (list): List of simulation results
    """
    # Convert results to DataFrame
    df = pd.DataFrame(results)
    
    # Calculate statistics
    avg_slippage = df['slippage_percentage'].mean() * 100
    avg_market_impact = df['market_impact_percentage'].mean() * 100
    avg_maker_proportion = df['maker_proportion'].mean() * 100
    avg_total_cost = df['total_cost_percentage'].mean()
    
    # Print statistics
    print("\nBacktest Results:")
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
    plt.savefig('backtest_results.png')
    plt.show()


def generate_sample_data(output_file, num_samples=100):
    """
    Generate sample historical data for testing.
    
    Args:
        output_file (str): Path to save the generated data
        num_samples (int): Number of samples to generate
    """
    # Generate timestamps
    start_time = datetime(2025, 5, 1, 0, 0, 0)
    timestamps = [
        (start_time + timedelta(minutes=i)).strftime('%Y-%m-%dT%H:%M:%SZ')
        for i in range(num_samples)
    ]
    
    # Generate order book data
    data = []
    base_price = 95000.0
    
    for i, timestamp in enumerate(timestamps):
        # Simulate price movement
        price_change = (i - num_samples / 2) / 10
        mid_price = base_price + price_change
        
        # Generate asks
        asks = [
            [str(mid_price + 0.1 * j), str(10.0 - j * 0.5)] 
            for j in range(1, 6)
        ]
        
        # Generate bids
        bids = [
            [str(mid_price - 0.1 * j), str(10.0 - j * 0.5)] 
            for j in range(1, 6)
        ]
        
        # Create row
        row = {
            'timestamp': timestamp,
            'symbol': 'BTC-USDT-SWAP',
            'asks': json.dumps(asks),
            'bids': json.dumps(bids)
        }
        
        data.append(row)
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)
    print(f"Generated sample data saved to {output_file}")


def main():
    """Main entry point for the backtest example."""
    # Check if sample data exists, if not generate it
    sample_data_file = 'sample_historical_data.csv'
    if not os.path.exists(sample_data_file):
        generate_sample_data(sample_data_file)
    
    # Load historical data
    historical_data = load_historical_data(sample_data_file)
    
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
    
    # Run backtest
    print(f"Running backtest with {len(historical_data)} data points...")
    results = run_backtest(historical_data, simulation_params)
    
    # Analyze results
    analyze_results(results)


if __name__ == "__main__":
    main()
