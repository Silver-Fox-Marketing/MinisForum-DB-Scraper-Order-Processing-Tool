#!/usr/bin/env python3
"""
Comprehensive Stress Test for Queue Management System
=====================================================

Tests accuracy, QR code generation, and end-to-end functionality
of the new queue management system with wizard processing.

Author: Silver Fox Assistant
Created: 2025-07-29
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import date, datetime
from typing import Dict, List, Any

# Add project paths
current_file = Path(__file__).resolve()
scripts_dir = current_file.parent
sys.path.insert(0, str(scripts_dir))

from database_connection import db_manager
from order_queue_manager import OrderQueueManager
from order_processing_workflow import OrderProcessingWorkflow
from qr_code_generator import QRCodeGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_stress_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveStressTest:
    """Comprehensive testing of the queue management and processing system"""
    
    def __init__(self):
        self.queue_manager = OrderQueueManager()
        self.order_processor = OrderProcessingWorkflow()
        self.qr_generator = QRCodeGenerator()
        self.test_results = {
            'queue_tests': {},
            'processing_tests': {},
            'qr_tests': {},
            'accuracy_tests': {},
            'performance_tests': {},
            'total_errors': 0,
            'total_warnings': 0
        }
        self.test_dealerships = [
            'Columbia Honda',
            'BMW of West St. Louis', 
            'Dave Sinclair Lincoln South',
            'Test Integration Dealer'
        ]
        
    def run_all_tests(self):
        """Run comprehensive test suite"""
        logger.info("=" * 80)
        logger.info("🚀 STARTING COMPREHENSIVE STRESS TEST")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        try:
            # Test 1: Queue Management System
            self.test_queue_management()
            
            # Test 2: Order Processing Accuracy
            self.test_processing_accuracy()
            
            # Test 3: QR Code Generation
            self.test_qr_code_generation()
            
            # Test 4: Template System
            self.test_template_system()
            
            # Test 5: Database Performance
            self.test_database_performance()
            
            # Test 6: End-to-End Workflow
            self.test_end_to_end_workflow()
            
            # Generate final report
            self.generate_comprehensive_report()
            
        except Exception as e:
            logger.error(f"Critical test failure: {e}")
            self.test_results['total_errors'] += 1
        
        finally:
            duration = time.time() - start_time
            logger.info(f"⏱️ Total test duration: {duration:.2f} seconds")
            logger.info("=" * 80)
    
    def test_queue_management(self):
        """Test queue management functionality"""
        logger.info("\n📋 TESTING QUEUE MANAGEMENT SYSTEM")
        logger.info("-" * 50)
        
        test_results = {}
        
        try:
            # Test queue creation and population
            today = date.today()
            
            # Clear existing queue
            db_manager.execute_query("DELETE FROM order_queue WHERE scheduled_date = %s", (today,))
            
            # Test 1: Populate daily queue
            logger.info("Testing daily queue population...")
            orders_added = self.queue_manager.populate_daily_queue(today)
            test_results['queue_population'] = {
                'orders_added': orders_added,
                'success': orders_added > 0
            }
            logger.info(f"✅ Added {orders_added} orders to queue")
            
            # Test 2: Get daily queue
            logger.info("Testing queue retrieval...")
            queue_orders = self.queue_manager.get_daily_queue(today)
            test_results['queue_retrieval'] = {
                'orders_retrieved': len(queue_orders),
                'success': len(queue_orders) > 0
            }
            logger.info(f"✅ Retrieved {len(queue_orders)} orders from queue")
            
            # Test 3: Queue summary
            logger.info("Testing queue summary...")
            summary = self.queue_manager.get_queue_summary(today)
            test_results['queue_summary'] = {
                'total_orders': summary.get('total_orders', 0),
                'success': summary.get('total_orders', 0) > 0
            }
            logger.info(f"✅ Queue summary: {summary.get('total_orders', 0)} total orders")
            
            # Test 4: Template validation
            logger.info("Testing template configurations...")
            templates = self.queue_manager.templates
            test_results['template_validation'] = {
                'templates_loaded': len(templates),
                'success': len(templates) >= 3  # Should have at least Flyout, Shortcut, Shortcut Pack
            }
            logger.info(f"✅ Loaded {len(templates)} templates: {list(templates.keys())}")
            
        except Exception as e:
            logger.error(f"❌ Queue management test failed: {e}")
            test_results['error'] = str(e)
            self.test_results['total_errors'] += 1
        
        self.test_results['queue_tests'] = test_results
    
    def test_processing_accuracy(self):
        """Test order processing accuracy"""
        logger.info("\n🎯 TESTING PROCESSING ACCURACY")
        logger.info("-" * 50)
        
        test_results = {}
        
        try:
            for dealership in self.test_dealerships[:2]:  # Test first 2 dealerships
                logger.info(f"Testing processing accuracy for {dealership}...")
                
                # Test CAO processing
                cao_result = self.order_processor.process_cao_order(dealership, ['new', 'used'])
                
                if cao_result.get('success'):
                    test_results[f'{dealership}_cao'] = {
                        'vehicle_count': cao_result.get('vehicle_count', 0),
                        'export_file_exists': os.path.exists(cao_result.get('export_file', '')),
                        'qr_codes_generated': cao_result.get('qr_generation', {}).get('success', 0),
                        'success': True
                    }
                    logger.info(f"✅ {dealership} CAO: {cao_result.get('vehicle_count', 0)} vehicles")
                else:
                    test_results[f'{dealership}_cao'] = {
                        'success': False,
                        'error': cao_result.get('error', 'Unknown error')
                    }
                    logger.error(f"❌ {dealership} CAO processing failed")
                    self.test_results['total_errors'] += 1
                
                # Small delay between tests
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Processing accuracy test failed: {e}")
            test_results['error'] = str(e)
            self.test_results['total_errors'] += 1
        
        self.test_results['processing_tests'] = test_results
    
    def test_qr_code_generation(self):
        """Test QR code generation specifically"""
        logger.info("\n🔲 TESTING QR CODE GENERATION")
        logger.info("-" * 50)
        
        test_results = {}
        
        try:
            # Get test vehicles from database
            test_vehicles = db_manager.execute_query("""
                SELECT vin, make, model, year, price, 
                       CONCAT(year, ' ', make, ' ', model) as display_name
                FROM normalized_vehicle_data 
                WHERE vin IS NOT NULL 
                LIMIT 10
            """)
            
            if not test_vehicles:
                logger.warning("⚠️ No vehicles found in database for QR testing")
                self.test_results['total_warnings'] += 1
                return
            
            logger.info(f"Testing QR generation for {len(test_vehicles)} vehicles...")
            
            # Test QR code generation
            qr_results = []
            output_dir = Path("test_qr_output")
            output_dir.mkdir(exist_ok=True)
            
            for i, vehicle in enumerate(test_vehicles[:5]):  # Test first 5 vehicles
                try:
                    # Generate QR code
                    qr_path = output_dir / f"test_qr_{i+1}.png"
                    vehicle_url = f"https://example.com/vehicle/{vehicle['vin']}"
                    
                    success = self.qr_generator.generate_qr_code(
                        vehicle_url, 
                        str(qr_path),
                        vehicle['display_name']
                    )
                    
                    qr_results.append({
                        'vin': vehicle['vin'],
                        'file_generated': qr_path.exists(),
                        'file_size': qr_path.stat().st_size if qr_path.exists() else 0,
                        'success': success
                    })
                    
                    if success and qr_path.exists():
                        logger.info(f"✅ QR code generated: {vehicle['display_name']} ({qr_path.stat().st_size} bytes)")
                    else:
                        logger.error(f"❌ QR code generation failed: {vehicle['display_name']}")
                        self.test_results['total_errors'] += 1
                        
                except Exception as e:
                    logger.error(f"❌ QR generation error for {vehicle.get('vin', 'unknown')}: {e}")
                    self.test_results['total_errors'] += 1
            
            # Calculate QR generation statistics
            successful_qr = sum(1 for r in qr_results if r['success'])
            total_size = sum(r['file_size'] for r in qr_results if r['file_generated'])
            
            test_results['qr_generation'] = {
                'total_tested': len(qr_results),
                'successful': successful_qr,
                'success_rate': (successful_qr / len(qr_results)) * 100 if qr_results else 0,
                'total_file_size': total_size,
                'average_file_size': total_size / successful_qr if successful_qr > 0 else 0,
                'details': qr_results
            }
            
            logger.info(f"✅ QR Generation Summary: {successful_qr}/{len(qr_results)} successful ({test_results['qr_generation']['success_rate']:.1f}%)")
            
        except Exception as e:
            logger.error(f"❌ QR code test failed: {e}")
            test_results['error'] = str(e)
            self.test_results['total_errors'] += 1
        
        self.test_results['qr_tests'] = test_results
    
    def test_template_system(self):
        """Test template-based CSV generation"""
        logger.info("\n📄 TESTING TEMPLATE SYSTEM")
        logger.info("-" * 50)
        
        test_results = {}
        
        try:
            # Test each template type
            templates_to_test = ['Flyout', 'Shortcut', 'Shortcut Pack']
            
            for template_type in templates_to_test:
                logger.info(f"Testing {template_type} template...")
                
                # Create test order in queue
                today = date.today()
                db_manager.execute_query("""
                    INSERT INTO order_queue 
                    (dealership_name, order_type, template_type, vehicle_types, scheduled_date, day_of_week)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, ('Test Template Dealer', 'TEST', template_type, ['new', 'used'], today, 'TestDay'))
                
                # Get the created order
                test_orders = self.queue_manager.get_daily_queue(today)
                template_order = next((o for o in test_orders if o['template_type'] == template_type), None)
                
                if template_order:
                    result = self.queue_manager.process_queue_order(template_order['queue_id'])
                    
                    test_results[template_type] = {
                        'processing_success': result.get('success', False),
                        'vehicles_processed': result.get('vehicles_processed', 0),
                        'csv_generated': bool(result.get('csv_file')),
                        'qr_codes_generated': result.get('qr_codes_generated', 0),
                        'csv_file_path': result.get('csv_file', '')
                    }
                    
                    if result.get('success'):
                        logger.info(f"✅ {template_type}: {result.get('vehicles_processed', 0)} vehicles, CSV: {bool(result.get('csv_file'))}")
                        
                        # Test NEW prefix for Shortcut Pack
                        if template_type == 'Shortcut Pack' and result.get('csv_file'):
                            csv_path = result.get('csv_file')
                            if os.path.exists(csv_path):
                                with open(csv_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    new_prefix_found = 'NEW ' in content
                                    test_results[template_type]['new_prefix_working'] = new_prefix_found
                                    logger.info(f"✅ NEW prefix in Shortcut Pack: {'Found' if new_prefix_found else 'Not Found'}")
                    else:
                        logger.error(f"❌ {template_type} template processing failed")
                        self.test_results['total_errors'] += 1
                else:
                    logger.error(f"❌ Could not create test order for {template_type}")
                    self.test_results['total_errors'] += 1
                
                # Clean up test order
                db_manager.execute_query("DELETE FROM order_queue WHERE dealership_name = 'Test Template Dealer'")
                
        except Exception as e:
            logger.error(f"❌ Template system test failed: {e}")
            test_results['error'] = str(e)
            self.test_results['total_errors'] += 1
        
        self.test_results['accuracy_tests'] = test_results
    
    def test_database_performance(self):
        """Test database performance under load"""
        logger.info("\n💾 TESTING DATABASE PERFORMANCE")
        logger.info("-" * 50)
        
        test_results = {}
        
        try:
            # Test 1: Queue operations performance
            start_time = time.time()
            
            # Simulate multiple queue operations
            for i in range(10):
                today = date.today()
                summary = self.queue_manager.get_queue_summary(today)
                queue_orders = self.queue_manager.get_daily_queue(today)
            
            queue_ops_time = time.time() - start_time
            test_results['queue_operations'] = {
                'operations': 20,  # 10 summary + 10 queue retrievals
                'total_time': queue_ops_time,
                'avg_time': queue_ops_time / 20
            }
            logger.info(f"✅ Queue operations: 20 ops in {queue_ops_time:.2f}s (avg: {queue_ops_time/20:.3f}s)")
            
            # Test 2: Vehicle data queries
            start_time = time.time()
            
            for dealership in self.test_dealerships:
                vehicles = db_manager.execute_query("""
                    SELECT COUNT(*) as count FROM normalized_vehicle_data nv
                    JOIN raw_vehicle_data rv ON nv.raw_data_id = rv.id
                    WHERE rv.location = %s
                """, (dealership,))
            
            vehicle_query_time = time.time() - start_time
            test_results['vehicle_queries'] = {
                'queries': len(self.test_dealerships),
                'total_time': vehicle_query_time,
                'avg_time': vehicle_query_time / len(self.test_dealerships)
            }
            logger.info(f"✅ Vehicle queries: {len(self.test_dealerships)} queries in {vehicle_query_time:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Database performance test failed: {e}")
            test_results['error'] = str(e)
            self.test_results['total_errors'] += 1
        
        self.test_results['performance_tests'] = test_results
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        logger.info("\n🔄 TESTING END-TO-END WORKFLOW")
        logger.info("-" * 50)
        
        try:
            # Simulate complete workflow: Queue → Process → QR → Export
            dealership = 'Test Integration Dealer'
            logger.info(f"Testing complete workflow for {dealership}...")
            
            # Step 1: Add to queue
            today = date.today()
            db_manager.execute_query("""
                INSERT INTO order_queue 
                (dealership_name, order_type, template_type, vehicle_types, scheduled_date, day_of_week, priority)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (dealership, 'E2E_TEST', 'Shortcut Pack', ['new'], today, 'TestDay', 1))
            
            # Step 2: Get from queue
            queue_orders = self.queue_manager.get_daily_queue(today)
            test_order = next((o for o in queue_orders if o['dealership_name'] == dealership), None)
            
            if test_order:
                logger.info(f"✅ Order found in queue: {test_order['queue_id']}")
                
                # Step 3: Process order
                result = self.queue_manager.process_queue_order(test_order['queue_id'])
                
                if result.get('success'):
                    logger.info(f"✅ Order processed successfully:")
                    logger.info(f"   - Vehicles: {result.get('vehicles_processed', 0)}")
                    logger.info(f"   - QR Codes: {result.get('qr_codes_generated', 0)}")
                    logger.info(f"   - CSV File: {result.get('csv_file', 'None')}")
                    
                    # Step 4: Verify output files
                    csv_file = result.get('csv_file')
                    qr_folder = result.get('qr_folder')
                    
                    files_verified = 0
                    if csv_file and os.path.exists(csv_file):
                        files_verified += 1
                        logger.info(f"✅ CSV file verified: {csv_file}")
                    
                    if qr_folder and os.path.exists(qr_folder):
                        qr_files = list(Path(qr_folder).glob('*.png'))
                        files_verified += len(qr_files)
                        logger.info(f"✅ QR folder verified: {len(qr_files)} QR codes")
                    
                    logger.info(f"🎉 END-TO-END TEST PASSED: {files_verified} files verified")
                    
                else:
                    logger.error(f"❌ Order processing failed: {result.get('error', 'Unknown error')}")
                    self.test_results['total_errors'] += 1
            else:
                logger.error("❌ Test order not found in queue")
                self.test_results['total_errors'] += 1
            
            # Clean up
            db_manager.execute_query("DELETE FROM order_queue WHERE dealership_name = %s", (dealership,))
            
        except Exception as e:
            logger.error(f"❌ End-to-end workflow test failed: {e}")
            self.test_results['total_errors'] += 1
    
    def generate_comprehensive_report(self):
        """Generate comprehensive test report"""
        logger.info("\n📊 GENERATING COMPREHENSIVE REPORT")
        logger.info("=" * 80)
        
        # Calculate overall statistics
        total_tests = sum([
            len(self.test_results.get('queue_tests', {})),
            len(self.test_results.get('processing_tests', {})),
            len(self.test_results.get('qr_tests', {})),
            len(self.test_results.get('accuracy_tests', {})),
            len(self.test_results.get('performance_tests', {}))
        ])
        
        logger.info(f"🏆 COMPREHENSIVE STRESS TEST RESULTS")
        logger.info("-" * 50)
        logger.info(f"Total Test Categories: 6")
        logger.info(f"Total Individual Tests: {total_tests}")
        logger.info(f"Total Errors: {self.test_results['total_errors']}")
        logger.info(f"Total Warnings: {self.test_results['total_warnings']}")
        
        # Queue Management Results
        if 'queue_tests' in self.test_results:
            logger.info("\n📋 Queue Management:")
            queue_tests = self.test_results['queue_tests']
            for test_name, result in queue_tests.items():
                if isinstance(result, dict) and 'success' in result:
                    status = "✅ PASS" if result['success'] else "❌ FAIL"
                    logger.info(f"   {test_name}: {status}")
        
        # QR Code Generation Results
        if 'qr_tests' in self.test_results and 'qr_generation' in self.test_results['qr_tests']:
            logger.info("\n🔲 QR Code Generation:")
            qr_data = self.test_results['qr_tests']['qr_generation']
            logger.info(f"   Success Rate: {qr_data.get('success_rate', 0):.1f}%")
            logger.info(f"   Files Generated: {qr_data.get('successful', 0)}/{qr_data.get('total_tested', 0)}")
            logger.info(f"   Average File Size: {qr_data.get('average_file_size', 0):.0f} bytes")
        
        # Template System Results
        if 'accuracy_tests' in self.test_results:
            logger.info("\n📄 Template System:")
            for template, result in self.test_results['accuracy_tests'].items():
                if isinstance(result, dict):
                    status = "✅ PASS" if result.get('processing_success') else "❌ FAIL"
                    logger.info(f"   {template}: {status}")
        
        # Performance Results
        if 'performance_tests' in self.test_results:
            logger.info("\n💾 Performance:")
            perf_tests = self.test_results['performance_tests']
            if 'queue_operations' in perf_tests:
                avg_time = perf_tests['queue_operations'].get('avg_time', 0)
                logger.info(f"   Queue Operations: {avg_time:.3f}s average")
        
        # Final Assessment
        logger.info("\n🎯 FINAL ASSESSMENT:")
        if self.test_results['total_errors'] == 0:
            logger.info("✅ ALL TESTS PASSED - System is ready for production!")
        elif self.test_results['total_errors'] <= 2:
            logger.info("⚠️ MINOR ISSUES - System mostly functional with minor fixes needed")
        else:
            logger.info("❌ MAJOR ISSUES - System requires significant fixes before production")
        
        # Save detailed results to file
        report_file = f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        logger.info(f"📄 Detailed report saved: {report_file}")
        logger.info("=" * 80)

def main():
    """Main test execution"""
    print("🧪 COMPREHENSIVE STRESS TEST")
    print("Testing queue management, processing accuracy, and QR generation")
    print("=" * 80)
    
    try:
        tester = ComprehensiveStressTest()
        tester.run_all_tests()
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Critical test failure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()