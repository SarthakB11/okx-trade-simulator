import logging
import time
from typing import Dict, List, Tuple, Optional
from sortedcontainers import SortedDict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("orderbook")

class OrderBook:
    """
    Represents the L2 order book state with efficient data structures for fast access and updates.
    Uses SortedDict for O(log n) operations on price levels.
    """
    def __init__(self):
        """Initialize an empty order book."""
        # SortedDict for bids (descending order by price)
        self.bids = SortedDict()
        # SortedDict for asks (ascending order by price)
        self.asks = SortedDict()
        self.timestamp = None
        self.exchange = None
        self.symbol = None
        self.last_update_time = None
    
    def update(self, data: Dict):
        """
        Update the order book with new data.
        
        Args:
            data: Dictionary containing order book data with keys:
                 'timestamp', 'exchange', 'symbol', 'asks', 'bids'
        """
        start_time = time.perf_counter()
        
        try:
            self.timestamp = data.get('timestamp')
            self.exchange = data.get('exchange')
            self.symbol = data.get('symbol')
            
            # Clear and update bids
            self.bids.clear()
            for price_str, qty_str in data.get('bids', []):
                price = float(price_str)
                qty = float(qty_str)
                if qty > 0:
                    # Store bids with negative key for descending order
                    self.bids[-price] = (price, qty)
            
            # Clear and update asks
            self.asks.clear()
            for price_str, qty_str in data.get('asks', []):
                price = float(price_str)
                qty = float(qty_str)
                if qty > 0:
                    self.asks[price] = (price, qty)
            
            self.last_update_time = time.time()
            
        except Exception as e:
            logger.error(f"Error updating order book: {str(e)}")
            raise
        
        # Calculate and log update time
        update_time_ms = (time.perf_counter() - start_time) * 1000
        logger.debug(f"Order book updated in {update_time_ms:.3f} ms")
        
        return update_time_ms
    
    def get_best_bid(self) -> Optional[float]:
        """Get the best (highest) bid price."""
        if not self.bids:
            return None
        # First key is the highest bid (stored with negative value)
        return -self.bids.keys()[0]
    
    def get_best_ask(self) -> Optional[float]:
        """Get the best (lowest) ask price."""
        if not self.asks:
            return None
        # First key is the lowest ask
        return self.asks.keys()[0]
    
    def get_mid_price(self) -> Optional[float]:
        """Get the mid price (average of best bid and best ask)."""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        
        if best_bid is None or best_ask is None:
            return None
            
        return (best_bid + best_ask) / 2
    
    def get_spread(self) -> Optional[float]:
        """Get the bid-ask spread."""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        
        if best_bid is None or best_ask is None:
            return None
            
        return best_ask - best_bid
    
    def get_spread_percentage(self) -> Optional[float]:
        """Get the bid-ask spread as a percentage of the mid price."""
        spread = self.get_spread()
        mid_price = self.get_mid_price()
        
        if spread is None or mid_price is None or mid_price == 0:
            return None
            
        return (spread / mid_price) * 100
    
    def get_depth(self, levels: int = 10) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
        """
        Get the order book depth up to the specified number of levels.
        
        Args:
            levels: Number of price levels to retrieve
            
        Returns:
            Tuple of (bids, asks) where each is a list of (price, quantity) tuples
        """
        bids_list = []
        asks_list = []
        
        # Get bid levels (highest first)
        for i, key in enumerate(self.bids.keys()):
            if i >= levels:
                break
            price, qty = self.bids[key]
            bids_list.append((price, qty))
        
        # Get ask levels (lowest first)
        for i, key in enumerate(self.asks.keys()):
            if i >= levels:
                break
            price, qty = self.asks[key]
            asks_list.append((price, qty))
        
        return bids_list, asks_list
    
    def calculate_market_order_cost(self, quantity_usd: float, is_buy: bool = True) -> Tuple[float, float, float]:
        """
        Calculate the cost of a market order by walking the order book.
        
        Args:
            quantity_usd: Order size in USD
            is_buy: True for buy order, False for sell order
            
        Returns:
            Tuple of (total_cost, average_price, slippage_percentage)
        """
        if quantity_usd <= 0:
            return 0.0, 0.0, 0.0
        
        remaining_quantity_usd = quantity_usd
        total_cost = 0.0
        total_quantity = 0.0
        
        # Reference price for slippage calculation
        reference_price = self.get_mid_price()
        if reference_price is None:
            logger.warning("Cannot calculate market order cost: no mid price available")
            return 0.0, 0.0, 0.0
        
        if is_buy:
            # Walk the ask side for a buy order
            for price_level in self.asks.keys():
                price, qty = self.asks[price_level]
                
                # Convert quantity at this level to USD
                level_quantity_usd = price * qty
                
                # How much we can fill at this level
                fill_quantity_usd = min(remaining_quantity_usd, level_quantity_usd)
                fill_quantity_asset = fill_quantity_usd / price
                
                # Add to totals
                total_cost += fill_quantity_asset * price
                total_quantity += fill_quantity_asset
                
                # Reduce remaining quantity
                remaining_quantity_usd -= fill_quantity_usd
                
                # Break if order is filled
                if remaining_quantity_usd <= 0:
                    break
        else:
            # Walk the bid side for a sell order
            for price_level in self.bids.keys():
                price, qty = self.bids[price_level]
                
                # Convert quantity at this level to USD
                level_quantity_usd = price * qty
                
                # How much we can fill at this level
                fill_quantity_usd = min(remaining_quantity_usd, level_quantity_usd)
                fill_quantity_asset = fill_quantity_usd / price
                
                # Add to totals
                total_cost += fill_quantity_asset * price
                total_quantity += fill_quantity_asset
                
                # Reduce remaining quantity
                remaining_quantity_usd -= fill_quantity_usd
                
                # Break if order is filled
                if remaining_quantity_usd <= 0:
                    break
        
        # Check if order was completely filled
        if remaining_quantity_usd > 0:
            logger.warning(f"Order not completely filled: {remaining_quantity_usd} USD remaining")
        
        # Calculate average price
        average_price = total_cost / total_quantity if total_quantity > 0 else 0
        
        # Calculate slippage percentage
        slippage_percentage = ((average_price / reference_price) - 1) * 100 if is_buy else \
                             (1 - (average_price / reference_price)) * 100
        
        return total_cost, average_price, slippage_percentage
    
    def get_order_book_features(self) -> Dict:
        """
        Extract features from the order book for use in models.
        
        Returns:
            Dictionary of features including spread, depth imbalance, etc.
        """
        features = {}
        
        # Basic features
        features['mid_price'] = self.get_mid_price()
        features['spread'] = self.get_spread()
        features['spread_percentage'] = self.get_spread_percentage()
        
        # Get depth
        bids, asks = self.get_depth(levels=10)
        
        # Calculate volume at different levels
        bid_volume = sum(qty for _, qty in bids)
        ask_volume = sum(qty for _, qty in asks)
        
        features['bid_volume'] = bid_volume
        features['ask_volume'] = ask_volume
        features['volume_imbalance'] = (bid_volume - ask_volume) / (bid_volume + ask_volume) if (bid_volume + ask_volume) > 0 else 0
        
        # Calculate weighted average prices
        if bids:
            features['weighted_bid_price'] = sum(price * qty for price, qty in bids) / sum(qty for _, qty in bids)
        else:
            features['weighted_bid_price'] = None
            
        if asks:
            features['weighted_ask_price'] = sum(price * qty for price, qty in asks) / sum(qty for _, qty in asks)
        else:
            features['weighted_ask_price'] = None
        
        # Calculate depth at different price levels (1%, 2%, 5% from mid)
        mid_price = features['mid_price']
        if mid_price is not None:
            # Bid side depth
            features['bid_depth_1pct'] = sum(qty for price, qty in bids if price >= mid_price * 0.99)
            features['bid_depth_2pct'] = sum(qty for price, qty in bids if price >= mid_price * 0.98)
            features['bid_depth_5pct'] = sum(qty for price, qty in bids if price >= mid_price * 0.95)
            
            # Ask side depth
            features['ask_depth_1pct'] = sum(qty for price, qty in asks if price <= mid_price * 1.01)
            features['ask_depth_2pct'] = sum(qty for price, qty in asks if price <= mid_price * 1.02)
            features['ask_depth_5pct'] = sum(qty for price, qty in asks if price <= mid_price * 1.05)
        
        return features
    
    def __str__(self) -> str:
        """String representation of the order book."""
        bid_levels, ask_levels = self.get_depth(5)
        
        result = f"Order Book: {self.symbol} @ {self.exchange}\n"
        result += f"Timestamp: {self.timestamp}\n"
        result += "Asks:\n"
        
        # Print asks in reverse order (highest first)
        for price, qty in reversed(ask_levels):
            result += f"  {price:.2f}: {qty:.6f}\n"
            
        # Print mid price
        mid_price = self.get_mid_price()
        if mid_price:
            result += f"Mid: {mid_price:.2f}\n"
        
        # Print bids
        result += "Bids:\n"
        for price, qty in bid_levels:
            result += f"  {price:.2f}: {qty:.6f}\n"
            
        return result
