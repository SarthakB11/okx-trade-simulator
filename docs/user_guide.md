# OKX Trade Simulator User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [Configuration](#configuration)
5. [Using the GUI](#using-the-gui)
6. [Using the API](#using-the-api)
7. [Examples](#examples)
8. [Troubleshooting](#troubleshooting)
9. [Performance Optimization](#performance-optimization)

## Introduction

The OKX Trade Simulator is a high-performance tool designed to estimate transaction costs and market impact for cryptocurrency trading. It leverages real-time market data from OKX exchange to provide accurate simulations of trade execution.

Key features include:
- Real-time market data processing via WebSocket connections
- Accurate order book management
- Multiple financial models for fee calculation, slippage estimation, and market impact
- User-friendly GUI for interactive use
- Comprehensive API for programmatic use
- Performance monitoring and optimization

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/yourusername/okx-trade-simulator.git
cd okx-trade-simulator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Getting Started

### Running the Application

To start the OKX Trade Simulator with the graphical user interface:

```bash
python main.py
```

### Running Tests

To run the test suite:

```bash
./run_tests.py
```

To run a specific test:

```bash
./run_tests.py test_orderbook
```

## Configuration

The OKX Trade Simulator can be configured using the `config.json` file. This file contains settings for:

- WebSocket connections
- Exchange parameters
- Simulation defaults
- UI preferences
- Logging settings
- Performance monitoring

Example configuration:

```json
{
    "websocket": {
        "okx": {
            "public_url": "wss://ws.okx.com:8443/ws/v5/public",
            "private_url": "wss://ws.okx.com:8443/ws/v5/private",
            "reconnect_interval": 5,
            "ping_interval": 30
        }
    },
    "exchange": {
        "okx": {
            "default_fee_tier": 0,
            "default_instruments": ["BTC-USDT-SWAP", "ETH-USDT-SWAP", "SOL-USDT-SWAP"]
        }
    },
    "simulation": {
        "default_order_type": "limit",
        "default_quantity_usd": 10000.0,
        "default_avg_daily_volume": 1000000.0,
        "default_volatility": 0.02
    }
}
```

## Using the GUI

The GUI provides an intuitive interface for interacting with the simulator:

1. **Input Panel**: Set simulation parameters
   - Exchange selection
   - Fee tier
   - Order type (limit, market)
   - Quantity (USD)
   - Direction (buy, sell)
   - Instrument selection

2. **Output Panel**: View simulation results
   - Execution price
   - Slippage
   - Market impact
   - Maker/taker proportion
   - Fees
   - Total cost

3. **Performance Panel**: Monitor system performance
   - Latency
   - Throughput
   - Memory usage

## Using the API

The OKX Trade Simulator can be used programmatically through its API:

### Basic Usage

```python
from src.models.simulation_engine import SimulationEngine
from src.data.orderbook import OrderBook
from src.models.fee_model import FeeModel
from src.models.slippage_model import SlippageModel
from src.models.market_impact_model import AlmgrenChrissModel
from src.models.maker_taker_model import MakerTakerModel
from src.utils.performance import PerformanceMonitor

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
simulation_params = {
    'exchange': 'OKX',
    'fee_tier': 0,
    'order_type': 'limit',
    'quantity_usd': 10000.0,
    'is_buy': True,
    'avg_daily_volume': 1000000.0,
    'volatility': 0.02
}
simulation_engine.set_parameters(simulation_params)

# Process market data
simulation_engine.process_tick(order_book_data)

# Get simulation results
results = simulation_engine.get_current_results()
```

### WebSocket Connection

```python
from src.websocket.connector import WebSocketConnector

# Initialize WebSocket connector
websocket_connector = WebSocketConnector()

# Set callbacks
websocket_connector.on_message = on_message_callback
websocket_connector.on_error = on_error_callback
websocket_connector.on_close = on_close_callback
websocket_connector.on_open = on_open_callback

# Connect to WebSocket
await websocket_connector.connect()

# Subscribe to order book channel
await websocket_connector.subscribe("books", "BTC-USDT-SWAP")
```

## Examples

The OKX Trade Simulator includes example scripts to demonstrate its usage:

### Backtesting Example

The `examples/backtest_example.py` script demonstrates how to use the simulator for backtesting with historical market data:

```bash
./examples/backtest_example.py
```

This script:
1. Generates or loads sample historical data
2. Runs a simulation with specified parameters
3. Analyzes and visualizes the results

### Real-time Example

The `examples/realtime_example.py` script demonstrates how to use the simulator in real-time mode with live market data:

```bash
./examples/realtime_example.py
```

This script:
1. Connects to the OKX WebSocket API
2. Processes real-time market data
3. Displays simulation results in real-time
4. Saves and analyzes results when stopped

## Troubleshooting

### Common Issues

1. **WebSocket Connection Errors**
   - Check your internet connection
   - Verify that the WebSocket URL in the configuration is correct
   - Ensure that you're not being rate-limited by the exchange

2. **Performance Issues**
   - Check the Performance Panel for high latency
   - Consider reducing the number of instruments being tracked
   - Optimize your hardware (more RAM, faster CPU)

3. **Inaccurate Results**
   - Ensure that your fee tier is set correctly
   - Verify that the order book data is being received properly
   - Check that the models are calibrated correctly

### Logging

The OKX Trade Simulator logs information to `okx_simulator.log`. Check this file for detailed information about errors and application behavior.

## Performance Optimization

To optimize the performance of the OKX Trade Simulator:

1. **Reduce Data Processing**
   - Subscribe only to the instruments you need
   - Use a lower refresh rate for the UI

2. **Hardware Optimization**
   - Run on a machine with sufficient RAM (8GB+)
   - Use a machine with a fast CPU
   - Ensure good network connectivity

3. **Code Optimization**
   - Profile the application to identify bottlenecks
   - Optimize critical code paths
   - Use more efficient data structures where appropriate
