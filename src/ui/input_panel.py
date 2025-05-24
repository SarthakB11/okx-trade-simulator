import logging
from typing import Callable, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QDoubleSpinBox, QPushButton, QFormLayout, QGroupBox
)
from PyQt6.QtCore import Qt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("input_panel")

class InputPanel(QWidget):
    """
    Input panel for the trade simulator.
    Collects user input parameters for the simulation.
    """
    
    def __init__(self, on_start_callback: Callable[[Dict[str, Any]], None], on_stop_callback: Callable[[], None]):
        """
        Initialize the input panel.
        
        Args:
            on_start_callback: Callback function when simulation starts
            on_stop_callback: Callback function when simulation stops
        """
        super().__init__()
        
        self.on_start_callback = on_start_callback
        self.on_stop_callback = on_stop_callback
        
        # Set up the UI
        self.setup_ui()
        
        # Initialize with default values
        self.reset_to_defaults()
        
        logger.info("Input panel initialized")
    
    def setup_ui(self):
        """Set up the user interface components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel("Input Parameters")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # Create form layout for inputs
        form_group = QGroupBox()
        form_layout = QFormLayout(form_group)
        
        # Exchange selection
        self.exchange_combo = QComboBox()
        self.exchange_combo.addItem("OKX")  # Only OKX for this assignment
        form_layout.addRow("Exchange:", self.exchange_combo)
        
        # Spot Asset selection
        self.asset_combo = QComboBox()
        self.asset_combo.addItems(["BTC-USDT", "ETH-USDT", "SOL-USDT", "XRP-USDT", "ADA-USDT"])
        self.asset_combo.setEditable(True)  # Allow custom input
        form_layout.addRow("Spot Asset:", self.asset_combo)
        
        # Order Type (fixed to 'market' for this assignment)
        self.order_type_combo = QComboBox()
        self.order_type_combo.addItem("market")
        self.order_type_combo.setEnabled(False)  # Disable as it's fixed
        form_layout.addRow("Order Type:", self.order_type_combo)
        
        # Quantity input
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(1.0, 10000.0)
        self.quantity_spin.setValue(100.0)
        self.quantity_spin.setSingleStep(10.0)
        self.quantity_spin.setPrefix("$ ")
        self.quantity_spin.setDecimals(2)
        form_layout.addRow("Quantity (~USD):", self.quantity_spin)
        
        # Volatility input
        self.volatility_spin = QDoubleSpinBox()
        self.volatility_spin.setRange(0.001, 1.0)
        self.volatility_spin.setValue(0.02)
        self.volatility_spin.setSingleStep(0.001)
        self.volatility_spin.setDecimals(4)
        form_layout.addRow("Volatility:", self.volatility_spin)
        
        # Fee Tier selection
        self.fee_tier_combo = QComboBox()
        self.fee_tier_combo.addItems(["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5"])
        form_layout.addRow("Fee Tier:", self.fee_tier_combo)
        
        # Add form to main layout
        main_layout.addWidget(form_group)
        
        # Add spacer
        main_layout.addStretch(1)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        # Reset button
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_button)
        
        # Start button
        self.start_button = QPushButton("Start Simulation")
        self.start_button.clicked.connect(self.on_start_clicked)
        self.start_button.setStyleSheet("background-color: #4CAF50; color: white;")
        button_layout.addWidget(self.start_button)
        
        # Stop button (initially disabled)
        self.stop_button = QPushButton("Stop Simulation")
        self.stop_button.clicked.connect(self.on_stop_clicked)
        self.stop_button.setStyleSheet("background-color: #F44336; color: white;")
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        # Add button layout to main layout
        main_layout.addLayout(button_layout)
    
    def reset_to_defaults(self):
        """Reset all inputs to default values."""
        self.exchange_combo.setCurrentText("OKX")
        self.asset_combo.setCurrentText("BTC-USDT")
        self.order_type_combo.setCurrentText("market")
        self.quantity_spin.setValue(100.0)
        self.volatility_spin.setValue(0.02)
        self.fee_tier_combo.setCurrentText("Tier 1")
        
        logger.info("Input values reset to defaults")
    
    def on_start_clicked(self):
        """Handle start button click event."""
        # Collect parameters
        parameters = self.get_parameters()
        
        # Log parameters
        logger.info(f"Starting simulation with parameters: {parameters}")
        
        # Update UI state
        self.set_input_state(False)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # Call the callback
        if self.on_start_callback:
            self.on_start_callback(parameters)
    
    def on_stop_clicked(self):
        """Handle stop button click event."""
        logger.info("Stopping simulation")
        
        # Update UI state
        self.set_input_state(True)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        # Call the callback
        if self.on_stop_callback:
            self.on_stop_callback()
    
    def get_parameters(self) -> Dict[str, Any]:
        """
        Get the current parameter values.
        
        Returns:
            Dictionary of parameter values
        """
        return {
            'exchange': self.exchange_combo.currentText(),
            'spotAsset': self.asset_combo.currentText(),
            'orderType': self.order_type_combo.currentText(),
            'quantityUSD': self.quantity_spin.value(),
            'volatility': self.volatility_spin.value(),
            'feeTier': self.fee_tier_combo.currentText()
        }
    
    def set_input_state(self, enabled: bool):
        """
        Enable or disable input controls.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.exchange_combo.setEnabled(enabled)
        self.asset_combo.setEnabled(enabled)
        # Order type is always disabled as it's fixed
        self.quantity_spin.setEnabled(enabled)
        self.volatility_spin.setEnabled(enabled)
        self.fee_tier_combo.setEnabled(enabled)
        self.reset_button.setEnabled(enabled)
