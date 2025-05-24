import unittest
from src.models.fee_model import FeeModel

class TestFeeModel(unittest.TestCase):
    """Test cases for the FeeModel class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fee_model = FeeModel()
    
    def test_calculate_fees_okx(self):
        """Test calculating fees for OKX exchange."""
        # Test different fee tiers for OKX
        # VIP 0
        fee_tier = 0
        order_type = "market"
        quantity_usd = 10000.0
        fees = self.fee_model.calculate_fees("OKX", fee_tier, order_type, quantity_usd)
        self.assertEqual(fees["maker_fee"], 8.0)  # 0.08% of 10000
        self.assertEqual(fees["taker_fee"], 10.0)  # 0.10% of 10000
        
        # VIP 1
        fee_tier = 1
        fees = self.fee_model.calculate_fees("OKX", fee_tier, order_type, quantity_usd)
        self.assertEqual(fees["maker_fee"], 7.0)  # 0.07% of 10000
        self.assertEqual(fees["taker_fee"], 9.0)  # 0.09% of 10000
        
        # VIP 5
        fee_tier = 5
        fees = self.fee_model.calculate_fees("OKX", fee_tier, order_type, quantity_usd)
        self.assertEqual(fees["maker_fee"], 0.0)  # 0.00% of 10000
        self.assertEqual(fees["taker_fee"], 6.0)  # 0.06% of 10000
    
    def test_calculate_fees_binance(self):
        """Test calculating fees for Binance exchange."""
        # Test different fee tiers for Binance
        # VIP 0
        fee_tier = 0
        order_type = "market"
        quantity_usd = 10000.0
        fees = self.fee_model.calculate_fees("Binance", fee_tier, order_type, quantity_usd)
        self.assertEqual(fees["maker_fee"], 10.0)  # 0.10% of 10000
        self.assertEqual(fees["taker_fee"], 10.0)  # 0.10% of 10000
        
        # VIP 1
        fee_tier = 1
        fees = self.fee_model.calculate_fees("Binance", fee_tier, order_type, quantity_usd)
        self.assertEqual(fees["maker_fee"], 9.0)  # 0.09% of 10000
        self.assertEqual(fees["taker_fee"], 10.0)  # 0.10% of 10000
        
        # VIP 9
        fee_tier = 9
        fees = self.fee_model.calculate_fees("Binance", fee_tier, order_type, quantity_usd)
        self.assertEqual(fees["maker_fee"], 0.0)  # 0.00% of 10000
        self.assertEqual(fees["taker_fee"], 3.5)  # 0.035% of 10000
    
    def test_calculate_fees_unknown_exchange(self):
        """Test calculating fees for an unknown exchange."""
        # Test with an unknown exchange
        exchange = "UnknownExchange"
        fee_tier = 0
        order_type = "market"
        quantity_usd = 10000.0
        
        # This should use the default fee structure
        fees = self.fee_model.calculate_fees(exchange, fee_tier, order_type, quantity_usd)
        self.assertEqual(fees["maker_fee"], 10.0)  # 0.10% of 10000
        self.assertEqual(fees["taker_fee"], 10.0)  # 0.10% of 10000
    
    def test_calculate_fees_limit_order(self):
        """Test calculating fees for a limit order."""
        # Test with a limit order
        exchange = "OKX"
        fee_tier = 0
        order_type = "limit"
        quantity_usd = 10000.0
        
        # For a limit order, we should use the maker fee
        fees = self.fee_model.calculate_fees(exchange, fee_tier, order_type, quantity_usd)
        self.assertEqual(fees["maker_fee"], 8.0)  # 0.08% of 10000
        self.assertEqual(fees["taker_fee"], 10.0)  # 0.10% of 10000
        
        # The effective fee should be the maker fee
        self.assertEqual(fees["effective_fee"], 8.0)
    
    def test_calculate_fees_market_order(self):
        """Test calculating fees for a market order."""
        # Test with a market order
        exchange = "OKX"
        fee_tier = 0
        order_type = "market"
        quantity_usd = 10000.0
        
        # For a market order, we should use the taker fee
        fees = self.fee_model.calculate_fees(exchange, fee_tier, order_type, quantity_usd)
        self.assertEqual(fees["maker_fee"], 8.0)  # 0.08% of 10000
        self.assertEqual(fees["taker_fee"], 10.0)  # 0.10% of 10000
        
        # The effective fee should be the taker fee
        self.assertEqual(fees["effective_fee"], 10.0)
    
    def test_calculate_fees_mixed_order(self):
        """Test calculating fees for a mixed order (part maker, part taker)."""
        # Test with a mixed order
        exchange = "OKX"
        fee_tier = 0
        order_type = "limit"
        quantity_usd = 10000.0
        maker_ratio = 0.7  # 70% maker, 30% taker
        
        # Calculate fees with a specific maker ratio
        fees = self.fee_model.calculate_fees(exchange, fee_tier, order_type, quantity_usd, maker_ratio)
        
        # The effective fee should be a weighted average of maker and taker fees
        expected_effective_fee = (0.7 * 8.0) + (0.3 * 10.0)  # 70% maker fee + 30% taker fee
        self.assertEqual(fees["effective_fee"], expected_effective_fee)
    
    def test_calculate_fees_zero_quantity(self):
        """Test calculating fees with zero quantity."""
        # Test with zero quantity
        exchange = "OKX"
        fee_tier = 0
        order_type = "market"
        quantity_usd = 0.0
        
        # All fees should be zero
        fees = self.fee_model.calculate_fees(exchange, fee_tier, order_type, quantity_usd)
        self.assertEqual(fees["maker_fee"], 0.0)
        self.assertEqual(fees["taker_fee"], 0.0)
        self.assertEqual(fees["effective_fee"], 0.0)
    
    def test_calculate_fees_negative_quantity(self):
        """Test calculating fees with negative quantity."""
        # Test with negative quantity
        exchange = "OKX"
        fee_tier = 0
        order_type = "market"
        quantity_usd = -10000.0
        
        # This should use the absolute value of the quantity
        fees = self.fee_model.calculate_fees(exchange, fee_tier, order_type, quantity_usd)
        self.assertEqual(fees["maker_fee"], 8.0)  # 0.08% of 10000
        self.assertEqual(fees["taker_fee"], 10.0)  # 0.10% of 10000
    
    def test_get_fee_structure(self):
        """Test getting the fee structure for an exchange."""
        # Test getting the fee structure for OKX
        fee_structure = self.fee_model.get_fee_structure("OKX")
        
        # Check that the fee structure has the expected keys
        self.assertIn("maker_fees", fee_structure)
        self.assertIn("taker_fees", fee_structure)
        
        # Check that the fee structures are lists
        self.assertIsInstance(fee_structure["maker_fees"], list)
        self.assertIsInstance(fee_structure["taker_fees"], list)
        
        # Check that the fee structures have the expected length
        self.assertEqual(len(fee_structure["maker_fees"]), 9)  # VIP 0-8
        self.assertEqual(len(fee_structure["taker_fees"]), 9)  # VIP 0-8
    
    def test_get_fee_tier_requirements(self):
        """Test getting the requirements for a fee tier."""
        # Test getting the requirements for OKX VIP 1
        requirements = self.fee_model.get_fee_tier_requirements("OKX", 1)
        
        # Check that the requirements have the expected keys
        self.assertIn("trading_volume_usd", requirements)
        self.assertIn("holding_amount_usd", requirements)
        
        # Check that the requirements are numbers
        self.assertIsInstance(requirements["trading_volume_usd"], (int, float))
        self.assertIsInstance(requirements["holding_amount_usd"], (int, float))
    
    def test_estimate_fee_tier(self):
        """Test estimating the fee tier based on trading volume and holding amount."""
        # Test estimating the fee tier for OKX
        exchange = "OKX"
        trading_volume_usd = 5000000.0  # $5M
        holding_amount_usd = 1000.0  # $1K
        
        # This should be VIP 1
        fee_tier = self.fee_model.estimate_fee_tier(exchange, trading_volume_usd, holding_amount_usd)
        self.assertEqual(fee_tier, 1)
        
        # Test with higher trading volume
        trading_volume_usd = 20000000.0  # $20M
        holding_amount_usd = 1000.0  # $1K
        
        # This should be VIP 2
        fee_tier = self.fee_model.estimate_fee_tier(exchange, trading_volume_usd, holding_amount_usd)
        self.assertEqual(fee_tier, 2)
        
        # Test with higher holding amount
        trading_volume_usd = 5000000.0  # $5M
        holding_amount_usd = 500000.0  # $500K
        
        # This should be VIP 2 (higher tier due to holding amount)
        fee_tier = self.fee_model.estimate_fee_tier(exchange, trading_volume_usd, holding_amount_usd)
        self.assertEqual(fee_tier, 2)


if __name__ == '__main__':
    unittest.main()
