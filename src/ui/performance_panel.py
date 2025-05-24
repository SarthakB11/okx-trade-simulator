import logging
from typing import Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QGridLayout,
    QProgressBar
)
from PyQt6.QtCore import Qt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("performance_panel")

class PerformanceMetric(QWidget):
    """Widget for displaying a performance metric with label and value."""
    
    def __init__(self, label: str, unit: str = "", warning_threshold: float = None):
        """
        Initialize the performance metric widget.
        
        Args:
            label: Label text
            unit: Unit text (e.g., ms, %)
            warning_threshold: Threshold for warning indication
        """
        super().__init__()
        
        self.label = label
        self.unit = unit
        self.warning_threshold = warning_threshold
        self.value = 0
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create label
        self.label_widget = QLabel(f"{label}:")
        self.label_widget.setMinimumWidth(150)
        layout.addWidget(self.label_widget)
        
        # Create value display
        self.value_widget = QLabel(self.format_value(self.value))
        self.value_widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.value_widget.setMinimumWidth(100)
        self.value_widget.setFont(self.get_monospace_font())
        layout.addWidget(self.value_widget)
    
    def get_monospace_font(self):
        """Get a monospace font for value displays."""
        font = self.font()
        font.setFamily("Monospace")
        return font
    
    def format_value(self, value) -> str:
        """
        Format the value with appropriate unit and precision.
        
        Args:
            value: The value to format
            
        Returns:
            Formatted value string
        """
        try:
            # Convert to float if possible
            float_value = float(value)
            
            # Format based on unit
            if self.unit == "ms":
                return f"{float_value:.3f} ms"
            elif self.unit == "%":
                return f"{float_value:.2f}%"
            elif self.unit == "tps":
                return f"{float_value:.2f} tps"
            else:
                return f"{float_value:.2f}"
        except (ValueError, TypeError):
            # If not a number, return as is
            return str(value)
    
    def update_value(self, value):
        """
        Update the displayed value.
        
        Args:
            value: New value to display
        """
        self.value = value
        
        # Format and update the display
        formatted_value = self.format_value(value)
        self.value_widget.setText(formatted_value)
        
        # Apply warning style if needed
        if self.warning_threshold is not None:
            if value > self.warning_threshold:
                self.value_widget.setStyleSheet("color: #F44336;")  # Red for warning
            else:
                self.value_widget.setStyleSheet("")


