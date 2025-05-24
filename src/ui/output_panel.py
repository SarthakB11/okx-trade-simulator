import logging
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("output_panel")

class OutputField(QWidget):
    """Widget for displaying a labeled output value with formatting."""
    
    def __init__(self, label: str, unit: str = "", highlight: bool = False):
        """
        Initialize the output field.
        
        Args:
            label: Label text
            unit: Unit text (e.g., $, %, ms)
            highlight: Whether to highlight this field
        """
        super().__init__()
        
        self.label = label
        self.unit = unit
        self.highlight = highlight
        self.value = "N/A"
        self.previous_value = None
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create label
        self.label_widget = QLabel(f"{label}:")
        self.label_widget.setMinimumWidth(180)
        layout.addWidget(self.label_widget)
        
        # Create value display
        self.value_widget = QLabel(self.format_value(self.value))
        self.value_widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.value_widget.setMinimumWidth(120)
        self.value_widget.setFont(self.get_value_font())
        
        if highlight:
            self.value_widget.setStyleSheet("font-weight: bold; color: #2196F3;")
        
        layout.addWidget(self.value_widget)
    
    def get_value_font(self):
        """Get the font for the value display."""
        font = self.value_widget.font()
        font.setFamily("Monospace")
        if self.highlight:
            font.setBold(True)
        return font
    
    def format_value(self, value) -> str:
        """
        Format the value with appropriate unit and precision.
        
        Args:
            value: The value to format
            
        Returns:
            Formatted value string
        """
        if value == "N/A":
            return value
        
        try:
            # Convert to float if possible
            float_value = float(value)
            
            # Format based on unit
            if self.unit == "$":
                return f"${float_value:.4f}"
            elif self.unit == "%":
                return f"{float_value:.4f}%"
            elif self.unit == "ms":
                return f"{float_value:.3f} ms"
            else:
                return f"{float_value:.6f}"
        except (ValueError, TypeError):
            # If not a number, return as is
            return str(value)
    
    def update_value(self, value):
        """
        Update the displayed value.
        
        Args:
            value: New value to display
        """
        self.previous_value = self.value
        self.value = value
        
        # Format and update the display
        formatted_value = self.format_value(value)
        self.value_widget.setText(formatted_value)
        
        # Highlight changes
        if self.previous_value is not None and self.previous_value != self.value:
            # Briefly change background to indicate update
            self.value_widget.setStyleSheet(
                f"background-color: #E3F2FD; {self.get_style_for_change()}"
            )
            
            # Reset style after a delay (would use QTimer in a real implementation)
            # For now, we'll just reset immediately
            if self.highlight:
                self.value_widget.setStyleSheet("font-weight: bold; color: #2196F3;")
            else:
                self.value_widget.setStyleSheet("")
    
    def get_style_for_change(self) -> str:
        """
        Get style based on value change direction.
        
        Returns:
            CSS style string
        """
        try:
            if self.previous_value == "N/A" or self.value == "N/A":
                return ""
                
            prev_val = float(self.previous_value)
            curr_val = float(self.value)
            
            if curr_val > prev_val:
                return "color: #4CAF50;" # Green for increase
            elif curr_val < prev_val:
                return "color: #F44336;" # Red for decrease
            else:
                return ""
        except (ValueError, TypeError):
            return ""


