import unittest
import numpy as np
from unittest.mock import patch
from src.models.slippage_model import SlippageModel

class TestSlippageModel(unittest.TestCase):
    """Test cases for the SlippageModel class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.slippage_model = SlippageModel()
        
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
    
    def test_predict_slippage_small_order(self):
        """Test predicting slippage for a small order."""
        # For a small order, slippage should be minimal
        quantity_usd = 1000.0
        slippage = self.slippage_model.predict_slippage(self.sample_features, quantity_usd)
        
        # Check that the slippage is reasonable
        self.assertGreaterEqual(slippage, 0.0)
        self.assertLessEqual(slippage, 0.001)  # Less than 0.1%
    
    def test_predict_slippage_large_order(self):
        """Test predicting slippage for a large order."""
        # For a large order, slippage should be significant
        quantity_usd = 100000.0
        slippage = self.slippage_model.predict_slippage(self.sample_features, quantity_usd)
        
        # Check that the slippage is reasonable
        self.assertGreater(slippage, 0.001)  # Greater than 0.1%
    
    def test_predict_slippage_with_imbalance(self):
        """Test predicting slippage with volume imbalance."""
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
        
        # For a buy order, slippage should be higher when ask-heavy
        quantity_usd = 50000.0
        is_buy = True
        
        balanced_slippage = self.slippage_model.predict_slippage(balanced_features, quantity_usd, is_buy)
        bid_heavy_slippage = self.slippage_model.predict_slippage(bid_heavy_features, quantity_usd, is_buy)
        ask_heavy_slippage = self.slippage_model.predict_slippage(ask_heavy_features, quantity_usd, is_buy)
        
        # Slippage should be higher when the order book is ask-heavy for a buy order
        self.assertGreater(ask_heavy_slippage, balanced_slippage)
        self.assertLess(bid_heavy_slippage, balanced_slippage)
        
        # For a sell order, slippage should be higher when bid-heavy
        is_buy = False
        
        balanced_slippage = self.slippage_model.predict_slippage(balanced_features, quantity_usd, is_buy)
        bid_heavy_slippage = self.slippage_model.predict_slippage(bid_heavy_features, quantity_usd, is_buy)
        ask_heavy_slippage = self.slippage_model.predict_slippage(ask_heavy_features, quantity_usd, is_buy)
        
        # Slippage should be higher when the order book is bid-heavy for a sell order
        self.assertLess(ask_heavy_slippage, balanced_slippage)
        self.assertGreater(bid_heavy_slippage, balanced_slippage)
    
    def test_predict_slippage_with_spread(self):
        """Test predicting slippage with different spreads."""
        # Create features with different spreads
        narrow_spread_features = self.sample_features.copy()
        narrow_spread_features['spread'] = 0.1
        narrow_spread_features['spread_percentage'] = 0.0001
        
        wide_spread_features = self.sample_features.copy()
        wide_spread_features['spread'] = 1.0
        wide_spread_features['spread_percentage'] = 0.001
        
        # For the same order size, slippage should be higher with a wider spread
        quantity_usd = 50000.0
        
        narrow_spread_slippage = self.slippage_model.predict_slippage(narrow_spread_features, quantity_usd)
        wide_spread_slippage = self.slippage_model.predict_slippage(wide_spread_features, quantity_usd)
        
        # Slippage should be higher with a wider spread
        self.assertGreater(wide_spread_slippage, narrow_spread_slippage)
    
    def test_predict_slippage_with_depth(self):
        """Test predicting slippage with different order book depths."""
        # Create features with different order book depths
        deep_book_features = self.sample_features.copy()
        deep_book_features['bid_depth'] = [
            [95445.4, 2000.0],
            [95445.3, 1500.0],
            [95440.0, 1000.0],
            [95435.0, 800.0],
            [95430.0, 500.0]
        ]
        deep_book_features['ask_depth'] = [
            [95445.5, 2000.0],
            [95448.0, 1500.0],
            [95450.0, 1000.0],
            [95455.0, 800.0],
            [95460.0, 500.0]
        ]
        
        shallow_book_features = self.sample_features.copy()
        shallow_book_features['bid_depth'] = [
            [95445.4, 200.0],
            [95445.3, 150.0],
            [95440.0, 100.0],
            [95435.0, 80.0],
            [95430.0, 50.0]
        ]
        shallow_book_features['ask_depth'] = [
            [95445.5, 200.0],
            [95448.0, 150.0],
            [95450.0, 100.0],
            [95455.0, 80.0],
            [95460.0, 50.0]
        ]
        
        # For the same order size, slippage should be higher with a shallower book
        quantity_usd = 50000.0
        
        deep_book_slippage = self.slippage_model.predict_slippage(deep_book_features, quantity_usd)
        shallow_book_slippage = self.slippage_model.predict_slippage(shallow_book_features, quantity_usd)
        
        # Slippage should be higher with a shallower book
        self.assertGreater(shallow_book_slippage, deep_book_slippage)
    
    def test_predict_slippage_zero_quantity(self):
        """Test predicting slippage with zero quantity."""
        # For zero quantity, slippage should be zero
        quantity_usd = 0.0
        slippage = self.slippage_model.predict_slippage(self.sample_features, quantity_usd)
        
        # Check that the slippage is zero
        self.assertEqual(slippage, 0.0)
    
    def test_predict_slippage_negative_quantity(self):
        """Test predicting slippage with negative quantity."""
        # For negative quantity, slippage should be calculated using the absolute value
        quantity_usd = -50000.0
        slippage = self.slippage_model.predict_slippage(self.sample_features, quantity_usd)
        
        # Check that the slippage is reasonable
        self.assertGreater(slippage, 0.0)
    
    @patch('sklearn.linear_model.LinearRegression')
    def test_train_model(self, mock_linear_regression):
        """Test training the slippage model."""
        # Create mock training data
        historical_data = []
        for i in range(100):
            features = self.sample_features.copy()
            features['mid_price'] = 95000.0 + i * 10.0
            features['spread'] = 0.1 + i * 0.01
            features['volume_imbalance'] = -0.5 + i * 0.01
            
            order_size = 1000.0 + i * 100.0
            slippage = 0.0001 + i * 0.0001
            
            historical_data.append({
                'features': features,
                'order_size': order_size,
                'slippage': slippage
            })
        
        # Train the model
        self.slippage_model.train_model(historical_data)
        
        # Check that the model was trained
        mock_linear_regression.return_value.fit.assert_called_once()
    
    def test_extract_features(self):
        """Test extracting features for the slippage model."""
        # Extract features from the sample features
        features = self.slippage_model.extract_features(self.sample_features, 50000.0)
        
        # Check that the features have the expected keys
        self.assertIn('spread_percentage', features)
        self.assertIn('volume_imbalance', features)
        self.assertIn('order_size_relative', features)
        
        # Check that the features have reasonable values
        self.assertGreaterEqual(features['spread_percentage'], 0.0)
        self.assertGreaterEqual(features['order_size_relative'], 0.0)
        self.assertLessEqual(features['volume_imbalance'], 1.0)
        self.assertGreaterEqual(features['volume_imbalance'], -1.0)
    
    def test_calculate_slippage_from_depth(self):
        """Test calculating slippage from order book depth."""
        # Calculate slippage for a buy order
        is_buy = True
        quantity_usd = 50000.0
        slippage = self.slippage_model.calculate_slippage_from_depth(
            self.sample_features['ask_depth'],
            self.sample_features['mid_price'],
            quantity_usd
        )
        
        # Check that the slippage is reasonable
        self.assertGreater(slippage, 0.0)
        
        # Calculate slippage for a sell order
        is_buy = False
        slippage = self.slippage_model.calculate_slippage_from_depth(
            self.sample_features['bid_depth'],
            self.sample_features['mid_price'],
            quantity_usd
        )
        
        # Check that the slippage is reasonable
        self.assertGreater(slippage, 0.0)
    
    def test_save_and_load_model(self):
        """Test saving and loading the slippage model."""
        # Create a temporary file path
        import tempfile
        import os
        
        temp_dir = tempfile.gettempdir()
        model_path = os.path.join(temp_dir, 'slippage_model.pkl')
        
        # Save the model
        self.slippage_model.save_model(model_path)
        
        # Load the model
        new_model = SlippageModel()
        new_model.load_model(model_path)
        
        # Check that the model was loaded
        self.assertIsNotNone(new_model.model)
        
        # Clean up
        if os.path.exists(model_path):
            os.remove(model_path)


if __name__ == '__main__':
    unittest.main()
