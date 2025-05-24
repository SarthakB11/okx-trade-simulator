import unittest
import asyncio
import json
from unittest.mock import MagicMock, patch
from src.websocket.connector import WebSocketConnector

class TestWebSocketConnector(unittest.TestCase):
    """Test cases for the WebSocketConnector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.connector = WebSocketConnector()
        self.connector.on_message = MagicMock()
        self.connector.on_error = MagicMock()
        self.connector.on_close = MagicMock()
        self.connector.on_open = MagicMock()
        
        # Sample WebSocket message
        self.sample_message = json.dumps({
            "event": "subscribe",
            "arg": {
                "channel": "books",
                "instId": "BTC-USDT-SWAP"
            }
        })
    
    @patch('websockets.connect')
    async def test_connect(self, mock_connect):
        """Test connecting to the WebSocket server."""
        # Mock the WebSocket connection
        mock_ws = MagicMock()
        mock_connect.return_value.__aenter__.return_value = mock_ws
        
        # Connect to the WebSocket server
        await self.connector.connect()
        
        # Check that the WebSocket connection was established
        mock_connect.assert_called_once()
        
        # Check that the on_open callback was called
        self.connector.on_open.assert_called_once()
    
    @patch('websockets.connect')
    async def test_disconnect(self, mock_connect):
        """Test disconnecting from the WebSocket server."""
        # Mock the WebSocket connection
        mock_ws = MagicMock()
        mock_connect.return_value.__aenter__.return_value = mock_ws
        
        # Connect to the WebSocket server
        await self.connector.connect()
        
        # Disconnect from the WebSocket server
        await self.connector.disconnect()
        
        # Check that the WebSocket connection was closed
        mock_ws.close.assert_called_once()
        
        # Check that the on_close callback was called
        self.connector.on_close.assert_called_once()
    
    @patch('websockets.connect')
    async def test_send_message(self, mock_connect):
        """Test sending a message to the WebSocket server."""
        # Mock the WebSocket connection
        mock_ws = MagicMock()
        mock_connect.return_value.__aenter__.return_value = mock_ws
        
        # Connect to the WebSocket server
        await self.connector.connect()
        
        # Send a message to the WebSocket server
        await self.connector.send_message(self.sample_message)
        
        # Check that the message was sent
        mock_ws.send.assert_called_once_with(self.sample_message)
    
    @patch('websockets.connect')
    async def test_receive_message(self, mock_connect):
        """Test receiving a message from the WebSocket server."""
        # Mock the WebSocket connection
        mock_ws = MagicMock()
        mock_connect.return_value.__aenter__.return_value = mock_ws
        
        # Set up the mock to return a message
        mock_ws.recv.return_value = self.sample_message
        
        # Connect to the WebSocket server
        await self.connector.connect()
        
        # Start the message loop
        # We'll run it for a short time and then stop it
        task = asyncio.create_task(self.connector._message_loop())
        await asyncio.sleep(0.1)
        task.cancel()
        
        # Check that the on_message callback was called with the correct message
        self.connector.on_message.assert_called_once_with(json.loads(self.sample_message))
    
    @patch('websockets.connect')
    async def test_reconnect(self, mock_connect):
        """Test reconnecting to the WebSocket server after a disconnection."""
        # Mock the WebSocket connection
        mock_ws = MagicMock()
        mock_connect.return_value.__aenter__.return_value = mock_ws
        
        # Set up the mock to raise an exception when receiving a message
        mock_ws.recv.side_effect = Exception("Connection lost")
        
        # Connect to the WebSocket server
        await self.connector.connect()
        
        # Start the message loop
        # We'll run it for a short time and then stop it
        task = asyncio.create_task(self.connector._message_loop())
        await asyncio.sleep(0.1)
        task.cancel()
        
        # Check that the on_error callback was called
        self.connector.on_error.assert_called_once()
        
        # Check that a reconnection was attempted
        self.assertEqual(mock_connect.call_count, 2)
    
    @patch('websockets.connect')
    async def test_subscribe(self, mock_connect):
        """Test subscribing to a channel."""
        # Mock the WebSocket connection
        mock_ws = MagicMock()
        mock_connect.return_value.__aenter__.return_value = mock_ws
        
        # Connect to the WebSocket server
        await self.connector.connect()
        
        # Subscribe to a channel
        channel = "books"
        instrument_id = "BTC-USDT-SWAP"
        await self.connector.subscribe(channel, instrument_id)
        
        # Check that the subscription message was sent
        expected_message = json.dumps({
            "op": "subscribe",
            "args": [{
                "channel": channel,
                "instId": instrument_id
            }]
        })
        mock_ws.send.assert_called_once_with(expected_message)
    
    @patch('websockets.connect')
    async def test_unsubscribe(self, mock_connect):
        """Test unsubscribing from a channel."""
        # Mock the WebSocket connection
        mock_ws = MagicMock()
        mock_connect.return_value.__aenter__.return_value = mock_ws
        
        # Connect to the WebSocket server
        await self.connector.connect()
        
        # Unsubscribe from a channel
        channel = "books"
        instrument_id = "BTC-USDT-SWAP"
        await self.connector.unsubscribe(channel, instrument_id)
        
        # Check that the unsubscription message was sent
        expected_message = json.dumps({
            "op": "unsubscribe",
            "args": [{
                "channel": channel,
                "instId": instrument_id
            }]
        })
        mock_ws.send.assert_called_once_with(expected_message)


# Helper function to run async tests
def run_async_test(test_func):
    """Run an async test function."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(test_func)
    finally:
        loop.close()


if __name__ == '__main__':
    unittest.main()
