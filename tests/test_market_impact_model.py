import unittest
import numpy as np
from src.models.market_impact_model import AlmgrenChrissModel

class TestMarketImpactModel(unittest.TestCase):
    """Test cases for the AlmgrenChrissModel class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.model = AlmgrenChrissModel()
        
        # Sample market parameters
        self.volatility = 0.02  # 2% daily volatility
        self.avg_daily_volume = 1000000.0  # $1M average daily volume
        self.mid_price = 95445.45  # Mid price
    
    def test_calculate_market_impact_small_order(self):
        """Test calculating market impact for a small order."""
        # For a small order, market impact should be minimal
        quantity_usd = 1000.0  # $1K order
        
        # Calculate market impact
        impact = self.model.calculate_market_impact(
            quantity_usd,
            self.volatility,
            self.avg_daily_volume,
            self.mid_price
        )
        
        # Check that the impact is reasonable
        self.assertGreaterEqual(impact, 0.0)
        self.assertLessEqual(impact, 0.001)  # Less than 0.1%
    
    def test_calculate_market_impact_large_order(self):
        """Test calculating market impact for a large order."""
        # For a large order, market impact should be significant
        quantity_usd = 100000.0  # $100K order
        
        # Calculate market impact
        impact = self.model.calculate_market_impact(
            quantity_usd,
            self.volatility,
            self.avg_daily_volume,
            self.mid_price
        )
        
        # Check that the impact is reasonable
        self.assertGreater(impact, 0.001)  # Greater than 0.1%
    
    def test_calculate_market_impact_with_volatility(self):
        """Test calculating market impact with different volatilities."""
        # Create different volatility scenarios
        low_volatility = 0.01  # 1% daily volatility
        high_volatility = 0.05  # 5% daily volatility
        
        # For the same order size, impact should be higher with higher volatility
        quantity_usd = 50000.0  # $50K order
        
        # Calculate impact with low volatility
        low_impact = self.model.calculate_market_impact(
            quantity_usd,
            low_volatility,
            self.avg_daily_volume,
            self.mid_price
        )
        
        # Calculate impact with high volatility
        high_impact = self.model.calculate_market_impact(
            quantity_usd,
            high_volatility,
            self.avg_daily_volume,
            self.mid_price
        )
        
        # Impact should be higher with higher volatility
        self.assertGreater(high_impact, low_impact)
    
    def test_calculate_market_impact_with_volume(self):
        """Test calculating market impact with different average daily volumes."""
        # Create different volume scenarios
        low_volume = 500000.0  # $500K average daily volume
        high_volume = 5000000.0  # $5M average daily volume
        
        # For the same order size, impact should be higher with lower volume
        quantity_usd = 50000.0  # $50K order
        
        # Calculate impact with low volume
        low_volume_impact = self.model.calculate_market_impact(
            quantity_usd,
            self.volatility,
            low_volume,
            self.mid_price
        )
        
        # Calculate impact with high volume
        high_volume_impact = self.model.calculate_market_impact(
            quantity_usd,
            self.volatility,
            high_volume,
            self.mid_price
        )
        
        # Impact should be higher with lower volume
        self.assertGreater(low_volume_impact, high_volume_impact)
    
    def test_calculate_market_impact_zero_quantity(self):
        """Test calculating market impact with zero quantity."""
        # For zero quantity, impact should be zero
        quantity_usd = 0.0
        
        # Calculate market impact
        impact = self.model.calculate_market_impact(
            quantity_usd,
            self.volatility,
            self.avg_daily_volume,
            self.mid_price
        )
        
        # Check that the impact is zero
        self.assertEqual(impact, 0.0)
    
    def test_calculate_market_impact_negative_quantity(self):
        """Test calculating market impact with negative quantity."""
        # For negative quantity, impact should be calculated using the absolute value
        quantity_usd = -50000.0  # -$50K order
        
        # Calculate market impact
        impact = self.model.calculate_market_impact(
            quantity_usd,
            self.volatility,
            self.avg_daily_volume,
            self.mid_price
        )
        
        # Check that the impact is reasonable
        self.assertGreater(impact, 0.0)
    
    def test_calculate_market_impact_zero_volatility(self):
        """Test calculating market impact with zero volatility."""
        # For zero volatility, impact should be zero
        volatility = 0.0
        quantity_usd = 50000.0  # $50K order
        
        # Calculate market impact
        impact = self.model.calculate_market_impact(
            quantity_usd,
            volatility,
            self.avg_daily_volume,
            self.mid_price
        )
        
        # Check that the impact is zero
        self.assertEqual(impact, 0.0)
    
    def test_calculate_market_impact_zero_volume(self):
        """Test calculating market impact with zero average daily volume."""
        # For zero volume, impact should be infinite, but the model should handle this
        avg_daily_volume = 0.0
        quantity_usd = 50000.0  # $50K order
        
        # Calculate market impact
        impact = self.model.calculate_market_impact(
            quantity_usd,
            self.volatility,
            avg_daily_volume,
            self.mid_price
        )
        
        # Check that the impact is reasonable
        self.assertGreater(impact, 0.0)
    
    def test_calculate_temporary_impact(self):
        """Test calculating temporary market impact."""
        # Calculate temporary impact
        quantity_usd = 50000.0  # $50K order
        
        # Calculate temporary impact
        temp_impact = self.model.calculate_temporary_impact(
            quantity_usd,
            self.volatility,
            self.avg_daily_volume,
            self.mid_price
        )
        
        # Check that the impact is reasonable
        self.assertGreater(temp_impact, 0.0)
    
    def test_calculate_permanent_impact(self):
        """Test calculating permanent market impact."""
        # Calculate permanent impact
        quantity_usd = 50000.0  # $50K order
        
        # Calculate permanent impact
        perm_impact = self.model.calculate_permanent_impact(
            quantity_usd,
            self.volatility,
            self.avg_daily_volume,
            self.mid_price
        )
        
        # Check that the impact is reasonable
        self.assertGreater(perm_impact, 0.0)
        
        # Permanent impact should be less than temporary impact
        temp_impact = self.model.calculate_temporary_impact(
            quantity_usd,
            self.volatility,
            self.avg_daily_volume,
            self.mid_price
        )
        
        self.assertLess(perm_impact, temp_impact)
    
    def test_set_parameters(self):
        """Test setting model parameters."""
        # Set new parameters
        new_params = {
            'alpha': 0.2,
            'beta': 0.5,
            'gamma': 1.2,
            'eta': 0.3
        }
        
        # Set the parameters
        self.model.set_parameters(new_params)
        
        # Check that the parameters were set correctly
        self.assertEqual(self.model.alpha, 0.2)
        self.assertEqual(self.model.beta, 0.5)
        self.assertEqual(self.model.gamma, 1.2)
        self.assertEqual(self.model.eta, 0.3)
    
    def test_get_parameters(self):
        """Test getting model parameters."""
        # Get the parameters
        params = self.model.get_parameters()
        
        # Check that the parameters have the expected keys
        self.assertIn('alpha', params)
        self.assertIn('beta', params)
        self.assertIn('gamma', params)
        self.assertIn('eta', params)
        
        # Check that the parameters have the expected values
        self.assertEqual(params['alpha'], self.model.alpha)
        self.assertEqual(params['beta'], self.model.beta)
        self.assertEqual(params['gamma'], self.model.gamma)
        self.assertEqual(params['eta'], self.model.eta)
    
    def test_calibrate_model(self):
        """Test calibrating the model with historical data."""
        # Create mock historical data
        historical_data = []
        for i in range(100):
            order_size = 1000.0 + i * 100.0
            volatility = 0.01 + i * 0.0001
            avg_daily_volume = 1000000.0
            mid_price = 95000.0 + i * 10.0
            impact = 0.0001 + i * 0.0001
            
            historical_data.append({
                'order_size': order_size,
                'volatility': volatility,
                'avg_daily_volume': avg_daily_volume,
                'mid_price': mid_price,
                'impact': impact
            })
        
        # Calibrate the model
        self.model.calibrate_model(historical_data)
        
        # Check that the parameters were updated
        params = self.model.get_parameters()
        self.assertIsNotNone(params['alpha'])
        self.assertIsNotNone(params['beta'])
        self.assertIsNotNone(params['gamma'])
        self.assertIsNotNone(params['eta'])
    
    def test_save_and_load_model(self):
        """Test saving and loading the model."""
        # Create a temporary file path
        import tempfile
        import os
        
        temp_dir = tempfile.gettempdir()
        model_path = os.path.join(temp_dir, 'market_impact_model.json')
        
        # Save the model
        self.model.save_model(model_path)
        
        # Load the model
        new_model = AlmgrenChrissModel()
        new_model.load_model(model_path)
        
        # Check that the parameters were loaded correctly
        self.assertEqual(new_model.alpha, self.model.alpha)
        self.assertEqual(new_model.beta, self.model.beta)
        self.assertEqual(new_model.gamma, self.model.gamma)
        self.assertEqual(new_model.eta, self.model.eta)
        
        # Clean up
        if os.path.exists(model_path):
            os.remove(model_path)


if __name__ == '__main__':
    unittest.main()
