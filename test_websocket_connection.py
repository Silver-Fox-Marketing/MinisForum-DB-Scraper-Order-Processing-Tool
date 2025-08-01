#!/usr/bin/env python3
"""
WebSocket Connection Test Script
Tests the WebSocket functionality without running the full web GUI
"""

import time
import logging
from flask import Flask
from flask_socketio import SocketIO, emit
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_websocket_basic():
    """Test basic WebSocket functionality"""
    
    print("🧪 Testing WebSocket Connection...")
    print("=" * 50)
    
    # Create minimal Flask app with Socket.IO
    app = Flask(__name__)
    app.secret_key = 'test_key'
    
    socketio = SocketIO(app, 
                       cors_allowed_origins="*", 
                       async_mode='threading',
                       logger=True, 
                       engineio_logger=False,
                       transports=['websocket', 'polling'])
    
    # Test message counter
    message_count = 0
    
    @socketio.on('connect')
    def handle_connect():
        print("✅ Client connected to WebSocket")
        emit('response', {'message': 'Connected successfully'})
    
    @socketio.on('disconnect')  
    def handle_disconnect():
        print("❌ Client disconnected from WebSocket")
    
    @app.route('/test')
    def test_route():
        return "WebSocket test server running"
    
    def simulate_scraper_messages():
        """Simulate scraper progress messages"""
        nonlocal message_count
        time.sleep(2)  # Wait for connections
        
        messages = [
            {'message': '🔄 Starting scraper test...', 'status': 'starting'},
            {'message': '📊 Processing data...', 'status': 'processing', 'progress': 50},
            {'message': '🏁 Test completed!', 'status': 'completed', 'progress': 100}
        ]
        
        for msg in messages:
            message_count += 1
            print(f"📡 Sending message {message_count}: {msg['message']}")
            socketio.emit('scraper_output', msg, broadcast=True)
            time.sleep(2)
    
    # Start background message simulation
    msg_thread = threading.Thread(target=simulate_scraper_messages, daemon=True)
    msg_thread.start()
    
    print("🚀 Starting WebSocket test server on http://127.0.0.1:5001")
    print("📱 Connect with browser to see if WebSocket works")
    print("🛑 Press Ctrl+C to stop")
    
    try:
        socketio.run(app, host='127.0.0.1', port=5001, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Test server stopped")

def check_socket_io_installation():
    """Check if required packages are installed"""
    print("🔍 Checking Socket.IO installation...")
    
    try:
        import flask_socketio
        print(f"✅ Flask-SocketIO version: {flask_socketio.__version__}")
    except ImportError:
        print("❌ Flask-SocketIO not installed")
        print("Install with: pip install flask-socketio")
        return False
    
    try:
        import socketio
        print(f"✅ Python-SocketIO version: {socketio.__version__}")
    except ImportError:
        print("❌ Python-SocketIO not installed")
        return False
    
    return True

def test_socket_io_config():
    """Test Socket.IO configuration"""
    print("\n🔧 Testing Socket.IO Configuration...")
    
    try:
        app = Flask(__name__)
        socketio = SocketIO(app, 
                           cors_allowed_origins="*", 
                           async_mode='threading',
                           logger=True, 
                           engineio_logger=False,
                           transports=['websocket', 'polling'])
        print("✅ Socket.IO configuration valid")
        return True
    except Exception as e:
        print(f"❌ Socket.IO configuration error: {e}")
        return False

if __name__ == "__main__":
    print("WebSocket Connection Diagnostic Tool")
    print("=" * 40)
    
    # Check installations
    if not check_socket_io_installation():
        exit(1)
    
    # Test configuration
    if not test_socket_io_config():
        exit(1)
    
    print("\n" + "=" * 40)
    print("Ready to test WebSocket connection!")
    print("This will start a test server on port 5001")
    
    response = input("\nStart WebSocket test server? (y/n): ").lower().strip()
    if response == 'y':
        test_websocket_basic()
    else:
        print("Test cancelled.")