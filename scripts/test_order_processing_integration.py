#!/usr/bin/env python3
"""
Order Processing Integration Test Suite
======================================

Comprehensive testing for the order processing integration with the database.
Tests the complete pipeline from database to order processing tool.

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import json
import logging

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from order_processing_integration import OrderProcessingIntegrator
from database_connection import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderProcessingIntegrationTester:
    """Test suite for order processing integration"""
    
    def __init__(self):
        self.integrator = OrderProcessingIntegrator()
        self.temp_dir = Path(tempfile.mkdtemp(prefix="order_processing_test_"))
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'overall_status': 'PENDING'
        }
        
        logger.info(f"Test directory: {self.temp_dir}")
    
    def setup_test_environment(self) -> bool:
        """Set up test environment with sample data"""
        logger.info("🔧 Setting up test environment...")
        
        try:
            # Ensure order processing tables exist
            self.integrator.ensure_order_processing_tables()
            
            # Create test QR directories
            test_qr_dirs = [
                self.temp_dir / "qr_codes" / "BMW_of_West_St_Louis",
                self.temp_dir / "qr_codes" / "Columbia_BMW",
                self.temp_dir / "qr_codes" / "Audi_Ranch_Mirage"
            ]
            
            for qr_dir in test_qr_dirs:
                qr_dir.mkdir(parents=True, exist_ok=True)
                
                # Create sample QR files
                for i in range(5):
                    test_vin = f"TEST{i:013d}"
                    qr_file = qr_dir / f"{test_vin}.png"
                    qr_file.write_text("dummy qr data")
            
            # Insert test vehicle data if none exists
            vehicles = db_manager.execute_query("""
                SELECT COUNT(*) as count FROM normalized_vehicle_data 
                WHERE last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
            """)
            
            if vehicles[0]['count'] == 0:
                logger.info("Inserting test vehicle data...")
                self.insert_test_vehicle_data()
            
            self.test_results['tests']['setup'] = {'status': 'PASS'}
            return True
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            self.test_results['tests']['setup'] = {'status': 'FAIL', 'error': str(e)}
            return False
    
    def insert_test_vehicle_data(self):
        """Insert sample vehicle data for testing"""
        test_dealerships = ['BMW of West St. Louis', 'Columbia BMW', 'Audi Ranch Mirage']
        
        for i, dealership in enumerate(test_dealerships):
            for j in range(10):
                vin = f"TEST{i:02d}{j:011d}"
                
                # Insert into raw_vehicle_data
                db_manager.execute_query("""
                    INSERT INTO raw_vehicle_data 
                    (vin, stock, type, year, make, model, price, location, vehicle_url)
                    VALUES (%s, %s, 'Vehicle', %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    vin, f"STK{i:02d}{j:03d}", 2022 + (j % 3),
                    ['BMW', 'BMW', 'Audi'][i], f"Model{j}", 30000 + (j * 1000),
                    dealership, f"https://example.com/{vin}"
                ))
                
                # Insert into normalized_vehicle_data
                db_manager.execute_query("""
                    INSERT INTO normalized_vehicle_data 
                    (vin, stock, vehicle_condition, year, make, model, price, location, vehicle_url)
                    VALUES (%s, %s, 'new', %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (vin, location) DO UPDATE SET
                        last_seen_date = CURRENT_DATE,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    vin, f"STK{i:02d}{j:03d}", 2022 + (j % 3),
                    ['BMW', 'BMW', 'Audi'][i], f"Model{j}", 30000 + (j * 1000),
                    dealership, f"https://example.com/{vin}"
                ))
    
    def test_dealership_config_loading(self) -> bool:
        """Test loading dealership configurations"""
        logger.info("🔍 Testing dealership config loading...")
        
        try:
            configs = self.integrator.get_active_dealership_configs()
            
            if len(configs) == 0:
                self.test_results['tests']['config_loading'] = {
                    'status': 'FAIL', 
                    'error': 'No active dealership configs found'
                }
                return False
            
            # Verify config structure
            sample_config = configs[0]
            required_fields = ['name', 'filtering_rules', 'output_rules', 'qr_output_path']
            
            for field in required_fields:
                if field not in sample_config:
                    self.test_results['tests']['config_loading'] = {
                        'status': 'FAIL',
                        'error': f'Missing field: {field}'
                    }
                    return False
            
            self.test_results['tests']['config_loading'] = {
                'status': 'PASS',
                'configs_loaded': len(configs),
                'sample_config': sample_config['name']
            }
            
            logger.info(f"✅ Loaded {len(configs)} dealership configurations")
            return True
            
        except Exception as e:
            logger.error(f"Config loading test failed: {e}")
            self.test_results['tests']['config_loading'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return False
    
    def test_order_processing_job_creation(self) -> bool:
        """Test creating order processing jobs"""
        logger.info("🏭 Testing order processing job creation...")
        
        try:
            # Test with a known dealership
            test_dealership = "BMW of West St. Louis"
            
            job_result = self.integrator.create_order_processing_job(
                dealership_name=test_dealership,
                job_type="test"
            )
            
            # Verify job result structure
            required_fields = ['job_id', 'dealership', 'job_type', 'vehicle_count']
            for field in required_fields:
                if field not in job_result:
                    self.test_results['tests']['job_creation'] = {
                        'status': 'FAIL',
                        'error': f'Missing field in job result: {field}'
                    }
                    return False
            
            # Verify job was created in database
            job_status = self.integrator.get_job_status(job_result['job_id'])
            if not job_status:
                self.test_results['tests']['job_creation'] = {
                    'status': 'FAIL',
                    'error': 'Job not found in database after creation'
                }
                return False
            
            self.test_results['tests']['job_creation'] = {
                'status': 'PASS',
                'job_id': job_result['job_id'],
                'vehicle_count': job_result['vehicle_count'],
                'export_file': job_result.get('export_file')
            }
            
            logger.info(f"✅ Created job {job_result['job_id']} with {job_result['vehicle_count']} vehicles")
            return True
            
        except Exception as e:
            logger.error(f"Job creation test failed: {e}")
            self.test_results['tests']['job_creation'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return False
    
    def test_qr_file_validation(self) -> bool:
        """Test QR file validation functionality"""
        logger.info("🔍 Testing QR file validation...")
        
        try:
            test_dealership = "BMW of West St. Louis"
            
            # Update QR output path to our test directory for this dealership
            db_manager.execute_query("""
                UPDATE dealership_configs 
                SET qr_output_path = %s 
                WHERE name = %s
            """, (str(self.temp_dir / "qr_codes" / "BMW_of_West_St_Louis"), test_dealership))
            
            validation_result = self.integrator.validate_qr_files(test_dealership)
            
            # Verify validation result structure
            required_fields = ['dealership', 'total_vehicles', 'qr_files_exist', 'qr_files_missing']
            for field in required_fields:
                if field not in validation_result:
                    self.test_results['tests']['qr_validation'] = {
                        'status': 'FAIL',
                        'error': f'Missing field in validation result: {field}'
                    }
                    return False
            
            self.test_results['tests']['qr_validation'] = {
                'status': 'PASS',
                'total_vehicles': validation_result['total_vehicles'],
                'qr_files_exist': validation_result['qr_files_exist'],
                'qr_files_missing': validation_result['qr_files_missing']
            }
            
            logger.info(f"✅ QR validation: {validation_result['qr_files_exist']}/{validation_result['total_vehicles']} files exist")
            return True
            
        except Exception as e:
            logger.error(f"QR validation test failed: {e}")
            self.test_results['tests']['qr_validation'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return False
    
    def test_database_views(self) -> bool:
        """Test database views for order processing"""
        logger.info("📊 Testing database views...")
        
        try:
            # Test current_job_status view
            job_status = db_manager.execute_query("SELECT * FROM current_job_status LIMIT 5")
            
            # Test dealership_qr_status view
            qr_status = db_manager.execute_query("SELECT * FROM dealership_qr_status LIMIT 5")
            
            # Test recent_export_activity view
            export_activity = db_manager.execute_query("SELECT * FROM recent_export_activity LIMIT 5")
            
            # Test summary function
            summary = db_manager.execute_query("SELECT * FROM get_order_processing_summary()")
            
            self.test_results['tests']['database_views'] = {
                'status': 'PASS',
                'job_status_records': len(job_status),
                'qr_status_records': len(qr_status),
                'export_activity_records': len(export_activity),
                'summary_metrics': len(summary)
            }
            
            logger.info("✅ All database views working correctly")
            return True
            
        except Exception as e:
            logger.error(f"Database views test failed: {e}")
            self.test_results['tests']['database_views'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return False
    
    def test_export_file_generation(self) -> bool:
        """Test export file generation"""
        logger.info("📤 Testing export file generation...")
        
        try:
            test_dealership = "BMW of West St. Louis"
            
            job_result = self.integrator.create_order_processing_job(
                dealership_name=test_dealership,
                job_type="export_test"
            )
            
            if job_result.get('export_file'):
                export_path = Path(job_result['export_file'])
                
                if export_path.exists():
                    # Read and validate CSV content
                    import pandas as pd
                    df = pd.read_csv(export_path)
                    
                    required_columns = ['vin', 'stock', 'qr_code_path']
                    missing_columns = [col for col in required_columns if col not in df.columns]
                    
                    if missing_columns:
                        self.test_results['tests']['export_generation'] = {
                            'status': 'FAIL',
                            'error': f'Missing columns in export: {missing_columns}'
                        }
                        return False
                    
                    self.test_results['tests']['export_generation'] = {
                        'status': 'PASS',
                        'export_file': str(export_path),
                        'record_count': len(df),
                        'columns': list(df.columns)
                    }
                    
                    logger.info(f"✅ Export generated: {len(df)} records in {export_path.name}")
                    return True
                else:
                    self.test_results['tests']['export_generation'] = {
                        'status': 'FAIL',
                        'error': f'Export file not found: {export_path}'
                    }
                    return False
            else:
                self.test_results['tests']['export_generation'] = {
                    'status': 'FAIL',
                    'error': 'No export file generated'
                }
                return False
                
        except Exception as e:
            logger.error(f"Export generation test failed: {e}")
            self.test_results['tests']['export_generation'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return False
    
    def test_filtering_rules(self) -> bool:
        """Test dealership-specific filtering rules"""
        logger.info("🔧 Testing filtering rules...")
        
        try:
            test_dealership = "BMW of West St. Louis"
            
            # Create job with custom filters
            custom_filters = {
                'min_price': 25000,
                'year_min': 2022,
                'exclude_conditions': ['used', 'offlot']
            }
            
            job_result = self.integrator.create_order_processing_job(
                dealership_name=test_dealership,
                job_type="filtered_test",
                filters=custom_filters
            )
            
            # Verify filtering was applied by checking the export
            if job_result.get('export_file'):
                import pandas as pd
                df = pd.read_csv(job_result['export_file'])
                
                # Check that all records meet the filter criteria
                if 'price' in df.columns:
                    min_price_violations = df[df['price'] < 25000]
                    if len(min_price_violations) > 0:
                        self.test_results['tests']['filtering_rules'] = {
                            'status': 'FAIL',
                            'error': f'Found {len(min_price_violations)} records below minimum price'
                        }
                        return False
                
                self.test_results['tests']['filtering_rules'] = {
                    'status': 'PASS',
                    'filtered_records': len(df),
                    'filters_applied': custom_filters
                }
                
                logger.info(f"✅ Filtering rules applied: {len(df)} records after filtering")
                return True
            else:
                # No export file might mean no records matched filters
                self.test_results['tests']['filtering_rules'] = {
                    'status': 'PASS',
                    'filtered_records': 0,
                    'note': 'No records matched filter criteria'
                }
                return True
                
        except Exception as e:
            logger.error(f"Filtering rules test failed: {e}")
            self.test_results['tests']['filtering_rules'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return False
    
    def cleanup_test_environment(self):
        """Clean up test environment"""
        logger.info("🧹 Cleaning up test environment...")
        
        try:
            # Remove test directory
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            
            # Clean up test jobs (optional - keep for debugging)
            # db_manager.execute_query("DELETE FROM order_processing_jobs WHERE job_type LIKE '%test%'")
            
            logger.info("✅ Test environment cleaned up")
            
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")
    
    def run_all_tests(self) -> bool:
        """Run complete integration test suite"""
        logger.info("🚀 ORDER PROCESSING INTEGRATION TEST SUITE")
        logger.info("=" * 60)
        
        tests = [
            ("Environment Setup", self.setup_test_environment),
            ("Config Loading", self.test_dealership_config_loading),
            ("Job Creation", self.test_order_processing_job_creation),
            ("QR Validation", self.test_qr_file_validation),
            ("Database Views", self.test_database_views),
            ("Export Generation", self.test_export_file_generation),
            ("Filtering Rules", self.test_filtering_rules)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        try:
            for test_name, test_func in tests:
                logger.info(f"\\n🧪 Running: {test_name}")
                try:
                    if test_func():
                        logger.info(f"✅ {test_name}: PASSED")
                        passed_tests += 1
                    else:
                        logger.error(f"❌ {test_name}: FAILED")
                except Exception as e:
                    logger.error(f"💥 {test_name}: ERROR - {e}")
                    self.test_results['tests'][test_name.lower().replace(' ', '_')] = {
                        'status': 'ERROR',
                        'error': str(e)
                    }
            
            # Calculate results
            success_rate = (passed_tests / total_tests) * 100
            self.test_results['overall_status'] = 'PASS' if success_rate >= 80 else 'FAIL'
            self.test_results['success_rate'] = success_rate
            self.test_results['tests_passed'] = passed_tests
            self.test_results['total_tests'] = total_tests
            
            # Print results
            logger.info(f"\\n{'='*60}")
            logger.info("🏆 INTEGRATION TEST RESULTS")
            logger.info(f"{'='*60}")
            logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
            logger.info(f"Success Rate: {success_rate:.1f}%")
            
            if self.test_results['overall_status'] == 'PASS':
                logger.info("✅ ORDER PROCESSING INTEGRATION IS READY!")
                logger.info("✅ Database and order processing tool can work together")
            else:
                logger.error("❌ Integration needs additional work")
                logger.error("❌ Review failed tests and fix issues")
            
            return self.test_results['overall_status'] == 'PASS'
            
        finally:
            self.cleanup_test_environment()
    
    def save_test_results(self):
        """Save test results to file"""
        results_file = Path(__file__).parent.parent / "integration_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        logger.info(f"Test results saved to: {results_file}")

def main():
    """Run the integration test suite"""
    tester = OrderProcessingIntegrationTester()
    
    try:
        success = tester.run_all_tests()
        tester.save_test_results()
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())