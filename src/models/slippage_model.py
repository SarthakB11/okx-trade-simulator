import logging
import numpy as np
from typing import Dict, Optional, List, Tuple
from sklearn.linear_model import LinearRegression, QuantileRegressor
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("slippage_model")

class SlippageModel:
    """
    Model for estimating expected slippage using linear or quantile regression.
    Extracts features from the order book to predict slippage for a given order size.
    """
    
    def __init__(self, regression_type: str = 'linear'):
        """
        Initialize the slippage model.
        
        Args:
            regression_type: Type of regression to use ('linear' or 'quantile')
        """
        self.regression_type = regression_type
        
        # Initialize model and scaler
        if regression_type == 'linear':
            self.model = LinearRegression()
        elif regression_type == 'quantile':
            # Use 0.95 quantile for a more conservative estimate
            self.model = QuantileRegressor(quantile=0.95, alpha=0.5)
        else:
            logger.warning(f"Unknown regression type: {regression_type}, using linear")
            self.regression_type = 'linear'
            self.model = LinearRegression()
            
        self.scaler = StandardScaler()
        self.is_fitted = False
        
        # Pre-trained coefficients (these would normally be learned from historical data)
        # For this assignment, we'll use reasonable default values
        self.default_coefficients = {
            'intercept': 0.01,  # Base slippage (1 basis point)
            'spread_percentage': 0.5,  # Higher spread -> higher slippage
            'order_size_to_depth_ratio': 0.8,  # Higher ratio -> higher slippage
            'volume_imbalance': -0.2,  # More bids than asks -> lower slippage for buys
            'volatility': 0.3  # Higher volatility -> higher slippage
        }
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        """
        Fit the regression model using historical data.
        
        Args:
            X: Feature matrix with columns [spread_percentage, order_size_to_depth_ratio, 
                                           volume_imbalance, volatility]
            y: Target slippage values
        """
        try:
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Fit model
            self.model.fit(X_scaled, y)
            self.is_fitted = True
            
            logger.info(f"Slippage model fitted successfully with {len(X)} samples")
            
            if hasattr(self.model, 'coef_'):
                logger.info(f"Model coefficients: {self.model.coef_}")
                logger.info(f"Model intercept: {self.model.intercept_}")
                
        except Exception as e:
            logger.error(f"Error fitting slippage model: {str(e)}")
            self.is_fitted = False
    
    def predict_slippage(self, 
                        order_book_features: Dict, 
                        quantity_usd: float, 
                        is_buy: bool = True,
                        volatility: float = 0.02) -> Dict[str, float]:
        """
        Predict slippage for a given order using the regression model.
        
        Args:
            order_book_features: Features extracted from the order book
            quantity_usd: Order size in USD
            is_buy: True for buy order, False for sell order
            volatility: Market volatility parameter
            
        Returns:
            Dictionary with slippage details
        """
        try:
            # Extract relevant features
            spread_percentage = order_book_features.get('spread_percentage', 0.01)
            
            # Determine which side of the book to use based on order type
            if is_buy:
                depth = order_book_features.get('ask_depth_5pct', 1.0)
                # For buy orders, more bids than asks is favorable
                volume_imbalance = order_book_features.get('volume_imbalance', 0.0)
            else:
                depth = order_book_features.get('bid_depth_5pct', 1.0)
                # For sell orders, more asks than bids is favorable (inverse of imbalance)
                volume_imbalance = -order_book_features.get('volume_imbalance', 0.0)
            
            # Calculate order size to depth ratio (key factor in slippage)
            # Avoid division by zero
            order_size_to_depth_ratio = quantity_usd / depth if depth > 0 else 1.0
            
            # Cap the ratio to avoid extreme predictions
            order_size_to_depth_ratio = min(order_size_to_depth_ratio, 1.0)
            
            # Prepare feature vector
            features = np.array([
                spread_percentage,
                order_size_to_depth_ratio,
                volume_imbalance,
                volatility
            ]).reshape(1, -1)
            
            # Predict slippage
            if self.is_fitted:
                # Scale features
                features_scaled = self.scaler.transform(features)
                
                # Make prediction
                slippage_percentage = self.model.predict(features_scaled)[0]
            else:
                # Use default coefficients if model is not fitted
                slippage_percentage = (
                    self.default_coefficients['intercept'] +
                    self.default_coefficients['spread_percentage'] * spread_percentage +
                    self.default_coefficients['order_size_to_depth_ratio'] * order_size_to_depth_ratio +
                    self.default_coefficients['volume_imbalance'] * volume_imbalance +
                    self.default_coefficients['volatility'] * volatility
                )
            
            # Ensure slippage is non-negative
            slippage_percentage = max(0.0, slippage_percentage)
            
            # Calculate slippage in USD
            mid_price = order_book_features.get('mid_price', 0.0)
            slippage_usd = (quantity_usd * slippage_percentage / 100)
            
            return {
                'slippage_percentage': slippage_percentage,
                'slippage_usd': slippage_usd,
                'features_used': {
                    'spread_percentage': spread_percentage,
                    'order_size_to_depth_ratio': order_size_to_depth_ratio,
                    'volume_imbalance': volume_imbalance,
                    'volatility': volatility
                }
            }
            
        except Exception as e:
            logger.error(f"Error predicting slippage: {str(e)}")
            
            # Return a default value in case of error
            return {
                'slippage_percentage': 0.05,  # Default 5 basis points
                'slippage_usd': quantity_usd * 0.0005,
                'error': str(e)
            }
