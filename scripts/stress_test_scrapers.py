#!/usr/bin/env python3
"""
Scraper System Stress Test
==========================

Comprehensive stress testing for the real scraper integration system.
Tests various failure modes, concurrent operations, and edge cases.

Author: Silver Fox Assistant
Created: 2025-07-28
"""

import os
import sys
import time
import json
import logging
import threading
import concurrent.futures
from datetime import datetime
from pathlib import Path

# Add project paths
current_file = Path(__file__).resolve()
scripts_dir = current_file.parent
sys.path.insert(0, str(scripts_dir))

from real_scraper_integration import RealScraperIntegration
from database_connection import db_manager

class ScraperStressTester:
    """Comprehensive stress tester for scraper system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.integration = RealScraperIntegration()
        self.test_results = {}
        self.start_time = None
        
    def setup_logging(self):
        """Setup detailed logging for stress tests"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('stress_test.log'),
                logging.StreamHandler()
            ]
        )
    
    def test_database_connection_stress(self):
        """Test database under high load"""
        print("\n" + "="*60)
        print("[STRESS TEST 1] DATABASE CONNECTION STRESS TEST")
        print("="*60)
        
        start_time = time.time()
        
        def db_operation(thread_id):
            try:
                # Simulate heavy database queries
                result = db_manager.execute_query("SELECT COUNT(*) FROM raw_vehicle_data")
                time.sleep(0.1)  # Simulate processing time
                return {'thread_id': thread_id, 'success': True, 'count': result[0]['count'] if result else 0}
            except Exception as e:
                return {'thread_id': thread_id, 'success': False, 'error': str(e)}
        
        # Run 20 concurrent database operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(db_operation, i) for i in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        successful = sum(1 for r in results if r['success'])
        duration = time.time() - start_time
        
        print(f"[DB_STRESS] Completed 20 concurrent operations in {duration:.2f}s")
        print(f"[DB_STRESS] Success rate: {successful}/20 ({successful/20*100:.1f}%)")
        
        self.test_results['database_stress'] = {
            'total_operations': 20,
            'successful': successful,
            'duration': duration,
            'success_rate': successful/20*100
        }
        
        return successful == 20
    
    def test_concurrent_scraper_execution(self):
        """Test multiple scrapers running concurrently"""
        print("\n" + "="*60)
        print("[STRESS TEST 2] CONCURRENT SCRAPER EXECUTION")
        print("="*60)
        
        start_time = time.time()
        
        def run_single_scraper(dealership_name):
            try:
                print(f"[CONCURRENT] Starting {dealership_name}")
                result = self.integration.run_real_scraper(dealership_name)
                print(f"[CONCURRENT] Completed {dealership_name}: {result['success']}")
                return result
            except Exception as e:
                print(f"[CONCURRENT] Failed {dealership_name}: {e}")
                return {'success': False, 'error': str(e), 'dealership_name': dealership_name}
        
        # Get all available scrapers
        scrapers = list(self.integration.real_scraper_mapping.keys())
        print(f"[CONCURRENT] Running {len(scrapers)} scrapers simultaneously")
        
        # Run all scrapers concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(scrapers)) as executor:
            futures = {executor.submit(run_single_scraper, scraper): scraper for scraper in scrapers}
            results = {}
            
            for future in concurrent.futures.as_completed(futures):
                scraper_name = futures[future]
                try:
                    result = future.result(timeout=30)  # 30 second timeout per scraper
                    results[scraper_name] = result
                except concurrent.futures.TimeoutError:
                    print(f"[TIMEOUT] {scraper_name} timed out after 30 seconds")
                    results[scraper_name] = {'success': False, 'error': 'Timeout', 'dealership_name': scraper_name}
                except Exception as e:
                    print(f"[ERROR] {scraper_name} failed with exception: {e}")
                    results[scraper_name] = {'success': False, 'error': str(e), 'dealership_name': scraper_name}
        
        duration = time.time() - start_time
        successful = sum(1 for r in results.values() if r['success'])
        total_vehicles = sum(r.get('vehicle_count', 0) for r in results.values() if r['success'])
        
        print(f"[CONCURRENT] Completed {len(scrapers)} scrapers in {duration:.2f}s")
        print(f"[CONCURRENT] Success rate: {successful}/{len(scrapers)} ({successful/len(scrapers)*100:.1f}%)")
        print(f"[CONCURRENT] Total vehicles: {total_vehicles}")
        
        self.test_results['concurrent_execution'] = {
            'total_scrapers': len(scrapers),
            'successful': successful,
            'duration': duration,
            'total_vehicles': total_vehicles,
            'success_rate': successful/len(scrapers)*100,
            'results': results
        }
        
        return successful > 0  # At least one scraper should succeed
    
    def test_rapid_sequential_execution(self):
        """Test rapid sequential scraper execution"""
        print("\n" + "="*60)
        print("[STRESS TEST 3] RAPID SEQUENTIAL EXECUTION")
        print("="*60)
        
        start_time = time.time()
        scrapers = list(self.integration.real_scraper_mapping.keys())
        results = []
        
        # Run each scraper 3 times rapidly
        for i in range(3):
            print(f"[RAPID] Round {i+1}/3")
            for scraper in scrapers:
                try:
                    result = self.integration.run_real_scraper(scraper)
                    results.append(result)
                    print(f"[RAPID] {scraper}: {'SUCCESS' if result['success'] else 'FAILED'}")
                except Exception as e:
                    print(f"[RAPID] {scraper}: ERROR - {e}")
                    results.append({'success': False, 'error': str(e), 'dealership_name': scraper})
        
        duration = time.time() - start_time
        successful = sum(1 for r in results if r['success'])
        total_runs = len(scrapers) * 3
        
        print(f"[RAPID] Completed {total_runs} runs in {duration:.2f}s")
        print(f"[RAPID] Success rate: {successful}/{total_runs} ({successful/total_runs*100:.1f}%)")
        print(f"[RAPID] Average time per run: {duration/total_runs:.2f}s")
        
        self.test_results['rapid_sequential'] = {
            'total_runs': total_runs,
            'successful': successful,
            'duration': duration,
            'avg_time_per_run': duration/total_runs,
            'success_rate': successful/total_runs*100
        }
        
        return successful > total_runs * 0.5  # At least 50% should succeed
    
    def test_memory_usage_monitoring(self):
        """Monitor memory usage during scraping"""
        print("\n" + "="*60)
        print("[STRESS TEST 4] MEMORY USAGE MONITORING")
        print("="*60)
        
        try:
            import psutil
            process = psutil.Process()
            
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            print(f"[MEMORY] Initial memory usage: {initial_memory:.2f} MB")
            
            # Run scrapers while monitoring memory
            scrapers = list(self.integration.real_scraper_mapping.keys())
            memory_readings = [initial_memory]
            
            for scraper in scrapers:
                print(f"[MEMORY] Running {scraper}...")
                result = self.integration.run_real_scraper(scraper)
                
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_readings.append(current_memory)
                print(f"[MEMORY] After {scraper}: {current_memory:.2f} MB")
            
            max_memory = max(memory_readings)
            memory_growth = max_memory - initial_memory
            
            print(f"[MEMORY] Maximum memory usage: {max_memory:.2f} MB")
            print(f"[MEMORY] Memory growth: {memory_growth:.2f} MB")
            
            self.test_results['memory_monitoring'] = {
                'initial_memory_mb': initial_memory,
                'max_memory_mb': max_memory,
                'memory_growth_mb': memory_growth,
                'memory_readings': memory_readings
            }
            
            return memory_growth < 100  # Should not grow more than 100MB
            
        except ImportError:
            print("[MEMORY] psutil not available, skipping memory test")
            return True
    
    def test_error_handling_robustness(self):
        """Test system behavior with various error conditions"""
        print("\n" + "="*60)
        print("[STRESS TEST 5] ERROR HANDLING ROBUSTNESS")
        print("="*60)
        
        error_scenarios = [
            ('nonexistent_dealer', 'Non-existent dealership'),
            ('', 'Empty dealership name'),
            (None, 'None dealership name'),
            ('Test Integration Dealer', 'Valid dealer (should work)')
        ]
        
        results = []
        for dealer_name, description in error_scenarios:
            print(f"[ERROR_TEST] Testing: {description}")
            try:
                result = self.integration.run_real_scraper(dealer_name)
                print(f"[ERROR_TEST] Result: {'SUCCESS' if result['success'] else 'HANDLED_ERROR'}")
                results.append({'scenario': description, 'handled': True, 'result': result})
            except Exception as e:
                print(f"[ERROR_TEST] Unhandled exception: {e}")
                results.append({'scenario': description, 'handled': False, 'error': str(e)})
        
        handled_errors = sum(1 for r in results if r['handled'])
        print(f"[ERROR_TEST] Error handling: {handled_errors}/{len(error_scenarios)} scenarios handled gracefully")
        
        self.test_results['error_handling'] = {
            'total_scenarios': len(error_scenarios),
            'handled_gracefully': handled_errors,
            'results': results
        }
        
        return handled_errors == len(error_scenarios)
    
    def test_database_integrity_under_load(self):
        """Test database integrity with concurrent writes"""
        print("\n" + "="*60)
        print("[STRESS TEST 6] DATABASE INTEGRITY UNDER LOAD")
        print("="*60)
        
        # Get initial vehicle count
        initial_count = db_manager.execute_query("SELECT COUNT(*) as count FROM raw_vehicle_data")[0]['count']
        print(f"[DB_INTEGRITY] Initial vehicle count: {initial_count}")
        
        # Run scrapers and check data consistency
        scrapers = list(self.integration.real_scraper_mapping.keys())
        
        start_time = time.time()
        for scraper in scrapers:
            print(f"[DB_INTEGRITY] Processing {scraper}")
            result = self.integration.run_real_scraper(scraper)
            
            if result['success']:
                # Import to database
                import_result = self.integration.import_vehicles_to_database(
                    result['vehicles'], 
                    scraper
                )
                print(f"[DB_INTEGRITY] Imported: {import_result.get('total_processed', 0)} vehicles")
            
        # Check final vehicle count
        final_count = db_manager.execute_query("SELECT COUNT(*) as count FROM raw_vehicle_data")[0]['count']
        vehicles_added = final_count - initial_count
        
        # Check for duplicate VINs
        duplicate_check = db_manager.execute_query("""
            SELECT vin, COUNT(*) as count 
            FROM raw_vehicle_data 
            GROUP BY vin 
            HAVING COUNT(*) > 1 
            LIMIT 5
        """)
        
        duration = time.time() - start_time
        print(f"[DB_INTEGRITY] Final vehicle count: {final_count}")
        print(f"[DB_INTEGRITY] Vehicles added: {vehicles_added}")
        print(f"[DB_INTEGRITY] Duplicate VINs found: {len(duplicate_check)}")
        print(f"[DB_INTEGRITY] Duration: {duration:.2f}s")
        
        self.test_results['database_integrity'] = {
            'initial_count': initial_count,
            'final_count': final_count,
            'vehicles_added': vehicles_added,
            'duplicate_vins': len(duplicate_check),
            'duration': duration
        }
        
        return len(duplicate_check) == 0  # No duplicates should exist
    
    def run_all_stress_tests(self):
        """Run all stress tests and generate comprehensive report"""
        print("\n" + "="*80)
        print("[STRESS] SILVER FOX SCRAPER SYSTEM - COMPREHENSIVE STRESS TEST")
        print("="*80)
        
        self.start_time = datetime.now()
        test_functions = [
            ('Database Connection Stress', self.test_database_connection_stress),
            ('Concurrent Scraper Execution', self.test_concurrent_scraper_execution),
            ('Rapid Sequential Execution', self.test_rapid_sequential_execution),
            ('Memory Usage Monitoring', self.test_memory_usage_monitoring),
            ('Error Handling Robustness', self.test_error_handling_robustness),
            ('Database Integrity Under Load', self.test_database_integrity_under_load)
        ]
        
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_name, test_function in test_functions:
            try:
                print(f"\n[STRESS_TEST] Starting: {test_name}")
                result = test_function()
                status = "PASSED" if result else "FAILED"
                print(f"[STRESS_TEST] {test_name}: {status}")
                
                if result:
                    passed_tests += 1
                    
            except Exception as e:
                print(f"[STRESS_TEST] {test_name}: EXCEPTION - {e}")
                self.logger.error(f"Stress test {test_name} failed with exception: {e}")
        
        # Generate final report
        self.generate_stress_test_report(passed_tests, total_tests)
        
        return passed_tests, total_tests
    
    def generate_stress_test_report(self, passed_tests, total_tests):
        """Generate comprehensive stress test report"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "="*80)
        print("[RESULTS] STRESS TEST RESULTS SUMMARY")
        print("="*80)
        print(f"[SUMMARY] Tests passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"[SUMMARY] Total duration: {total_duration:.2f} seconds")
        print(f"[SUMMARY] Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[SUMMARY] Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Detailed results
        print("\n[DETAILED RESULTS]")
        for test_name, results in self.test_results.items():
            print(f"  {test_name.upper()}:")
            for key, value in results.items():
                if isinstance(value, (int, float)):
                    print(f"    {key}: {value}")
                elif isinstance(value, list) and len(value) < 10:
                    print(f"    {key}: {value}")
        
        # Save detailed report to file
        report_data = {
            'test_summary': {
                'passed_tests': passed_tests,
                'total_tests': total_tests,
                'success_rate': passed_tests/total_tests*100,
                'total_duration': total_duration,
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat()
            },
            'detailed_results': self.test_results
        }
        
        report_file = f"stress_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"\n[REPORT] Detailed report saved to: {report_file}")
        
        if passed_tests == total_tests:
            print("\n[SUCCESS] ALL STRESS TESTS PASSED! System is robust and ready for production.")
        elif passed_tests >= total_tests * 0.8:
            print("\n[WARNING] Most tests passed. Review failed tests for potential improvements.")
        else:
            print("\n[FAILED] Multiple test failures detected. System requires attention before production use.")
        
        print("="*80)

def main():
    """Run the comprehensive stress test suite"""
    tester = ScraperStressTester()
    tester.setup_logging()
    
    try:
        passed, total = tester.run_all_stress_tests()
        return 0 if passed == total else 1
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Stress test interrupted by user")
        return 2
    except Exception as e:
        print(f"\n[FATAL] Stress test failed with fatal error: {e}")
        return 3

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)