import logging
import time
from typing import Dict, Any, Optional, Callable

from src.data.order_book import OrderBook
from src.models.fee_model import FeeModel
from src.models.slippage_model import SlippageModel
from src.models.market_impact_model import AlmgrenChrissModel
from src.models.maker_taker_model import MakerTakerModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("simulation_engine")

class SimulationEngine:
    """
    Main simulation engine that coordinates all models and processes real-time data.
    Calculates all output parameters based on the current order book state and input parameters.
    """
    
    def __init__(self, simulation_id: str, parameters: Dict[str, Any], output_callback: Callable[[Dict[str, Any]], None]):
        """
        Initialize the simulation engine.
        
        Args:
            simulation_id: Unique identifier for this simulation
            parameters: Simulation parameters including exchange, asset, quantity, etc.
            output_callback: Callback function to send output to UI
        """
        self.simulation_id = simulation_id
        self.parameters = parameters
        self.output_callback = output_callback
        
        # Initialize order book
        spot_asset = parameters.get('spotAsset', 'BTC-USDT')
        self.order_book = OrderBook(symbol=spot_asset, max_depth=20)
        
        # Initialize models
        self.fee_model = FeeModel()
        self.slippage_model = SlippageModel(regression_type='linear')
        self.market_impact_model = AlmgrenChrissModel()
        self.maker_taker_model = MakerTakerModel()
        
        # Initialize performance metrics
        self.processing_times = []
        self.last_tick_time = None
        self.tick_count = 0
        
        logger.info(f"Simulation engine initialized with ID: {simulation_id}")
        logger.info(f"Parameters: {parameters}")
    
    def process_tick(self, tick_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a market data tick and calculate all output parameters.
        
        Args:
            tick_data: Market data tick from WebSocket
            
        Returns:
            Dictionary with all calculated output parameters
        """
        try:
            # Measure processing start time
            start_time = time.perf_counter()
            
            # Update tick count and timing
            self.tick_count += 1
            current_time = time.time()
            
            # Calculate time since last tick
            time_since_last_tick = None
            if self.last_tick_time is not None:
                time_since_last_tick = current_time - self.last_tick_time
            self.last_tick_time = current_time
            
            # Update order book
            # Make sure the tick data is in the expected format
            order_book_data = {
                'timestamp': tick_data.get('timestamp', ''),
                'exchange': tick_data.get('exchange', 'OKX'),
                'symbol': tick_data.get('symbol', self.parameters.get('spotAsset', 'BTC-USDT')),
                'asks': tick_data.get('asks', []),
                'bids': tick_data.get('bids', [])
            }
            
            # Update the order book and measure the time it takes
            order_book_update_time = self.order_book.update(order_book_data)
            
            # Extract parameters
            exchange = self.parameters.get('exchange', 'OKX')
            spot_asset = self.parameters.get('spotAsset', 'BTC-USDT')
            order_type = self.parameters.get('orderType', 'market')
            quantity_usd = self.parameters.get('quantityUSD', 100.0)
            volatility = self.parameters.get('volatility', 0.02)
            fee_tier = self.parameters.get('feeTier', 'Tier 1')
            
            # Get order book features for model input
            try:
                order_book_features = self.order_book.get_order_book_features()
                logger.info(f"Got order book features with {len(order_book_features)} metrics")
            except Exception as e:
                logger.error(f"Error getting order book features: {str(e)}")
                order_book_features = {
                    'mid_price': 0,
                    'spread': 0,
                    'spread_percentage': 0,
                    'volume_imbalance': 0,
                    'bid_depth_5pct': 1000,
                    'ask_depth_5pct': 1000
                }
            
            # 1. Predict maker/taker proportion
            maker_taker_result = self.maker_taker_model.predict_proportion(
                order_book_features=order_book_features,
                quantity_usd=quantity_usd,
                order_type=order_type,
                volatility=volatility
            )
            
            # 2. Calculate expected fees
            fee_result = self.fee_model.calculate_fees(
                exchange=exchange,
                fee_tier=fee_tier,
                order_type=order_type,
                quantity_usd=quantity_usd,
                maker_taker_proportion=maker_taker_result
            )
            
            # 3. Calculate expected slippage
            slippage_result = self.slippage_model.predict_slippage(
                order_book_features=order_book_features,
                quantity_usd=quantity_usd,
                is_buy=True,  # Assuming buy order for simplicity
                volatility=volatility
            )
            
            # 4. Calculate expected market impact
            market_impact_result = self.market_impact_model.calculate_market_impact(
                quantity_usd=quantity_usd,
                volatility=volatility,
                mid_price=order_book_features.get('mid_price')
            )
            
            # 5. Calculate net cost
            net_cost_usd = (
                slippage_result['slippage_usd'] +
                fee_result['total_fee_usd'] +
                market_impact_result['total_impact_usd']
            )
            
            # Measure processing end time
            end_time = time.perf_counter()
            processing_time_ms = (end_time - start_time) * 1000
            
            # Store processing time for performance metrics
            self.processing_times.append(processing_time_ms)
            
            # Calculate average processing time
            avg_processing_time = sum(self.processing_times) / len(self.processing_times)
            
            # Prepare output
            output = {
                'simulationId': self.simulation_id,
                'timestampUTC': tick_data.get('timestamp'),
                'expectedSlippageUSD': slippage_result['slippage_usd'],
                'expectedFeesUSD': fee_result['total_fee_usd'],
                'expectedMarketImpactUSD': market_impact_result['total_impact_usd'],
                'netCostUSD': net_cost_usd,
                'makerTakerProportion': {
                    'maker': maker_taker_result['maker'],
                    'taker': maker_taker_result['taker']
                },
                'internalLatencyMs': processing_time_ms,
                'performance': {
                    'averageLatencyMs': avg_processing_time,
                    'tickCount': self.tick_count,
                    'orderBookUpdateTimeMs': order_book_update_time,
                    'timeSinceLastTickMs': time_since_last_tick * 1000 if time_since_last_tick else None
                }
            }
            
            # Send output to callback
            if self.output_callback:
                self.output_callback(output)
            
            return output
            
        except Exception as e:
            logger.error(f"Error processing tick: {str(e)}")
            
            # Create error output
            error_output = {
                'simulationId': self.simulation_id,
                'timestampUTC': tick_data.get('timestamp') if tick_data else None,
                'status': 'error',
                'error': str(e)
            }
            
            # Send error to callback
            if self.output_callback:
                self.output_callback(error_output)
            
            return error_output
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the simulation.
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.processing_times:
            return {
                'averageLatencyMs': 0,
                'minLatencyMs': 0,
                'maxLatencyMs': 0,
                'p95LatencyMs': 0,
                'p99LatencyMs': 0,
                'tickCount': 0,
                'ticksPerSecond': 0
            }
        
        # Calculate statistics
        avg_latency = sum(self.processing_times) / len(self.processing_times)
        min_latency = min(self.processing_times)
        max_latency = max(self.processing_times)
        
        # Sort for percentiles
        sorted_times = sorted(self.processing_times)
        p95_index = int(len(sorted_times) * 0.95)
        p99_index = int(len(sorted_times) * 0.99)
        
        p95_latency = sorted_times[p95_index] if p95_index < len(sorted_times) else max_latency
        p99_latency = sorted_times[p99_index] if p99_index < len(sorted_times) else max_latency
        
        # Calculate ticks per second if we have timing information
        ticks_per_second = 0
        if self.tick_count > 1 and self.last_tick_time is not None:
            elapsed_time = self.last_tick_time - time.time() + (self.tick_count / 1)  # Rough estimate
            if elapsed_time > 0:
                ticks_per_second = self.tick_count / elapsed_time
        
        return {
            'averageLatencyMs': avg_latency,
            'minLatencyMs': min_latency,
            'maxLatencyMs': max_latency,
            'p95LatencyMs': p95_latency,
            'p99LatencyMs': p99_latency,
            'tickCount': self.tick_count,
            'ticksPerSecond': ticks_per_second
        }
