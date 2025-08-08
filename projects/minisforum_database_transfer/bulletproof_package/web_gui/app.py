#!/usr/bin/env python3
"""
MinisForum Database Web GUI
==========================

Local web-based control interface for the dealership database system.
Provides visual dealership management, scraper control, and report generation.

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from flask_socketio import SocketIO, emit
import threading
import time

# Add the scripts directory to Python path for imports
scripts_dir = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

# Import our existing modules with error handling
DEMO_MODE = False
try:
    from database_connection import db_manager
    from csv_importer_complete import CompleteCSVImporter
    from order_processing_integration import OrderProcessingIntegrator
    from qr_code_generator import QRCodeGenerator
    from data_exporter import DataExporter
    from order_queue_manager import OrderQueueManager
    print("OK Basic modules imported successfully")
    
    print("Attempting to import OrderProcessingWorkflow...")
    from correct_order_processing import CorrectOrderProcessor
    print("OK CorrectOrderProcessor imported successfully")
    
    print("Attempting to import RealScraperIntegration...")
    from real_scraper_integration import RealScraperIntegration
    print("OK RealScraperIntegration imported successfully")
    
    print("Attempting to import Scraper18Controller...")
    try:
        from scraper18_controller import Scraper18WebController
        print("OK Scraper18Controller imported successfully")
    except Exception as e:
        print(f"Warning: Scraper18Controller import failed: {e}")
        Scraper18WebController = None
    print("OK All backend modules imported successfully")
    
    # Check if database is available
    if db_manager._connection_pool is None:
        DEMO_MODE = True
        print("WARNING Running in DEMO MODE - Database not available")
    else:
        print("OK Database connection available")
        
except ImportError as e:
    print(f"ERROR Critical import error: {e}")
    print("Please ensure all Python dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# Flask app setup
app = Flask(__name__)
app.secret_key = 'silver_fox_marketing_minisforum_2025'
socketio = SocketIO(app, 
                   cors_allowed_origins="*", 
                   async_mode='threading',
                   logger=True, 
                   engineio_logger=False,
                   transports=['websocket', 'polling'])

# Initialize scraper18_controller with socketio after socketio is created
scraper18_controller = None
if not DEMO_MODE and Scraper18WebController is not None:
    scraper18_controller = Scraper18WebController(socketio=socketio)
    print("OK Scraper18Controller configured with SocketIO")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('web_gui.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScraperController:
    """Controls scraper operations and manages system state"""
    
    def __init__(self, socketio=None):
        self.csv_importer = CompleteCSVImporter()
        self.order_processor = OrderProcessingIntegrator()
        self.qr_generator = QRCodeGenerator()
        self.data_exporter = DataExporter()
        # Using scraper18_controller instead of RealScraperIntegration
        self.socketio = socketio
        self.scraper_running = False
        self.last_scrape_time = None
        self.scrape_results = {}
        
    def get_dealership_configs(self):
        """Get all dealership configurations"""
        try:
            configs = db_manager.execute_query("""
                SELECT name, filtering_rules, output_rules, qr_output_path, is_active, updated_at
                FROM dealership_configs 
                ORDER BY name
            """)
            
            for config in configs:
                # Handle JSON/JSONB data safely - PostgreSQL JSONB returns as dict
                try:
                    # If already a dict (JSONB from PostgreSQL), use as-is
                    if isinstance(config['filtering_rules'], dict):
                        config['filtering_rules'] = config['filtering_rules']
                    elif config['filtering_rules']:
                        config['filtering_rules'] = json.loads(config['filtering_rules'])
                    else:
                        config['filtering_rules'] = {}
                        
                    if isinstance(config['output_rules'], dict):
                        config['output_rules'] = config['output_rules']
                    elif config['output_rules']:
                        config['output_rules'] = json.loads(config['output_rules'])
                    else:
                        config['output_rules'] = {}
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"JSON parsing error for config: {e}")
                    config['filtering_rules'] = {}
                    config['output_rules'] = {}
            
            return configs
        except Exception as e:
            logger.error(f"Failed to get dealership configs: {e}")
            return []
    
    def update_dealership_config(self, dealership_name, filtering_rules, is_active=True):
        """Update dealership configuration"""
        try:
            db_manager.execute_query("""
                UPDATE dealership_configs 
                SET filtering_rules = %s, is_active = %s, updated_at = CURRENT_TIMESTAMP
                WHERE name = %s
            """, (json.dumps(filtering_rules), is_active, dealership_name))
            
            return True
        except Exception as e:
            logger.error(f"Failed to update dealership config: {e}")
            return False
    
    def run_scraper(self, selected_dealerships=None, csv_file_path=None):
        """Run the complete scraper pipeline with REAL scrapers"""
        try:
            self.scraper_running = True
            self.scrape_results = {
                'start_time': datetime.now(),
                'dealerships': {},
                'total_vehicles': 0,
                'total_real_data': 0,
                'total_fallback_data': 0,
                'errors': [],
                'duration': 0,
                'missing_vins': 0
            }
            
            logger.info("🚀 Starting REAL SCRAPER pipeline...")
            
            # Step 1: Import CSV data (if provided)
            if csv_file_path and os.path.exists(csv_file_path):
                logger.info(f"Importing CSV: {csv_file_path}")
                import_result = self.csv_importer.import_csv(csv_file_path)
                
                if import_result and import_result.get('success'):
                    self.scrape_results['csv_vehicles'] = import_result.get('processed', 0)
                    self.scrape_results['missing_vins'] = import_result.get('missing_vins', 0)
                    logger.info(f"CSV import successful: {import_result['processed']} vehicles")
            
            # Step 2: Run REAL scrapers for selected dealerships only
            logger.info("🎯 Running REAL scrapers to fetch live data...")
            
            # Get available real scrapers
            available_scrapers = self.real_scraper_integration.real_scraper_mapping.keys()
            logger.info(f"Available real scrapers: {list(available_scrapers)}")
            
            # Filter to only run selected dealerships that have real scrapers
            dealerships_to_scrape = []
            if selected_dealerships:
                dealerships_to_scrape = [d for d in selected_dealerships if d in available_scrapers]
                logger.info(f"Selected dealerships with real scrapers: {dealerships_to_scrape}")
            else:
                # If no specific selection, run all available real scrapers
                dealerships_to_scrape = list(available_scrapers)
                logger.info("No specific selection - running all available real scrapers")
            
            # Run real scrapers for selected dealerships
            for dealership_name in dealerships_to_scrape:
                try:
                    logger.info(f"🔄 Running REAL scraper for: {dealership_name}")
                    
                    # Run the real scraper
                    scraper_result = self.real_scraper_integration.run_real_scraper(dealership_name)
                    
                    if scraper_result['success']:
                        # Import vehicles to database
                        import_result = self.real_scraper_integration.import_vehicles_to_database(
                            scraper_result['vehicles'], 
                            dealership_name
                        )
                        
                        # Record results
                        self.scrape_results['dealerships'][dealership_name] = {
                            'vehicle_count': scraper_result['vehicle_count'],
                            'duration': scraper_result['duration_seconds'],
                            'data_source': scraper_result['data_source'],
                            'is_real_data': scraper_result['is_real_data'],
                            'import_result': import_result,
                            'status': 'completed'
                        }
                        
                        self.scrape_results['total_vehicles'] += scraper_result['vehicle_count']
                        
                        if scraper_result['is_real_data']:
                            self.scrape_results['total_real_data'] += scraper_result['vehicle_count']
                            logger.info(f"🎉 {dealership_name}: {scraper_result['vehicle_count']} vehicles (REAL DATA)")
                        else:
                            self.scrape_results['total_fallback_data'] += scraper_result['vehicle_count']
                            logger.warning(f"⚠️ {dealership_name}: {scraper_result['vehicle_count']} vehicles (FALLBACK)")
                        
                    else:
                        self.scrape_results['dealerships'][dealership_name] = {
                            'status': 'failed',
                            'error': scraper_result.get('error', 'Unknown error')
                        }
                        self.scrape_results['errors'].append(f"{dealership_name}: {scraper_result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    logger.error(f"Error running real scraper for {dealership_name}: {e}")
                    self.scrape_results['dealerships'][dealership_name] = {
                        'status': 'failed',
                        'error': str(e)
                    }
                    self.scrape_results['errors'].append(f"{dealership_name}: {str(e)}")
            
            # Step 3: Process remaining dealerships (if selected and not already processed)
            if selected_dealerships:
                remaining_dealerships = [d for d in selected_dealerships if d not in available_scrapers]
                
                for dealership in remaining_dealerships:
                    try:
                        logger.info(f"📋 Processing remaining dealership: {dealership}")
                        
                        # Create order processing job for dealerships without real scrapers
                        job = self.order_processor.create_order_processing_job(dealership)
                        
                        if job and job.get('job_id'):
                            self.scrape_results['dealerships'][dealership] = {
                                'job_id': job['job_id'],
                                'vehicle_count': job.get('vehicle_count', 0),
                                'qr_generated': job.get('qr_generation', {}).get('success', 0),
                                'export_file': job.get('export_file'),
                                'status': 'completed',
                                'data_source': 'existing_database_data'
                            }
                            self.scrape_results['total_vehicles'] += job.get('vehicle_count', 0)
                            logger.info(f"Completed {dealership}: {job['vehicle_count']} vehicles (from database)")
                        else:
                            self.scrape_results['dealerships'][dealership] = {
                                'status': 'failed',
                                'error': 'Job creation failed'
                            }
                            
                    except Exception as e:
                        logger.error(f"Error processing {dealership}: {e}")
                        self.scrape_results['dealerships'][dealership] = {
                            'status': 'failed',
                            'error': str(e)
                        }
                        self.scrape_results['errors'].append(f"{dealership}: {str(e)}")
            
            # Calculate duration
            self.scrape_results['end_time'] = datetime.now()
            self.scrape_results['duration'] = (self.scrape_results['end_time'] - self.scrape_results['start_time']).total_seconds()
            
            self.last_scrape_time = self.scrape_results['end_time']
            
            # Log comprehensive results
            logger.info("=" * 60)
            logger.info("🏆 REAL SCRAPER PIPELINE COMPLETED")
            logger.info("=" * 60)
            logger.info(f"Total vehicles: {self.scrape_results['total_vehicles']}")
            logger.info(f"Real data: {self.scrape_results['total_real_data']}")
            logger.info(f"Fallback data: {self.scrape_results['total_fallback_data']}")
            logger.info(f"Duration: {self.scrape_results['duration']:.1f} seconds")
            logger.info(f"Success rate: {len([d for d in self.scrape_results['dealerships'].values() if d['status'] == 'completed'])}/{len(self.scrape_results['dealerships'])}")
            
            if self.scrape_results['total_real_data'] > 0:
                logger.info("🎉 SUCCESS: Real data extracted from live APIs!")
            else:
                logger.warning("⚠️ No real data extracted - check API connectivity")
            
            return self.scrape_results
            
        except Exception as e:
            logger.error(f"Real scraper pipeline failed: {e}")
            self.scrape_results['errors'].append(str(e))
            return self.scrape_results
        finally:
            self.scraper_running = False
    
    def generate_adobe_report(self, dealerships=None):
        """Generate Adobe-ready export files"""
        try:
            if not dealerships:
                dealerships = [d['name'] for d in self.get_dealership_configs() if d['is_active']]
            
            export_files = []
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            for dealership in dealerships:
                export_file = self.data_exporter.export_dealership_data(
                    dealership, 
                    f"exports/adobe_export_{dealership.replace(' ', '_')}_{timestamp}.csv"
                )
                if export_file:
                    export_files.append(export_file)
            
            return export_files
        except Exception as e:
            logger.error(f"Adobe report generation failed: {e}")
            return []
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        try:
            if not self.scrape_results:
                return None
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'scrape_date': self.scrape_results['start_time'].strftime('%Y-%m-%d'),
                'scrape_time': self.scrape_results['start_time'].strftime('%H:%M:%S'),
                'duration_seconds': self.scrape_results['duration'],
                'duration_formatted': f"{self.scrape_results['duration']:.1f} seconds",
                'total_vehicles': self.scrape_results['total_vehicles'],
                'missing_vins': self.scrape_results['missing_vins'],
                'dealerships_processed': len(self.scrape_results['dealerships']),
                'dealerships_successful': len([d for d in self.scrape_results['dealerships'].values() if d.get('status') == 'completed']),
                'dealerships_failed': len([d for d in self.scrape_results['dealerships'].values() if d.get('status') == 'failed']),
                'total_errors': len(self.scrape_results['errors']),
                'dealership_details': [],
                'errors': self.scrape_results['errors']
            }
            
            for name, details in self.scrape_results['dealerships'].items():
                report['dealership_details'].append({
                    'name': name,
                    'vehicle_count': details.get('vehicle_count', 0),
                    'qr_generated': details.get('qr_generated', 0),
                    'status': details.get('status', 'unknown'),
                    'export_file': details.get('export_file')
                })
            
            return report
        except Exception as e:
            logger.error(f"Summary report generation failed: {e}")
            return None

# Global scraper controller
scraper_controller = ScraperController(socketio)

# Global order processor
order_processor = CorrectOrderProcessor()

# Global queue manager
queue_manager = OrderQueueManager()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/websocket-test')
def websocket_test():
    """WebSocket connection test page"""
    return render_template('websocket_test.html')

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
                'updated_at': '2025-07-25'
            },
            {
                'name': 'Mercedes-Benz of St. Louis',
                'filtering_rules': {'exclude_conditions': ['offlot'], 'min_price': 30000},
                'output_rules': {'include_qr': True, 'sort_by': ['model', 'year']},
                'qr_output_path': 'C:\\qr_codes\\mercedes_stl\\',
                'is_active': True,
                'updated_at': '2025-07-25'
            },
            {
                'name': 'Audi West County',
                'filtering_rules': {'exclude_conditions': ['offlot'], 'min_price': 28000},
                'output_rules': {'include_qr': True, 'sort_by': ['make', 'model']},
                'qr_output_path': 'C:\\qr_codes\\audi_west\\',
                'is_active': False,
                'updated_at': '2025-07-25'
            }
        ]
        return jsonify(demo_configs)
    else:
        configs = scraper_controller.get_dealership_configs()
        return jsonify(configs)

@app.route('/api/dealerships/<dealership_name>', methods=['POST'])
def update_dealership(dealership_name):
    """API endpoint to update dealership configuration"""
    data = request.get_json()
    
    filtering_rules = data.get('filtering_rules', {})
    is_active = data.get('is_active', True)
    
    success = scraper_controller.update_dealership_config(dealership_name, filtering_rules, is_active)
    
    if success:
        return jsonify({'success': True, 'message': 'Dealership updated successfully'})
    else:
        return jsonify({'success': False, 'message': 'Failed to update dealership'}), 500

@app.route('/api/scraper/start', methods=['POST'])
def start_scraper_legacy():
    """API endpoint to start scraper"""
    if scraper_controller.scraper_running:
        return jsonify({'success': False, 'message': 'Scraper already running'}), 400
    
    data = request.get_json()
    selected_dealerships = data.get('dealerships', [])
    csv_file_path = data.get('csv_file_path')
    
    # Run scraper in background thread
    def run_scraper_thread():
        scraper_controller.run_scraper(selected_dealerships, csv_file_path)
    
    thread = threading.Thread(target=run_scraper_thread)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': 'Scraper started successfully'})

@app.route('/api/scraper/status')
def scraper_status():
    """API endpoint to get scraper status"""
    return jsonify({
        'running': scraper_controller.scraper_running,
        'last_scrape': scraper_controller.last_scrape_time.isoformat() if scraper_controller.last_scrape_time else None,
        'results': scraper_controller.scrape_results
    })

@app.route('/api/reports/adobe')
def generate_adobe_report():
    """API endpoint to generate Adobe report"""
    dealerships = request.args.getlist('dealerships')
    files = scraper_controller.generate_adobe_report(dealerships if dealerships else None)
    
    return jsonify({
        'success': True,
        'files': files,
        'count': len(files)
    })

@app.route('/api/reports/summary')
def get_summary_report():
    """API endpoint to get summary report"""
    report = scraper_controller.generate_summary_report()
    
    if report:
        return jsonify(report)
    else:
        return jsonify({'error': 'No scrape data available'}), 404

@app.route('/api/logs')
def get_logs():
    """API endpoint to get recent log entries"""
    try:
        log_file = 'web_gui.log'
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
                # Return last 100 lines
                return jsonify({'logs': lines[-100:]})
        else:
            return jsonify({'logs': []})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/raw-data')
def get_raw_data():
    """API endpoint to get raw vehicle data overview"""
    try:
        # Get overall statistics
        total_count = db_manager.execute_query("SELECT COUNT(*) as count FROM raw_vehicle_data")[0]['count']
        
        # Get by location/dealership
        by_location = db_manager.execute_query("""
            SELECT location, COUNT(*) as count, 
                   MIN(import_timestamp) as first_import,
                   MAX(import_timestamp) as last_import
            FROM raw_vehicle_data 
            WHERE location IS NOT NULL
            GROUP BY location 
            ORDER BY count DESC
        """)
        
        # Get recent imports
        recent = db_manager.execute_query("""
            SELECT vin, make, model, year, location, import_timestamp
            FROM raw_vehicle_data 
            ORDER BY import_timestamp DESC 
            LIMIT 10
        """)
        
        return jsonify({
            'total_count': total_count,
            'by_location': by_location,
            'recent_imports': recent
        })
    except Exception as e:
        logger.error(f"Failed to get raw data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/normalized-data')
def get_normalized_data():
    """API endpoint to get normalized vehicle data overview"""
    try:
        # Get overall statistics
        total_count = db_manager.execute_query("SELECT COUNT(*) as count FROM normalized_vehicle_data")[0]['count']
        
        # Get by make
        by_make = db_manager.execute_query("""
            SELECT make, COUNT(*) as count, 
                   AVG(price) as avg_price,
                   MIN(year) as min_year,
                   MAX(year) as max_year
            FROM normalized_vehicle_data 
            WHERE make IS NOT NULL
            GROUP BY make 
            ORDER BY count DESC
            LIMIT 10
        """)
        
        # Get recent updates
        recent = db_manager.execute_query("""
            SELECT vin, make, model, year, price, updated_at
            FROM normalized_vehicle_data 
            ORDER BY updated_at DESC 
            LIMIT 10
        """)
        
        return jsonify({
            'total_count': total_count,
            'by_make': by_make,
            'recent_updates': recent
        })
    except Exception as e:
        logger.error(f"Failed to get normalized data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/order-processing')
def get_order_processing():
    """API endpoint to get order processing overview"""
    try:
        # Get job statistics
        total_jobs = db_manager.execute_query("SELECT COUNT(*) as count FROM order_processing_jobs")[0]['count']
        
        # Get jobs by status
        by_status = db_manager.execute_query("""
            SELECT status, COUNT(*) as count
            FROM order_processing_jobs 
            GROUP BY status 
            ORDER BY count DESC
        """)
        
        # Get recent jobs
        recent_jobs = db_manager.execute_query("""
            SELECT dealership_name, job_type, vehicle_count, status, created_at, export_file
            FROM order_processing_jobs 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        # Get summary statistics
        stats = db_manager.execute_query("""
            SELECT 
                SUM(vehicle_count) as total_vehicles_processed,
                AVG(vehicle_count) as avg_vehicles_per_job,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_jobs,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_jobs
            FROM order_processing_jobs
        """)[0]
        
        return jsonify({
            'total_jobs': total_jobs,
            'by_status': by_status,
            'recent_jobs': recent_jobs,
            'statistics': stats
        })
    except Exception as e:
        logger.error(f"Failed to get order processing data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/order-form')
def order_form():
    """Order processing form page"""
    return render_template('order_form.html')

@app.route('/order-wizard')
def order_wizard():
    """Order processing wizard page"""
    return render_template('order_wizard.html')

@app.route('/test')
def test_page():
    """Simple test page to debug issues"""
    return render_template('test_page.html')

@app.route('/api/orders/today-schedule')
def get_today_schedule():
    """Get today's CAO schedule"""
    try:
        schedule = order_processor.get_todays_cao_schedule()
        return jsonify(schedule)
    except Exception as e:
        logger.error(f"Error getting today's schedule: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/process-cao', methods=['POST'])
def process_cao_orders():
    """Process selected CAO orders"""
    try:
        data = request.get_json()
        dealerships = data.get('dealerships', [])
        vehicle_types = data.get('vehicle_types', ['new', 'cpo', 'used'])
        
        results = []
        for dealership in dealerships:
            # Use shortcut_pack as default template - can be made configurable
            template_type = data.get('template_type', 'shortcut_pack')
            result = order_processor.process_cao_order(dealership, template_type)
            results.append(result)
        
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error processing CAO orders: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/process-daily-cao', methods=['POST'])
def process_daily_cao():
    """Process all daily CAO orders"""
    try:
        results = order_processor.process_daily_cao_orders()
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error processing daily CAO: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/process-list', methods=['POST'])
def process_list_order():
    """Process list-based order"""
    try:
        data = request.get_json()
        dealership = data.get('dealership')
        vins = data.get('vins', [])
        
        if not dealership:
            return jsonify({'error': 'Dealership name required'}), 400
        if not vins:
            return jsonify({'error': 'VIN list required'}), 400
        
        template_type = data.get('template_type', 'shortcut_pack')
        result = order_processor.process_list_order(dealership, vins, template_type)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing list order: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download_csv/<filename>')
def download_csv(filename):
    """Download generated Adobe CSV files"""
    try:
        # Security check - only allow CSV files from orders directory
        if not filename.endswith('.csv'):
            return "Invalid file type", 400
        
        # Find the file in orders directory (check both locations)
        web_gui_orders_dir = Path(__file__).parent / "orders"
        scripts_orders_dir = Path(__file__).parent.parent / "scripts" / "orders"
        
        # Search for the file in both locations
        csv_file = None
        for orders_dir in [web_gui_orders_dir, scripts_orders_dir]:
            for root, dirs, files in os.walk(orders_dir):
                if filename in files:
                    csv_file = Path(root) / filename
                    break
            if csv_file:
                break
        
        if not csv_file or not csv_file.exists():
            return "File not found", 404
        
        return send_file(str(csv_file), as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.error(f"Error downloading CSV: {e}")
        return "Download error", 500

@app.route('/api/test-database')
def test_database():
    """Test database connectivity for system status"""
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
        logger.error(f"Database test failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'Database connection failed'
        }), 500

@app.route('/api/dealership-inventory/<dealership_name>')
def get_dealership_inventory(dealership_name):
    """API endpoint to get inventory verification for a specific dealership"""
    try:
        # Get raw data count
        raw_count = db_manager.execute_query("""
            SELECT COUNT(*) as count FROM raw_vehicle_data 
            WHERE location = %s
        """, (dealership_name,))[0]['count']
        
        # Get normalized data count
        norm_count = db_manager.execute_query("""
            SELECT COUNT(*) as count FROM normalized_vehicle_data nv
            JOIN raw_vehicle_data rv ON nv.raw_data_id = rv.id
            WHERE rv.location = %s
        """, (dealership_name,))[0]['count']
        
        # Get recent scraper runs for this dealership
        recent_jobs = db_manager.execute_query("""
            SELECT job_type, vehicle_count, status, created_at
            FROM order_processing_jobs 
            WHERE dealership_name = %s
            ORDER BY created_at DESC 
            LIMIT 5
        """, (dealership_name,))
        
        # Get unique makes/models
        inventory_breakdown = db_manager.execute_query("""
            SELECT make, COUNT(*) as count, 
                   MIN(year) as min_year, MAX(year) as max_year,
                   AVG(price) as avg_price
            FROM raw_vehicle_data 
            WHERE location = %s AND make IS NOT NULL
            GROUP BY make 
            ORDER BY count DESC
        """, (dealership_name,))
        
        return jsonify({
            'dealership_name': dealership_name,
            'raw_vehicle_count': raw_count,
            'normalized_vehicle_count': norm_count,
            'recent_jobs': recent_jobs,
            'inventory_breakdown': inventory_breakdown,
            'data_quality_score': (norm_count / raw_count * 100) if raw_count > 0 else 0
        })
    except Exception as e:
        logger.error(f"Failed to get dealership inventory for {dealership_name}: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# ORDER QUEUE MANAGEMENT API ENDPOINTS
# =============================================================================

@app.route('/api/queue/daily/<target_date>')
def get_daily_queue(target_date):
    """Get the daily order queue for a specific date"""
    try:
        from datetime import datetime
        
        # Parse date string (YYYY-MM-DD format)
        queue_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        orders = queue_manager.get_daily_queue(queue_date)
        return jsonify(orders)
        
    except Exception as e:
        logger.error(f"Error getting daily queue: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/queue/today')
def get_todays_queue():
    """Get today's order queue"""
    try:
        from datetime import date
        orders = queue_manager.get_daily_queue(date.today())
        return jsonify(orders)
        
    except Exception as e:
        logger.error(f"Error getting today's queue: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/queue/populate/<target_date>', methods=['POST'])
def populate_queue_for_date(target_date):
    """Populate the queue for a specific date"""
    try:
        from datetime import datetime
        
        # Parse date string (YYYY-MM-DD format)
        queue_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        orders_added = queue_manager.populate_daily_queue(queue_date)
        return jsonify({
            'success': True,
            'orders_added': orders_added,
            'date': target_date
        })
        
    except Exception as e:
        logger.error(f"Error populating queue: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/queue/populate-today', methods=['POST'])
def populate_todays_queue():
    """Populate today's queue based on weekly schedule"""
    try:
        from datetime import date
        orders_added = queue_manager.populate_daily_queue(date.today())
        return jsonify({
            'success': True,
            'orders_added': orders_added,
            'date': date.today().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error populating today's queue: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/queue/update-status/<int:queue_id>', methods=['POST'])
def update_queue_order_status(queue_id):
    """Update the status of a queue order"""
    try:
        data = request.get_json()
        status = data.get('status', 'pending')
        assigned_to = data.get('assigned_to')
        notes = data.get('notes')
        
        success = queue_manager.update_order_status(queue_id, status, assigned_to, notes)
        
        if success:
            return jsonify({'success': True, 'queue_id': queue_id, 'status': status})
        else:
            return jsonify({'success': False, 'error': 'Failed to update status'}), 500
            
    except Exception as e:
        logger.error(f"Error updating queue order status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/queue/process/<int:queue_id>', methods=['POST'])
def process_queue_order(queue_id):
    """Process a specific order from the queue"""
    try:
        result = queue_manager.process_queue_order(queue_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing queue order: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/queue/summary/<target_date>')
def get_queue_summary(target_date):
    """Get queue summary for a specific date"""
    try:
        from datetime import datetime
        
        # Parse date string (YYYY-MM-DD format)
        queue_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        summary = queue_manager.get_queue_summary(queue_date)
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error getting queue summary: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/queue/summary-today')
def get_todays_queue_summary():
    """Get today's queue summary"""
    try:
        from datetime import date
        summary = queue_manager.get_queue_summary(date.today())
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error getting today's queue summary: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/queue/templates')
def get_queue_templates():
    """Get available order templates"""
    try:
        templates = queue_manager.templates
        return jsonify(templates)
        
    except Exception as e:
        logger.error(f"Error getting queue templates: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/queue/add-custom-order', methods=['POST'])
def add_custom_queue_order():
    """Add a custom order to the queue"""
    try:
        data = request.get_json()
        
        dealership_name = data.get('dealership_name')
        order_type = data.get('order_type', 'Manual')
        template_type = data.get('template_type', 'Flyout')
        vehicle_types = data.get('vehicle_types', ['new', 'used'])
        scheduled_date = data.get('scheduled_date')
        priority = data.get('priority', 1)
        notes = data.get('notes', '')
        
        if not dealership_name or not scheduled_date:
            return jsonify({'error': 'Missing required fields'}), 400
        
        from datetime import datetime
        queue_date = datetime.strptime(scheduled_date, '%Y-%m-%d').date()
        day_name = queue_date.strftime('%A')
        
        # Insert custom order
        db_manager.execute_query("""
            INSERT INTO order_queue 
            (dealership_name, order_type, template_type, vehicle_types, 
             scheduled_date, day_of_week, priority, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (dealership_name, order_type, template_type, vehicle_types, 
              queue_date, day_name, priority, notes))
        
        return jsonify({'success': True, 'message': 'Custom order added to queue'})
        
    except Exception as e:
        logger.error(f"Error adding custom queue order: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# DATA SEARCH API ENDPOINTS
# =============================================================================

@app.route('/api/data/search')
def search_vehicle_data():
    """Search vehicle data with filters and pagination"""
    try:
        # Get query parameters
        query = request.args.get('query', '').strip()
        filter_by = request.args.get('filter_by', 'all')  # all, date, dealer
        data_type = request.args.get('data_type', 'both')  # raw, normalized, both
        sort_by = request.args.get('sort_by', 'import_timestamp')
        sort_order = request.args.get('sort_order', 'desc')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Date filtering
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Dealer filtering
        dealer_names = request.args.getlist('dealer_names')
        
        # Build base query based on data type - with deduplication by VIN showing most recent scrape
        if data_type == 'raw':
            base_query = """
                WITH ranked_vehicles AS (
                    SELECT 
                        r.vin, r.stock, r.location, r.year, r.make, r.model,
                        r.trim, r.ext_color as exterior_color, r.price, r.type as vehicle_type,
                        r.import_timestamp, 'raw' as data_source,
                        COUNT(*) OVER (PARTITION BY r.vin) as scrape_count,
                        MIN(r.import_timestamp) OVER (PARTITION BY r.vin) as first_scraped,
                        ROW_NUMBER() OVER (PARTITION BY r.vin ORDER BY r.import_timestamp DESC, r.id DESC) as rn
                    FROM raw_vehicle_data r
                )
                SELECT vin, stock, location, year, make, model, trim, 
                       exterior_color, price, vehicle_type, import_timestamp, data_source, scrape_count, first_scraped
                FROM ranked_vehicles
                WHERE rn = 1
            """
        elif data_type == 'normalized':
            base_query = """
                WITH ranked_vehicles AS (
                    SELECT 
                        n.vin, n.stock, n.location, n.year, n.make, n.model,
                        n.trim, '' as exterior_color, n.price, n.vehicle_condition as vehicle_type,
                        r.import_timestamp, 'normalized' as data_source,
                        COUNT(*) OVER (PARTITION BY n.vin) as scrape_count,
                        MIN(r.import_timestamp) OVER (PARTITION BY n.vin) as first_scraped,
                        ROW_NUMBER() OVER (PARTITION BY n.vin ORDER BY r.import_timestamp DESC, n.id DESC) as rn
                    FROM normalized_vehicle_data n
                    JOIN raw_vehicle_data r ON n.raw_data_id = r.id
                )
                SELECT vin, stock, location, year, make, model, trim, 
                       exterior_color, price, vehicle_type, import_timestamp, data_source, scrape_count, first_scraped
                FROM ranked_vehicles 
                WHERE rn = 1
            """
        else:  # both - deduplicated showing most recent from either source
            base_query = """
                WITH all_vehicles AS (
                    SELECT 
                        r.vin, r.stock, r.location, r.year, r.make, r.model,
                        r.trim, r.ext_color as exterior_color, r.price, r.type as vehicle_type,
                        r.import_timestamp, 'raw' as data_source, r.id
                    FROM raw_vehicle_data r
                    UNION ALL
                    SELECT 
                        n.vin, n.stock, n.location, n.year, n.make, n.model,
                        n.trim, '' as exterior_color, n.price, n.vehicle_condition as vehicle_type,
                        r.import_timestamp, 'normalized' as data_source, n.id
                    FROM normalized_vehicle_data n
                    JOIN raw_vehicle_data r ON n.raw_data_id = r.id
                ),
                ranked_vehicles AS (
                    SELECT 
                        vin, stock, location, year, make, model, trim, 
                        exterior_color, price, vehicle_type, import_timestamp, data_source,
                        COUNT(*) OVER (PARTITION BY vin) as scrape_count,
                        MIN(import_timestamp) OVER (PARTITION BY vin) as first_scraped,
                        ROW_NUMBER() OVER (PARTITION BY vin ORDER BY import_timestamp DESC, id DESC) as rn
                    FROM all_vehicles
                )
                SELECT vin, stock, location, year, make, model, trim, 
                       exterior_color, price, vehicle_type, import_timestamp, data_source, scrape_count, first_scraped
                FROM ranked_vehicles
                WHERE rn = 1
            """
        
        # Build WHERE conditions
        conditions = []
        params = []
        
        # Text search
        if query:
            search_condition = """
                (LOWER(vin) LIKE LOWER(%s) OR 
                 LOWER(stock) LIKE LOWER(%s) OR
                 LOWER(location) LIKE LOWER(%s) OR
                 LOWER(make) LIKE LOWER(%s) OR
                 LOWER(model) LIKE LOWER(%s) OR
                 LOWER(trim) LIKE LOWER(%s))
            """
            search_param = f'%{query}%'
            conditions.append(search_condition)
            params.extend([search_param] * 6)
        
        # Date filtering
        if filter_by == 'date' and start_date:
            conditions.append("DATE(import_timestamp) >= %s")
            params.append(start_date)
        if filter_by == 'date' and end_date:
            conditions.append("DATE(import_timestamp) <= %s")
            params.append(end_date)
        
        # Dealer filtering
        if filter_by == 'dealer' and dealer_names:
            dealer_placeholders = ','.join(['%s'] * len(dealer_names))
            conditions.append(f"location IN ({dealer_placeholders})")
            params.extend(dealer_names)
        
        # Header filters
        header_filters = {
            'header_filter_location': 'location',
            'header_filter_year': 'year', 
            'header_filter_make': 'make',
            'header_filter_model': 'model',
            'header_filter_vehicle_type': 'vehicle_type' if data_type == 'raw' else 'vehicle_condition',
            'header_filter_import_date': None  # Special handling for date
        }
        
        for param_name, db_field in header_filters.items():
            filter_value = request.args.get(param_name, '').strip()
            if filter_value:
                if param_name == 'header_filter_import_date':
                    conditions.append("DATE(import_timestamp) = %s")
                    params.append(filter_value)
                elif param_name == 'header_filter_vehicle_type':
                    if data_type == 'raw':
                        conditions.append("vehicle_type = %s")
                    else:
                        conditions.append("vehicle_condition = %s") 
                    params.append(filter_value)
                else:
                    conditions.append(f"{db_field} = %s")
                    params.append(filter_value)
        
        # Add conditions to query
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        # Add ordering
        valid_sort_fields = ['vin', 'year', 'make', 'model', 'price', 'mileage', 'import_timestamp', 'location']
        if sort_by in valid_sort_fields:
            sort_direction = 'ASC' if sort_order.lower() == 'asc' else 'DESC'
            base_query += f" ORDER BY {sort_by} {sort_direction}"
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM ({base_query}) as count_query"
        count_result = db_manager.execute_query(count_query, params)
        total_count = count_result[0]['total'] if count_result else 0
        
        # Add pagination
        base_query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        # Execute main query
        results = db_manager.execute_query(base_query, params)
        
        # Format results
        formatted_results = []
        for row in results:
            formatted_row = dict(row)
            # Format price
            if formatted_row.get('price'):
                formatted_row['price_formatted'] = f"${formatted_row['price']:,.2f}"
            # Format mileage
            if formatted_row.get('mileage'):
                formatted_row['mileage_formatted'] = f"{formatted_row['mileage']:,} mi"
            formatted_results.append(formatted_row)
        
        return jsonify({
            'success': True,
            'data': formatted_results,
            'total_count': total_count,
            'page_info': {
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_count,
                'total_pages': (total_count + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error searching vehicle data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/dealers')
def get_available_dealers():
    """Get list of available dealers for filtering"""
    try:
        dealers = db_manager.execute_query("""
            SELECT DISTINCT location as name
            FROM raw_vehicle_data 
            WHERE location IS NOT NULL 
            ORDER BY location
        """)
        
        dealer_list = [row['name'] for row in dealers]
        return jsonify({'success': True, 'dealers': dealer_list})
        
    except Exception as e:
        logger.error(f"Error getting dealer list: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/date-range')
def get_available_date_range():
    """Get available date range for filtering"""
    try:
        date_range = db_manager.execute_query("""
            SELECT 
                MIN(DATE(import_timestamp)) as min_date,
                MAX(DATE(import_timestamp)) as max_date
            FROM raw_vehicle_data
        """)
        
        if date_range:
            return jsonify({
                'success': True,
                'min_date': str(date_range[0]['min_date']) if date_range[0]['min_date'] else None,
                'max_date': str(date_range[0]['max_date']) if date_range[0]['max_date'] else None
            })
        else:
            return jsonify({'success': True, 'min_date': None, 'max_date': None})
        
    except Exception as e:
        logger.error(f"Error getting date range: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/filter-options')
def get_filter_options():
    """Get dynamic filter options based on current search criteria"""
    try:
        # Get the same filters that would be applied to the search
        query = request.args.get('query', '').strip()
        
        # Get existing filter values to exclude from counts
        existing_filters = {
            'location': request.args.get('filter_location', ''),
            'year': request.args.get('filter_year', ''),
            'make': request.args.get('filter_make', ''),
            'model': request.args.get('filter_model', ''),
            'vehicle_type': request.args.get('filter_vehicle_type', ''),
            'import_date': request.args.get('filter_import_date', '')
        }
        
        # Build WHERE conditions
        conditions = []
        params = []
        
        # Text search
        if query:
            search_condition = """
                (LOWER(r.vin) LIKE LOWER(%s) OR 
                 LOWER(r.stock) LIKE LOWER(%s) OR
                 LOWER(r.location) LIKE LOWER(%s) OR
                 LOWER(r.make) LIKE LOWER(%s) OR
                 LOWER(r.model) LIKE LOWER(%s) OR
                 LOWER(r.trim) LIKE LOWER(%s))
            """
            search_param = f'%{query}%'
            conditions.append(search_condition)
            params.extend([search_param] * 6)
        
        # Apply existing filters (except the one we're getting options for)
        for field, value in existing_filters.items():
            if value:
                if field == 'import_date':
                    conditions.append("DATE(r.import_timestamp) = %s")
                else:
                    db_field = field if field != 'vehicle_type' else 'type'
                    conditions.append(f"r.{db_field} = %s")
                params.append(value)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Get distinct values for each filterable field
        filter_queries = {
            'locations': f"""
                SELECT DISTINCT r.location as value, COUNT(*) as count
                FROM raw_vehicle_data r
                WHERE {where_clause} AND r.location IS NOT NULL
                GROUP BY r.location 
                ORDER BY count DESC, r.location
            """,
            'years': f"""
                SELECT DISTINCT r.year as value, COUNT(*) as count
                FROM raw_vehicle_data r
                WHERE {where_clause} AND r.year IS NOT NULL
                GROUP BY r.year 
                ORDER BY r.year DESC
            """,
            'makes': f"""
                SELECT DISTINCT r.make as value, COUNT(*) as count
                FROM raw_vehicle_data r
                WHERE {where_clause} AND r.make IS NOT NULL
                GROUP BY r.make 
                ORDER BY count DESC, r.make
            """,
            'models': f"""
                SELECT DISTINCT r.model as value, COUNT(*) as count
                FROM raw_vehicle_data r
                WHERE {where_clause} AND r.model IS NOT NULL
                GROUP BY r.model 
                ORDER BY count DESC, r.model
            """,
            'vehicle_types': f"""
                SELECT DISTINCT r.type as value, COUNT(*) as count
                FROM raw_vehicle_data r
                WHERE {where_clause} AND r.type IS NOT NULL
                GROUP BY r.type 
                ORDER BY count DESC, r.type
            """,
            'import_dates': f"""
                SELECT DISTINCT DATE(r.import_timestamp) as value, COUNT(*) as count
                FROM raw_vehicle_data r
                WHERE {where_clause} AND r.import_timestamp IS NOT NULL
                GROUP BY DATE(r.import_timestamp) 
                ORDER BY DATE(r.import_timestamp) DESC
            """
        }
        
        result = {}
        for filter_name, query_sql in filter_queries.items():
            try:
                filter_data = db_manager.execute_query(query_sql, params)
                result[filter_name] = [
                    {
                        'value': str(row['value']),
                        'count': row['count'],
                        'label': f"{row['value']} ({row['count']})"
                    }
                    for row in filter_data[:50]  # Limit to 50 options
                ]
            except Exception as e:
                logger.error(f"Error getting {filter_name}: {e}")
                result[filter_name] = []
        
        return jsonify({
            'success': True,
            'filters': result
        })
        
    except Exception as e:
        logger.error(f"Error getting filter options: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/vin-history')
def get_vin_history():
    """Get VIN history data for the viewer - READ ONLY"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 100))
        search_query = request.args.get('query', '').strip()
        dealership_filter = request.args.get('dealership', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Build query conditions
        conditions = []
        params = []
        
        # Search filter
        if search_query:
            conditions.append("(LOWER(vh.vin) LIKE LOWER(%s) OR LOWER(vh.dealership_name) LIKE LOWER(%s))")
            search_param = f'%{search_query}%'
            params.extend([search_param, search_param])
        
        # Dealership filter
        if dealership_filter:
            conditions.append("vh.dealership_name = %s")
            params.append(dealership_filter)
        
        # Date range filters
        if date_from:
            conditions.append("vh.order_date >= %s")
            params.append(date_from)
        
        if date_to:
            conditions.append("vh.order_date <= %s")
            params.append(date_to)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM vin_history vh WHERE {where_clause}"
        total_result = db_manager.execute_query(count_query, params)
        total_count = total_result[0]['total'] if total_result else 0
        
        # Get VIN history data with vehicle details
        query = f"""
            SELECT 
                vh.id,
                vh.vin,
                vh.dealership_name,
                vh.order_date,
                vh.created_at,
                vh.vehicle_type,
                r.stock,
                r.year,
                r.make,
                r.model,
                r.trim,
                r.status,
                r.price
            FROM vin_history vh
            LEFT JOIN raw_vehicle_data r ON vh.vin = r.vin AND vh.dealership_name = r.location
            WHERE {where_clause}
            ORDER BY vh.order_date DESC, vh.created_at DESC
            LIMIT %s OFFSET %s
        """
        
        # Add pagination params
        params.extend([per_page, offset])
        
        results = db_manager.execute_query(query, params)
        
        # Get summary statistics
        stats_query = """
            SELECT 
                COUNT(DISTINCT vin) as unique_vins,
                COUNT(DISTINCT dealership_name) as unique_dealerships,
                COUNT(*) as total_records,
                MIN(order_date) as earliest_date,
                MAX(order_date) as latest_date
            FROM vin_history
        """
        stats = db_manager.execute_query(stats_query)[0]
        
        # Get dealership list for filter dropdown
        dealership_query = """
            SELECT DISTINCT dealership_name, COUNT(*) as count
            FROM vin_history
            GROUP BY dealership_name
            ORDER BY dealership_name
        """
        dealerships = db_manager.execute_query(dealership_query)
        
        return jsonify({
            'success': True,
            'data': results,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': (total_count + per_page - 1) // per_page
            },
            'statistics': stats,
            'dealerships': dealerships
        })
        
    except Exception as e:
        logger.error(f"Error getting VIN history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/vehicle-history/<vin>')
def get_vehicle_history(vin):
    """Get simple scrape history for a specific VIN - all raw scrapes in chronological order"""
    try:
        if not vin:
            return jsonify({'error': 'VIN is required'}), 400
        
        # Get all scrape history for this VIN - simple list, no complex processing
        scrape_query = """
            SELECT 
                r.id,
                r.import_timestamp,
                r.location as dealership,
                r.price,
                r.year, r.make, r.model, r.trim,
                r.type as vehicle_type,
                r.ext_color as exterior_color,
                r.stock,
                r.mileage
            FROM raw_vehicle_data r
            WHERE r.vin = %s
            ORDER BY r.import_timestamp DESC
        """
        
        scrape_results = db_manager.execute_query(scrape_query, [vin])
        
        # Format scrapes as simple list
        scrapes = []
        for scrape in scrape_results:
            scrape_data = {
                'id': scrape['id'],
                'date': scrape['import_timestamp'].isoformat() if scrape['import_timestamp'] else None,
                'dealership': scrape['dealership'],
                'price': float(scrape['price']) if scrape['price'] else None,
                'price_formatted': f"${scrape['price']:,.2f}" if scrape['price'] else 'N/A',
                'year': scrape['year'],
                'make': scrape['make'],
                'model': scrape['model'],
                'trim': scrape['trim'],
                'vehicle_type': scrape['vehicle_type'],
                'exterior_color': scrape['exterior_color'],
                'stock': scrape['stock'],
                'mileage': scrape['mileage'],
                'mileage_formatted': f"{scrape['mileage']:,} mi" if scrape['mileage'] else 'N/A'
            }
            scrapes.append(scrape_data)
        
        # Get first and last scrape timestamps
        first_scraped = None
        last_scraped = None
        if scrapes:
            # Since ordered DESC, first result is most recent, last is oldest
            last_scraped = scrapes[0]['date']
            first_scraped = scrapes[-1]['date']
        
        return jsonify({
            'success': True,
            'vin': vin,
            'scrapes': scrapes,
            'total_scrapes': len(scrapes),
            'first_scraped': first_scraped,
            'last_scraped': last_scraped
        })
        
    except Exception as e:
        logger.error(f"Error getting vehicle scrapes for VIN {vin}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/vehicle-single/<vin>')
def get_single_vehicle_data(vin):
    """Get single vehicle data (raw or normalized) for individual row toggle"""
    try:
        if not vin:
            return jsonify({'error': 'VIN is required'}), 400
        
        data_type = request.args.get('data_type', 'raw')  # Default to raw
        
        if data_type == 'raw':
            query = """
                SELECT 
                    r.vin, r.stock, r.location, r.year, r.make, r.model,
                    r.trim, r.ext_color as exterior_color, r.price, r.type as vehicle_type,
                    r.import_timestamp, 'raw' as data_source,
                    COUNT(*) OVER (PARTITION BY r.vin) as scrape_count
                FROM raw_vehicle_data r
                WHERE r.vin = %s
                ORDER BY r.import_timestamp DESC
                LIMIT 1
            """
        else:  # normalized
            query = """
                SELECT 
                    n.vin, n.stock, n.location, n.year, n.make, n.model,
                    n.trim, '' as exterior_color, n.price, n.vehicle_condition as vehicle_type,
                    r.import_timestamp, 'normalized' as data_source,
                    1 as scrape_count
                FROM normalized_vehicle_data n
                JOIN raw_vehicle_data r ON n.raw_data_id = r.id
                WHERE n.vin = %s
                ORDER BY r.import_timestamp DESC
                LIMIT 1
            """
        
        result = db_manager.execute_query(query, [vin])
        
        if not result:
            if data_type == 'normalized':
                return jsonify({'error': 'No normalized data found for this VIN'}), 404
            else:
                return jsonify({'error': 'No data found for this VIN'}), 404
        
        vehicle = dict(result[0])
        
        # Format price
        if vehicle.get('price'):
            vehicle['price_formatted'] = f"${vehicle['price']:,.2f}"
        
        # Format mileage (if available)
        if vehicle.get('mileage'):
            vehicle['mileage_formatted'] = f"{vehicle['mileage']:,} mi"
            
        return jsonify({
            'success': True,
            'vehicle': vehicle,
            'data_type': data_type
        })
        
    except Exception as e:
        logger.error(f"Error getting single vehicle data for VIN {vin}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/export', methods=['POST'])
def export_search_results():
    """Export search results to CSV"""
    try:
        # Get the same parameters as search
        data = request.get_json()
        query = data.get('query', '').strip()
        filter_by = data.get('filter_by', 'all')
        data_type = data.get('data_type', 'both')
        sort_by = data.get('sort_by', 'import_timestamp')
        sort_order = data.get('sort_order', 'desc')
        
        # Use the same query logic as search but without pagination
        # This is a simplified version - in production you'd want to refactor the common logic
        
        if data_type == 'raw':
            base_query = """
                SELECT 
                    r.vin, r.stock_number, r.dealer_name as location, r.year, r.make, r.model,
                    r.trim, r.exterior_color, r.mileage, r.price, r.vehicle_type,
                    r.import_timestamp
                FROM raw_vehicle_data r
                WHERE 1=1
            """
        elif data_type == 'normalized':
            base_query = """
                SELECT 
                    n.vin, n.stock_number, r.dealer_name as location, n.year, n.make, n.model,
                    n.trim, n.exterior_color, n.mileage, n.price, n.vehicle_type,
                    r.import_timestamp
                FROM normalized_vehicle_data n
                JOIN raw_vehicle_data r ON n.raw_data_id = r.id
                WHERE 1=1
            """
        else:  # both
            base_query = """
                SELECT vin, stock_number, location, year, make, model, trim, 
                       exterior_color, mileage, price, vehicle_type, import_timestamp
                FROM (
                    SELECT 
                        r.vin, r.stock_number, r.dealer_name as location, r.year, r.make, r.model,
                        r.trim, r.exterior_color, r.mileage, r.price, r.vehicle_type,
                        r.import_timestamp
                    FROM raw_vehicle_data r
                    UNION ALL
                    SELECT 
                        n.vin, n.stock_number, r.dealer_name as location, n.year, n.make, n.model,
                        n.trim, n.exterior_color, n.mileage, n.price, n.vehicle_type,
                        r.import_timestamp
                    FROM normalized_vehicle_data n
                    JOIN raw_vehicle_data r ON n.raw_data_id = r.id
                ) combined_data
                WHERE 1=1
            """
        
        # Add text search if provided
        params = []
        if query:
            search_condition = """
                AND (LOWER(vin) LIKE LOWER(%s) OR 
                     LOWER(stock_number) LIKE LOWER(%s) OR
                     LOWER(location) LIKE LOWER(%s) OR
                     LOWER(make) LIKE LOWER(%s) OR
                     LOWER(model) LIKE LOWER(%s) OR
                     LOWER(trim) LIKE LOWER(%s))
            """
            search_param = f'%{query}%'
            base_query += search_condition
            params.extend([search_param] * 6)
        
        # Add ordering
        valid_sort_fields = ['vin', 'year', 'make', 'model', 'price', 'mileage', 'import_timestamp', 'location']
        if sort_by in valid_sort_fields:
            sort_direction = 'ASC' if sort_order.lower() == 'asc' else 'DESC'
            base_query += f" ORDER BY {sort_by} {sort_direction}"
        
        # Execute query
        results = db_manager.execute_query(base_query, params)
        
        # Generate CSV content
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'vin', 'stock_number', 'location', 'year', 'make', 'model', 
            'trim', 'exterior_color', 'mileage', 'price', 'vehicle_type', 'import_timestamp'
        ])
        
        writer.writeheader()
        for row in results:
            writer.writerow(dict(row))
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"vehicle_search_export_{timestamp}.csv"
        
        # Save to file
        export_path = Path('exports') / filename
        with open(export_path, 'w', newline='', encoding='utf-8') as f:
            f.write(output.getvalue())
        
        return jsonify({
            'success': True, 
            'filename': filename,
            'row_count': len(results),
            'download_url': f'/api/download/{filename}'
        })
        
    except Exception as e:
        logger.error(f"Error exporting search results: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<filename>')
def download_export_file(filename):
    """Download exported file"""
    try:
        export_path = Path('exports') / filename
        if export_path.exists():
            return send_file(export_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
            
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# DEALERSHIP SETTINGS API ENDPOINTS
# =============================================================================

@app.route('/api/dealership-settings')
def get_dealership_settings():
    """Get all dealership settings"""
    try:
        query = """
            SELECT 
                dc.id,
                dc.name,
                dc.filtering_rules,
                dc.output_rules,
                dc.is_active,
                COUNT(DISTINCT rd.vin) as vehicle_count,
                MAX(rd.import_date) as last_import
            FROM dealership_configs dc
            LEFT JOIN raw_vehicle_data rd ON dc.name = rd.location
            GROUP BY dc.id, dc.name, dc.filtering_rules, dc.output_rules, dc.is_active
            ORDER BY dc.name
        """
        
        dealerships = db_manager.execute_query(query)
        
        # Process filtering rules for each dealership
        settings = []
        for dealership in dealerships:
            filtering_rules = dealership.get('filtering_rules', {})
            if isinstance(filtering_rules, str):
                try:
                    filtering_rules = json.loads(filtering_rules)
                except:
                    filtering_rules = {}
            
            # Extract vehicle types
            vehicle_types = filtering_rules.get('vehicle_types', ['new', 'used', 'certified'])
            
            settings.append({
                'id': dealership['id'],
                'name': dealership['name'],
                'active': dealership.get('is_active', True),
                'vehicle_count': dealership.get('vehicle_count', 0),
                'last_import': dealership.get('last_import'),
                'vehicle_types': vehicle_types,
                'filtering_rules': filtering_rules,
                'output_rules': dealership.get('output_rules', {})
            })
        
        return jsonify({
            'success': True,
            'dealerships': settings,
            'total': len(settings)
        })
        
    except Exception as e:
        logger.error(f"Error getting dealership settings: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dealership-settings/<int:dealership_id>', methods=['PUT'])
def update_dealership_settings(dealership_id):
    """Update settings for a specific dealership"""
    try:
        data = request.get_json()
        
        # Get current dealership config
        current = db_manager.execute_query(
            "SELECT * FROM dealership_configs WHERE id = %s",
            (dealership_id,)
        )
        
        if not current:
            return jsonify({'error': 'Dealership not found'}), 404
        
        # Update filtering rules
        filtering_rules = current[0].get('filtering_rules', {})
        if isinstance(filtering_rules, str):
            try:
                filtering_rules = json.loads(filtering_rules)
            except:
                filtering_rules = {}
        
        # Update vehicle types if provided
        if 'vehicle_types' in data:
            filtering_rules['vehicle_types'] = data['vehicle_types']
        
        # Update other filtering rules if provided
        if 'min_year' in data:
            filtering_rules['min_year'] = data['min_year']
        if 'min_price' in data:
            filtering_rules['min_price'] = data['min_price']
        if 'max_price' in data:
            filtering_rules['max_price'] = data['max_price']
        
        # Update the database
        update_query = """
            UPDATE dealership_configs 
            SET filtering_rules = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        db_manager.execute_query(
            update_query,
            (json.dumps(filtering_rules), dealership_id)
        )
        
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully',
            'dealership_id': dealership_id
        })
        
    except Exception as e:
        logger.error(f"Error updating dealership settings: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dealership-settings/bulk', methods=['PUT'])
def bulk_update_dealership_settings():
    """Bulk update settings for multiple dealerships"""
    try:
        data = request.get_json()
        vehicle_types = data.get('vehicle_types', [])
        dealership_ids = data.get('dealership_ids', [])
        
        if not vehicle_types:
            return jsonify({'error': 'Vehicle types required'}), 400
        
        # If no specific dealerships provided, update all
        if not dealership_ids:
            dealership_query = "SELECT id FROM dealership_configs"
            result = db_manager.execute_query(dealership_query)
            dealership_ids = [row['id'] for row in result]
        
        updated_count = 0
        
        for dealership_id in dealership_ids:
            # Get current config
            current = db_manager.execute_query(
                "SELECT filtering_rules FROM dealership_configs WHERE id = %s",
                (dealership_id,)
            )
            
            if current:
                filtering_rules = current[0].get('filtering_rules', {})
                if isinstance(filtering_rules, str):
                    try:
                        filtering_rules = json.loads(filtering_rules)
                    except:
                        filtering_rules = {}
                
                # Update vehicle types
                filtering_rules['vehicle_types'] = vehicle_types
                
                # Update the database
                db_manager.execute_query(
                    "UPDATE dealership_configs SET filtering_rules = %s WHERE id = %s",
                    (json.dumps(filtering_rules), dealership_id)
                )
                
                updated_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Updated {updated_count} dealerships',
            'updated_count': updated_count
        })
        
    except Exception as e:
        logger.error(f"Error bulk updating dealership settings: {e}")
        return jsonify({'error': str(e)}), 500

def _parse_price(price_value):
    """Parse price value from CSV, handling various formats including HTML content"""
    if pd.isna(price_value) or price_value is None:
        return 0.0
    
    price_str = str(price_value).strip()
    
    # Handle empty values
    if not price_str or price_str.lower() in ['', 'nan', 'none', 'null']:
        return 0.0
    
    # Handle "call for price" variations
    if 'call' in price_str.lower() or 'contact' in price_str.lower():
        return 0.0
    
    # Remove HTML tags
    import re
    price_str = re.sub(r'<[^>]+>', '', price_str)
    
    # Remove common currency symbols and formatting
    price_str = re.sub(r'[,$\s]', '', price_str)
    
    # Extract numeric value
    numeric_match = re.search(r'[\d,]+\.?\d*', price_str)
    if numeric_match:
        try:
            return float(numeric_match.group().replace(',', ''))
        except ValueError:
            return 0.0
    
    return 0.0

@app.route('/api/csv-import/process', methods=['POST'])
def process_csv_import():
    """Process CSV import for order processing validation testing"""
    try:
        # Get form data
        dealership_name = request.form.get('dealership')
        order_type = request.form.get('order_type', 'cao')  # cao or list
        keep_data = request.form.get('keep_data', 'false').lower() == 'true'
        
        if 'csv_file' not in request.files:
            return jsonify({'error': 'No CSV file provided'}), 400
        
        csv_file = request.files['csv_file']
        if csv_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not dealership_name:
            return jsonify({'error': 'Dealership selection required'}), 400
        
        # Read and parse CSV with validation
        try:
            import pandas as pd
            import io
            
            # Read CSV content
            csv_content = csv_file.read().decode('utf-8')
            df = pd.read_csv(io.StringIO(csv_content))
            
            logger.info(f"CSV loaded: {len(df)} rows, columns: {list(df.columns)}")
            
            # Debug: Check for URL-related columns
            url_columns = [col for col in df.columns if 'url' in col.lower() or 'link' in col.lower()]
            logger.info(f"Found URL-related columns: {url_columns}")
            if url_columns:
                # Show sample URL values from first few rows
                for col in url_columns[:3]:  # Check up to 3 URL columns
                    sample_urls = df[col].dropna().head(3).tolist()
                    logger.info(f"Sample values from '{col}': {sample_urls}")
            
            # Debug and validate VIN columns with broader search
            potential_vin_columns = ['VIN', 'Vin', 'vin', 'Vehicle_VIN', 'VehicleVIN', 'Vehicle Identification Number']
            vin_column = None
            
            # First, check if any column contains VIN-like data (17 characters)
            logger.info("Checking for VIN columns...")
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ['vin']):
                    sample_values = df[col].dropna().head(3).tolist()
                    logger.info(f"Potential VIN column '{col}': {sample_values}")
                    
                    # Check if values look like actual VINs (17 characters)
                    if sample_values:
                        sample_str = str(sample_values[0]).strip()
                        if len(sample_str) == 17 and sample_str.isalnum():
                            vin_column = col
                            logger.info(f"Selected VIN column: {vin_column}")
                            break
            
            # Fallback to exact name match if no 17-char VINs found
            if not vin_column:
                for col in potential_vin_columns:
                    if col in df.columns:
                        vin_column = col
                        logger.info(f"Fallback VIN column: {vin_column}")
                        break
            
            if not vin_column:
                return jsonify({'error': f'CSV must contain a VIN column. Found columns: {list(df.columns)}'}), 400
            
            # Get dealership settings for filtering
            dealership_settings = db_manager.execute_query("""
                SELECT filtering_rules FROM dealership_configs 
                WHERE name = %s AND is_active = true
            """, (dealership_name,))
            
            allowed_types = ['new', 'used', 'certified']  # Default if no settings found
            if dealership_settings and dealership_settings[0]['filtering_rules']:
                filtering_rules = dealership_settings[0]['filtering_rules']
                # Handle both JSON string and dict formats
                if isinstance(filtering_rules, str):
                    import json
                    filtering_rules = json.loads(filtering_rules)
                
                if isinstance(filtering_rules, dict) and 'vehicle_types' in filtering_rules:
                    allowed_types = filtering_rules['vehicle_types']
            
            logger.info(f"Dealership {dealership_name} processes: {allowed_types}")
            
        except Exception as e:
            return jsonify({'error': f'Failed to parse CSV: {str(e)}'}), 400
        
        # Convert DataFrame to list of dictionaries with validation and filtering
        vehicles = []
        skipped_vehicles = 0
        
        for _, row in df.iterrows():
            # Map CSV columns to our standard format with detected VIN column
            vehicle = {
                'vin': str(row.get(vin_column, '')).strip(),
                'stock': str(row.get('Stock', row.get('stock_number', row.get('Stock Number', '')))).strip(),
                'year': int(row.get('Year', row.get('year', row.get('Model Year', 0)))) if pd.notna(row.get('Year', row.get('year', row.get('Model Year', 0)))) else 0,
                'make': str(row.get('Make', row.get('make', row.get('Brand', '')))).strip(),
                'model': str(row.get('Model', row.get('model', ''))).strip(),
                'trim': str(row.get('Trim', row.get('trim', row.get('Series', '')))).strip(),
                'type': str(row.get('Type', row.get('vehicle_type', row.get('Vehicle Type', row.get('Status', 'Unknown'))))).lower().strip(),
                'price': self._parse_price(row.get('Price', row.get('price', row.get('MSRP', row.get('List Price', 0))))),
                'ext_color': str(row.get('Ext Color', row.get('exterior_color', row.get('External Color', '')))).strip(),
                'vehicle_url': str(row.get('Vehicle URL', row.get('vehicle_url', row.get('URL', row.get('Link', row.get('VehicleURL', row.get('Vehicle Link', row.get('Detail URL', row.get('Details URL', row.get('Vehicle Detail URL', '')))))))))).strip(),
                'location': dealership_name,
                'import_timestamp': datetime.now(),
                'import_date': datetime.now().date()
            }
            
            # Validate and filter vehicle
            if not vehicle['vin'] or len(vehicle['vin']) < 10:
                skipped_vehicles += 1
                continue
            
            # Apply dealership filtering
            vehicle_type = vehicle['type'].lower()
            type_matches = False
            
            for allowed_type in allowed_types:
                if allowed_type.lower() in vehicle_type or (allowed_type.lower() == 'certified' and ('cpo' in vehicle_type or 'certified' in vehicle_type)):
                    type_matches = True
                    break
            
            if not type_matches:
                skipped_vehicles += 1
                logger.debug(f"Skipping vehicle {vehicle['vin']} - type '{vehicle['type']}' not in allowed types {allowed_types}")
                continue
            
            vehicles.append(vehicle)
        
        if not vehicles:
            return jsonify({'error': f'No valid vehicles found in CSV after filtering. Skipped {skipped_vehicles} vehicles.'}), 400
        
        logger.info(f"Processed {len(vehicles)} vehicles from CSV, skipped {skipped_vehicles}")
        
        # Import CSV data to database for processing
        import_timestamp = datetime.now()
        imported_vins = []
        
        # Insert vehicles into database
        for vehicle in vehicles:
            try:
                # Use the exact import timestamp for all vehicles for easy cleanup
                vehicle['import_timestamp'] = import_timestamp
                
                db_manager.execute_query("""
                    INSERT INTO raw_vehicle_data 
                    (vin, stock, year, make, model, trim, type, price, ext_color, vehicle_url, location, import_timestamp, import_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (vin, location) DO UPDATE SET
                        stock = EXCLUDED.stock,
                        year = EXCLUDED.year,
                        make = EXCLUDED.make,
                        model = EXCLUDED.model,
                        trim = EXCLUDED.trim,
                        type = EXCLUDED.type,
                        price = EXCLUDED.price,
                        ext_color = EXCLUDED.ext_color,
                        vehicle_url = EXCLUDED.vehicle_url,
                        import_timestamp = EXCLUDED.import_timestamp,
                        import_date = EXCLUDED.import_date
                """, (
                    vehicle['vin'], vehicle['stock'], vehicle['year'], vehicle['make'], 
                    vehicle['model'], vehicle['trim'], vehicle['type'], vehicle['price'],
                    vehicle['ext_color'], vehicle['vehicle_url'], vehicle['location'],
                    vehicle['import_timestamp'], vehicle['import_date']
                ))
                imported_vins.append(vehicle['vin'])
            except Exception as e:
                logger.error(f"Failed to insert vehicle {vehicle['vin']}: {e}")
        
        logger.info(f"Successfully imported {len(imported_vins)} vehicles to database")
        
        try:
            # Process using existing order processing logic
            if order_type == 'cao':
                # CAO processing - compare against VIN history
                logger.info(f"Processing CAO order for {dealership_name}")
                result = order_processor.process_cao_order(dealership_name, 'shortcut_pack')
            else:
                # LIST processing - process specific VIN list
                logger.info(f"Processing LIST order for {dealership_name} with {len(imported_vins)} VINs")
                result = order_processor.process_list_order(dealership_name, imported_vins, 'shortcut_pack')
            
            # Add CSV-specific information to result
            result.update({
                'csv_vehicles_imported': len(vehicles),
                'csv_vehicles_skipped': skipped_vehicles,
                'csv_filtering_applied': allowed_types,
                'data_kept_for_wizard': keep_data,
                'import_timestamp': import_timestamp.isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error during order processing: {e}")
            result = {
                'success': False,
                'error': f'Order processing failed: {str(e)}',
                'csv_vehicles_imported': len(vehicles),
                'csv_vehicles_skipped': skipped_vehicles
            }
        
        finally:
            # Clean up CSV import data unless user wants to keep it for wizard testing
            if not keep_data:
                logger.info(f"Cleaning up CSV import data for timestamp {import_timestamp}")
                cleanup_count = db_manager.execute_query("""
                    DELETE FROM raw_vehicle_data 
                    WHERE import_timestamp = %s AND location = %s
                """, (import_timestamp, dealership_name))
                logger.info(f"Cleaned up {cleanup_count} imported records")
            else:
                logger.info(f"Keeping CSV import data for Order Processing Wizard testing - timestamp: {import_timestamp}")
                # Mark the data with a special comment for later identification
                db_manager.execute_query("""
                    UPDATE raw_vehicle_data 
                    SET import_source = 'CSV_TEST_IMPORT'
                    WHERE import_timestamp = %s AND location = %s
                """, (import_timestamp, dealership_name))
        
        # Add CSV import info to the result
        result['csv_import_info'] = {
            'filename': csv_file.filename,
            'total_rows': len(vehicles),
            'order_type': order_type,
            'dealership': dealership_name,
            'import_timestamp': datetime.now().isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing CSV import: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# =============================================================================
# CSV DATA EDITOR API ENDPOINTS
# =============================================================================

@app.route('/api/csv/get-data/<filename>')
def get_csv_data(filename):
    """Get CSV data for editing in the data editor"""
    try:
        # Security check - only allow CSV files from orders directory
        if not filename.endswith('.csv'):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Find the file in orders directory (check both locations)
        web_gui_orders_dir = Path(__file__).parent / "orders"
        scripts_orders_dir = Path(__file__).parent.parent / "scripts" / "orders"
        
        csv_file = None
        for orders_dir in [web_gui_orders_dir, scripts_orders_dir]:
            for root, dirs, files in os.walk(orders_dir):
                if filename in files:
                    csv_file = Path(root) / filename
                    break
            if csv_file:
                break
        
        if not csv_file or not csv_file.exists():
            return jsonify({'error': 'CSV file not found'}), 404
        
        # Read and parse CSV data
        import csv
        csv_data = {
            'headers': [],
            'rows': []
        }
        
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            
            # Read headers
            csv_data['headers'] = next(reader, [])
            
            # Read data rows
            for row in reader:
                csv_data['rows'].append(row)
        
        return jsonify(csv_data)
        
    except Exception as e:
        logger.error(f"Error getting CSV data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/csv/save-data', methods=['POST'])
def save_csv_data():
    """Save edited CSV data back to file"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        csv_data = data.get('data')
        
        if not filename or not csv_data:
            return jsonify({'error': 'Missing filename or data'}), 400
        
        # Security check
        if not filename.endswith('.csv'):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Find the file in orders directory
        orders_dir = Path(__file__).parent.parent / "scripts" / "orders"
        
        csv_file = None
        for root, dirs, files in os.walk(orders_dir):
            if filename in files:
                csv_file = Path(root) / filename
                break
        
        if not csv_file:
            return jsonify({'error': 'CSV file not found'}), 404
        
        # Create backup
        backup_file = csv_file.with_suffix('.csv.backup')
        if csv_file.exists():
            import shutil
            shutil.copy2(csv_file, backup_file)
        
        # Write updated data
        import csv
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write headers
            if csv_data.get('headers'):
                writer.writerow(csv_data['headers'])
            
            # Write data rows
            for row in csv_data.get('rows', []):
                writer.writerow(row)
        
        logger.info(f"CSV data saved successfully: {filename}")
        return jsonify({'success': True, 'message': 'Data saved successfully'})
        
    except Exception as e:
        logger.error(f"Error saving CSV data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/qr/regenerate', methods=['POST'])
def regenerate_qr_codes():
    """Regenerate QR codes after CSV data changes"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'Missing filename'}), 400
        
        # Extract dealership name from filename
        # Format: dealership_template_timestamp.csv
        dealership_name = filename.split('_')[0].replace('_', ' ')
        
        # Use the order processor to regenerate QR codes
        result = order_processor.regenerate_qr_codes_for_csv(filename)
        
        if result.get('success'):
            return jsonify({
                'success': True, 
                'message': f"Regenerated {result.get('qr_codes_generated', 0)} QR codes"
            })
        else:
            return jsonify({'error': result.get('error', 'QR regeneration failed')}), 500
            
    except Exception as e:
        logger.error(f"Error regenerating QR codes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/qr/regenerate-with-urls', methods=['POST'])
def regenerate_qr_codes_with_urls():
    """Regenerate QR codes with custom URLs for each vehicle"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        vehicle_urls = data.get('vehicle_urls', [])
        
        if not filename:
            return jsonify({'error': 'Missing filename'}), 400
        
        if not vehicle_urls:
            return jsonify({'error': 'Missing vehicle URL data'}), 400
        
        # Use the order processor to regenerate QR codes with custom URLs
        result = order_processor.regenerate_qr_codes_with_urls(filename, vehicle_urls)
        
        if result.get('success'):
            return jsonify({
                'success': True, 
                'message': f"Regenerated {result.get('qr_codes_generated', 0)} QR codes with custom URLs",
                'qr_codes_generated': result.get('qr_codes_generated', 0)
            })
        else:
            return jsonify({'error': result.get('error', 'QR regeneration failed')}), 500
            
    except Exception as e:
        logger.error(f"Error regenerating QR codes with URLs: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# REAL-TIME SCRAPER MANAGEMENT ENDPOINTS
# =============================================================================

def scraper_output_callback(output_msg):
    """Callback function to broadcast scraper output via WebSocket"""
    try:
        socketio.emit('scraper_output', output_msg)
    except Exception as e:
        logger.error(f"Error broadcasting scraper output: {e}")

# Scraper18 controller is initialized above and handles its own Socket.IO emissions

@app.route('/api/scrapers/start', methods=['POST'])
def start_scraper():
    """Start scraping for a specific dealership"""
    try:
        data = request.get_json()
        # Support both singular and plural formats for compatibility
        dealership_names = data.get('dealership_names', [])
        dealership_name = data.get('dealership_name')
        
        # If plural format is used, take the first dealership
        if dealership_names and len(dealership_names) > 0:
            dealership_name = dealership_names[0]
        
        if not dealership_name:
            return jsonify({'success': False, 'error': 'Dealership name required'}), 400
            
        if DEMO_MODE or scraper18_controller is None:
            # Simulate demo scraper output for testing
            def simulate_demo_scraper():
                import time
                socketio.emit('scraper_output', {
                    'message': f'🔄 DEMO: Starting scraper for {dealership_name}',
                    'status': 'starting',
                    'dealership': dealership_name
                })
                
                time.sleep(2)
                socketio.emit('scraper_output', {
                    'message': f'📊 DEMO: Processing pages for {dealership_name}',
                    'status': 'processing',
                    'progress': 25,
                    'vehicles_processed': 15,
                    'dealership': dealership_name
                })
                
                time.sleep(3)
                socketio.emit('scraper_output', {
                    'message': f'🏁 DEMO: Completed scraper for {dealership_name}',
                    'status': 'completed',
                    'progress': 100,
                    'vehicles_processed': 45,
                    'dealership': dealership_name
                })
            
            # Run demo in background thread
            demo_thread = threading.Thread(target=simulate_demo_scraper, daemon=True)
            demo_thread.start()
            
            return jsonify({
                'success': True,
                'message': f'DEMO: Started scraper for {dealership_name}',
                'demo_mode': True
            })
        
        # Start scraper in background thread
        def run_scraper():
            try:
                result = scraper18_controller.run_single_scraper(dealership_name, force_run=True)
                logger.info(f"Scraper result for {dealership_name}: {result}")
            except Exception as e:
                logger.error(f"Error running scraper for {dealership_name}: {e}")
        
        thread = threading.Thread(target=run_scraper, daemon=True)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Started scraper for {dealership_name}',
            'dealership': dealership_name
        })
            
    except Exception as e:
        logger.error(f"Error starting scraper: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test-websocket', methods=['POST'])
def test_websocket():
    """Test WebSocket connection by sending a test message"""
    try:
        test_message = {
            'message': '🧪 WebSocket test message',
            'status': 'testing',
            'timestamp': datetime.now().isoformat()
        }
        socketio.emit('scraper_output', test_message)
        logger.info("Test WebSocket message sent")
        return jsonify({'success': True, 'message': 'Test message sent via WebSocket'})
    except Exception as e:
        logger.error(f"Error sending test WebSocket message: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scrapers/stop', methods=['POST'])
def stop_scraper():
    """Stop scraping for a specific dealership"""
    try:
        data = request.get_json()
        dealership_name = data.get('dealership_name')
        
        if not dealership_name:
            return jsonify({'success': False, 'error': 'Dealership name required'}), 400
            
        if DEMO_MODE or scraper18_controller is None:
            return jsonify({
                'success': True,
                'message': f'DEMO: Stopped scraper for {dealership_name}',
                'demo_mode': True
            })
        
        # Note: Scraper18 system doesn't support stopping individual scrapers
        # They run to completion or fail
        return jsonify({
            'success': True,
            'message': f'Scraper18 system runs to completion - cannot stop {dealership_name}',
            'dealership': dealership_name,
            'info': 'Scraper18 scrapers run to completion and cannot be stopped mid-execution'
        })
            
    except Exception as e:
        logger.error(f"Error stopping scraper: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scrapers/status')
def get_scrapers_status():
    """Get status of all active scrapers"""
    try:
        if DEMO_MODE or scraper18_controller is None:
            return jsonify({
                'success': True,
                'scrapers': {
                    'Columbia Honda': {
                        'status': 'running',
                        'vehicles_scraped': 142,
                        'pages_processed': 6,
                        'current_url': 'https://www.columbiahonda.com/api/vhcliaa/vehicle-pages/cosmos/srp/vehicles/12345/67890?pt=6',
                        'runtime_seconds': 45,
                        'demo_mode': True
                    }
                },
                'demo_mode': True
            })
        
        # Scraper18 system runs scrapers to completion
        # Status is managed through Socket.IO events during execution
        return jsonify({
            'success': True,
            'scrapers': {},  # Active scrapers are tracked via Socket.IO
            'active_count': 0,
            'info': 'Scraper18 system tracks progress via real-time Socket.IO events'
        })
        
    except Exception as e:
        logger.error(f"Error getting scrapers status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scrapers/status/<dealership_name>')
def get_scraper_status(dealership_name):
    """Get status of specific scraper"""
    try:
        if DEMO_MODE or scraper18_controller is None:
            return jsonify({
                'success': True,
                'scraper': {
                    'dealership_name': dealership_name,
                    'status': 'running',
                    'vehicles_scraped': 89,
                    'pages_processed': 4,
                    'current_url': f'https://www.{dealership_name.lower().replace(" ", "")}.com/inventory',
                    'runtime_seconds': 32,
                    'demo_mode': True
                },
                'demo_mode': True
            })
        
        # Scraper18 system doesn't maintain persistent status
        # Status is provided through Socket.IO events
        return jsonify({
            'success': True,
            'scraper': {
                'dealership_name': dealership_name,
                'status': 'idle',
                'info': 'Scraper18 system provides status via Socket.IO events during execution'
            }
        })
            
    except Exception as e:
        logger.error(f"Error getting scraper status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scrapers/output/<dealership_name>')
def get_scraper_output(dealership_name):
    """Get recent output from specific scraper"""
    try:
        max_lines = request.args.get('max_lines', 50, type=int)
        
        if DEMO_MODE or scraper_manager is None:
            # Return demo output
            demo_output = [
                {
                    'timestamp': '14:23:15',
                    'stream': 'stdout',
                    'message': f'Processing URL: https://www.{dealership_name.lower().replace(" ","")}.com/inventory/page/3',
                    'scraper': dealership_name.lower().replace(' ', ''),
                    'dealership': dealership_name,
                    'vehicles_scraped': 67,
                    'pages_processed': 3,
                    'current_url': f'https://www.{dealership_name.lower().replace(" ","")}.com/inventory/page/3'
                },
                {
                    'timestamp': '14:23:16',
                    'stream': 'stdout', 
                    'message': '3 : 24 : 67 : 8',
                    'scraper': dealership_name.lower().replace(' ', ''),
                    'dealership': dealership_name,
                    'vehicles_scraped': 67,
                    'pages_processed': 3,
                    'current_url': f'https://www.{dealership_name.lower().replace(" ","")}.com/inventory/page/3'
                },
                {
                    'timestamp': '14:23:17',
                    'stream': 'stdout',
                    'message': f'3 : 24 : 2022 Honda Civic - 12345 : https://www.{dealership_name.lower().replace(" ","")}.com/inventory/12345',
                    'scraper': dealership_name.lower().replace(' ', ''),
                    'dealership': dealership_name,
                    'vehicles_scraped': 68,
                    'pages_processed': 3,
                    'current_url': f'https://www.{dealership_name.lower().replace(" ","")}.com/inventory/12345'
                }
            ]
            
            return jsonify({
                'success': True,
                'output': demo_output,
                'demo_mode': True
            })
            
        # Scraper18 system outputs directly to Socket.IO during execution
        # No persistent output storage
        return jsonify({
            'success': True,
            'output': [],
            'line_count': 0,
            'info': 'Scraper18 system streams output directly via Socket.IO during execution'
        })
        
    except Exception as e:
        logger.error(f"Error getting scraper output: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'status': 'Connected to scraper console'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('subscribe_scraper')
def handle_subscribe_scraper(data):
    """Subscribe to specific scraper output"""
    dealership_name = data.get('dealership_name')
    logger.info(f"Client {request.sid} subscribed to scraper: {dealership_name}")
    emit('subscribed', {'dealership': dealership_name, 'status': 'Subscribed to scraper output'})

@socketio.on('unsubscribe_scraper')
def handle_unsubscribe_scraper(data):
    """Unsubscribe from specific scraper output"""
    dealership_name = data.get('dealership_name')
    logger.info(f"Client {request.sid} unsubscribed from scraper: {dealership_name}")
    emit('unsubscribed', {'dealership': dealership_name, 'status': 'Unsubscribed from scraper output'})

@app.route('/api/download/qr-folder', methods=['POST'])
def download_qr_folder():
    """Download QR codes folder as a zip file"""
    try:
        import zipfile
        import io
        from pathlib import Path
        
        data = request.get_json()
        folder_path = data.get('folder_path')
        dealership = data.get('dealership', 'dealership')
        
        if not folder_path or not Path(folder_path).exists():
            return jsonify({'error': 'Invalid folder path'}), 400
            
        # Create a zip file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            folder = Path(folder_path)
            for file_path in folder.glob('*.png'):
                zip_file.write(file_path, file_path.name)
                
        zip_buffer.seek(0)
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'{dealership.replace(" ", "_")}_qr_codes.zip'
        )
        
    except Exception as e:
        logger.error(f"Error creating QR zip file: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('exports', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Load production configuration
    try:
        from production_config import get_config
        config = get_config()
        
        # Apply production settings
        if hasattr(config, 'init_app'):
            config.init_app(app)
        
        app.config.from_object(config)
        
        logger.info("Starting MinisForum Database Web GUI (Production Mode)")
        
        # Use production settings
        app.run(
            host=getattr(config, 'HOST', '127.0.0.1'),
            port=getattr(config, 'PORT', 5000),
            debug=getattr(config, 'DEBUG', False),
            threaded=getattr(config, 'THREADED', True)
        )
        
    except ImportError:
        # Fallback to basic configuration
        logger.warning("Production config not found, using basic settings")
        app.run(host='127.0.0.1', port=5000, debug=False)