# OKX Trade Simulator

A high-performance trade simulator leveraging real-time market data to estimate transaction costs and market impact for cryptocurrency trading.

## Overview

This application connects to OKX SPOT exchange WebSocket endpoints to stream full L2 orderbook data. It processes this data in real-time to calculate:

- Expected Slippage (using linear/quantile regression)
- Expected Fees (rule-based fee model)
- Expected Market Impact (Almgren-Chriss model)
- Net Cost (Slippage + Fees + Market Impact)
- Maker/Taker proportion (logistic regression)
- Internal Latency (processing time per tick)

## Requirements

- Python 3.8+
- VPN access to OKX (for market data access)
- Dependencies listed in requirements.txt

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Ensure you have VPN access to OKX

## Usage

Run the application:

```
python src/main.py
```

## Project Structure

- `src/`: Source code
  - `models/`: Financial models implementation
  - `ui/`: User interface components
  - `websocket/`: WebSocket connection handling
  - `utils/`: Utility functions
  - `data/`: Data structures and processing

## License

This project is for demonstration purposes only.
