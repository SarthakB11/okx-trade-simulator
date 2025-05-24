import logging
from typing import Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fee_model")

class FeeModel:
    """
    Rule-based fee model for calculating expected transaction fees.
    Uses the exchange fee tiers to determine the appropriate fee rate.
    """
    
    # OKX fee tiers (as of May 2025)
    # These values should be updated based on the latest OKX documentation
    OKX_FEE_TIERS = {
        # Format: 'Tier': {'maker': maker_fee_rate, 'taker': taker_fee_rate}
        'Tier 1': {'maker': 0.0008, 'taker': 0.0010},
        'Tier 2': {'maker': 0.0006, 'taker': 0.0008},
        'Tier 3': {'maker': 0.0004, 'taker': 0.0006},
        'Tier 4': {'maker': 0.0002, 'taker': 0.0004},
        'Tier 5': {'maker': 0.0000, 'taker': 0.0002},
        # Add more tiers as needed
    }
    
    def __init__(self):
        """Initialize the fee model."""
        self.exchange_fee_tiers = {
            'OKX': self.OKX_FEE_TIERS,
            # Add other exchanges as needed
        }
    
    def calculate_fees(self, 
                      exchange: str, 
                      fee_tier: str, 
                      order_type: str, 
                      quantity_usd: float,
                      maker_taker_proportion: Dict[str, float] = None) -> Dict[str, float]:
        """
        Calculate expected fees based on exchange, fee tier, order type, and quantity.
        
        Args:
            exchange: Exchange name (e.g., 'OKX')
            fee_tier: Fee tier name (e.g., 'Tier 1')
            order_type: Order type (e.g., 'market')
            quantity_usd: Order quantity in USD
            maker_taker_proportion: Dict with 'maker' and 'taker' proportions
                                   (if None, assumes 100% taker for market orders)
        
        Returns:
            Dictionary with fee details including:
            - maker_fee_usd: Fee for maker portion
            - taker_fee_usd: Fee for taker portion
            - total_fee_usd: Total fee
        """
        # Validate inputs
        if exchange not in self.exchange_fee_tiers:
            logger.warning(f"Unknown exchange: {exchange}, using default OKX fees")
            exchange = 'OKX'
            
        exchange_tiers = self.exchange_fee_tiers[exchange]
        
        if fee_tier not in exchange_tiers:
            logger.warning(f"Unknown fee tier: {fee_tier}, using Tier 1")
            fee_tier = 'Tier 1'
            
        # Get fee rates for the specified tier
        fee_rates = exchange_tiers[fee_tier]
        maker_fee_rate = fee_rates['maker']
        taker_fee_rate = fee_rates['taker']
        
        # Determine maker/taker proportion based on order type
        if maker_taker_proportion is None:
            if order_type.lower() == 'market':
                # Market orders are typically 100% taker
                maker_proportion = 0.0
                taker_proportion = 1.0
            else:
                # Default for other order types (not used in this assignment)
                maker_proportion = 0.5
                taker_proportion = 0.5
        else:
            maker_proportion = maker_taker_proportion.get('maker', 0.0)
            taker_proportion = maker_taker_proportion.get('taker', 1.0)
            
            # Ensure proportions sum to 1.0
            total_proportion = maker_proportion + taker_proportion
            if total_proportion > 0:
                maker_proportion /= total_proportion
                taker_proportion /= total_proportion
        
        # Calculate fees
        maker_fee_usd = quantity_usd * maker_proportion * maker_fee_rate
        taker_fee_usd = quantity_usd * taker_proportion * taker_fee_rate
        total_fee_usd = maker_fee_usd + taker_fee_usd
        
        return {
            'maker_fee_usd': maker_fee_usd,
            'taker_fee_usd': taker_fee_usd,
            'total_fee_usd': total_fee_usd,
            'maker_fee_rate': maker_fee_rate,
            'taker_fee_rate': taker_fee_rate,
            'maker_proportion': maker_proportion,
            'taker_proportion': taker_proportion
        }
