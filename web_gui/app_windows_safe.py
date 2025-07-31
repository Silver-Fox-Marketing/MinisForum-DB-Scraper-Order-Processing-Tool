#!/usr/bin/env python3
"""
Windows-Safe Web GUI for Testing - Silver Fox Marketing
=======================================================

Windows-compatible version without emojis that cause encoding issues.

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

# Add the scripts directory to Python path
scripts_dir = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

# Configure logging without emoji characters
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('minimal_web_gui.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)
app.secret_key = 'silver_fox_marketing_minimal_2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables for testing
DEMO_MODE = True
import_errors = []

# Try to import modules with error handling
try:
    from database_connection import db_manager
    logger.info("[OK] Database connection imported")
    
    # Test database connection
    result = db_manager.execute_query("SELECT 1 as test")
    if result and result[0]['test'] == 1:
        DEMO_MODE = False
        logger.info("[OK] Database connection working")
    else:
        logger.warning("[WARN] Database query failed, using demo mode")
        
except Exception as e:
    logger.error(f"[ERROR] Database connection failed: {e}")
    import_errors.append(f"database_connection: {str(e)}")

try:
    from order_processing_workflow import OrderProcessingWorkflow
    order_processor = OrderProcessingWorkflow()
    logger.info("[OK] Order processing workflow imported")
except Exception as e:
    logger.error(f"[ERROR] Order processing workflow failed: {e}")
    import_errors.append(f"order_processing_workflow: {str(e)}")
    order_processor = None

try:
    from real_scraper_integration import RealScraperIntegration
    scraper_integration = RealScraperIntegration(socketio)
    logger.info("[OK] Real scraper integration imported")
except Exception as e:
    logger.error(f"[ERROR] Real scraper integration failed: {e}")
    import_errors.append(f"real_scraper_integration: {str(e)}")
    scraper_integration = None

@app.route('/')
def index():
    """Main dashboard page"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index: {e}")
        return f"<h1>Error rendering index.html</h1><p>{str(e)}</p>", 500

@app.route('/test')
def test_page():
    """Test page to verify server is working"""
    status = {
        'server_status': 'running',
        'demo_mode': DEMO_MODE,
        'import_errors': import_errors,
        'timestamp': datetime.now().isoformat(),
        'python_version': sys.version,
        'flask_working': True,
        'order_processor_available': order_processor is not None,
        'scraper_integration_available': scraper_integration is not None
    }
    
    return f"""
    <html>
    <head><title>Silver Fox Test Server</title></head>
    <body>
        <h1>Silver Fox Web GUI - Test Page</h1>
        <h2>Server Status: RUNNING</h2>
        <pre>{json.dumps(status, indent=2)}</pre>
        
        <h2>Available Routes</h2>
        <ul>
            <li><a href="/">/</a> - Main dashboard</li>
            <li><a href="/test">/test</a> - This test page</li>
            <li><a href="/api/test-database">/api/test-database</a> - Test database</li>
            <li><a href="/api/dealerships">/api/dealerships</a> - Get dealerships</li>
            <li><a href="/order-form">/order-form</a> - Order form</li>
            <li><a href="/stress-test">/stress-test</a> - Run stress tests</li>
        </ul>
        
        <h2>System Status</h2>
        {'<p style="color: green;">[OK] All imports successful</p>' if not import_errors else f'<p style="color: red;">[ERROR] Import errors:</p><ul>{"".join(f"<li>{error}</li>" for error in import_errors)}</ul>'}
        
        <h2>Quick Actions</h2>
        <button onclick="window.open('/order-form', '_blank')">Open Order Form</button>
        <button onclick="runStressTest()">Run Stress Test</button>
        
        <script>
        function runStressTest() {{
            fetch('/api/stress-test', {{method: 'POST'}})
                .then(response => response.json())
                .then(data => {{
                    alert('Stress test completed. Check logs for details.');
                    console.log(data);
                }})
                .catch(error => {{
                    alert('Error running stress test: ' + error);
                }});
        }}
        </script>
    </body>
    </html>
    """

@app.route('/stress-test')
def stress_test_page():
    """Stress test dashboard"""
    return """
    <html>
    <head><title>Stress Test Dashboard</title></head>
    <body>
        <h1>Silver Fox Stress Test Dashboard</h1>
        <div id="status">Ready to run stress tests...</div>
        
        <h2>Test Categories</h2>
        <button onclick="runTest('database')">Database Tests</button>
        <button onclick="runTest('cao')">CAO Order Tests</button>
        <button onclick="runTest('list')">List Order Tests</button>
        <button onclick="runTest('concurrent')">Concurrent Tests</button>
        <button onclick="runTest('all')">Run All Tests</button>
        
        <h2>Results</h2>
        <div id="results"></div>
        
        <script>
        function runTest(testType) {
            document.getElementById('status').innerHTML = 'Running ' + testType + ' tests...';
            
            fetch('/api/stress-test', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({test_type: testType})
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('status').innerHTML = 'Test completed!';
                document.getElementById('results').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            })
            .catch(error => {
                document.getElementById('status').innerHTML = 'Test failed: ' + error;
            });
        }
        </script>
    </body>
    </html>
    """

@app.route('/api/test-database')
def test_database():
    """Test database connectivity"""
    if DEMO_MODE:
        return jsonify({
            'status': 'demo_mode',
            'message': 'Database not available, running in demo mode',
            'demo_data': True
        })
    
    try:
        result = db_manager.execute_query("SELECT 1 as test, CURRENT_TIMESTAMP as timestamp")
        return jsonify({
            'status': 'success',
            'result': result,
            'message': 'Database connection working'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'Database connection failed'
        }), 500

