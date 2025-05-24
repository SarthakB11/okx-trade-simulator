import unittest
import json
from src.data.orderbook import OrderBook

class TestOrderBook(unittest.TestCase):
    """Test cases for the OrderBook class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.orderbook = OrderBook()
        
        # Sample order book data
        self.sample_data = {
            "timestamp": "2025-05-04T10:39:13Z",
            "exchange": "OKX",
            "symbol": "BTC-USDT-SWAP",
            "asks": [
                ["95445.5", "9.06"],
                ["95448.0", "2.05"],
                ["95450.0", "5.10"],
                ["95455.0", "3.20"],
                ["95460.0", "7.50"]
            ],
            "bids": [
                ["95445.4", "1104.23"],
                ["95445.3", "0.02"],
                ["95440.0", "10.50"],
                ["95435.0", "8.75"],
                ["95430.0", "15.30"]
            ]
        }
    
    def test_update(self):
        """Test updating the order book with new data."""
        # Update the order book
        update_time = self.orderbook.update(self.sample_data)
        
        # Check that the update time is reasonable
        self.assertGreaterEqual(update_time, 0)
        
        # Check that the order book properties were updated
        self.assertEqual(self.orderbook.timestamp, "2025-05-04T10:39:13Z")
        self.assertEqual(self.orderbook.exchange, "OKX")
        self.assertEqual(self.orderbook.symbol, "BTC-USDT-SWAP")
        
        # Check that the order book has the correct number of levels
        self.assertEqual(len(self.orderbook.asks), 5)
        self.assertEqual(len(self.orderbook.bids), 5)
    
    def test_get_best_bid_ask(self):
        """Test getting the best bid and ask prices."""
        # Update the order book
        self.orderbook.update(self.sample_data)
        
        # Check best bid and ask
        self.assertEqual(self.orderbook.get_best_bid(), 95445.4)
        self.assertEqual(self.orderbook.get_best_ask(), 95445.5)
    
    def test_get_mid_price(self):
        """Test getting the mid price."""
        # Update the order book
        self.orderbook.update(self.sample_data)
        
        # Check mid price
        expected_mid = (95445.4 + 95445.5) / 2
        self.assertEqual(self.orderbook.get_mid_price(), expected_mid)
    
    def test_get_spread(self):
        """Test getting the bid-ask spread."""
        # Update the order book
        self.orderbook.update(self.sample_data)
        
        # Check spread
        expected_spread = 95445.5 - 95445.4
        self.assertEqual(self.orderbook.get_spread(), expected_spread)
    
    def test_get_depth(self):
        """Test getting the order book depth."""
        # Update the order book
        self.orderbook.update(self.sample_data)
        
        # Get depth with default levels (10)
        bids, asks = self.orderbook.get_depth()
        
        # Check that we got the correct number of levels
        self.assertEqual(len(bids), 5)  # We only have 5 levels in the sample data
        self.assertEqual(len(asks), 5)  # We only have 5 levels in the sample data
        
        # Check that the levels are in the correct order
        self.assertEqual(bids[0][0], 95445.4)  # Highest bid first
        self.assertEqual(asks[0][0], 95445.5)  # Lowest ask first
    
    def test_calculate_market_order_cost(self):
        """Test calculating the cost of a market order."""
        # Update the order book
        self.orderbook.update(self.sample_data)
        
        # Calculate cost of a buy order
        total_cost, avg_price, slippage = self.orderbook.calculate_market_order_cost(1000.0, True)
        
        # Check that the results are reasonable
        self.assertGreater(total_cost, 0)
        self.assertGreater(avg_price, 0)
        
        # Calculate cost of a sell order
        total_cost, avg_price, slippage = self.orderbook.calculate_market_order_cost(1000.0, False)
        
        # Check that the results are reasonable
        self.assertGreater(total_cost, 0)
        self.assertGreater(avg_price, 0)
    
    def test_get_order_book_features(self):
        """Test extracting features from the order book."""
        # Update the order book
        self.orderbook.update(self.sample_data)
        
        # Get features
        features = self.orderbook.get_order_book_features()
        
        # Check that the features dictionary contains the expected keys
        self.assertIn('mid_price', features)
        self.assertIn('spread', features)
        self.assertIn('spread_percentage', features)
        self.assertIn('bid_volume', features)
        self.assertIn('ask_volume', features)
        self.assertIn('volume_imbalance', features)
    
    def test_empty_order_book(self):
        """Test behavior with an empty order book."""
        # Create an empty order book
        empty_data = {
            "timestamp": "2025-05-04T10:39:13Z",
            "exchange": "OKX",
            "symbol": "BTC-USDT-SWAP",
            "asks": [],
            "bids": []
        }
        
        # Update the order book
        self.orderbook.update(empty_data)
        
        # Check that the best bid and ask are None
        self.assertIsNone(self.orderbook.get_best_bid())
        self.assertIsNone(self.orderbook.get_best_ask())
        
        # Check that the mid price is None
        self.assertIsNone(self.orderbook.get_mid_price())
        
        # Check that the spread is None
        self.assertIsNone(self.orderbook.get_spread())
        
        # Check that the depth is empty
        bids, asks = self.orderbook.get_depth()
        self.assertEqual(len(bids), 0)
        self.assertEqual(len(asks), 0)
    
    def test_string_representation(self):
        """Test the string representation of the order book."""
        # Update the order book
        self.orderbook.update(self.sample_data)
        
        # Get string representation
        order_book_str = str(self.orderbook)
        
        # Check that the string contains important information
        self.assertIn("BTC-USDT-SWAP", order_book_str)
        self.assertIn("OKX", order_book_str)
        self.assertIn("Asks", order_book_str)
        self.assertIn("Bids", order_book_str)


if __name__ == '__main__':
    unittest.main()
