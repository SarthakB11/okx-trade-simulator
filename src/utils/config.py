import os
import json
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("config")

class Config:
    """
    Configuration manager for the OKX Trade Simulator.
    Handles loading, saving, and accessing configuration settings.
    """
    
    DEFAULT_CONFIG = {
        "websocket": {
            "base_uri": "wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook",
            "reconnect_delay": 1,
            "max_reconnect_delay": 60,
            "heartbeat_interval": 30
        },
        "ui": {
            "update_interval_ms": 100,
            "theme": "light",
            "default_window_size": [1200, 800]
        },
        "simulation": {
            "default_parameters": {
                "exchange": "OKX",
                "spotAsset": "BTC-USDT",
                "orderType": "market",
                "quantityUSD": 100.0,
                "volatility": 0.02,
                "feeTier": "Tier 1"
            },
            "available_assets": [
                "BTC-USDT",
                "ETH-USDT",
                "SOL-USDT",
                "XRP-USDT",
                "ADA-USDT",
                "DOT-USDT",
                "AVAX-USDT",
                "MATIC-USDT"
            ],
            "fee_tiers": [
                "Tier 1",
                "Tier 2",
                "Tier 3",
                "Tier 4",
                "Tier 5"
            ]
        },
        "performance": {
            "warning_thresholds": {
                "processing_latency_ms": 5.0,
                "ui_update_latency_ms": 10.0,
                "end_to_end_latency_ms": 15.0
            },
            "critical_thresholds": {
                "processing_latency_ms": 10.0,
                "ui_update_latency_ms": 20.0,
                "end_to_end_latency_ms": 30.0
            }
        },
        "logging": {
            "level": "INFO",
            "file": "trade_simulator.log",
            "max_size_mb": 10,
            "backup_count": 3
        }
    }
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to the configuration file
        """
        self.config_file = config_file
        self.config = self.DEFAULT_CONFIG.copy()
        
        # Load configuration from file if it exists
        self.load()
        
        logger.info("Configuration initialized")
    
    def load(self) -> bool:
        """
        Load configuration from file.
        
        Returns:
            True if configuration was loaded successfully, False otherwise
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                
                # Merge loaded config with default config
                self._merge_configs(self.config, loaded_config)
                
                logger.info(f"Configuration loaded from {self.config_file}")
                return True
            else:
                logger.info(f"Configuration file {self.config_file} not found, using defaults")
                return False
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return False
    
    def save(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            True if configuration was saved successfully, False otherwise
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Dot-separated path to the configuration value (e.g., 'websocket.base_uri')
            default: Default value to return if the key is not found
            
        Returns:
            Configuration value or default
        """
        try:
            parts = key.split('.')
            value = self.config
            
            for part in parts:
                value = value[part]
            
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set a configuration value.
        
        Args:
            key: Dot-separated path to the configuration value (e.g., 'websocket.base_uri')
            value: Value to set
            
        Returns:
            True if the value was set successfully, False otherwise
        """
        try:
            parts = key.split('.')
            config = self.config
            
            # Navigate to the parent of the target key
            for part in parts[:-1]:
                if part not in config:
                    config[part] = {}
                config = config[part]
            
            # Set the value
            config[parts[-1]] = value
            
            return True
        except Exception as e:
            logger.error(f"Error setting configuration value: {str(e)}")
            return False
    
    def _merge_configs(self, target: Dict, source: Dict):
        """
        Recursively merge source config into target config.
        
        Args:
            target: Target configuration dictionary
            source: Source configuration dictionary
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_configs(target[key], value)
            else:
                target[key] = value
    
    def get_websocket_uri(self, exchange: str, symbol: str) -> str:
        """
        Get the WebSocket URI for a specific exchange and symbol.
        
        Args:
            exchange: Exchange name (e.g., 'OKX')
            symbol: Trading pair symbol (e.g., 'BTC-USDT')
            
        Returns:
            WebSocket URI
        """
        base_uri = self.get('websocket.base_uri')
        
        # Convert symbol to the format expected by the WebSocket endpoint
        # For this example, we'll just append "-SWAP" to the symbol
        ws_symbol = f"{symbol}-SWAP"
        
        return f"{base_uri}/{exchange.lower()}/{ws_symbol}"
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """
        Get the default simulation parameters.
        
        Returns:
            Dictionary of default parameters
        """
        return self.get('simulation.default_parameters', {}).copy()
    
    def get_available_assets(self) -> list:
        """
        Get the list of available assets.
        
        Returns:
            List of available assets
        """
        return self.get('simulation.available_assets', []).copy()
    
    def get_fee_tiers(self) -> list:
        """
        Get the list of fee tiers.
        
        Returns:
            List of fee tiers
        """
        return self.get('simulation.fee_tiers', []).copy()
    
    def get_performance_thresholds(self) -> Dict[str, Dict[str, float]]:
        """
        Get the performance warning and critical thresholds.
        
        Returns:
            Dictionary with warning and critical thresholds
        """
        return {
            'warning': self.get('performance.warning_thresholds', {}),
            'critical': self.get('performance.critical_thresholds', {})
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get the logging configuration.
        
        Returns:
            Dictionary with logging configuration
        """
        return self.get('logging', {}).copy()


# Create a singleton instance
config = Config()