class OutputPanel(QWidget):
    """
    Output panel for displaying simulation results.
    Shows calculated values for slippage, fees, market impact, etc.
    """
    
    def __init__(self):
        """Initialize the output panel."""
        super().__init__()
        
        # Set up the UI
        self.setup_ui()
        
        logger.info("Output panel initialized")
    
    def setup_ui(self):
        """Set up the user interface components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel("Processed Output Values")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # Create group box for outputs
        group_box = QGroupBox()
        grid_layout = QGridLayout(group_box)
        
        # Create output fields
        self.expected_slippage = OutputField("Expected Slippage", "$")
        self.expected_fees = OutputField("Expected Fees", "$")
        self.expected_market_impact = OutputField("Expected Market Impact", "$")
        self.net_cost = OutputField("Net Cost", "$", highlight=True)
        
        # Maker/Taker proportion needs special handling
        self.maker_taker_label = QLabel("Maker/Taker Proportion:")
        self.maker_taker_value = QLabel("N/A")
        self.maker_taker_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.maker_taker_value.setFont(self.get_monospace_font())
        
        # Internal latency
        self.internal_latency = OutputField("Internal Latency", "ms")
        
        # Timestamp
        self.timestamp_label = QLabel("Last Update:")
        self.timestamp_value = QLabel("N/A")
        self.timestamp_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # Add fields to grid layout
        grid_layout.addWidget(self.expected_slippage, 0, 0)
        grid_layout.addWidget(self.expected_fees, 1, 0)
        grid_layout.addWidget(self.expected_market_impact, 2, 0)
        grid_layout.addWidget(self.net_cost, 3, 0)
        
        # Add maker/taker proportion
        maker_taker_widget = QWidget()
        maker_taker_layout = QHBoxLayout(maker_taker_widget)
        maker_taker_layout.setContentsMargins(0, 0, 0, 0)
        maker_taker_layout.addWidget(self.maker_taker_label)
        maker_taker_layout.addWidget(self.maker_taker_value)
        grid_layout.addWidget(maker_taker_widget, 4, 0)
        
        # Add internal latency
        grid_layout.addWidget(self.internal_latency, 5, 0)
        
        # Add timestamp
        timestamp_widget = QWidget()
        timestamp_layout = QHBoxLayout(timestamp_widget)
        timestamp_layout.setContentsMargins(0, 0, 0, 0)
        timestamp_layout.addWidget(self.timestamp_label)
        timestamp_layout.addWidget(self.timestamp_value)
        grid_layout.addWidget(timestamp_widget, 6, 0)
        
        # Add group box to main layout
        main_layout.addWidget(group_box)
        
        # Add stretch to push everything to the top
        main_layout.addStretch(1)
    
    def get_monospace_font(self):
        """Get a monospace font for value displays."""
        font = self.font()
        font.setFamily("Monospace")
        return font
    
    def update_values(self, data: Dict[str, Any]):
        """
        Update all output values with new data.
        
        Args:
            data: Dictionary with output values
        """
        # Update individual fields
        self.expected_slippage.update_value(data.get('expectedSlippageUSD', 'N/A'))
        self.expected_fees.update_value(data.get('expectedFeesUSD', 'N/A'))
        self.expected_market_impact.update_value(data.get('expectedMarketImpactUSD', 'N/A'))
        self.net_cost.update_value(data.get('netCostUSD', 'N/A'))
        
        # Update maker/taker proportion
        maker_taker = data.get('makerTakerProportion', {})
        if maker_taker:
            maker = maker_taker.get('maker', 0)
            taker = maker_taker.get('taker', 0)
            self.maker_taker_value.setText(f"Maker: {maker:.2%}, Taker: {taker:.2%}")
        else:
            self.maker_taker_value.setText("N/A")
        
        # Update internal latency
        self.internal_latency.update_value(data.get('internalLatencyMs', 'N/A'))
        
        # Update timestamp
        self.timestamp_value.setText(str(data.get('timestampUTC', 'N/A')))
        
        logger.debug(f"Output panel updated with data: {data}")
    
    def reset(self):
        """Reset all output values to N/A."""
        self.expected_slippage.update_value('N/A')
        self.expected_fees.update_value('N/A')
        self.expected_market_impact.update_value('N/A')
        self.net_cost.update_value('N/A')
        self.maker_taker_value.setText('N/A')
        self.internal_latency.update_value('N/A')
        self.timestamp_value.setText('N/A')
        
        logger.info("Output panel reset")
