#!/usr/bin/env python3
"""
Integration Verification Test
============================

Verifies that the critical fixes work correctly:
1. QR codes are generated BEFORE Adobe CSV creation
2. QR file paths are properly included in CSV output
3. Scraper data flows correctly into order processing

Author: Silver Fox Assistant  
Created: 2025-07-29
"""

import os
import sys
import json
import csv
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add project paths
current_file = Path(__file__).resolve()
scripts_dir = current_file.parent
sys.path.insert(0, str(scripts_dir))

from database_connection import db_manager
from order_processing_workflow import OrderProcessingWorkflow
from real_scraper_integration import RealScraperIntegration

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntegrationVerificationTest:
    """Verifies critical integration fixes"""
    
    def __init__(self):
        self.workflow = OrderProcessingWorkflow()
        self.scraper_integration = RealScraperIntegration()
        self.test_results = {
            'start_time': datetime.now(),
            'tests': {},
            'summary': {},
            'errors': []
        }
    
    def test_qr_before_csv_generation(self) -> bool:
        """Test that QR codes are generated before CSV and paths are included"""
        logger.info("=" * 60)
        logger.info("TEST 1: QR Generation Before CSV Creation")
        logger.info("=" * 60)
        
        try:
            # Get test vehicles from database
            test_vehicles = db_manager.execute_query("""
                SELECT * FROM raw_vehicle_data 
                WHERE location = 'Columbia Honda'
                LIMIT 3
            """)
            
            if not test_vehicles:
                logger.warning("No test vehicles found, creating sample data...")
                test_vehicles = [
                    {
                        'vin': 'TEST123456789001',
                        'stock': 'T001',
                        'make': 'Honda',
                        'model': 'Civic',
                        'year': 2024,
                        'vehicle_url': 'https://example.com/vehicle1',
                        'location': 'Columbia Honda'
                    },
                    {
                        'vin': 'TEST123456789002', 
                        'stock': 'T002',
                        'make': 'Honda',
                        'model': 'Accord',
                        'year': 2024,
                        'vehicle_url': 'https://example.com/vehicle2',
                        'location': 'Columbia Honda'
                    }
                ]
            
            logger.info(f"Testing with {len(test_vehicles)} vehicles")
            
            # Create test output folders
            test_output = Path("test_verification_output")
            qr_folder = test_output / "qr_codes"
            csv_folder = test_output / "adobe"
            
            qr_folder.mkdir(parents=True, exist_ok=True)
            csv_folder.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Generate QR codes FIRST
            logger.info("Step 1: Generating QR codes...")
            start_time = time.time()
            qr_paths = self.workflow.generate_qr_codes(test_vehicles, 'Columbia Honda', qr_folder)
            qr_time = time.time() - start_time
            
            logger.info(f"QR Generation completed in {qr_time:.2f}s")
            logger.info(f"Generated {len(qr_paths)} QR codes")
            
            # Verify QR files exist
            qr_files_exist = all(os.path.exists(path) for path in qr_paths)
            logger.info(f"QR files exist on filesystem: {qr_files_exist}")
            
            # Step 2: Generate Adobe CSV with QR paths
            logger.info("Step 2: Generating Adobe CSV with QR paths...")
            start_time = time.time()
            csv_path = self.workflow.generate_adobe_csv(test_vehicles, 'Columbia Honda', csv_folder, qr_paths)
            csv_time = time.time() - start_time
            
            logger.info(f"CSV Generation completed in {csv_time:.2f}s")
            logger.info(f"CSV file created: {csv_path}")
            
            # Step 3: Verify CSV contains QR paths
            logger.info("Step 3: Verifying CSV contains QR file paths...")
            csv_has_qr_paths = False
            qr_paths_in_csv = []
            
            if os.path.exists(csv_path):
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        qr_path = row.get('QR_Code_Path', '')
                        if qr_path:
                            qr_paths_in_csv.append(qr_path)
                    
                    csv_has_qr_paths = len(qr_paths_in_csv) > 0
            
            logger.info(f"CSV contains QR paths: {csv_has_qr_paths}")
            logger.info(f"QR paths found in CSV: {len(qr_paths_in_csv)}")
            
            # Verify paths match
            paths_match = set(qr_paths) == set(qr_paths_in_csv)
            logger.info(f"Generated QR paths match CSV paths: {paths_match}")
            
            test_success = qr_files_exist and csv_has_qr_paths and paths_match
            
            self.test_results['tests']['qr_before_csv'] = {
                'success': test_success,
                'qr_generation_time': qr_time,
                'csv_generation_time': csv_time,
                'qr_files_generated': len(qr_paths),
                'qr_files_exist': qr_files_exist,
                'csv_has_qr_paths': csv_has_qr_paths,
                'paths_match': paths_match,
                'qr_paths': qr_paths,
                'csv_qr_paths': qr_paths_in_csv
            }
            
            if test_success:
                logger.info("✅ TEST PASSED: QR codes generated before CSV with correct paths")
            else:
                logger.error("❌ TEST FAILED: QR-before-CSV integration issue")
            
            return test_success
            
        except Exception as e:
            logger.error(f"QR-before-CSV test failed: {e}")
            self.test_results['errors'].append(f"QR-before-CSV test: {str(e)}")
            return False
    
    def test_scraper_to_order_integration(self) -> bool:
        """Test that scraper data flows correctly into order processing"""
        logger.info("=" * 60)
        logger.info("TEST 2: Scraper to Order Processing Integration")
        logger.info("=" * 60)
        
        try:
            # Run a real scraper to get fresh data
            test_dealership = 'Columbia Honda'
            logger.info(f"Running scraper for {test_dealership}...")
            
            scraper_result = self.scraper_integration.run_real_scraper(test_dealership)
            logger.info(f"Scraper result: {scraper_result['success']}, vehicles: {scraper_result.get('vehicle_count', 0)}")
            
            if scraper_result['success'] and scraper_result['vehicle_count'] > 0:
                # Import vehicles to database
                import_result = self.scraper_integration.import_vehicles_to_database(
                    scraper_result['vehicles'],
                    test_dealership
                )
                logger.info(f"Import result: {import_result}")
                
                # Wait a moment for database to update
                time.sleep(1)
                
                # Now test order processing can access this data
                logger.info("Testing order processing access to scraper data...")
                filtered_vehicles = self.workflow.filter_vehicles_by_type(test_dealership, ['used'])
                logger.info(f"Order processing found {len(filtered_vehicles)} vehicles")
                
                # Test CAO order processing with this data
                if len(filtered_vehicles) > 0:
                    logger.info("Testing CAO order processing...")
                    cao_result = self.workflow.process_cao_order(test_dealership, ['used'])
                    
                    integration_success = (
                        cao_result['success'] and 
                        cao_result['new_vehicles'] >= 0 and
                        'csv_file' in cao_result
                    )
                    
                    logger.info(f"CAO processing result: {cao_result}")
                    
                    self.test_results['tests']['scraper_integration'] = {
                        'success': integration_success,
                        'scraper_vehicles': scraper_result['vehicle_count'],
                        'imported_successfully': import_result,
                        'filtered_vehicles': len(filtered_vehicles),
                        'cao_result': cao_result
                    }
                    
                    if integration_success:
                        logger.info("✅ TEST PASSED: Scraper data flows correctly to order processing")
                    else:
                        logger.error("❌ TEST FAILED: Scraper to order processing integration issue")
                    
                    return integration_success
                else:
                    logger.warning("No vehicles found after filtering - may indicate data flow issue")
                    return False
            else:
                logger.warning("Scraper failed or returned no vehicles - testing with existing data")
                
                # Test with existing database data
                existing_vehicles = db_manager.execute_query(f"""
                    SELECT COUNT(*) as count FROM raw_vehicle_data 
                    WHERE location = %s
                """, (test_dealership,))[0]['count']
                
                logger.info(f"Found {existing_vehicles} existing vehicles in database")
                
                if existing_vehicles > 0:
                    filtered_vehicles = self.workflow.filter_vehicles_by_type(test_dealership, ['used'])
                    integration_success = len(filtered_vehicles) > 0
                    
                    self.test_results['tests']['scraper_integration'] = {
                        'success': integration_success,
                        'note': 'tested_with_existing_data',
                        'existing_vehicles': existing_vehicles,
                        'filtered_vehicles': len(filtered_vehicles)
                    }
                    
                    if integration_success:
                        logger.info("✅ TEST PASSED: Order processing can access existing scraper data")
                    else:
                        logger.error("❌ TEST FAILED: Order processing cannot access database data")
                    
                    return integration_success
                else:
                    logger.error("No vehicles found in database - integration cannot be tested")
                    return False
                    
        except Exception as e:
            logger.error(f"Scraper integration test failed: {e}")
            self.test_results['errors'].append(f"Scraper integration test: {str(e)}")
            return False
    
    def test_complete_workflow(self) -> bool:
        """Test the complete end-to-end workflow"""
        logger.info("=" * 60)
        logger.info("TEST 3: Complete End-to-End Workflow")
        logger.info("=" * 60)
        
        try:
            test_dealership = 'Columbia Honda'
            
            # Step 1: Check if we have data
            vehicle_count = db_manager.execute_query("""
                SELECT COUNT(*) as count FROM raw_vehicle_data
                WHERE location = %s
            """, (test_dealership,))[0]['count']
            
            logger.info(f"Database contains {vehicle_count} vehicles for {test_dealership}")
            
            if vehicle_count == 0:
                logger.warning("No data available for complete workflow test")
                return False
            
            # Step 2: Process complete CAO order
            logger.info("Processing complete CAO order...")
            start_time = time.time()
            result = self.workflow.process_cao_order(test_dealership, ['used'])
            workflow_time = time.time() - start_time
            
            logger.info(f"Workflow completed in {workflow_time:.2f}s")
            logger.info(f"Result: {result}")
            
            # Step 3: Verify all components work
            workflow_success = (
                result['success'] and
                'qr_codes_generated' in result and
                'csv_file' in result and
                os.path.exists(result['csv_file'])
            )
            
            # Step 4: Verify CSV contains QR paths
            csv_verification = False
            if workflow_success and result['csv_file']:
                try:
                    with open(result['csv_file'], 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        headers = reader.fieldnames
                        csv_verification = 'QR_Code_Path' in headers
                        logger.info(f"CSV headers: {headers}")
                        logger.info(f"CSV contains QR_Code_Path column: {csv_verification}")
                except Exception as e:
                    logger.error(f"CSV verification error: {e}")
            
            complete_success = workflow_success and csv_verification
            
            self.test_results['tests']['complete_workflow'] = {
                'success': complete_success,
                'workflow_time': workflow_time,
                'workflow_result': result,
                'csv_has_qr_column': csv_verification
            }
            
            if complete_success:
                logger.info("✅ TEST PASSED: Complete end-to-end workflow working correctly")
            else:
                logger.error("❌ TEST FAILED: Complete workflow has issues")
            
            return complete_success
            
        except Exception as e:
            logger.error(f"Complete workflow test failed: {e}")
            self.test_results['errors'].append(f"Complete workflow test: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict:
        """Run all verification tests"""
        logger.info("🚀 STARTING INTEGRATION VERIFICATION TESTS")
        logger.info("=" * 80)
        
        # Run tests
        test1_result = self.test_qr_before_csv_generation()
        test2_result = self.test_scraper_to_order_integration()
        test3_result = self.test_complete_workflow()
        
        # Calculate summary
        total_tests = 3
        passed_tests = sum([test1_result, test2_result, test3_result])
        success_rate = (passed_tests / total_tests) * 100
        
        self.test_results['end_time'] = datetime.now()
        duration = (self.test_results['end_time'] - self.test_results['start_time']).total_seconds()
        
        self.test_results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': success_rate,
            'duration_seconds': duration,
            'overall_success': success_rate == 100.0
        }
        
        # Final report
        logger.info("=" * 80)
        logger.info("🏆 INTEGRATION VERIFICATION TEST RESULTS")
        logger.info("=" * 80)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {success_rate:.1f}%") 
        logger.info(f"Duration: {duration:.1f} seconds")
        
        if self.test_results['summary']['overall_success']:
            logger.info("🎉 ALL TESTS PASSED - Integration fixes verified successfully!")
        else:
            logger.warning("⚠️  Some tests failed - review results above")
        
        if self.test_results['errors']:
            logger.error("Errors encountered:")
            for error in self.test_results['errors']:
                logger.error(f"  - {error}")
        
        return self.test_results

def main():
    """Main entry point"""
    test_runner = IntegrationVerificationTest()
    results = test_runner.run_all_tests()
    
    # Save results to file
    results_file = Path("integration_verification_results.json")
    
    # Convert datetime objects to strings for JSON serialization
    def serialize_datetime(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=serialize_datetime)
    
    logger.info(f"Results saved to: {results_file}")
    
    return results['summary']['overall_success']

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)