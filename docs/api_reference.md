# OKX Trade Simulator API Reference

This document provides detailed information about the classes and methods available in the OKX Trade Simulator.

## Table of Contents

1. [WebSocket Module](#websocket-module)
2. [Data Module](#data-module)
3. [Models Module](#models-module)
4. [UI Module](#ui-module)
5. [Utils Module](#utils-module)

## WebSocket Module

### WebSocketConnector

The `WebSocketConnector` class manages the connection to the OKX WebSocket API.

#### Methods

##### `__init__(self)`
Initialize the WebSocket connector.

##### `async connect(self)`
Connect to the WebSocket server.

```python
connector = WebSocketConnector()
await connector.connect()
```

##### `async disconnect(self)`
Disconnect from the WebSocket server.

```python
await connector.disconnect()
```

##### `async send_message(self, message)`
Send a message to the WebSocket server.

Parameters:
- `message` (str): The message to send.

```python
await connector.send_message(json.dumps({
    "op": "subscribe",
    "args": [{
        "channel": "books",
        "instId": "BTC-USDT-SWAP"
    }]
}))
```

##### `async subscribe(self, channel, instrument_id)`
Subscribe to a channel for a specific instrument.

Parameters:
- `channel` (str): The channel to subscribe to (e.g., "books").
- `instrument_id` (str): The instrument to subscribe to (e.g., "BTC-USDT-SWAP").

```python
await connector.subscribe("books", "BTC-USDT-SWAP")
```

##### `async unsubscribe(self, channel, instrument_id)`
Unsubscribe from a channel for a specific instrument.

Parameters:
- `channel` (str): The channel to unsubscribe from.
- `instrument_id` (str): The instrument to unsubscribe from.

```python
await connector.unsubscribe("books", "BTC-USDT-SWAP")
```

#### Callbacks

The `WebSocketConnector` class provides several callback methods that can be overridden:

- `on_message(self, message)`: Called when a message is received.
- `on_error(self, error)`: Called when an error occurs.
- `on_close(self)`: Called when the connection is closed.
- `on_open(self)`: Called when the connection is opened.

```python
connector = WebSocketConnector()
connector.on_message = lambda message: print(f"Received: {message}")
connector.on_error = lambda error: print(f"Error: {error}")
connector.on_close = lambda: print("Connection closed")
connector.on_open = lambda: print("Connection opened")
```

## Data Module

### OrderBook

The `OrderBook` class manages the L2 order book data.

#### Methods

##### `__init__(self)`
Initialize the order book.

##### `update(self, data)`
Update the order book with new data.

Parameters:
- `data` (dict): The order book data.

Returns:
- `float`: The time taken to update the order book in milliseconds.

```python
order_book = OrderBook()
update_time = order_book.update({
    'timestamp': '2025-05-04T10:39:13Z',
    'exchange': 'OKX',
    'symbol': 'BTC-USDT-SWAP',
    'asks': [['95445.5', '9.06'], ['95448.0', '2.05']],
    'bids': [['95445.4', '1104.23'], ['95445.3', '0.02']]
})
```

##### `get_best_bid(self)`
Get the best bid price.

Returns:
- `float`: The best bid price.

```python
best_bid = order_book.get_best_bid()
```

##### `get_best_ask(self)`
Get the best ask price.

Returns:
- `float`: The best ask price.

```python
best_ask = order_book.get_best_ask()
```

##### `get_mid_price(self)`
Get the mid price.

Returns:
- `float`: The mid price.

```python
mid_price = order_book.get_mid_price()
```

##### `get_spread(self)`
Get the bid-ask spread.

Returns:
- `float`: The bid-ask spread.

```python
spread = order_book.get_spread()
```

##### `get_depth(self, levels=10)`
Get the order book depth.

Parameters:
- `levels` (int): The number of levels to retrieve.

Returns:
- `tuple`: A tuple containing the bids and asks.

```python
bids, asks = order_book.get_depth(levels=5)
```

##### `calculate_market_order_cost(self, quantity_usd, is_buy)`
Calculate the cost of a market order.

Parameters:
- `quantity_usd` (float): The order quantity in USD.
- `is_buy` (bool): Whether the order is a buy order.

Returns:
- `tuple`: A tuple containing the total cost, average price, and slippage.

```python
total_cost, avg_price, slippage = order_book.calculate_market_order_cost(10000.0, True)
```

##### `get_order_book_features(self)`
Get features from the order book for use in models.

Returns:
- `dict`: A dictionary of order book features.

```python
features = order_book.get_order_book_features()
```

## Models Module

### FeeModel

The `FeeModel` class calculates expected transaction fees based on exchange fee tiers.

#### Methods

##### `__init__(self)`
Initialize the fee model.

##### `calculate_fees(self, exchange, fee_tier, order_type, quantity_usd, maker_ratio=None)`
Calculate the fees for an order.

Parameters:
- `exchange` (str): The exchange (e.g., "OKX").
- `fee_tier` (int): The fee tier (e.g., 0 for VIP 0).
- `order_type` (str): The order type (e.g., "limit" or "market").
- `quantity_usd` (float): The order quantity in USD.
- `maker_ratio` (float, optional): The proportion of the order filled as maker.

Returns:
- `dict`: A dictionary containing the maker fee, taker fee, and effective fee.

```python
fee_model = FeeModel()
fees = fee_model.calculate_fees("OKX", 0, "limit", 10000.0, 0.7)
```

##### `get_fee_structure(self, exchange)`
Get the fee structure for an exchange.

Parameters:
- `exchange` (str): The exchange.

Returns:
- `dict`: A dictionary containing the maker and taker fee structures.

```python
fee_structure = fee_model.get_fee_structure("OKX")
```

##### `get_fee_tier_requirements(self, exchange, fee_tier)`
Get the requirements for a fee tier.

Parameters:
- `exchange` (str): The exchange.
- `fee_tier` (int): The fee tier.

Returns:
- `dict`: A dictionary containing the trading volume and holding amount requirements.

```python
requirements = fee_model.get_fee_tier_requirements("OKX", 1)
```

##### `estimate_fee_tier(self, exchange, trading_volume_usd, holding_amount_usd)`
Estimate the fee tier based on trading volume and holding amount.

Parameters:
- `exchange` (str): The exchange.
- `trading_volume_usd` (float): The 30-day trading volume in USD.
- `holding_amount_usd` (float): The holding amount in USD.

Returns:
- `int`: The estimated fee tier.

```python
fee_tier = fee_model.estimate_fee_tier("OKX", 5000000.0, 1000.0)
```

### SlippageModel

The `SlippageModel` class estimates expected slippage using linear regression.

#### Methods

##### `__init__(self)`
Initialize the slippage model.

##### `predict_slippage(self, order_book_features, quantity_usd, is_buy=None)`
Predict the slippage for an order.

Parameters:
- `order_book_features` (dict): Features extracted from the order book.
- `quantity_usd` (float): The order quantity in USD.
- `is_buy` (bool, optional): Whether the order is a buy order.

Returns:
- `float`: The predicted slippage as a percentage.

```python
slippage_model = SlippageModel()
slippage = slippage_model.predict_slippage(order_book_features, 10000.0, True)
```

##### `train_model(self, historical_data)`
Train the slippage model using historical data.

Parameters:
- `historical_data` (list): A list of dictionaries containing historical data.

```python
slippage_model.train_model(historical_data)
```

##### `save_model(self, file_path)`
Save the trained model to a file.

Parameters:
- `file_path` (str): The path to save the model.

```python
slippage_model.save_model("slippage_model.pkl")
```

##### `load_model(self, file_path)`
Load a trained model from a file.

Parameters:
- `file_path` (str): The path to load the model from.

```python
slippage_model.load_model("slippage_model.pkl")
```

### AlmgrenChrissModel

The `AlmgrenChrissModel` class calculates market impact based on order size and volatility.

#### Methods

##### `__init__(self)`
Initialize the market impact model.

##### `calculate_market_impact(self, quantity_usd, volatility, avg_daily_volume=None, mid_price=None)`
Calculate the market impact for an order.

Parameters:
- `quantity_usd` (float): The order quantity in USD.
- `volatility` (float): The volatility of the instrument.
- `avg_daily_volume` (float, optional): The average daily volume in USD.
- `mid_price` (float, optional): The mid price of the instrument.

Returns:
- `float`: The calculated market impact as a percentage.

```python
market_impact_model = AlmgrenChrissModel()
impact = market_impact_model.calculate_market_impact(10000.0, 0.02, 1000000.0, 95445.45)
```

##### `calculate_temporary_impact(self, quantity_usd, volatility, avg_daily_volume, mid_price)`
Calculate the temporary market impact.

Parameters:
- `quantity_usd` (float): The order quantity in USD.
- `volatility` (float): The volatility of the instrument.
- `avg_daily_volume` (float): The average daily volume in USD.
- `mid_price` (float): The mid price of the instrument.

Returns:
- `float`: The calculated temporary impact as a percentage.

```python
temp_impact = market_impact_model.calculate_temporary_impact(10000.0, 0.02, 1000000.0, 95445.45)
```

##### `calculate_permanent_impact(self, quantity_usd, volatility, avg_daily_volume, mid_price)`
Calculate the permanent market impact.

Parameters:
- `quantity_usd` (float): The order quantity in USD.
- `volatility` (float): The volatility of the instrument.
- `avg_daily_volume` (float): The average daily volume in USD.
- `mid_price` (float): The mid price of the instrument.

Returns:
- `float`: The calculated permanent impact as a percentage.

```python
perm_impact = market_impact_model.calculate_permanent_impact(10000.0, 0.02, 1000000.0, 95445.45)
```

##### `set_parameters(self, params)`
Set the model parameters.

Parameters:
- `params` (dict): A dictionary of parameters.

```python
market_impact_model.set_parameters({
    'alpha': 0.2,
    'beta': 0.5,
    'gamma': 1.2,
    'eta': 0.3
})
```

##### `get_parameters(self)`
Get the model parameters.

Returns:
- `dict`: A dictionary of parameters.

```python
params = market_impact_model.get_parameters()
```

##### `calibrate_model(self, historical_data)`
Calibrate the model using historical data.

Parameters:
- `historical_data` (list): A list of dictionaries containing historical data.

```python
market_impact_model.calibrate_model(historical_data)
```

##### `save_model(self, file_path)`
Save the model parameters to a file.

Parameters:
- `file_path` (str): The path to save the parameters.

```python
market_impact_model.save_model("market_impact_model.json")
```

##### `load_model(self, file_path)`
Load model parameters from a file.

Parameters:
- `file_path` (str): The path to load the parameters from.

```python
market_impact_model.load_model("market_impact_model.json")
```

### MakerTakerModel

The `MakerTakerModel` class predicts the proportion of an order filled as maker vs. taker.

#### Methods

##### `__init__(self)`
Initialize the maker/taker model.

##### `predict_proportion(self, order_book_features, quantity_usd, is_buy=None)`
Predict the proportion of an order filled as maker.

Parameters:
- `order_book_features` (dict): Features extracted from the order book.
- `quantity_usd` (float): The order quantity in USD.
- `is_buy` (bool, optional): Whether the order is a buy order.

Returns:
- `float`: The predicted maker proportion.

```python
maker_taker_model = MakerTakerModel()
maker_proportion = maker_taker_model.predict_proportion(order_book_features, 10000.0, True)
```

##### `train_model(self, historical_data)`
Train the maker/taker model using historical data.

Parameters:
- `historical_data` (list): A list of dictionaries containing historical data.

```python
maker_taker_model.train_model(historical_data)
```

##### `save_model(self, file_path)`
Save the trained model to a file.

Parameters:
- `file_path` (str): The path to save the model.

```python
maker_taker_model.save_model("maker_taker_model.pkl")
```

##### `load_model(self, file_path)`
Load a trained model from a file.

Parameters:
- `file_path` (str): The path to load the model from.

```python
maker_taker_model.load_model("maker_taker_model.pkl")
```

##### `calculate_expected_fees(self, exchange, fee_tier, order_type, quantity_usd, maker_proportion)`
Calculate expected fees based on the maker/taker proportion.

Parameters:
- `exchange` (str): The exchange.
- `fee_tier` (int): The fee tier.
- `order_type` (str): The order type.
- `quantity_usd` (float): The order quantity in USD.
- `maker_proportion` (float): The proportion of the order filled as maker.

Returns:
- `float`: The expected fees in USD.

```python
expected_fees = maker_taker_model.calculate_expected_fees("OKX", 0, "limit", 10000.0, 0.7)
```

### SimulationEngine

The `SimulationEngine` class coordinates model calculations and processes real-time market data.

#### Methods

##### `__init__(self, order_book, fee_model, slippage_model, market_impact_model, maker_taker_model, performance_monitor)`
Initialize the simulation engine.

Parameters:
- `order_book` (OrderBook): The order book.
- `fee_model` (FeeModel): The fee model.
- `slippage_model` (SlippageModel): The slippage model.
- `market_impact_model` (AlmgrenChrissModel): The market impact model.
- `maker_taker_model` (MakerTakerModel): The maker/taker model.
- `performance_monitor` (PerformanceMonitor): The performance monitor.

```python
simulation_engine = SimulationEngine(
    order_book,
    fee_model,
    slippage_model,
    market_impact_model,
    maker_taker_model,
    performance_monitor
)
```

##### `set_parameters(self, params)`
Set the simulation parameters.

Parameters:
- `params` (dict): A dictionary of parameters.

```python
simulation_engine.set_parameters({
    'exchange': 'OKX',
    'fee_tier': 0,
    'order_type': 'limit',
    'quantity_usd': 10000.0,
    'is_buy': True,
    'avg_daily_volume': 1000000.0,
    'volatility': 0.02
})
```

##### `process_tick(self, tick_data)`
Process a market data tick.

Parameters:
- `tick_data` (dict): The market data tick.

```python
simulation_engine.process_tick(tick_data)
```

##### `get_current_results(self)`
Get the current simulation results.

Returns:
- `dict`: A dictionary of simulation results.

```python
results = simulation_engine.get_current_results()
```

##### `reset(self)`
Reset the simulation engine.

```python
simulation_engine.reset()
```

## UI Module

### MainWindow

The `MainWindow` class is the main application window.

#### Methods

##### `__init__(self, simulation_engine, websocket_connector, performance_monitor, config)`
Initialize the main window.

Parameters:
- `simulation_engine` (SimulationEngine): The simulation engine.
- `websocket_connector` (WebSocketConnector): The WebSocket connector.
- `performance_monitor` (PerformanceMonitor): The performance monitor.
- `config` (Config): The configuration.

```python
main_window = MainWindow(
    simulation_engine,
    websocket_connector,
    performance_monitor,
    config
)
```

##### `show(self)`
Show the main window.

```python
main_window.show()
```

##### `update_simulation_results(self, results)`
Update the simulation results in the UI.

Parameters:
- `results` (dict): The simulation results.

```python
main_window.update_simulation_results(results)
```

##### `update_performance_metrics(self, metrics)`
Update the performance metrics in the UI.

Parameters:
- `metrics` (dict): The performance metrics.

```python
main_window.update_performance_metrics(metrics)
```

##### `update_connection_status(self, connected)`
Update the connection status in the UI.

Parameters:
- `connected` (bool): Whether the connection is established.

```python
main_window.update_connection_status(True)
```

##### `show_error(self, error)`
Show an error message in the UI.

Parameters:
- `error` (str): The error message.

```python
main_window.show_error("Connection failed")
```

### InputPanel

The `InputPanel` class collects user input parameters for the simulation.

#### Methods

##### `__init__(self, parent=None)`
Initialize the input panel.

Parameters:
- `parent` (QWidget, optional): The parent widget.

```python
input_panel = InputPanel()
```

##### `get_parameters(self)`
Get the input parameters.

Returns:
- `dict`: A dictionary of input parameters.

```python
params = input_panel.get_parameters()
```

##### `set_parameters(self, params)`
Set the input parameters.

Parameters:
- `params` (dict): A dictionary of input parameters.

```python
input_panel.set_parameters({
    'exchange': 'OKX',
    'fee_tier': 0,
    'order_type': 'limit',
    'quantity_usd': 10000.0,
    'is_buy': True
})
```

### OutputPanel

The `OutputPanel` class displays simulation results in the UI.

#### Methods

##### `__init__(self, parent=None)`
Initialize the output panel.

Parameters:
- `parent` (QWidget, optional): The parent widget.

```python
output_panel = OutputPanel()
```

##### `update_values(self, data)`
Update the displayed values.

Parameters:
- `data` (dict): The simulation results.

```python
output_panel.update_values(results)
```

### PerformancePanel

The `PerformancePanel` class displays performance metrics in the UI.

#### Methods

##### `__init__(self, parent=None)`
Initialize the performance panel.

Parameters:
- `parent` (QWidget, optional): The parent widget.

```python
performance_panel = PerformancePanel()
```

##### `update_values(self, data)`
Update the displayed values.

Parameters:
- `data` (dict): The performance metrics.

```python
performance_panel.update_values(metrics)
```

## Utils Module

### PerformanceMonitor

The `PerformanceMonitor` class tracks and monitors performance metrics.

#### Methods

##### `__init__(self)`
Initialize the performance monitor.

```python
performance_monitor = PerformanceMonitor()
```

##### `record_tick_received(self)`
Record that a tick was received.

```python
performance_monitor.record_tick_received()
```

##### `record_orderbook_updated(self, update_time)`
Record that the order book was updated.

Parameters:
- `update_time` (float): The time taken to update the order book in milliseconds.

```python
performance_monitor.record_orderbook_updated(update_time)
```

##### `record_simulation_completed(self, simulation_time)`
Record that a simulation was completed.

Parameters:
- `simulation_time` (float): The time taken to complete the simulation in milliseconds.

```python
performance_monitor.record_simulation_completed(simulation_time)
```

##### `get_average_latency(self)`
Get the average latency.

Returns:
- `float`: The average latency in milliseconds.

```python
avg_latency = performance_monitor.get_average_latency()
```

##### `get_throughput(self)`
Get the throughput.

Returns:
- `float`: The throughput in messages per second.

```python
throughput = performance_monitor.get_throughput()
```

##### `get_metrics(self)`
Get all performance metrics.

Returns:
- `dict`: A dictionary of performance metrics.

```python
metrics = performance_monitor.get_metrics()
```

### Config

The `Config` class manages application settings and configuration parameters.

#### Methods

##### `__init__(self)`
Initialize the configuration.

```python
config = Config()
```

##### `load(self, file_path='config.json')`
Load configuration from a file.

Parameters:
- `file_path` (str, optional): The path to the configuration file.

```python
config.load("config.json")
```

##### `save(self, file_path='config.json')`
Save configuration to a file.

Parameters:
- `file_path` (str, optional): The path to save the configuration.

```python
config.save("config.json")
```

##### `get(self, section, key, default=None)`
Get a configuration value.

Parameters:
- `section` (str): The configuration section.
- `key` (str): The configuration key.
- `default` (any, optional): The default value if the key is not found.

Returns:
- The configuration value.

```python
value = config.get("websocket", "reconnect_interval", 5)
```

##### `set(self, section, key, value)`
Set a configuration value.

Parameters:
- `section` (str): The configuration section.
- `key` (str): The configuration key.
- `value` (any): The configuration value.

```python
config.set("websocket", "reconnect_interval", 10)
```
