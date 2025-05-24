"""
Order Book Implementation for OKX Trade Simulator

This module implements a real-time order book that processes and maintains
market data from the OKX exchange.
"""

import time
import logging
from typing import Dict, List, Optional, Union, Any, Tuple

from sortedcontainers import SortedDict

logger = logging.getLogger(__name__)

class OrderBook:
    """
    Order book for a trading instrument.
    Maintains real-time order book state with bids and asks.
    """
    
    def __init__(self, symbol: str, max_depth: int = 100):
        """
        Initialize an order book for a trading instrument.
        
        Args:
            symbol: Trading instrument symbol
            max_depth: Maximum depth to maintain for each side
        """
        self.symbol = symbol
        self.max_depth = max_depth
        
        # Order book state
        self.asks = SortedDict()  # Price -> Quantity
        self.bids = SortedDict()  # Price -> Quantity
        
        # Metadata
        self.last_update_time = 0
        self.is_initialized = False
        
        # Mid price
        self.mid_price = None
        
        logger.info(f"Order book initialized for {symbol}")
    
    def update(self, data: Dict[str, Any]) -> float:
        """Update the order book with new data.
        
        Args:
            data: Dictionary containing order book data with 'asks' and 'bids' lists
            
        Returns:
            float: Timestamp of the update
        """
        # Extract timestamp
        timestamp = data.get('timestamp', time.time() * 1000)  # Default to current time in milliseconds
        
        # Convert timestamp to float if it's a string
        if isinstance(timestamp, str):
            try:
                timestamp = float(timestamp)
            except ValueError:
                # If conversion fails, use current time
                timestamp = time.time() * 1000
        
        # Update asks
        asks = data.get('asks', [])
        if asks:
            self._update_side(asks, is_bid=False)
        
        # Update bids
        bids = data.get('bids', [])
        if bids:
            self._update_side(bids, is_bid=True)
        
        # Update timestamp
        self.last_update_time = timestamp
        
        # Recalculate mid price
        self._calculate_mid_price()
        
        # Set initialized flag
        self.is_initialized = True
        
        return timestamp
    
    def _update_side(self, levels: List[List[Union[str, float]]], is_bid: bool) -> None:
        """Update one side of the order book.
        
        Args:
            levels: List of price levels as [price, quantity] pairs
            is_bid: True for bids, False for asks
        """
        # Get the appropriate side
        side = self.bids if is_bid else self.asks
        
        # Clear the side if this is a snapshot
        side.clear()
        
        # Process each level
        for level in levels:
            # Ensure we have at least price and quantity
            if len(level) < 2:
                continue
            
            # Extract price and quantity
            # OKX API format: [price(str), size(str), liquidated_orders(str), orders(str)]
            try:
                price = float(level[0])
                quantity = float(level[1])
            except (ValueError, TypeError):
                logger.warning(f"Failed to parse price level: {level}")
                continue
            
            # Skip levels with zero quantity
            if quantity <= 0:
                continue
            
            # Add or update the level
            side[price] = quantity
            
        # Trim to max depth if needed
        if is_bid:
            # For bids, keep highest prices (descending order)
            while len(side) > self.max_depth:
                side.popitem(index=0)  # Remove the lowest bid
        else:
            # For asks, keep lowest prices (ascending order)
            while len(side) > self.max_depth:
                side.popitem(index=-1)  # Remove the highest ask
    
    def _calculate_mid_price(self) -> None:
        """Recalculate the mid price."""
        if not self.bids or not self.asks:
            self.mid_price = None
            return
        
        # Get best bid and ask
        best_bid = self.bids.peekitem(-1)[0] if self.bids else None
        best_ask = self.asks.peekitem(0)[0] if self.asks else None
        
        # Calculate mid price
        if best_bid and best_ask:
            self.mid_price = (best_bid + best_ask) / 2
        else:
            self.mid_price = None
    
    def get_mid_price(self) -> float:
        """
        Get the mid-price of the order book.
        
        Returns:
            float: Mid-price or 0 if order book is empty
        """
        if not self.is_initialized or not self.bids or not self.asks:
            return 0
            
        return self.mid_price if self.mid_price else 0
    
    def get_spread(self) -> float:
        """
        Get the bid-ask spread.
        
        Returns:
            float: Spread or 0 if order book is empty
        """
        if not self.is_initialized or not self.bids or not self.asks:
            return 0
            
        best_bid = self.bids.peekitem(-1)[0] if self.bids else 0
        best_ask = self.asks.peekitem(0)[0] if self.asks else 0
        
        if best_bid == 0 or best_ask == 0:
            return 0
            
        return best_ask - best_bid
    
    def get_depth(self, price_levels: int = 10) -> Dict[str, List[List[float]]]:
        """
        Get the order book depth.
        
        Args:
            price_levels: Number of price levels to include
        
        Returns:
            Dict with asks and bids arrays
        """
        asks_depth = []
        bids_depth = []
        
        # Get ask levels
        for i, (price, quantity) in enumerate(self.asks.items()):
            if i >= price_levels:
                break
            asks_depth.append([price, quantity])
        
        # Get bid levels
        for i, (price, quantity) in enumerate(self.bids.items()):
            if i >= price_levels:
                break
            bids_depth.append([price, quantity])
        
        return {
            "asks": asks_depth,
            "bids": bids_depth
        }
    
    def _estimate_price_impact(self, size: float, is_buy: bool) -> float:
        """
        Estimate the price impact of a market order.
        
        Args:
            size: Order size
            is_buy: True for buy order, False for sell order
            
        Returns:
            float: Estimated price impact as a percentage of mid price
        """
        if not self.is_initialized or not self.bids or not self.asks:
            return 0.0
        
        try:
            # Get the relevant side of the book
            book_side = self.asks if is_buy else self.bids
            
            # Get the mid price
            mid_price = self.mid_price
            if not mid_price and self.bids and self.asks:
                mid_price = (self.bids.peekitem(-1)[0] + self.asks.peekitem(0)[0]) / 2
            
            if not mid_price:
                return 0.0
            
            # Calculate the weighted average price for the given size
            remaining_size = size
            total_cost = 0.0
            
            # For asks (buy orders), we want to iterate in ascending price order
            # For bids (sell orders), we want to iterate in descending price order
            if is_buy:
                # For buys, start with lowest asks
                items = list(book_side.items())
            else:
                # For sells, start with highest bids
                items = list(reversed(list(book_side.items())))
            
            for price, qty in items:
                if remaining_size <= 0:
                    break
                
                # Calculate how much we can take from this level
                taken = min(remaining_size, qty)
                total_cost += taken * price
                remaining_size -= taken
            
            # If we couldn't fill the entire order, use the last price
            if remaining_size > 0:
                if book_side:
                    last_price = items[-1][0] if items else (mid_price * 1.05 if is_buy else mid_price * 0.95)
                    total_cost += remaining_size * last_price
                else:
                    # No liquidity, assume high impact
                    return 0.05  # 5% impact
            
            # Calculate the average price
            avg_price = total_cost / size
            
            # Calculate the impact as a percentage of mid price
            impact = abs(avg_price - mid_price) / mid_price
            
            return impact
            
        except Exception as e:
            logger.error(f"Error estimating price impact: {str(e)}")
            return 0.0
    
    def calculate_market_depth(self, price_range_percent: float = 1.0) -> Dict[str, float]:
        """
        Calculate market depth statistics.
        
        Args:
            price_range_percent: Price range as percentage of mid price
        
        Returns:
            Dict with market depth statistics
        """
        if not self.is_initialized or not self.bids or not self.asks:
            return {
                "bid_volume": 0,
                "ask_volume": 0,
                "bid_ask_ratio": 0,
                "mid_price": 0
            }
        
        mid_price = self.get_mid_price()
        if mid_price == 0:
            return {
                "bid_volume": 0,
                "ask_volume": 0,
                "bid_ask_ratio": 0,
                "mid_price": 0
            }
        
        # Calculate price range
        price_range = mid_price * (price_range_percent / 100)
        min_price = mid_price - price_range
        max_price = mid_price + price_range
        
        # Calculate volumes
        bid_volume = sum(quantity for price, quantity in self.bids.items() if price >= min_price)
        ask_volume = sum(quantity for price, quantity in self.asks.items() if price <= max_price)
        
        # Calculate bid/ask ratio
        bid_ask_ratio = bid_volume / ask_volume if ask_volume > 0 else 0
        
        return {
            "bid_volume": bid_volume,
            "ask_volume": ask_volume,
            "bid_ask_ratio": bid_ask_ratio,
            "mid_price": mid_price
        }
        
    def get_order_book_features(self) -> Dict[str, float]:
        """
        Extract features from the order book for model input.
        
        Returns:
            Dict of features:
                - mid_price: Current mid price
                - spread: Current spread
                - bid_ask_imbalance: Imbalance between bid and ask volumes
                - depth_1_5_10: Liquidity at different depths
                - ...
        """
        features = {}
        
        # Check if order book is initialized
        if not self.is_initialized or not self.bids or not self.asks:
            logger.warning("Order book not initialized or empty, cannot extract features")
            return features
        
        try:
            # Get best bid and ask
            best_bid_price, best_bid_qty = self.bids.peekitem(-1)
            best_ask_price, best_ask_qty = self.asks.peekitem(0)
            
            # Basic features
            features['mid_price'] = (best_bid_price + best_ask_price) / 2
            features['spread'] = best_ask_price - best_bid_price
            features['spread_pct'] = (best_ask_price - best_bid_price) / features['mid_price'] * 100
            
            # Volume imbalance
            bid_volume = sum(qty for _, qty in self.bids.items())
            ask_volume = sum(qty for _, qty in self.asks.items())
            total_volume = bid_volume + ask_volume
            
            if total_volume > 0:
                features['bid_ask_imbalance'] = (bid_volume - ask_volume) / total_volume
            else:
                features['bid_ask_imbalance'] = 0
            
            # Depth at different levels
            for depth in [1, 5, 10]:
                # For bids, we want the highest prices (last n items)
                bid_items = list(self.bids.items())
                bid_depth = sum(qty for _, qty in bid_items[-depth:]) if len(bid_items) >= depth else sum(qty for _, qty in bid_items)
                
                # For asks, we want the lowest prices (first n items)
                ask_items = list(self.asks.items())
                ask_depth = sum(qty for _, qty in ask_items[:depth]) if len(ask_items) >= depth else sum(qty for _, qty in ask_items)
                
                features[f'bid_depth_{depth}'] = bid_depth
                features[f'ask_depth_{depth}'] = ask_depth
                features[f'depth_imbalance_{depth}'] = (bid_depth - ask_depth) / (bid_depth + ask_depth) if (bid_depth + ask_depth) > 0 else 0
            
            # Price impact estimates
            for size in [1, 5, 10]:
                features[f'bid_impact_{size}'] = self._estimate_price_impact(size, is_buy=False)
                features[f'ask_impact_{size}'] = self._estimate_price_impact(size, is_buy=True)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting order book features: {str(e)}")
            return {}
