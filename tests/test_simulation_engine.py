import unittest
from unittest.mock import MagicMock, patch
from src.models.simulation_engine import SimulationEngine
from src.data.orderbook import OrderBook
from src.models.fee_model import FeeModel
from src.models.slippage_model import SlippageModel
from src.models.market_impact_model import AlmgrenChrissModel
from src.models.maker_taker_model import MakerTakerModel
from src.utils.performance import PerformanceMonitor

class TestSimulationEngine(unittest.TestCase):
    """Test cases for the SimulationEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock components
        self.order_book = MagicMock(spec=OrderBook)
        self.fee_model = MagicMock(spec=FeeModel)
        self.slippage_model = MagicMock(spec=SlippageModel)
        self.market_impact_model = MagicMock(spec=AlmgrenChrissModel)
        self.maker_taker_model = MagicMock(spec=MakerTakerModel)
        self.performance_monitor = MagicMock(spec=PerformanceMonitor)
        
        # Create simulation engine
        self.simulation_engine = SimulationEngine(
            self.order_book,
            self.fee_model,
            self.slippage_model,
            self.market_impact_model,
            self.maker_taker_model,
            self.performance_monitor
        )
        
        # Set up mock returns
        self.order_book.get_best_bid.return_value = 95445.4
        self.order_book.get_best_ask.return_value = 95445.5
        self.order_book.get_mid_price.return_value = 95445.45
        self.order_book.get_spread.return_value = 0.1
        self.order_book.get_order_book_features.return_value = {
            'mid_price': 95445.45,
            'spread': 0.1,
            'spread_percentage': 0.0001,
            'bid_volume': 1138.8,
            'ask_volume': 26.91,
            'volume_imbalance': 0.954
        }
        
        self.maker_taker_model.predict_proportion.return_value = 0.7
        self.slippage_model.predict_slippage.return_value = 0.0005
        self.market_impact_model.calculate_market_impact.return_value = 0.0003
        self.fee_model.calculate_fees.return_value = {
            'maker_fee': 8.0,
            'taker_fee': 10.0,
            'effective_fee': 8.6
        }
        
        # Sample tick data
        self.sample_tick = {
            'timestamp': '2025-05-04T10:39:13Z',
            'exchange': 'OKX',
            'symbol': 'BTC-USDT-SWAP',
            'asks': [
                ['95445.5', '9.06'],
                ['95448.0', '2.05'],
                ['95450.0', '5.10'],
                ['95455.0', '3.20'],
                ['95460.0', '7.50']
            ],
            'bids': [
                ['95445.4', '1104.23'],
                ['95445.3', '0.02'],
                ['95440.0', '10.50'],
                ['95435.0', '8.75'],
                ['95430.0', '15.30']
            ]
        }
        
        # Default simulation parameters
        self.simulation_engine.set_parameters({
            'exchange': 'OKX',
            'fee_tier': 0,
            'order_type': 'limit',
            'quantity_usd': 10000.0,
            'is_buy': True,
            'avg_daily_volume': 1000000.0,
            'volatility': 0.02
        })
    
    def test_set_parameters(self):
        """Test setting simulation parameters."""
        # Set new parameters
        params = {
            'exchange': 'Binance',
            'fee_tier': 1,
            'order_type': 'market',
            'quantity_usd': 20000.0,
            'is_buy': False,
            'avg_daily_volume': 2000000.0,
            'volatility': 0.03
        }
        
        self.simulation_engine.set_parameters(params)
        
        # Check that the parameters were set correctly
        self.assertEqual(self.simulation_engine.exchange, 'Binance')
        self.assertEqual(self.simulation_engine.fee_tier, 1)
        self.assertEqual(self.simulation_engine.order_type, 'market')
        self.assertEqual(self.simulation_engine.quantity_usd, 20000.0)
        self.assertEqual(self.simulation_engine.is_buy, False)
        self.assertEqual(self.simulation_engine.avg_daily_volume, 2000000.0)
        self.assertEqual(self.simulation_engine.volatility, 0.03)
    
    def test_process_tick(self):
        """Test processing a market data tick."""
        # Create a mock for the simulation_result signal
        self.simulation_engine.simulation_result = MagicMock()
        
        # Process a tick
        self.simulation_engine.process_tick(self.sample_tick)
        
        # Check that the order book was updated
        self.order_book.update.assert_called_once_with(self.sample_tick)
        
        # Check that the order book features were retrieved
        self.order_book.get_order_book_features.assert_called_once()
        
        # Check that the maker/taker proportion was predicted
        self.maker_taker_model.predict_proportion.assert_called_once()
        
        # Check that the slippage was predicted
        self.slippage_model.predict_slippage.assert_called_once()
        
        # Check that the market impact was calculated
        self.market_impact_model.calculate_market_impact.assert_called_once()
        
        # Check that the fees were calculated
        self.fee_model.calculate_fees.assert_called_once()
        
        # Check that the simulation result signal was emitted
        self.simulation_engine.simulation_result.emit.assert_called_once()
        
        # Check that the performance monitor was updated
        self.performance_monitor.record_simulation_completed.assert_called_once()
    
    def test_calculate_total_cost(self):
        """Test calculating the total cost of a trade."""
        # Set up mock returns
        mid_price = 95445.45
        quantity_usd = 10000.0
        slippage = 0.0005
        market_impact = 0.0003
        fees = 8.6
        
        # Calculate total cost
        total_cost, total_cost_percentage = self.simulation_engine.calculate_total_cost(
            mid_price, quantity_usd, slippage, market_impact, fees
        )
        
        # Check that the total cost is correct
        expected_cost = (slippage + market_impact) * quantity_usd + fees
        self.assertEqual(total_cost, expected_cost)
        
        # Check that the total cost percentage is correct
        expected_percentage = (total_cost / quantity_usd) * 100
        self.assertEqual(total_cost_percentage, expected_percentage)
    
    def test_calculate_execution_price(self):
        """Test calculating the execution price."""
        # Set up test parameters
        mid_price = 95445.45
        slippage_percentage = 0.0005
        market_impact_percentage = 0.0003
        is_buy = True
        
        # Calculate execution price
        execution_price = self.simulation_engine.calculate_execution_price(
            mid_price, slippage_percentage, market_impact_percentage, is_buy
        )
        
        # Check that the execution price is correct
        expected_price = mid_price * (1 + slippage_percentage + market_impact_percentage)
        self.assertEqual(execution_price, expected_price)
        
        # Test with a sell order
        is_buy = False
        execution_price = self.simulation_engine.calculate_execution_price(
            mid_price, slippage_percentage, market_impact_percentage, is_buy
        )
        
        # Check that the execution price is correct
        expected_price = mid_price * (1 - slippage_percentage - market_impact_percentage)
        self.assertEqual(execution_price, expected_price)
    
    def test_calculate_quantity_filled(self):
        """Test calculating the quantity filled."""
        # Set up test parameters
        quantity_usd = 10000.0
        execution_price = 95500.0
        
        # Calculate quantity filled
        quantity_filled = self.simulation_engine.calculate_quantity_filled(
            quantity_usd, execution_price
        )
        
        # Check that the quantity filled is correct
        expected_quantity = quantity_usd / execution_price
        self.assertEqual(quantity_filled, expected_quantity)
    
    def test_format_results(self):
        """Test formatting the simulation results."""
        # Set up test parameters
        mid_price = 95445.45
        execution_price = 95493.0
        quantity_usd = 10000.0
        quantity_filled = 0.1047
        slippage_percentage = 0.0005
        market_impact_percentage = 0.0003
        maker_proportion = 0.7
        fees = 8.6
        total_cost = 88.6
        total_cost_percentage = 0.886
        
        # Format results
        results = self.simulation_engine.format_results(
            mid_price,
            execution_price,
            quantity_usd,
            quantity_filled,
            slippage_percentage,
            market_impact_percentage,
            maker_proportion,
            fees,
            total_cost,
            total_cost_percentage
        )
        
        # Check that the results have the expected keys
        self.assertIn('mid_price', results)
        self.assertIn('execution_price', results)
        self.assertIn('quantity_usd', results)
        self.assertIn('quantity_filled', results)
        self.assertIn('slippage_percentage', results)
        self.assertIn('market_impact_percentage', results)
        self.assertIn('maker_proportion', results)
        self.assertIn('fees', results)
        self.assertIn('total_cost', results)
        self.assertIn('total_cost_percentage', results)
        
        # Check that the results have the expected values
        self.assertEqual(results['mid_price'], mid_price)
        self.assertEqual(results['execution_price'], execution_price)
        self.assertEqual(results['quantity_usd'], quantity_usd)
        self.assertEqual(results['quantity_filled'], quantity_filled)
        self.assertEqual(results['slippage_percentage'], slippage_percentage)
        self.assertEqual(results['market_impact_percentage'], market_impact_percentage)
        self.assertEqual(results['maker_proportion'], maker_proportion)
        self.assertEqual(results['fees'], fees)
        self.assertEqual(results['total_cost'], total_cost)
        self.assertEqual(results['total_cost_percentage'], total_cost_percentage)
    
    def test_get_current_results(self):
        """Test getting the current simulation results."""
        # Get current results
        results = self.simulation_engine.get_current_results()
        
        # Check that the results have the expected keys
        self.assertIn('mid_price', results)
        self.assertIn('execution_price', results)
        self.assertIn('quantity_usd', results)
        self.assertIn('quantity_filled', results)
        self.assertIn('slippage_percentage', results)
        self.assertIn('market_impact_percentage', results)
        self.assertIn('maker_proportion', results)
        self.assertIn('fees', results)
        self.assertIn('total_cost', results)
        self.assertIn('total_cost_percentage', results)
    
    def test_reset(self):
        """Test resetting the simulation engine."""
        # Reset the simulation engine
        self.simulation_engine.reset()
        
        # Check that the parameters were reset
        self.assertEqual(self.simulation_engine.exchange, '')
        self.assertEqual(self.simulation_engine.fee_tier, 0)
        self.assertEqual(self.simulation_engine.order_type, '')
        self.assertEqual(self.simulation_engine.quantity_usd, 0.0)
        self.assertEqual(self.simulation_engine.is_buy, True)
        self.assertEqual(self.simulation_engine.avg_daily_volume, 0.0)
        self.assertEqual(self.simulation_engine.volatility, 0.0)


if __name__ == '__main__':
    unittest.main()
