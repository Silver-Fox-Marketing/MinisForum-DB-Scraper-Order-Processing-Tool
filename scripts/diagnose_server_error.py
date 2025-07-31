#!/usr/bin/env python3
"""
Web GUI Server Error Diagnostic Tool
====================================

Diagnose and fix internal server errors in the web GUI.

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import os
import sys
import traceback
from pathlib import Path

# Add the scripts directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_imports():
    """Test all critical imports"""
    print("🔄 Testing Basic Imports...")
    
    try:
        from database_connection import db_manager
        print("✅ database_connection imported successfully")
    except Exception as e:
        print(f"❌ database_connection failed: {e}")
        traceback.print_exc()
        return False
    
    try:
        from csv_importer_complete import CompleteCSVImporter
        print("✅ csv_importer_complete imported successfully")
    except Exception as e:
        print(f"❌ csv_importer_complete failed: {e}")
        traceback.print_exc()
        return False
    
    try:
        from order_processing_integration import OrderProcessingIntegrator
        print("✅ order_processing_integration imported successfully")
    except Exception as e:
        print(f"❌ order_processing_integration failed: {e}")
        traceback.print_exc()
        return False
    
    try:
        from qr_code_generator import QRCodeGenerator
        print("✅ qr_code_generator imported successfully")
    except Exception as e:
        print(f"❌ qr_code_generator failed: {e}")
        traceback.print_exc()
        return False
    
    try:
        from data_exporter import DataExporter
        print("✅ data_exporter imported successfully")
    except Exception as e:
        print(f"❌ data_exporter failed: {e}")
        traceback.print_exc()
        return False
    
    try:
        from order_processing_workflow import OrderProcessingWorkflow
        print("✅ order_processing_workflow imported successfully")
    except Exception as e:
        print(f"❌ order_processing_workflow failed: {e}")
        traceback.print_exc()
        return False
    
    try:
        from real_scraper_integration import RealScraperIntegration
        print("✅ real_scraper_integration imported successfully")
    except Exception as e:
        print(f"❌ real_scraper_integration failed: {e}")
        traceback.print_exc()
        return False
    
    return True

def test_database_connection():
    """Test database connectivity"""
    print("\n🔄 Testing Database Connection...")
    
    try:
        from database_connection import db_manager
        
        # Test basic query
        result = db_manager.execute_query("SELECT 1 as test")
        if result and result[0]['test'] == 1:
            print("✅ Database connection working")
            return True
        else:
            print("❌ Database query returned unexpected result")
            return False
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        traceback.print_exc()
        return False

def test_flask_app_creation():
    """Test Flask app creation"""
    print("\n🔄 Testing Flask App Creation...")
    
    try:
        # Change to web_gui directory
        web_gui_dir = Path(__file__).parent.parent / 'web_gui'
        os.chdir(web_gui_dir)
        
        # Try to import Flask components
        from flask import Flask
        print("✅ Flask imported successfully")
        
        # Test basic app creation
        app = Flask(__name__)
        app.secret_key = 'test_key'
        print("✅ Flask app created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask app creation failed: {e}")
        traceback.print_exc()
        return False

def test_socketio_integration():
    """Test SocketIO integration"""
    print("\n🔄 Testing SocketIO Integration...")
    
    try:
        from flask import Flask
        from flask_socketio import SocketIO
        
        app = Flask(__name__)
        app.secret_key = 'test_key'
        socketio = SocketIO(app, cors_allowed_origins="*")
        
        print("✅ SocketIO integration working")
        return True
        
    except Exception as e:
        print(f"❌ SocketIO integration failed: {e}")
        traceback.print_exc()
        return False

def diagnose_app_py():
    """Diagnose the main app.py file"""
    print("\n🔄 Diagnosing app.py...")
    
    try:
        # Read app.py and check for syntax issues
        web_gui_dir = Path(__file__).parent.parent / 'web_gui'
        app_py_path = web_gui_dir / 'app.py'
        
        if not app_py_path.exists():
            print(f"❌ app.py not found at {app_py_path}")
            return False
        
        # Try to compile the file
        with open(app_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        compile(content, str(app_py_path), 'exec')
        print("✅ app.py syntax is valid")
        
        # Try to import it
        sys.path.insert(0, str(web_gui_dir))
        
        # Remove any cached imports
        if 'app' in sys.modules:
            del sys.modules['app']
        
        import app
        print("✅ app.py imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ app.py diagnosis failed: {e}")
        traceback.print_exc()
        return False

def create_minimal_test_server():
    """Create a minimal test server to isolate issues"""
    print("\n🔄 Creating Minimal Test Server...")
    
    minimal_app_content = '''#!/usr/bin/env python3
"""
Minimal Test Server for Debugging
"""

from flask import Flask, render_template, jsonify
import os
import sys

# Add the scripts directory to Python path
scripts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts')
sys.path.insert(0, scripts_dir)

app = Flask(__name__)
app.secret_key = 'test_key'

@app.route('/')
def index():
    """Basic test route"""
    return '''
    <html>
    <head><title>Test Server</title></head>
    <body>
        <h1>Test Server Working</h1>
        <p>Basic Flask server is running successfully.</p>
        <a href="/test-db">Test Database</a> |
        <a href="/test-imports">Test Imports</a>
    </body>
    </html>
    '''

@app.route('/test-db')
def test_db():
    """Test database connection"""
    try:
        from database_connection import db_manager
        result = db_manager.execute_query("SELECT 1 as test")
        return jsonify({"status": "success", "result": result})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

@app.route('/test-imports')
def test_imports():
    """Test critical imports"""
    import_results = {}
    
    modules = [
        'database_connection',
        'csv_importer_complete', 
        'order_processing_workflow',
        'real_scraper_integration'
    ]
    
    for module in modules:
        try:
            __import__(module)
            import_results[module] = "success"
        except Exception as e:
            import_results[module] = str(e)
    
    return jsonify(import_results)

if __name__ == '__main__':
    print("Starting minimal test server...")
    app.run(host='127.0.0.1', port=5001, debug=True)
'''
    
    try:
        web_gui_dir = Path(__file__).parent.parent / 'web_gui'
        test_server_path = web_gui_dir / 'test_server.py'
        
        with open(test_server_path, 'w', encoding='utf-8') as f:
            f.write(minimal_app_content)
        
        print(f"✅ Minimal test server created at {test_server_path}")
        print("   Run with: python test_server.py")
        print("   Access at: http://127.0.0.1:5001")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create test server: {e}")
        return False

def main():
    """Run comprehensive diagnosis"""
    print("🔍 WEB GUI SERVER ERROR DIAGNOSIS")
    print("=" * 50)
    
    all_passed = True
    
    # Test sequence
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Database Connection", test_database_connection),
        ("Flask App Creation", test_flask_app_creation),
        ("SocketIO Integration", test_socketio_integration),
        ("app.py Diagnosis", diagnose_app_py),
        ("Create Test Server", create_minimal_test_server)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ Test framework error: {e}")
            traceback.print_exc()
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 DIAGNOSIS COMPLETE - All tests passed")
        print("   The server should be working. Try running app.py again.")
    else:
        print("💥 DIAGNOSIS COMPLETE - Issues found")
        print("   Use the minimal test server to isolate problems.")
        print("   Run: python test_server.py")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)