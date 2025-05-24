import sys
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QStatusBar, QSplitter
)
from PyQt6.QtCore import Qt, QTimer

from src.ui.input_panel import InputPanel
from src.ui.output_panel import OutputPanel
from src.ui.performance_panel import PerformancePanel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("main_window")

class MainWindow(QMainWindow):
    """
    Main application window for the OKX Trade Simulator.
    Contains the input panel, output panel, and performance monitoring.
    """
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        # Set window properties
        self.setWindowTitle("OKX Trade Simulator")
        self.setMinimumSize(1200, 800)
        
        # Create central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create header
        self.create_header()
        
        # Create main content area with splitter
        self.create_main_content()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Initialize timer for UI updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(100)  # Update every 100ms
        
        logger.info("Main window initialized")
    
    def create_header(self):
        """Create the header section with title and connection status."""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        
        # Title label
        title_label = QLabel("OKX Trade Simulator")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        # Connection status
        self.connection_status = QLabel("Disconnected")
        self.connection_status.setStyleSheet("color: red;")
        
        # Add to layout
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(QLabel("Connection Status:"))
        header_layout.addWidget(self.connection_status)
        
        # Add to main layout
        self.main_layout.addWidget(header_widget)
    
    def create_main_content(self):
        """Create the main content area with input and output panels."""
        # Create splitter for resizable panels
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Create input panel (left side)
        self.input_panel = InputPanel(self.on_simulation_start, self.on_simulation_stop)
        
        # Create right side container
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create output panel (right side, top)
        self.output_panel = OutputPanel()
        
        # Create performance panel (right side, bottom)
        self.performance_panel = PerformancePanel()
        
        # Add output and performance panels to right container
        right_layout.addWidget(self.output_panel, 2)  # 2:1 ratio
        right_layout.addWidget(self.performance_panel, 1)
        
        # Add panels to splitter
        self.splitter.addWidget(self.input_panel)
        self.splitter.addWidget(right_container)
        
        # Set initial sizes (1:2 ratio for left:right)
        self.splitter.setSizes([400, 800])
        
        # Add splitter to main layout
        self.main_layout.addWidget(self.splitter)
    
    def on_simulation_start(self, parameters):
        """
        Handle simulation start event from input panel.
        
        Args:
            parameters: Dictionary of simulation parameters
        """
        logger.info(f"Starting simulation with parameters: {parameters}")
        self.status_bar.showMessage("Simulation starting...")
        
        # Update connection status
        self.connection_status.setText("Connecting...")
        self.connection_status.setStyleSheet("color: orange;")
        
        # Reset output panel
        self.output_panel.reset()
        
        # Reset performance panel
        self.performance_panel.reset()
        
        # Here we would start the actual simulation
        # This will be implemented in the main controller
    
    def on_simulation_stop(self):
        """Handle simulation stop event from input panel."""
        logger.info("Stopping simulation")
        self.status_bar.showMessage("Simulation stopped")
        
        # Update connection status
        self.connection_status.setText("Disconnected")
        self.connection_status.setStyleSheet("color: red;")
        
        # Here we would stop the actual simulation
        # This will be implemented in the main controller
    
    def update_connection_status(self, connected):
        """
        Update the connection status indicator.
        
        Args:
            connected: Boolean indicating connection status
        """
        if connected:
            self.connection_status.setText("Connected")
            self.connection_status.setStyleSheet("color: green;")
        else:
            self.connection_status.setText("Disconnected")
            self.connection_status.setStyleSheet("color: red;")
    
    def update_ui(self):
        """Periodic UI update function."""
        # This will be used for real-time updates
        pass
    
    def update_simulation_output(self, output_data):
        """
        Update the output panel with new simulation results.
        
        Args:
            output_data: Dictionary with simulation output values
        """
        # Update output panel
        self.output_panel.update_values(output_data)
        
        # Update performance panel if performance data is available
        if 'performance' in output_data:
            self.performance_panel.update_values(output_data['performance'])
        
        # Update status bar
        self.status_bar.showMessage(f"Last update: {output_data.get('timestampUTC', 'N/A')}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        logger.info("Application closing")
        # Clean up resources
        self.update_timer.stop()
        # Accept the close event
        event.accept()


def main():
    """Main entry point for the UI application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