@app.route('/api/dealerships')
def get_dealerships():
    """API endpoint to get dealership configurations"""
    if DEMO_MODE:
        # Return demo data when database is not available
        demo_configs = [
            {
                'name': 'BMW of West St. Louis',
                'filtering_rules': {'exclude_conditions': ['offlot'], 'min_price': 25000},
                'output_rules': {'include_qr': True, 'sort_by': ['make', 'model']},
                'qr_output_path': 'C:\\qr_codes\\bmw_west_stl\\',
                'is_active': True,
                'updated_at': '2025-07-29'
            },
            {
                'name': 'Columbia Honda',
                'filtering_rules': {'exclude_conditions': ['offlot'], 'min_price': 20000},
                'output_rules': {'include_qr': True, 'sort_by': ['model', 'year']},
                'qr_output_path': 'C:\\qr_codes\\columbia_honda\\',
                'is_active': True,
                'updated_at': '2025-07-29'
            },
            {
                'name': 'Dave Sinclair Lincoln South',
                'filtering_rules': {'exclude_conditions': ['offlot'], 'min_price': 30000},
                'output_rules': {'include_qr': True, 'sort_by': ['make', 'model']},
                'qr_output_path': 'C:\\qr_codes\\dave_sinclair\\',
                'is_active': True,
                'updated_at': '2025-07-29'
            }
        ]
        return jsonify(demo_configs)
    
    try:
        configs = db_manager.execute_query("""
            SELECT name, filtering_rules, output_rules, qr_output_path, is_active, updated_at
            FROM dealership_configs 
            ORDER BY name
        """)
        return jsonify(configs)
    except Exception as e:
        logger.error(f"Failed to get dealership configs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/order-form')
def order_form():
    """Order processing form page"""
    try:
        return render_template('order_form.html')
    except Exception as e:
        logger.error(f"Error rendering order form: {e}")
        return f"<h1>Error rendering order_form.html</h1><p>{str(e)}</p><br><a href='/test'>Back to test page</a>", 500

@app.route('/api/orders/today-schedule')
def get_today_schedule():
    """Get today's CAO schedule"""
    if DEMO_MODE or not order_processor:
        return jsonify([
            {'name': 'BMW of West St. Louis', 'template': 'Shortcut'},
            {'name': 'Columbia Honda', 'template': 'Flyout'},
            {'name': 'Dave Sinclair Lincoln South', 'template': 'Shortcut Pack'}
        ])
    
    try:
        schedule = order_processor.get_todays_cao_schedule()
        return jsonify(schedule)
    except Exception as e:
        logger.error(f"Error getting today's schedule: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/process-cao', methods=['POST'])
def process_cao_orders():
    """Process selected CAO orders"""
    if not order_processor:
        return jsonify({'error': 'Order processor not available'}), 500
    
    try:
        data = request.get_json()
        dealerships = data.get('dealerships', [])
        vehicle_types = data.get('vehicle_types', ['new', 'cpo', 'used'])
        
        results = []
        for dealership in dealerships:
            if DEMO_MODE:
                # Return demo results
                result = {
                    'dealership': dealership,
                    'success': True,
                    'order_type': 'CAO',
                    'new_vehicles': 5,
                    'total_vehicles': 25,
                    'qr_codes_generated': 5,
                    'qr_folder': f'C:\\qr_codes\\{dealership.lower().replace(" ", "_")}\\',
                    'csv_file': f'{dealership}_cao_export.csv'
                }
            else:
                result = order_processor.process_cao_order(dealership, vehicle_types)
            results.append(result)
        
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error processing CAO orders: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stress-test', methods=['POST'])
def run_stress_test():
    """Run comprehensive stress test"""
    try:
        # Import and run stress test
        from comprehensive_order_stress_test import OrderProcessingStressTest
        
        data = request.get_json() if request.is_json else {}
        test_type = data.get('test_type', 'all')
        
        tester = OrderProcessingStressTest()
        
        if test_type == 'database':
            tester.test_database_connectivity()
            tester.test_database_performance_under_load()
        elif test_type == 'cao':
            tester.test_cao_order_processing()
        elif test_type == 'list':
            tester.test_list_order_processing()
        elif test_type == 'concurrent':
            tester.test_concurrent_processing()
        else:
            # Run comprehensive test
            results = tester.run_comprehensive_stress_test()
            return jsonify(results)
        
        return jsonify({
            'status': 'completed',
            'test_type': test_type,
            'results': tester.test_results
        })
        
    except Exception as e:
        logger.error(f"Stress test failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return f"<h1>404 - Page Not Found</h1><p>The requested URL was not found.</p><a href='/test'>Go to test page</a>", 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return f"<h1>500 - Internal Server Error</h1><p>{str(error)}</p><a href='/test'>Go to test page</a>", 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('exports', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    logger.info("[START] Starting Silver Fox Web GUI (Windows Safe)")
    logger.info(f"[INFO] Demo Mode: {DEMO_MODE}")
    logger.info(f"[INFO] Import Errors: {len(import_errors)}")
    
    print("=" * 60)
    print("SILVER FOX WEB GUI - WINDOWS SAFE VERSION")
    print("=" * 60)
    print(f"Server starting on: http://127.0.0.1:5001")
    print(f"Test page: http://127.0.0.1:5001/test")
    print(f"Order form: http://127.0.0.1:5001/order-form")
    print(f"Stress tests: http://127.0.0.1:5001/stress-test")
    print("=" * 60)
    
    # Start with debug mode for testing
    app.run(
        host='127.0.0.1', 
        port=5001,  # Use different port to avoid conflicts
        debug=True,
        threaded=True
    )