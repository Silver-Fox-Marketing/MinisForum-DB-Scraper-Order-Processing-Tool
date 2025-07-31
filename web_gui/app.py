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
    
    print("Attempting to import ScraperManager...")
    try:
        from scraper_manager import scraper_manager
        print("OK ScraperManager imported successfully")
    except Exception as e:
        print(f"Warning: ScraperManager import failed: {e}")
        scraper_manager = None
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
socketio = SocketIO(app, cors_allowed_origins="*")

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
        self.real_scraper_integration = RealScraperIntegration(socketio)
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
        
        # Build base query based on data type
        if data_type == 'raw':
            base_query = """
                SELECT 
                    r.vin, r.stock, r.location, r.year, r.make, r.model,
                    r.trim, r.ext_color as exterior_color, r.price, r.type as vehicle_type,
                    r.import_timestamp, 'raw' as data_source
                FROM raw_vehicle_data r
                WHERE 1=1
            """
        elif data_type == 'normalized':
            base_query = """
                SELECT 
                    n.vin, n.stock, n.location, n.year, n.make, n.model,
                    n.trim, '' as exterior_color, n.price, n.vehicle_condition as vehicle_type,
                    r.import_timestamp, 'normalized' as data_source
                FROM normalized_vehicle_data n
                JOIN raw_vehicle_data r ON n.raw_data_id = r.id
                WHERE 1=1
            """
        else:  # both
            base_query = """
                SELECT vin, stock, location, year, make, model, trim, 
                       exterior_color, price, vehicle_type, import_timestamp, data_source
                FROM (
                    SELECT 
                        r.vin, r.stock, r.location, r.year, r.make, r.model,
                        r.trim, r.ext_color as exterior_color, r.price, r.type as vehicle_type,
                        r.import_timestamp, 'raw' as data_source
                    FROM raw_vehicle_data r
                    UNION ALL
                    SELECT 
                        n.vin, n.stock, n.location, n.year, n.make, n.model,
                        n.trim, '' as exterior_color, n.price, n.vehicle_condition as vehicle_type,
                        r.import_timestamp, 'normalized' as data_source
                    FROM normalized_vehicle_data n
                    JOIN raw_vehicle_data r ON n.raw_data_id = r.id
                ) combined_data
                WHERE 1=1
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
        socketio.emit('scraper_output', output_msg, broadcast=True)
    except Exception as e:
        logger.error(f"Error broadcasting scraper output: {e}")

# Add callback to scraper manager
if not DEMO_MODE and scraper_manager is not None:
    scraper_manager.add_output_callback(scraper_output_callback)

@app.route('/api/scrapers/start', methods=['POST'])
def start_scraper():
    """Start scraping for a specific dealership"""
    try:
        data = request.get_json()
        dealership_name = data.get('dealership_name')
        
        if not dealership_name:
            return jsonify({'success': False, 'error': 'Dealership name required'}), 400
            
        if DEMO_MODE or scraper_manager is None:
            return jsonify({
                'success': True,
                'message': f'DEMO: Started scraper for {dealership_name}',
                'demo_mode': True
            })
            
        success = scraper_manager.start_scraper(dealership_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Started scraper for {dealership_name}',
                'dealership': dealership_name
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to start scraper for {dealership_name}'
            }), 400
            
    except Exception as e:
        logger.error(f"Error starting scraper: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scrapers/stop', methods=['POST'])
def stop_scraper():
    """Stop scraping for a specific dealership"""
    try:
        data = request.get_json()
        dealership_name = data.get('dealership_name')
        
        if not dealership_name:
            return jsonify({'success': False, 'error': 'Dealership name required'}), 400
            
        if DEMO_MODE or scraper_manager is None:
            return jsonify({
                'success': True,
                'message': f'DEMO: Stopped scraper for {dealership_name}',
                'demo_mode': True
            })
            
        success = scraper_manager.stop_scraper(dealership_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Stopped scraper for {dealership_name}',
                'dealership': dealership_name
            })
        else:
            return jsonify({
                'success': False,
                'error': f'No active scraper found for {dealership_name}'
            }), 400
            
    except Exception as e:
        logger.error(f"Error stopping scraper: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scrapers/status')
def get_scrapers_status():
    """Get status of all active scrapers"""
    try:
        if DEMO_MODE or scraper_manager is None:
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
            
        # Cleanup completed scrapers first
        scraper_manager.cleanup_completed_scrapers()
        
        status = scraper_manager.get_all_scrapers_status()
        
        return jsonify({
            'success': True,
            'scrapers': status,
            'active_count': len(status)
        })
        
    except Exception as e:
        logger.error(f"Error getting scrapers status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scrapers/status/<dealership_name>')
def get_scraper_status(dealership_name):
    """Get status of specific scraper"""
    try:
        if DEMO_MODE or scraper_manager is None:
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
            
        status = scraper_manager.get_scraper_status(dealership_name)
        
        if status:
            return jsonify({
                'success': True,
                'scraper': status
            })
        else:
            return jsonify({
                'success': False,
                'error': f'No active scraper found for {dealership_name}'
            }), 404
            
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
            
        output = scraper_manager.get_recent_output(dealership_name, max_lines)
        
        return jsonify({
            'success': True,
            'output': output,
            'line_count': len(output)
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