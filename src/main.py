import asyncio
import logging
import sys
import uuid
import signal
from typing import Dict, Any
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, QThread

from src.ui.main_window import MainWindow
from src.websocket.connector import WebSocketConnector
from src.models.simulation_engine import SimulationEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trade_simulator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main")

class WebSocketWorker(QObject):
    """Worker class for handling WebSocket operations in a separate thread."""
    
    connected = pyqtSignal(bool)
    output_updated = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.connector = None
        self.simulation_engine = None
        self.running = False
        self.loop = None
    
    def on_message(self, data: Dict[str, Any]):
        """
        Handle incoming WebSocket messages.
        
        Args:
            data: Market data tick from WebSocket
        """
        if self.simulation_engine and self.running:
            # Process the tick with the simulation engine
            output = self.simulation_engine.process_tick(data)
            
            # Emit signal with output data
            self.output_updated.emit(output)
    
    async def run_websocket(self, uri: str, simulation_id: str, parameters: Dict[str, Any]):
        """
        Run the WebSocket connection and processing loop.
        
        Args:
            uri: WebSocket endpoint URI
            simulation_id: Unique identifier for the simulation
            parameters: Simulation parameters
        """
        try:
            # Initialize simulation engine
            self.simulation_engine = SimulationEngine(
                simulation_id=simulation_id,
                parameters=parameters,
                output_callback=lambda output: self.output_updated.emit(output)
            )
            
            # Initialize WebSocket connector
            self.connector = WebSocketConnector(uri, self.on_message)
            
            # Connect to WebSocket
            await self.connector.connect()
            self.connected.emit(True)
            self.running = True
            
            # Keep the connection alive until stopped
            while self.running:
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error in WebSocket worker: {str(e)}")
            self.connected.emit(False)
            self.running = False
        finally:
            # Clean up
            if self.connector:
                await self.connector.disconnect()
            self.connected.emit(False)
            self.running = False
    
    def start(self, uri: str, simulation_id: str, parameters: Dict[str, Any]):
        """
        Start the WebSocket worker.
        
        Args:
            uri: WebSocket endpoint URI
            simulation_id: Unique identifier for the simulation
            parameters: Simulation parameters
        """
        # Create a new event loop for this thread
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Start the WebSocket connection
        self.loop.run_until_complete(self.run_websocket(uri, simulation_id, parameters))
    
    def stop(self):
        """Stop the WebSocket worker."""
        self.running = False
        
        # Stop the event loop
        if self.loop and self.loop.is_running():
            self.loop.stop()


class TradeSimulatorApp:
    """Main application controller for the OKX Trade Simulator."""
    
    def __init__(self):
        """Initialize the application."""
        # Create Qt application
        self.app = QApplication(sys.argv)
        
        # Create main window
        self.main_window = MainWindow()
        
        # Connect signals
        self.main_window.input_panel.on_start_callback = self.start_simulation
        self.main_window.input_panel.on_stop_callback = self.stop_simulation
        
        # Initialize WebSocket worker thread
        self.worker_thread = QThread()
        self.worker = WebSocketWorker()
        self.worker.moveToThread(self.worker_thread)
        
        # Connect worker signals
        self.worker.connected.connect(self.main_window.update_connection_status)
        self.worker.output_updated.connect(self.main_window.update_simulation_output)
        
        # Start worker thread
        self.worker_thread.start()
        
        # Initialize simulation state
        self.simulation_id = None
        self.simulation_running = False
        
        # Set up signal handling for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        
        logger.info("Trade Simulator application initialized")
    
    def start_simulation(self, parameters: Dict[str, Any]):
        """
        Start a new simulation.
        
        Args:
            parameters: Simulation parameters
        """
        if self.simulation_running:
            logger.warning("Simulation already running")
            return
        
        # Generate a unique ID for this simulation
        self.simulation_id = str(uuid.uuid4())
        
        # Construct WebSocket URI
        exchange = parameters.get('exchange', 'OKX')
        asset = parameters.get('spotAsset', 'BTC-USDT')
        
        # Map asset to the correct WebSocket endpoint format
        # For this example, we'll just append "-SWAP" to the asset
        # In a real implementation, this would be more sophisticated
        ws_symbol = f"{asset}-SWAP"
        
        uri = f"wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/{exchange.lower()}/{ws_symbol}"
        
        logger.info(f"Starting simulation {self.simulation_id} with URI: {uri}")
        
        # Start the WebSocket worker
        self.worker_thread.started.connect(
            lambda: self.worker.start(uri, self.simulation_id, parameters)
        )
        
        self.simulation_running = True
    
    def stop_simulation(self):
        """Stop the current simulation."""
        if not self.simulation_running:
            logger.warning("No simulation running")
            return
        
        logger.info(f"Stopping simulation {self.simulation_id}")
        
        # Stop the WebSocket worker
        self.worker.stop()
        
        self.simulation_running = False
        self.simulation_id = None
    
    def run(self):
        """Run the application."""
        # Show the main window
        self.main_window.show()
        
        # Run the Qt event loop
        return self.app.exec()
    
    def cleanup(self):
        """Clean up resources before exiting."""
        # Stop any running simulation
        if self.simulation_running:
            self.stop_simulation()
        
        # Quit the worker thread
        self.worker_thread.quit()
        self.worker_thread.wait()
        
        logger.info("Application resources cleaned up")
    
    def signal_handler(self, sig, frame):
        """Handle signals for graceful shutdown."""
        logger.info(f"Signal {sig} received, shutting down...")
        self.cleanup()
        sys.exit(0)


def main():
    """Main entry point for the application."""
    try:
        # Create and run the application
        app = TradeSimulatorApp()
        exit_code = app.run()
        
        # Clean up before exiting
        app.cleanup()
        
        return exit_code
    except Exception as e:
        logger.error(f"Unhandled exception in main: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
