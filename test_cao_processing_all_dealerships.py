#!/usr/bin/env python3
"""
CAO Processing Test for All Dealerships
=======================================
Tests CAO processing across all dealerships to identify configuration issues.
This script will help identify which dealerships need fixing before production.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add project paths
current_file = Path(__file__).resolve()
sys.path.insert(0, str(current_file.parent / "projects" / "minisforum_database_transfer" / "bulletproof_package" / "scripts"))

from database_connection import db_manager
from correct_order_processing import CorrectOrderProcessor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DealershipCAOTester:
    """Tests CAO processing for all dealerships"""
    
    def __init__(self):
        self.processor = CorrectOrderProcessor()
        self.test_results = []
        
    def get_all_dealerships(self):
        """Get list of all dealerships that have active scraper data"""
        try:
            query = """
                SELECT DISTINCT rvd.location as dealership_name, 
                       COUNT(*) as vehicle_count,
                       MAX(si.import_timestamp) as latest_import
                FROM raw_vehicle_data rvd
                JOIN scraper_imports si ON rvd.import_id = si.import_id
                WHERE si.status = 'active'
                GROUP BY rvd.location
                ORDER BY rvd.location
            """
            
            dealerships = db_manager.execute_query(query)
            logger.info(f"Found {len(dealerships)} dealerships with active scraper data")
            
            return dealerships
            
        except Exception as e:
            logger.error(f"Error getting dealerships: {e}")
            return []
    
    def get_dealership_config(self, dealership_name):
        """Get configuration for a specific dealership"""
        try:
            query = """
                SELECT * FROM dealership_configs 
                WHERE name = %s
            """
            
            config = db_manager.execute_query(query, (dealership_name,))
            return config[0] if config else None
            
        except Exception as e:
            logger.error(f"Error getting config for {dealership_name}: {e}")
            return None
    
    def test_cao_processing(self, dealership_name):
        """Test CAO processing for a specific dealership"""
        test_result = {
            'dealership': dealership_name,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'vehicle_count': 0,
            'new_vehicles': 0,
            'errors': [],
            'warnings': [],
            'config_issues': []
        }
        
        try:
            logger.info(f"Testing CAO processing for: {dealership_name}")
            
            # Check if dealership has configuration
            config = self.get_dealership_config(dealership_name)
            if not config:
                test_result['config_issues'].append("No dealership configuration found")
                test_result['warnings'].append("Dealership not configured for CAO processing")
                return test_result
            
            # Check vehicle type filters - filtering_rules can be JSON string or dict
            filtering_rules = config.get('filtering_rules')
            if filtering_rules:
                try:
                    import json
                    # Handle both string and dict formats
                    if isinstance(filtering_rules, str):
                        rules = json.loads(filtering_rules)
                    elif isinstance(filtering_rules, dict):
                        rules = filtering_rules
                    else:
                        rules = {}
                        test_result['config_issues'].append("Filtering_rules has unexpected format")
                    
                    vehicle_types = rules.get('vehicle_types', [])
                    if not vehicle_types:
                        test_result['config_issues'].append("No vehicle types configured in filtering_rules")
                except (json.JSONDecodeError, TypeError) as e:
                    test_result['config_issues'].append(f"Invalid filtering_rules format: {str(e)}")
            else:
                test_result['config_issues'].append("No filtering_rules configured")
            
            # Check for VIN log table
            vin_log_table = dealership_name.lower().replace(' ', '_').replace('.', '').replace("'", '') + '_vin_log'
            
            table_check = db_manager.execute_query("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            """, (vin_log_table,))
            
            if not table_check:
                test_result['config_issues'].append(f"VIN log table {vin_log_table} does not exist")
            
            # Attempt CAO processing
            try:
                result = self.processor.process_cao_order([dealership_name], skip_vin_logging=True)
                
                if result.get('success'):
                    test_result['success'] = True
                    test_result['vehicle_count'] = result.get('total_vehicle_count', 0)
                    test_result['new_vehicles'] = result.get('new_vehicle_count', 0)
                    
                    # Check for reasonable results
                    if test_result['vehicle_count'] == 0:
                        test_result['warnings'].append("No vehicles found in active import")
                    elif test_result['new_vehicles'] == 0:
                        test_result['warnings'].append("No new vehicles (all in VIN log already)")
                    elif test_result['new_vehicles'] > 1000:
                        test_result['warnings'].append(f"Unusually high new vehicle count: {test_result['new_vehicles']}")
                        
                else:
                    test_result['errors'].append(f"CAO processing failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as cao_error:
                test_result['errors'].append(f"CAO processing exception: {str(cao_error)}")
            
        except Exception as e:
            test_result['errors'].append(f"Test setup error: {str(e)}")
            logger.error(f"Error testing {dealership_name}: {e}")
        
        return test_result
    
    def test_all_dealerships(self):
        """Test CAO processing for all dealerships"""
        logger.info("Starting comprehensive CAO testing for all dealerships")
        
        dealerships = self.get_all_dealerships()
        if not dealerships:
            logger.error("No dealerships found with active scraper data")
            return
        
        total_dealerships = len(dealerships)
        successful_tests = 0
        failed_tests = 0
        
        for i, dealership in enumerate(dealerships, 1):
            dealership_name = dealership['dealership_name']
            vehicle_count = dealership['vehicle_count']
            
            print(f"\n[TEST {i:2d}/{total_dealerships}] {dealership_name} ({vehicle_count} vehicles)")
            print("=" * 60)
            
            test_result = self.test_cao_processing(dealership_name)
            self.test_results.append(test_result)
            
            # Print results
            if test_result['success']:
                successful_tests += 1
                status = "[SUCCESS]"
                print(f"{status} CAO processing completed")
                print(f"  - Total vehicles: {test_result['vehicle_count']}")
                print(f"  - New vehicles: {test_result['new_vehicles']}")
            else:
                failed_tests += 1
                status = "[FAILED]"
                print(f"{status} CAO processing failed")
            
            # Print warnings
            if test_result['warnings']:
                print("  Warnings:")
                for warning in test_result['warnings']:
                    print(f"    - {warning}")
            
            # Print errors
            if test_result['errors']:
                print("  Errors:")
                for error in test_result['errors']:
                    print(f"    - {error}")
            
            # Print config issues
            if test_result['config_issues']:
                print("  Configuration Issues:")
                for issue in test_result['config_issues']:
                    print(f"    - {issue}")
        
        # Summary
        print(f"\n{'='*60}")
        print("CAO PROCESSING TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total dealerships tested: {total_dealerships}")
        print(f"Successful tests: {successful_tests}")
        print(f"Failed tests: {failed_tests}")
        print(f"Success rate: {(successful_tests/total_dealerships*100):.1f}%")
        
        # Identify problem dealerships
        failed_dealerships = [r for r in self.test_results if not r['success']]
        if failed_dealerships:
            print(f"\nDEALERSHIPS REQUIRING ATTENTION:")
            for result in failed_dealerships:
                print(f"  - {result['dealership']}: {len(result['errors'])} errors, {len(result['config_issues'])} config issues")
        
        return self.test_results
    
    def save_results(self, filename=None):
        """Save test results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cao_test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.test_results, f, indent=2)
            
            logger.info(f"Test results saved to: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return None

def main():
    """Main test execution"""
    print("CAO Processing Test for All Dealerships")
    print("=" * 60)
    print("This script tests CAO processing across all dealerships")
    print("to identify configuration issues before production deployment.")
    print()
    
    tester = DealershipCAOTester()
    
    try:
        # Run comprehensive tests
        results = tester.test_all_dealerships()
        
        # Save results
        results_file = tester.save_results()
        
        print(f"\nTest completed. Results saved to: {results_file}")
        
        # Quick analysis
        failed_count = len([r for r in results if not r['success']])
        if failed_count > 0:
            print(f"\nACTION REQUIRED: {failed_count} dealerships need configuration fixes")
        else:
            print("\nEXCELLENT: All dealerships passed CAO processing tests!")
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"ERROR: Test execution failed - {e}")

if __name__ == "__main__":
    main()