class LatencyGauge(QWidget):
    """Widget for displaying latency with a gauge visualization."""
    
    def __init__(self, label: str, warning_threshold: float = 10.0, critical_threshold: float = 20.0):
        """
        Initialize the latency gauge widget.
        
        Args:
            label: Label text
            warning_threshold: Threshold for warning indication (ms)
            critical_threshold: Threshold for critical indication (ms)
        """
        super().__init__()
        
        self.label = label
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.value = 0
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create label
        self.label_widget = QLabel(f"{label}:")
        layout.addWidget(self.label_widget)
        
        # Create gauge (progress bar)
        self.gauge = QProgressBar()
        self.gauge.setRange(0, int(critical_threshold * 1.5))  # Set range beyond critical threshold
        self.gauge.setValue(0)
        self.gauge.setTextVisible(True)
        self.gauge.setFormat("%v ms")
        layout.addWidget(self.gauge)
        
        # Create value display
        self.value_widget = QLabel("0.000 ms")
        self.value_widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.value_widget.setFont(self.get_monospace_font())
        layout.addWidget(self.value_widget)
    
    def get_monospace_font(self):
        """Get a monospace font for value displays."""
        font = self.font()
        font.setFamily("Monospace")
        return font
    
    def update_value(self, value):
        """
        Update the displayed value and gauge.
        
        Args:
            value: New value to display (in ms)
        """
        self.value = value
        
        # Update gauge
        self.gauge.setValue(int(value))
        
        # Update text display
        self.value_widget.setText(f"{value:.3f} ms")
        
        # Update gauge color based on thresholds
        if value > self.critical_threshold:
            self.gauge.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #BDBDBD;
                    border-radius: 3px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #F44336;  /* Red for critical */
                }
            """)
        elif value > self.warning_threshold:
            self.gauge.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #BDBDBD;
                    border-radius: 3px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #FF9800;  /* Orange for warning */
                }
            """)
        else:
            self.gauge.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #BDBDBD;
                    border-radius: 3px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;  /* Green for good */
                }
            """)


class PerformancePanel(QWidget):
    """
    Panel for displaying performance metrics.
    Shows latency, throughput, and other performance indicators.
    """
    
    def __init__(self):
        """Initialize the performance panel."""
        super().__init__()
        
        # Set up the UI
        self.setup_ui()
        
        logger.info("Performance panel initialized")
    
    def setup_ui(self):
        """Set up the user interface components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel("Performance Metrics")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # Create latency group
        latency_group = QGroupBox("Latency Monitoring")
        latency_layout = QHBoxLayout(latency_group)
        
        # Create latency gauges
        self.processing_latency = LatencyGauge("Processing Latency", 5.0, 10.0)
        self.ui_latency = LatencyGauge("UI Update Latency", 10.0, 20.0)
        self.end_to_end_latency = LatencyGauge("End-to-End Latency", 15.0, 30.0)
        
        # Add gauges to layout
        latency_layout.addWidget(self.processing_latency)
        latency_layout.addWidget(self.ui_latency)
        latency_layout.addWidget(self.end_to_end_latency)
        
        # Add latency group to main layout
        main_layout.addWidget(latency_group)
        
        # Create metrics group
        metrics_group = QGroupBox("System Metrics")
        metrics_layout = QGridLayout(metrics_group)
        
        # Create metrics
        self.avg_latency = PerformanceMetric("Average Latency", "ms", 10.0)
        self.min_latency = PerformanceMetric("Min Latency", "ms")
        self.max_latency = PerformanceMetric("Max Latency", "ms", 20.0)
        self.p95_latency = PerformanceMetric("95th Percentile", "ms", 15.0)
        self.ticks_per_second = PerformanceMetric("Ticks Per Second", "tps")
        self.tick_count = PerformanceMetric("Total Ticks")
        
        # Add metrics to layout
        metrics_layout.addWidget(self.avg_latency, 0, 0)
        metrics_layout.addWidget(self.min_latency, 0, 1)
        metrics_layout.addWidget(self.max_latency, 1, 0)
        metrics_layout.addWidget(self.p95_latency, 1, 1)
        metrics_layout.addWidget(self.ticks_per_second, 2, 0)
        metrics_layout.addWidget(self.tick_count, 2, 1)
        
        # Add metrics group to main layout
        main_layout.addWidget(metrics_group)
    
    def update_values(self, data: Dict[str, Any]):
        """
        Update all performance metrics with new data.
        
        Args:
            data: Dictionary with performance metrics
        """
        # Update latency gauges
        self.processing_latency.update_value(data.get('processingLatencyMs', 0))
        self.ui_latency.update_value(data.get('uiUpdateLatencyMs', 0))
        self.end_to_end_latency.update_value(data.get('endToEndLatencyMs', 0))
        
        # Update metrics
        self.avg_latency.update_value(data.get('averageLatencyMs', 0))
        self.min_latency.update_value(data.get('minLatencyMs', 0))
        self.max_latency.update_value(data.get('maxLatencyMs', 0))
        self.p95_latency.update_value(data.get('p95LatencyMs', 0))
        self.ticks_per_second.update_value(data.get('ticksPerSecond', 0))
        self.tick_count.update_value(data.get('tickCount', 0))
        
        logger.debug(f"Performance panel updated with data: {data}")
    
    def reset(self):
        """Reset all performance metrics to zero."""
        # Reset latency gauges
        self.processing_latency.update_value(0)
        self.ui_latency.update_value(0)
        self.end_to_end_latency.update_value(0)
        
        # Reset metrics
        self.avg_latency.update_value(0)
        self.min_latency.update_value(0)
        self.max_latency.update_value(0)
        self.p95_latency.update_value(0)
        self.ticks_per_second.update_value(0)
        self.tick_count.update_value(0)
        
        logger.info("Performance panel reset")
