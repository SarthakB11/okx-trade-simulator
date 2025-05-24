import logging
import math
from typing import Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("market_impact_model")

class AlmgrenChrissModel:
    """
    Implementation of the Almgren-Chriss market impact model.
    
    This model calculates both temporary and permanent price impact
    of a trade based on order size, volatility, and market parameters.
    
    Reference: https://www.linkedin.com/pulse/understanding-almgren-chriss-model-optimal-portfolio-execution-pal-pmeqc/
    """
    
    def __init__(self):
        """Initialize the Almgren-Chriss model with default parameters."""
        # Default model parameters
        # These would typically be calibrated based on market data
        
        # Temporary impact factor (η)
        self.eta = 0.1
        
        # Permanent impact factor (γ)
        self.gamma = 0.1
        
        # Default time horizon in seconds (for a single market order, this is small)
        self.default_time_horizon = 1.0
        
        # Scaling factor for USD to asset quantity conversion
        self.quantity_scaling = 1.0
    
    def calculate_market_impact(self, 
                               quantity_usd: float, 
                               volatility: float,
                               mid_price: Optional[float] = None,
                               time_horizon: Optional[float] = None) -> Dict[str, float]:
        """
        Calculate market impact using the Almgren-Chriss model.
        
        Args:
            quantity_usd: Order size in USD
            volatility: Market volatility parameter (annualized)
            mid_price: Current mid price (optional, used for scaling)
            time_horizon: Time horizon for execution in seconds (optional)
            
        Returns:
            Dictionary with market impact details including:
            - temporary_impact_usd: Immediate price movement during execution
            - permanent_impact_usd: Lasting price change after execution
            - total_impact_usd: Total market impact cost
        """
        try:
            # Use default time horizon if not provided
            if time_horizon is None or time_horizon <= 0:
                time_horizon = self.default_time_horizon
            
            # Convert annualized volatility to the time horizon
            # σ_T = σ * sqrt(T/252) where T is in days (assuming 252 trading days per year)
            # For seconds, we use σ * sqrt(T/(252*24*60*60))
            volatility_scaled = volatility * math.sqrt(time_horizon / (252 * 24 * 60 * 60))
            
            # Scale quantity if mid price is provided
            # This converts USD amount to asset quantity
            if mid_price is not None and mid_price > 0:
                quantity_asset = quantity_usd / mid_price
            else:
                # If no mid price, use the scaling factor
                quantity_asset = quantity_usd * self.quantity_scaling
            
            # Calculate absolute quantity for the formulas
            abs_quantity = abs(quantity_asset)
            
            # Calculate temporary impact using the formula:
            # I_temp = σ × |v| × (1/T)^(1/2) × η
            # Where:
            # - σ is volatility
            # - |v| is absolute order size
            # - T is time horizon
            # - η is temporary impact factor
            temporary_impact_factor = volatility_scaled * abs_quantity * (1 / time_horizon) ** 0.5 * self.eta
            
            # Calculate permanent impact using the formula:
            # I_perm = γ × σ × |v|
            # Where:
            # - γ is permanent impact factor
            # - σ is volatility
            # - |v| is absolute order size
            permanent_impact_factor = self.gamma * volatility_scaled * abs_quantity
            
            # Convert impact factors to USD
            if mid_price is not None and mid_price > 0:
                temporary_impact_usd = temporary_impact_factor * mid_price
                permanent_impact_usd = permanent_impact_factor * mid_price
            else:
                # If no mid price, assume the factors are already in USD
                temporary_impact_usd = temporary_impact_factor
                permanent_impact_usd = permanent_impact_factor
            
            # Total impact is the sum of temporary and permanent
            total_impact_usd = temporary_impact_usd + permanent_impact_usd
            
            return {
                'temporary_impact_usd': temporary_impact_usd,
                'permanent_impact_usd': permanent_impact_usd,
                'total_impact_usd': total_impact_usd,
                'parameters': {
                    'eta': self.eta,
                    'gamma': self.gamma,
                    'volatility': volatility,
                    'volatility_scaled': volatility_scaled,
                    'time_horizon': time_horizon,
                    'quantity_asset': quantity_asset
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating market impact: {str(e)}")
            
            # Return default values in case of error
            return {
                'temporary_impact_usd': quantity_usd * 0.0001,  # Default 1 basis point
                'permanent_impact_usd': quantity_usd * 0.0001,  # Default 1 basis point
                'total_impact_usd': quantity_usd * 0.0002,      # Default 2 basis points
                'error': str(e)
            }
    
    def calibrate(self, 
                 eta: Optional[float] = None, 
                 gamma: Optional[float] = None,
                 quantity_scaling: Optional[float] = None):
        """
        Calibrate the model parameters based on market data or user input.
        
        Args:
            eta: Temporary impact factor
            gamma: Permanent impact factor
            quantity_scaling: Scaling factor for USD to asset quantity conversion
        """
        if eta is not None and eta > 0:
            self.eta = eta
            
        if gamma is not None and gamma > 0:
            self.gamma = gamma
            
        if quantity_scaling is not None and quantity_scaling > 0:
            self.quantity_scaling = quantity_scaling
            
        logger.info(f"Almgren-Chriss model calibrated: eta={self.eta}, gamma={self.gamma}, quantity_scaling={self.quantity_scaling}")
