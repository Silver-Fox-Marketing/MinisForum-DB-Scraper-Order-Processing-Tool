#!/usr/bin/env python3
"""
Comprehensive Order Processing Stress Test
==========================================

Bulletproof stress testing for the complete Silver Fox order processing system.
Tests all components under realistic and extreme load conditions.

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import os
import sys
import time
import json
import random
import threading
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

# Add the scripts directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database_connection import db_manager
    from order_processing_workflow import OrderProcessingWorkflow
    from real_scraper_integration import RealScraperIntegration
    print("[OK] All test modules imported successfully")
except ImportError as e:
    print(f"[ERROR] Critical import error: {e}")
    sys.exit(1)

class OrderProcessingStressTest:
    """Comprehensive stress testing for order processing system"""
    
    def __init__(self):
        self.workflow = OrderProcessingWorkflow()
        self.scraper_integration = RealScraperIntegration()
        self.test_results = {
            'start_time': datetime.now(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'errors': [],
            'performance_metrics': {},
            'database_performance': {},
            'concurrent_test_results': {},
            'stress_test_summary': {}
        }
        self.test_dealerships = [
            'BMW of West St. Louis',
            'Columbia Honda', 
            'Dave Sinclair Lincoln South',
            'Joe Machens Toyota',
            'Suntrup Ford Kirkwood'
        ]
        self.test_vins = [
            'WBA33DZ09KFG12345',
            'JHMCV6F30MC123456', 
            '3FADP4EJ8GM123456',
            'JTDKBRFU8L3123456',
            '1FTFW1ET0EKC12345'
        ]
        
    def log_test(self, test_name: str, success: bool, details: str = "", metrics: Dict = None):
        """Log test results"""
        self.test_results['tests_run'] += 1
        if success:
            self.test_results['tests_passed'] += 1
            status = "[PASS]"
        else:
            self.test_results['tests_failed'] += 1
            self.test_results['errors'].append(f"{test_name}: {details}")
            status = "[FAIL]"
        
        if metrics:
            self.test_results['performance_metrics'][test_name] = metrics
            
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
        if metrics:
            for key, value in metrics.items():
                print(f"    {key}: {value}")
        print()
    
    def test_database_connectivity(self) -> bool:
        """Test database connectivity and basic operations"""
        print("[TEST] Testing Database Connectivity...")
        
        try:
            # Test basic connection
            start_time = time.time()
            result = db_manager.execute_query("SELECT 1 as test")
            connection_time = time.time() - start_time
            
            if not result or result[0]['test'] != 1:
                self.log_test("Database Basic Connection", False, "Query returned unexpected result")
                return False
            
            # Test order processing tables exist
            required_tables = ['vin_history', 'order_schedule', 'daily_scrape_logs', 'dealership_configs']
            for table in required_tables:
                start_time = time.time()
                result = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {table}")
                query_time = time.time() - start_time
                
                if result is None:
                    self.log_test(f"Table Check: {table}", False, "Table not accessible")
                    return False
                    
                self.log_test(f"Table Check: {table}", True, 
                            f"Rows: {result[0]['count']}", 
                            {'query_time_ms': round(query_time * 1000, 2)})
            
            self.log_test("Database Basic Connection", True, 
                         "All connections successful", 
                         {'connection_time_ms': round(connection_time * 1000, 2)})
            return True
            
        except Exception as e:
            self.log_test("Database Basic Connection", False, str(e))
            return False
    
    def test_order_processing_workflow_init(self) -> bool:
        """Test OrderProcessingWorkflow initialization"""
        print("🔄 Testing Order Processing Workflow Init...")
        
        try:
            # Test workflow initialization
            workflow = OrderProcessingWorkflow()
            
            # Test getting today's schedule
            start_time = time.time()
            schedule = workflow.get_todays_cao_schedule()
            schedule_time = time.time() - start_time
            
            self.log_test("Order Workflow Init", True, 
                         f"Schedule entries: {len(schedule)}", 
                         {'schedule_query_time_ms': round(schedule_time * 1000, 2)})
            return True
            
        except Exception as e:
            self.log_test("Order Workflow Init", False, str(e))
            return False
    
    def test_cao_order_processing(self) -> bool:
        """Test CAO order processing with real dealership"""
        print("🔄 Testing CAO Order Processing...")
        
        success_count = 0
        total_tests = len(self.test_dealerships)
        
        for dealership in self.test_dealerships:
            try:
                print(f"   Testing CAO for: {dealership}")
                start_time = time.time()
                
                # Process CAO order
                result = self.workflow.process_cao_order(dealership, ['new', 'used'])
                processing_time = time.time() - start_time
                
                if result.get('success'):
                    success_count += 1
                    self.log_test(f"CAO Processing: {dealership}", True,
                                f"Vehicles: {result.get('new_vehicles', 0)}, QR: {result.get('qr_codes_generated', 0)}",
                                {'processing_time_ms': round(processing_time * 1000, 2)})
                else:
                    self.log_test(f"CAO Processing: {dealership}", False, 
                                result.get('error', 'Unknown error'))
                    
            except Exception as e:
                self.log_test(f"CAO Processing: {dealership}", False, str(e))
        
        overall_success = success_count >= (total_tests * 0.6)  # 60% success rate minimum
        self.log_test("CAO Processing Overall", overall_success,
                     f"Success rate: {success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)")
        
        return overall_success
    
    def test_list_order_processing(self) -> bool:
        """Test list-based order processing with VIN lists"""
        print("🔄 Testing List Order Processing...")
        
        success_count = 0
        
        for i, dealership in enumerate(self.test_dealerships[:3]):  # Test first 3 dealerships
            try:
                print(f"   Testing List Order for: {dealership}")
                
                # Create test VIN list (2-3 VINs per test)
                test_vins = self.test_vins[i:i+3]
                
                start_time = time.time()
                result = self.workflow.process_list_order(dealership, test_vins)
                processing_time = time.time() - start_time
                
                if result.get('success'):
                    success_count += 1
                    self.log_test(f"List Processing: {dealership}", True,
                                f"Found: {result.get('found_vehicles', 0)}/{len(test_vins)} VINs",
                                {'processing_time_ms': round(processing_time * 1000, 2)})
                else:
                    self.log_test(f"List Processing: {dealership}", False,
                                result.get('error', 'Unknown error'))
                    
            except Exception as e:
                self.log_test(f"List Processing: {dealership}", False, str(e))
        
        overall_success = success_count >= 2  # At least 2 out of 3 should succeed
        self.log_test("List Processing Overall", overall_success,
                     f"Success rate: {success_count}/3")
        
        return overall_success
    
    def test_vin_comparison_logic(self) -> bool:
        """Test VIN comparison and history tracking"""
        print("🔄 Testing VIN Comparison Logic...")
        
        try:
            dealership = self.test_dealerships[0]
            
            # Test with known VINs
            current_vins = self.test_vins[:3]
            
            start_time = time.time()
            new_vins, removed_vins = self.workflow.compare_vin_lists(dealership, current_vins)
            comparison_time = time.time() - start_time
            
            # Record these VINs in history
            self.workflow.record_vin_history(dealership, current_vins)
            
            # Test again with modified list (add one, remove one)
            modified_vins = current_vins[1:] + ['TESTVIN123456789ABC']
            
            start_time = time.time()
            new_vins_2, removed_vins_2 = self.workflow.compare_vin_lists(dealership, modified_vins)
            comparison_time_2 = time.time() - start_time
            
            # Should detect 1 new and 1 removed
            expected_new = 1
            expected_removed = 1
            
            success = (len(new_vins_2) == expected_new and len(removed_vins_2) == expected_removed)
            
            self.log_test("VIN Comparison Logic", success,
                         f"New: {len(new_vins_2)}/{expected_new}, Removed: {len(removed_vins_2)}/{expected_removed}",
                         {
                             'first_comparison_ms': round(comparison_time * 1000, 2),
                             'second_comparison_ms': round(comparison_time_2 * 1000, 2)
                         })
            
            return success
            
        except Exception as e:
            self.log_test("VIN Comparison Logic", False, str(e))
            return False
    
    def test_qr_generation_system(self) -> bool:
        """Test QR code generation system"""
        print("🔄 Testing QR Code Generation...")
        
        try:
            # Create test vehicle data
            test_vehicles = [
                {
                    'vin': 'TESTVIN123456789ABC',
                    'url': 'https://example.com/vehicle/1',
                    'year': '2024',
                    'make': 'Test',
                    'model': 'Vehicle'
                }
            ]
            
            dealership = 'Test Dealership'
            
            start_time = time.time()
            result = self.workflow.generate_qr_codes(test_vehicles, dealership)
            generation_time = time.time() - start_time
            
            success = result.get('success', False) and result.get('generated_count', 0) > 0
            
            # Verify QR folder exists
            qr_folder = result.get('qr_folder', '')
            folder_exists = os.path.exists(qr_folder) if qr_folder else False
            
            self.log_test("QR Code Generation", success and folder_exists,
                         f"Generated: {result.get('generated_count', 0)}, Folder: {folder_exists}",
                         {'generation_time_ms': round(generation_time * 1000, 2)})
            
            return success and folder_exists
            
        except Exception as e:
            self.log_test("QR Code Generation", False, str(e))
            return False
    
    def test_concurrent_processing(self) -> bool:
        """Test concurrent order processing"""
        print("🔄 Testing Concurrent Processing...")
        
        def process_concurrent_order(dealership_index):
            """Process order in thread"""
            try:
                dealership = self.test_dealerships[dealership_index % len(self.test_dealerships)]
                start_time = time.time()
                
                # Alternate between CAO and List orders
                if dealership_index % 2 == 0:
                    result = self.workflow.process_cao_order(dealership, ['new'])
                    order_type = 'CAO'
                else:
                    test_vins = [self.test_vins[dealership_index % len(self.test_vins)]]
                    result = self.workflow.process_list_order(dealership, test_vins)
                    order_type = 'List'
                
                processing_time = time.time() - start_time
                
                return {
                    'thread_id': threading.current_thread().ident,
                    'dealership': dealership,
                    'order_type': order_type,
                    'success': result.get('success', False),
                    'processing_time': processing_time,
                    'error': result.get('error') if not result.get('success') else None
                }
                
            except Exception as e:
                return {
                    'thread_id': threading.current_thread().ident,
                    'dealership': f'Index_{dealership_index}',
                    'success': False,
                    'error': str(e),
                    'processing_time': 0
                }
        
        # Run 5 concurrent orders
        concurrent_count = 5
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_count) as executor:
            futures = [executor.submit(process_concurrent_order, i) for i in range(concurrent_count)]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        success_rate = len(successful) / concurrent_count
        avg_processing_time = sum(r['processing_time'] for r in successful) / len(successful) if successful else 0
        
        # Store detailed results
        self.test_results['concurrent_test_results'] = {
            'total_orders': concurrent_count,
            'successful_orders': len(successful),
            'failed_orders': len(failed),
            'success_rate': success_rate,
            'total_time': total_time,
            'average_processing_time': avg_processing_time,
            'detailed_results': results
        }
        
        # Consider success if 80% or more succeed
        overall_success = success_rate >= 0.8
        
        self.log_test("Concurrent Processing", overall_success,
                     f"Success: {len(successful)}/{concurrent_count} ({success_rate*100:.1f}%)",
                     {
                         'total_time_s': round(total_time, 2),
                         'avg_processing_time_s': round(avg_processing_time, 2)
                     })
        
        return overall_success
    
    def test_database_performance_under_load(self) -> bool:
        """Test database performance under load"""
        print("🔄 Testing Database Performance Under Load...")
        
        def database_operation(operation_id):
            """Perform database operation"""
            try:
                start_time = time.time()
                
                # Mix of different database operations
                operations = [
                    lambda: db_manager.execute_query("SELECT COUNT(*) FROM raw_vehicle_data"),
                    lambda: db_manager.execute_query("SELECT * FROM dealership_configs LIMIT 5"),
                    lambda: db_manager.execute_query("SELECT * FROM vin_history WHERE dealership_name = %s LIMIT 10", ('BMW of West St. Louis',)),
                    lambda: db_manager.execute_query("INSERT INTO vin_history (dealership_name, vin, order_date) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", 
                                                   (f'Test_Dealership_{operation_id}', f'TESTVIN{operation_id:06d}ABC', datetime.now().date()))
                ]
                
                operation = operations[operation_id % len(operations)]
                result = operation()
                
                operation_time = time.time() - start_time
                
                return {
                    'operation_id': operation_id,
                    'success': result is not None,
                    'operation_time': operation_time,
                    'operation_type': operation.__name__ if hasattr(operation, '__name__') else f'op_{operation_id % len(operations)}'
                }
                
            except Exception as e:
                return {
                    'operation_id': operation_id,
                    'success': False,
                    'error': str(e),
                    'operation_time': 0
                }
        
        # Run 20 concurrent database operations
        load_test_count = 20
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(database_operation, i) for i in range(load_test_count)]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Analyze performance
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        if successful:
            avg_operation_time = sum(r['operation_time'] for r in successful) / len(successful)
            max_operation_time = max(r['operation_time'] for r in successful)
            min_operation_time = min(r['operation_time'] for r in successful)
        else:
            avg_operation_time = max_operation_time = min_operation_time = 0
        
        success_rate = len(successful) / load_test_count
        
        # Store performance metrics
        self.test_results['database_performance'] = {
            'total_operations': load_test_count,
            'successful_operations': len(successful),
            'failed_operations': len(failed),
            'success_rate': success_rate,
            'total_time': total_time,
            'avg_operation_time': avg_operation_time,
            'max_operation_time': max_operation_time,
            'min_operation_time': min_operation_time,
            'operations_per_second': load_test_count / total_time
        }
        
        # Consider success if 95% or more succeed and average time < 1 second
        overall_success = success_rate >= 0.95 and avg_operation_time < 1.0
        
        self.log_test("Database Performance Under Load", overall_success,
                     f"Success: {len(successful)}/{load_test_count} ({success_rate*100:.1f}%)",
                     {
                         'avg_time_ms': round(avg_operation_time * 1000, 2),
                         'max_time_ms': round(max_operation_time * 1000, 2),
                         'ops_per_sec': round(load_test_count / total_time, 2)
                     })
        
        return overall_success
    
    def test_error_handling_recovery(self) -> bool:
        """Test error handling and recovery mechanisms"""
        print("🔄 Testing Error Handling and Recovery...")
        
        test_scenarios = [
            # Invalid dealership name
            lambda: self.workflow.process_cao_order("INVALID_DEALERSHIP_NAME", ['new']),
            # Empty VIN list
            lambda: self.workflow.process_list_order(self.test_dealerships[0], []),
            # Invalid VIN format
            lambda: self.workflow.process_list_order(self.test_dealerships[0], ['INVALID_VIN', 'ALSO_INVALID']),
            # Malformed vehicle types
            lambda: self.workflow.process_cao_order(self.test_dealerships[0], ['invalid_type', 'another_invalid']),
        ]
        
        successful_error_handling = 0
        
        for i, test_scenario in enumerate(test_scenarios):
            try:
                print(f"   Testing error scenario {i+1}...")
                start_time = time.time()
                
                result = test_scenario()
                handling_time = time.time() - start_time
                
                # Good error handling should return a structured error, not crash
                if isinstance(result, dict) and 'success' in result and not result['success']:
                    successful_error_handling += 1
                    self.log_test(f"Error Handling Scenario {i+1}", True,
                                f"Graceful error: {result.get('error', 'Unknown')[:50]}...",
                                {'handling_time_ms': round(handling_time * 1000, 2)})
                else:
                    self.log_test(f"Error Handling Scenario {i+1}", False,
                                "Did not handle error gracefully")
                    
            except Exception as e:
                # Unhandled exceptions are bad
                self.log_test(f"Error Handling Scenario {i+1}", False,
                            f"Unhandled exception: {str(e)[:50]}...")
        
        overall_success = successful_error_handling >= len(test_scenarios) * 0.75  # 75% should handle errors gracefully
        
        self.log_test("Error Handling Overall", overall_success,
                     f"Graceful handling: {successful_error_handling}/{len(test_scenarios)}")
        
        return overall_success
    
    def run_comprehensive_stress_test(self) -> Dict[str, Any]:
        """Run complete stress test suite"""
        print("🚀 STARTING COMPREHENSIVE STRESS TEST")
        print("=" * 60)
        
        # Test sequence - order matters for dependencies
        test_sequence = [
            ("Database Connectivity", self.test_database_connectivity),
            ("Workflow Initialization", self.test_order_processing_workflow_init),
            ("CAO Order Processing", self.test_cao_order_processing),
            ("List Order Processing", self.test_list_order_processing),
            ("VIN Comparison Logic", self.test_vin_comparison_logic),
            ("QR Generation System", self.test_qr_generation_system),
            ("Concurrent Processing", self.test_concurrent_processing),
            ("Database Performance", self.test_database_performance_under_load),
            ("Error Handling", self.test_error_handling_recovery)
        ]
        
        for test_name, test_function in test_sequence:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                test_function()
            except Exception as e:
                self.log_test(test_name, False, f"Test framework error: {str(e)}")
                print(f"❌ CRITICAL: Test framework error in {test_name}")
                print(f"Error: {e}")
                traceback.print_exc()
        
        # Calculate final results
        self.test_results['end_time'] = datetime.now()
        self.test_results['total_duration'] = (self.test_results['end_time'] - self.test_results['start_time']).total_seconds()
        self.test_results['success_rate'] = (self.test_results['tests_passed'] / self.test_results['tests_run']) * 100 if self.test_results['tests_run'] > 0 else 0
        
        # Generate summary
        self.generate_stress_test_summary()
        
        return self.test_results
    
    def generate_stress_test_summary(self):
        """Generate comprehensive test summary"""
        summary = {
            'overall_status': 'PASS' if self.test_results['success_rate'] >= 80 else 'FAIL',
            'total_tests': self.test_results['tests_run'],
            'passed_tests': self.test_results['tests_passed'],
            'failed_tests': self.test_results['tests_failed'],
            'success_rate': round(self.test_results['success_rate'], 1),
            'total_duration': round(self.test_results['total_duration'], 2),
            'critical_failures': len([e for e in self.test_results['errors'] if 'Database' in e or 'Critical' in e]),
            'performance_summary': {
                'database_ops_per_sec': self.test_results.get('database_performance', {}).get('operations_per_second', 0),
                'concurrent_success_rate': self.test_results.get('concurrent_test_results', {}).get('success_rate', 0) * 100,
                'avg_processing_time': round(self.test_results.get('concurrent_test_results', {}).get('average_processing_time', 0), 2)
            }
        }
        
        self.test_results['stress_test_summary'] = summary
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 STRESS TEST SUMMARY")
        print("=" * 60)
        print(f"Overall Status: {'🎉 PASS' if summary['overall_status'] == 'PASS' else '💥 FAIL'}")
        print(f"Tests Run: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']} ({summary['success_rate']}%)")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Duration: {summary['total_duration']} seconds")
        print(f"Critical Failures: {summary['critical_failures']}")
        
        print(f"\n📊 Performance Metrics:")
        print(f"Database Operations/sec: {summary['performance_summary']['database_ops_per_sec']:.1f}")
        print(f"Concurrent Success Rate: {summary['performance_summary']['concurrent_success_rate']:.1f}%")
        print(f"Avg Processing Time: {summary['performance_summary']['avg_processing_time']}s")
        
        if self.test_results['errors']:
            print(f"\n❌ Failed Tests:")
            for error in self.test_results['errors']:
                print(f"   - {error}")
        
        print("\n" + "=" * 60)
        
        # Save detailed results to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"stress_test_results_{timestamp}.json"
        
        try:
            with open(results_file, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            print(f"📁 Detailed results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️ Could not save results file: {e}")

def main():
    """Run the comprehensive stress test"""
    print("🔥 SILVER FOX ORDER PROCESSING STRESS TEST")
    print("Bulletproof testing of the complete system")
    print("=" * 60)
    
    tester = OrderProcessingStressTest()
    results = tester.run_comprehensive_stress_test()
    
    # Return exit code based on results
    success_rate = results.get('success_rate', 0)
    critical_failures = len([e for e in results.get('errors', []) if 'Database' in e or 'Critical' in e])
    
    if success_rate >= 80 and critical_failures == 0:
        print("🎉 STRESS TEST COMPLETED - SYSTEM IS BULLETPROOF!")
        return 0
    else:
        print("💥 STRESS TEST FAILED - SYSTEM NEEDS ATTENTION")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)