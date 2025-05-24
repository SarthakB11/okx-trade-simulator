import logging
import numpy as np
from typing import Dict, Optional
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("maker_taker_model")

class MakerTakerModel:
    """
    Logistic regression model to predict the proportion of an order
    that will be filled as maker vs. taker.
    """
    
    def __init__(self):
        """Initialize the maker/taker proportion prediction model."""
        self.model = LogisticRegression(random_state=42)
        self.scaler = StandardScaler()
        self.is_fitted = False
        
        # Pre-trained coefficients (these would normally be learned from historical data)
        # For this assignment, we'll use reasonable default values
        self.default_coefficients = {
            'intercept': 2.0,  # Bias toward taker for market orders
            'order_type_market': 2.0,  # Strong bias for market orders being taker
            'spread_percentage': 0.5,  # Higher spread -> higher taker proportion
            'order_size_to_depth_ratio': 0.8,  # Higher ratio -> higher taker proportion
            'volatility': 0.3  # Higher volatility -> higher taker proportion
        }
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        """
        Fit the logistic regression model using historical data.
        
        Args:
            X: Feature matrix with columns [order_type_market, spread_percentage, 
                                           order_size_to_depth_ratio, volatility]
            y: Binary target values (1 for taker, 0 for maker)
        """
        try:
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Fit model
            self.model.fit(X_scaled, y)
            self.is_fitted = True
            
            logger.info(f"Maker/taker model fitted successfully with {len(X)} samples")
            
            if hasattr(self.model, 'coef_'):
                logger.info(f"Model coefficients: {self.model.coef_}")
                logger.info(f"Model intercept: {self.model.intercept_}")
                
        except Exception as e:
            logger.error(f"Error fitting maker/taker model: {str(e)}")
            self.is_fitted = False
    
    def predict_proportion(self, 
                          order_book_features: Dict, 
                          quantity_usd: float,
                          order_type: str = 'market',
                          volatility: float = 0.02) -> Dict[str, float]:
        """
        Predict the maker/taker proportion for a given order.
        
        Args:
            order_book_features: Features extracted from the order book
            quantity_usd: Order size in USD
            order_type: Order type ('market' or 'limit')
            volatility: Market volatility parameter
            
        Returns:
            Dictionary with maker/taker proportions
        """
        try:
            # Extract relevant features
            spread_percentage = order_book_features.get('spread_percentage', 0.01)
            
            # For simplicity, we'll use the average of bid and ask depth
            bid_depth = order_book_features.get('bid_depth_5pct', 1.0)
            ask_depth = order_book_features.get('ask_depth_5pct', 1.0)
            avg_depth = (bid_depth + ask_depth) / 2
            
            # Calculate order size to depth ratio
            order_size_to_depth_ratio = quantity_usd / avg_depth if avg_depth > 0 else 1.0
            
            # Cap the ratio to avoid extreme predictions
            order_size_to_depth_ratio = min(order_size_to_depth_ratio, 1.0)
            
            # Encode order type (1 for market, 0 for limit)
            order_type_market = 1.0 if order_type.lower() == 'market' else 0.0
            
            # Prepare feature vector
            features = np.array([
                order_type_market,
                spread_percentage,
                order_size_to_depth_ratio,
                volatility
            ]).reshape(1, -1)
            
            # Predict taker probability
            if self.is_fitted:
                # Scale features
                features_scaled = self.scaler.transform(features)
                
                # Predict probability of being taker (class 1)
                taker_probability = self.model.predict_proba(features_scaled)[0, 1]
            else:
                # Use default coefficients if model is not fitted
                # Apply logistic function to linear combination of features
                z = (
                    self.default_coefficients['intercept'] +
                    self.default_coefficients['order_type_market'] * order_type_market +
                    self.default_coefficients['spread_percentage'] * spread_percentage +
                    self.default_coefficients['order_size_to_depth_ratio'] * order_size_to_depth_ratio +
                    self.default_coefficients['volatility'] * volatility
                )
                taker_probability = 1 / (1 + np.exp(-z))
            
            # For market orders, ensure high taker probability
            if order_type.lower() == 'market':
                # Market orders are primarily taker, but some exchanges may have features
                # that allow market orders to be partially maker (e.g., if they add liquidity)
                # For simplicity, we'll ensure market orders have at least 90% taker probability
                taker_probability = max(taker_probability, 0.9)
            
            # Calculate maker probability (complement of taker)
            maker_probability = 1.0 - taker_probability
            
            return {
                'maker': maker_probability,
                'taker': taker_probability,
                'features_used': {
                    'order_type_market': order_type_market,
                    'spread_percentage': spread_percentage,
                    'order_size_to_depth_ratio': order_size_to_depth_ratio,
                    'volatility': volatility
                }
            }
            
        except Exception as e:
            logger.error(f"Error predicting maker/taker proportion: {str(e)}")
            
            # Return default values in case of error
            if order_type.lower() == 'market':
                # Default for market orders: 100% taker
                return {'maker': 0.0, 'taker': 1.0, 'error': str(e)}
            else:
                # Default for limit orders: 80% maker, 20% taker
                return {'maker': 0.8, 'taker': 0.2, 'error': str(e)}
