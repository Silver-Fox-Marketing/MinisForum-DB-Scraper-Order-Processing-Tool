#!/usr/bin/env python3
"""
Web Server Startup Script
========================

Starts the Flask web server for testing the integrated system.
Handles imports and ensures all modules are available.

Author: Silver Fox Assistant
Created: 2025-07-30
"""

import sys
import os
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
web_gui_dir = project_root / "web_gui"
scripts_dir = project_root / "scripts"

sys.path.insert(0, str(web_gui_dir))
sys.path.insert(0, str(scripts_dir))

def start_server():
    """Start the Flask web server"""
    try:
        print("[STARTUP] Starting Silver Fox Web Server...")
        print(f"[INFO] Project root: {project_root}")
        print(f"[INFO] Web GUI: {web_gui_dir}")
        print(f"[INFO] Scripts: {scripts_dir}")
        
        # Change to web_gui directory
        os.chdir(web_gui_dir)
        
        # Import and run the Flask app
        from app import app, socketio
        
        print("[SUCCESS] Flask app imported successfully")
        print("[SERVER] Starting server on http://127.0.0.1:5000")
        print("[ACCESS] Access the dashboard at: http://127.0.0.1:5000")
        print("[TEST] Access test page at: http://127.0.0.1:5000/test")
        print()
        print("Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Start the server
        socketio.run(app, host='127.0.0.1', port=5000, debug=False)
        
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        print("[HELP] Make sure all dependencies are installed")
    except Exception as e:
        print(f"[ERROR] Server startup failed: {e}")

if __name__ == "__main__":
    start_server()