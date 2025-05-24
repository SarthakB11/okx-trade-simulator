import unittest
import numpy as np
from unittest.mock import patch
from src.models.maker_taker_model import MakerTakerModel

class TestMakerTakerModel(unittest.TestCase):
    """Test cases for the MakerTakerModel class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.model = MakerTakerModel()
        
        # Sample order book features
        self.sample_features = {
            'mid_price': 95445.45,
            'spread': 0.1,
            'spread_percentage': 0.0001,
            'bid_volume': 1138.8,
            'ask_volume': 26.91,
            'volume_imbalance': 0.954,
            'bid_depth': [
                [95445.4, 1104.23],
                [95445.3, 0.02],
                [95440.0, 10.50],
                [95435.0, 8.75],
                [95430.0, 15.30]
            ],
            'ask_depth': [
                [95445.5, 9.06],
                [95448.0, 2.05],
                [95450.0, 5.10],
                [95455.0, 3.20],
                [95460.0, 7.50]
            ]
        }
    
    def test_predict_proportion_small_order(self):
        """Test predicting maker/taker proportion for a small order."""
        # For a small order, we expect a high maker proportion
        quantity_usd = 1000.0
        maker_proportion = self.model.predict_proportion(self.sample_features, quantity_usd)
        
        # Check that the proportion is reasonable
        self.assertGreaterEqual(maker_proportion, 0.0)
        self.assertLessEqual(maker_proportion, 1.0)
        self.assertGreater(maker_proportion, 0.5)  # Small orders should have higher maker proportion
    
    def test_predict_proportion_large_order(self):
        """Test predicting maker/taker proportion for a large order."""
        # For a large order, we expect a low maker proportion
        quantity_usd = 100000.0
        maker_proportion = self.model.predict_proportion(self.sample_features, quantity_usd)
        
        # Check that the proportion is reasonable
        self.assertGreaterEqual(maker_proportion, 0.0)
        self.assertLessEqual(maker_proportion, 1.0)
        self.assertLess(maker_proportion, 0.5)  # Large orders should have lower maker proportion
    
    def test_predict_proportion_with_imbalance(self):
        """Test predicting maker/taker proportion with volume imbalance."""
        # Create features with different volume imbalances
        balanced_features = self.sample_features.copy()
        balanced_features['bid_volume'] = 100.0
        balanced_features['ask_volume'] = 100.0
        balanced_features['volume_imbalance'] = 0.0
        
        bid_heavy_features = self.sample_features.copy()
        bid_heavy_features['bid_volume'] = 200.0
        bid_heavy_features['ask_volume'] = 100.0
        bid_heavy_features['volume_imbalance'] = 0.333
        
        ask_heavy_features = self.sample_features.copy()
        ask_heavy_features['bid_volume'] = 100.0
        ask_heavy_features['ask_volume'] = 200.0
        ask_heavy_features['volume_imbalance'] = -0.333
        
        # For a buy order, maker proportion should be higher when bid-heavy
        quantity_usd = 50000.0
        is_buy = True
        
        balanced_proportion = self.model.predict_proportion(balanced_features, quantity_usd, is_buy)
        bid_heavy_proportion = self.model.predict_proportion(bid_heavy_features, quantity_usd, is_buy)
        ask_heavy_proportion = self.model.predict_proportion(ask_heavy_features, quantity_usd, is_buy)
        
        # Maker proportion should be higher when the order book is bid-heavy for a buy order
        self.assertGreater(bid_heavy_proportion, balanced_proportion)
        self.assertLess(ask_heavy_proportion, balanced_proportion)
        
        # For a sell order, maker proportion should be higher when ask-heavy
        is_buy = False
        
        balanced_proportion = self.model.predict_proportion(balanced_features, quantity_usd, is_buy)
        bid_heavy_proportion = self.model.predict_proportion(bid_heavy_features, quantity_usd, is_buy)
        ask_heavy_proportion = self.model.predict_proportion(ask_heavy_features, quantity_usd, is_buy)
        
        # Maker proportion should be higher when the order book is ask-heavy for a sell order
        self.assertLess(bid_heavy_proportion, balanced_proportion)
        self.assertGreater(ask_heavy_proportion, balanced_proportion)
    
    def test_predict_proportion_with_spread(self):
        """Test predicting maker/taker proportion with different spreads."""
        # Create features with different spreads
        narrow_spread_features = self.sample_features.copy()
        narrow_spread_features['spread'] = 0.1
        narrow_spread_features['spread_percentage'] = 0.0001
        
        wide_spread_features = self.sample_features.copy()
        wide_spread_features['spread'] = 1.0
        wide_spread_features['spread_percentage'] = 0.001
        
        # For the same order size, maker proportion should be higher with a wider spread
        quantity_usd = 50000.0
        
        narrow_spread_proportion = self.model.predict_proportion(narrow_spread_features, quantity_usd)
        wide_spread_proportion = self.model.predict_proportion(wide_spread_features, quantity_usd)
        
        # Maker proportion should be higher with a wider spread
        self.assertGreater(wide_spread_proportion, narrow_spread_proportion)
    
    def test_predict_proportion_zero_quantity(self):
        """Test predicting maker/taker proportion with zero quantity."""
        # For zero quantity, the proportion should be 1.0 (all maker)
        quantity_usd = 0.0
        maker_proportion = self.model.predict_proportion(self.sample_features, quantity_usd)
        
        # Check that the proportion is 1.0
        self.assertEqual(maker_proportion, 1.0)
    
    def test_predict_proportion_negative_quantity(self):
        """Test predicting maker/taker proportion with negative quantity."""
        # For negative quantity, the proportion should be calculated using the absolute value
        quantity_usd = -50000.0
        maker_proportion = self.model.predict_proportion(self.sample_features, quantity_usd)
        
        # Check that the proportion is reasonable
        self.assertGreaterEqual(maker_proportion, 0.0)
        self.assertLessEqual(maker_proportion, 1.0)
    
    @patch('sklearn.linear_model.LogisticRegression')
    def test_train_model(self, mock_logistic_regression):
        """Test training the maker/taker model."""
        # Create mock training data
        historical_data = []
        for i in range(100):
            features = self.sample_features.copy()
            features['mid_price'] = 95000.0 + i * 10.0
            features['spread'] = 0.1 + i * 0.01
            features['volume_imbalance'] = -0.5 + i * 0.01
            
            order_size = 1000.0 + i * 100.0
            maker_proportion = 0.8 - i * 0.005  # Decreasing maker proportion as order size increases
            
            historical_data.append({
                'features': features,
                'order_size': order_size,
                'maker_proportion': maker_proportion
            })
        
        # Train the model
        self.model.train_model(historical_data)
        
        # Check that the model was trained
        mock_logistic_regression.return_value.fit.assert_called_once()
    
    def test_extract_features(self):
        """Test extracting features for the maker/taker model."""
        # Extract features from the sample features
        features = self.model.extract_features(self.sample_features, 50000.0)
        
        # Check that the features have the expected keys
        self.assertIn('spread_percentage', features)
        self.assertIn('volume_imbalance', features)
        self.assertIn('order_size_relative', features)
        
        # Check that the features have reasonable values
        self.assertGreaterEqual(features['spread_percentage'], 0.0)
        self.assertGreaterEqual(features['order_size_relative'], 0.0)
        self.assertLessEqual(features['volume_imbalance'], 1.0)
        self.assertGreaterEqual(features['volume_imbalance'], -1.0)
    
    def test_save_and_load_model(self):
        """Test saving and loading the maker/taker model."""
        # Create a temporary file path
        import tempfile
        import os
        
        temp_dir = tempfile.gettempdir()
        model_path = os.path.join(temp_dir, 'maker_taker_model.pkl')
        
        # Save the model
        self.model.save_model(model_path)
        
        # Load the model
        new_model = MakerTakerModel()
        new_model.load_model(model_path)
        
        # Check that the model was loaded
        self.assertIsNotNone(new_model.model)
        
        # Clean up
        if os.path.exists(model_path):
            os.remove(model_path)
    
    def test_calculate_expected_fees(self):
        """Test calculating expected fees based on maker/taker proportion."""
        # Set up test parameters
        exchange = "OKX"
        fee_tier = 0
        order_type = "limit"
        quantity_usd = 10000.0
        maker_proportion = 0.7  # 70% maker, 30% taker
        
        # Calculate expected fees
        expected_fees = self.model.calculate_expected_fees(
            exchange,
            fee_tier,
            order_type,
            quantity_usd,
            maker_proportion
        )
        
        # Check that the fees are reasonable
        self.assertGreaterEqual(expected_fees, 0.0)
        
        # For OKX VIP 0, maker fee is 0.08% and taker fee is 0.10%
        # Expected fee = (0.7 * 0.08% + 0.3 * 0.10%) * 10000 = (0.7 * 8 + 0.3 * 10) = 5.6 + 3 = 8.6
        expected_fee_value = (0.7 * 8.0) + (0.3 * 10.0)
        self.assertEqual(expected_fees, expected_fee_value)


if __name__ == '__main__':
    unittest.main()
