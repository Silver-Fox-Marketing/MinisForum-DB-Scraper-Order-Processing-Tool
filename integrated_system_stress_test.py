#!/usr/bin/env python3
"""
Integrated System Stress Test
============================

Comprehensive test of the integrated order processing system:
1. Backend CorrectOrderProcessor functionality
2. Web interface API endpoints
3. Database connectivity and data integrity
4. File generation and download system
5. Dealership name mapping

Author: Silver Fox Assistant
Created: 2025-07-30
"""

import sys
import os
import json
import time
import requests
import threading
from pathlib import Path
from typing import Dict, List, Any

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "scripts"))
sys.path.insert(0, str(project_root / "web_gui"))

# Import modules
from scripts.database_connection import db_manager
from scripts.correct_order_processing import CorrectOrderProcessor

class IntegratedSystemStressTester:
    """Comprehensive stress test for the integrated system"""
    
    def __init__(self):
        self.results = {
            'backend_tests': {},
            'web_interface_tests': {},
            'integration_tests': {},
            'performance_tests': {},
            'errors': []
        }
        self.web_server_url = "http://127.0.0.1:5000"
        self.order_processor = None
        
    def run_all_tests(self):
        """Run comprehensive stress test suite"""
        print("[SYSTEM] Starting Integrated System Stress Test")
        print("=" * 60)
        
        # Test 1: Backend System Tests
        print("\n[1] BACKEND SYSTEM TESTS")
        self.test_database_connectivity()
        self.test_dealership_data_availability()
        self.test_order_processor_initialization()
        self.test_dealership_name_mapping()
        self.test_order_processing_logic()
        
        # Test 2: Web Interface Tests  
        print("\n[2] WEB INTERFACE TESTS")
        self.test_web_server_connectivity()
        self.test_api_endpoints()
        self.test_dealership_api()
        self.test_order_processing_api()
        
        # Test 3: Integration Tests
        print("\n[3] INTEGRATION TESTS")
        self.test_end_to_end_processing()
        self.test_file_generation_and_download()
        
        # Test 4: Performance Tests
        print("\n[4] PERFORMANCE TESTS")
        self.test_concurrent_processing()
        
        # Print comprehensive results
        self.print_test_results()
        
    def test_database_connectivity(self):
        """Test database connectivity and basic queries"""
        try:
            print("  [TEST] Testing database connectivity...")
            
            # Test basic connection
            result = db_manager.execute_query("SELECT 1 as test")
            assert result[0]['test'] == 1
            
            # Test dealership configs table
            configs = db_manager.execute_query("SELECT COUNT(*) as count FROM dealership_configs")
            config_count = configs[0]['count']
            
            # Test raw vehicle data
            vehicles = db_manager.execute_query("SELECT COUNT(*) as count FROM raw_vehicle_data")
            vehicle_count = vehicles[0]['count']
            
            self.results['backend_tests']['database_connectivity'] = {
                'status': 'PASS',
                'dealership_configs': config_count,
                'total_vehicles': vehicle_count
            }
            print(f"    [PASS] Database connected - {config_count} configs, {vehicle_count} vehicles")
            
        except Exception as e:
            self.results['backend_tests']['database_connectivity'] = {'status': 'FAIL', 'error': str(e)}
            self.results['errors'].append(f"Database connectivity: {e}")
            print(f"    [FAIL] Database connectivity failed: {e}")
    
    def test_dealership_data_availability(self):
        """Test availability of dealership data"""
        try:
            print("  🏢 Testing dealership data availability...")
            
            # Check for our key dealerships
            key_dealerships = ['Dave Sinclair Lincoln', 'BMW of West St. Louis', 'Columbia Honda']
            available_dealerships = {}
            
            for dealership in key_dealerships:
                result = db_manager.execute_query(
                    "SELECT COUNT(*) as count FROM raw_vehicle_data WHERE dealer_name = %s",
                    (dealership,)
                )
                count = result[0]['count']
                available_dealerships[dealership] = count
                
            self.results['backend_tests']['dealership_data'] = {
                'status': 'PASS' if all(count > 0 for count in available_dealerships.values()) else 'PARTIAL',
                'dealerships': available_dealerships
            }
            
            for dealer, count in available_dealerships.items():
                status = "[PASS]" if count > 0 else "[WARN]"
                print(f"    {status} {dealer}: {count} vehicles")
                
        except Exception as e:
            self.results['backend_tests']['dealership_data'] = {'status': 'FAIL', 'error': str(e)}
            self.results['errors'].append(f"Dealership data: {e}")
            print(f"    [FAIL] Dealership data test failed: {e}")
    
    def test_order_processor_initialization(self):
        """Test CorrectOrderProcessor initialization"""
        try:
            print("  ⚙️ Testing CorrectOrderProcessor initialization...")
            
            self.order_processor = CorrectOrderProcessor()
            
            # Check if dealership mapping exists
            assert hasattr(self.order_processor, 'dealership_name_mapping')
            assert 'Dave Sinclair Lincoln South' in self.order_processor.dealership_name_mapping
            
            # Check output directory
            assert self.order_processor.output_base.exists()
            
            self.results['backend_tests']['order_processor_init'] = {
                'status': 'PASS',
                'mapping_count': len(self.order_processor.dealership_name_mapping),
                'output_path': str(self.order_processor.output_base)
            }
            print(f"    [PASS] CorrectOrderProcessor initialized with {len(self.order_processor.dealership_name_mapping)} mappings")
            
        except Exception as e:
            self.results['backend_tests']['order_processor_init'] = {'status': 'FAIL', 'error': str(e)}
            self.results['errors'].append(f"Order processor init: {e}")
            print(f"    [FAIL] Order processor initialization failed: {e}")
    
    def test_dealership_name_mapping(self):
        """Test the critical dealership name mapping fix"""
        try:
            print("  [PROC] Testing dealership name mapping...")
            
            if not self.order_processor:
                self.order_processor = CorrectOrderProcessor()
            
            # Test mapping: Dave Sinclair Lincoln South -> Dave Sinclair Lincoln
            config_name = "Dave Sinclair Lincoln South"
            mapped_name = self.order_processor.dealership_name_mapping.get(config_name)
            
            assert mapped_name == "Dave Sinclair Lincoln"
            
            # Test that mapped name has data
            vehicles = self.order_processor._get_dealership_vehicles(config_name)
            
            self.results['backend_tests']['name_mapping'] = {
                'status': 'PASS',
                'mapping_works': mapped_name == "Dave Sinclair Lincoln",
                'vehicles_found': len(vehicles) if vehicles else 0
            }
            print(f"    [PASS] Name mapping works: {config_name} -> {mapped_name} ({len(vehicles)} vehicles)")
            
        except Exception as e:
            self.results['backend_tests']['name_mapping'] = {'status': 'FAIL', 'error': str(e)}
            self.results['errors'].append(f"Name mapping: {e}")
            print(f"    [FAIL] Name mapping test failed: {e}")
    
    def test_order_processing_logic(self):
        """Test core order processing logic"""
        try:
            print("  [INFO] Testing order processing logic...")
            
            if not self.order_processor:
                self.order_processor = CorrectOrderProcessor()
            
            # Process a small order for Dave Sinclair Lincoln South
            start_time = time.time()
            result = self.order_processor.process_cao_order("Dave Sinclair Lincoln South", "shortcut_pack")
            processing_time = time.time() - start_time
            
            self.results['backend_tests']['order_processing'] = {
                'status': 'PASS' if result.get('success') else 'FAIL',
                'processing_time': round(processing_time, 2),
                'vehicles_processed': result.get('total_vehicles', 0),
                'new_vehicles': result.get('new_vehicles', 0),
                'qr_codes_generated': result.get('qr_codes_generated', 0),
                'csv_generated': bool(result.get('download_csv'))
            }
            
            if result.get('success'):
                print(f"    [PASS] Order processed in {processing_time:.2f}s - {result.get('new_vehicles', 0)} new vehicles, {result.get('qr_codes_generated', 0)} QR codes")
            else:
                print(f"    [FAIL] Order processing failed: {result.get('error', 'Unknown error')}")
                self.results['errors'].append(f"Order processing: {result.get('error')}")
                
        except Exception as e:
            self.results['backend_tests']['order_processing'] = {'status': 'FAIL', 'error': str(e)}
            self.results['errors'].append(f"Order processing logic: {e}")
            print(f"    [FAIL] Order processing test failed: {e}")
    
    def test_web_server_connectivity(self):
        """Test web server connectivity"""
        try:
            print("  [WEB] Testing web server connectivity...")
            
            response = requests.get(f"{self.web_server_url}/", timeout=10)
            
            self.results['web_interface_tests']['server_connectivity'] = {
                'status': 'PASS' if response.status_code == 200 else 'FAIL',
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds()
            }
            
            if response.status_code == 200:
                print(f"    [PASS] Web server responding ({response.elapsed.total_seconds():.2f}s)")
            else:
                print(f"    [FAIL] Web server returned {response.status_code}")
                self.results['errors'].append(f"Web server returned {response.status_code}")
                
        except Exception as e:
            self.results['web_interface_tests']['server_connectivity'] = {'status': 'FAIL', 'error': str(e)}
            self.results['errors'].append(f"Web server connectivity: {e}")
            print(f"    [FAIL] Web server connectivity failed: {e}")
    
    def test_api_endpoints(self):
        """Test critical API endpoints"""
        try:
            print("  🔌 Testing API endpoints...")
            
            endpoints = [
                ('/api/dealerships', 'GET'),
                ('/api/system/status', 'GET')
            ]
            
            endpoint_results = {}
            
            for endpoint, method in endpoints:
                try:
                    if method == 'GET':
                        response = requests.get(f"{self.web_server_url}{endpoint}", timeout=10)
                    
                    endpoint_results[endpoint] = {
                        'status_code': response.status_code,
                        'success': 200 <= response.status_code < 300,
                        'response_time': response.elapsed.total_seconds()
                    }
                    
                    status = "[PASS]" if endpoint_results[endpoint]['success'] else "[FAIL]"
                    print(f"    {status} {endpoint}: {response.status_code} ({response.elapsed.total_seconds():.2f}s)")
                    
                except Exception as e:
                    endpoint_results[endpoint] = {'error': str(e), 'success': False}
                    print(f"    [FAIL] {endpoint}: {e}")
            
            self.results['web_interface_tests']['api_endpoints'] = endpoint_results
                
        except Exception as e:
            self.results['web_interface_tests']['api_endpoints'] = {'status': 'FAIL', 'error': str(e)}
            self.results['errors'].append(f"API endpoints: {e}")
            print(f"    [FAIL] API endpoints test failed: {e}")
    
    def test_dealership_api(self):
        """Test dealership API specifically"""
        try:
            print("  🏢 Testing dealership API...")
            
            response = requests.get(f"{self.web_server_url}/api/dealerships", timeout=10)
            
            if response.status_code == 200:
                dealerships = response.json()
                
                # Check for our key dealerships
                dealer_names = [d.get('name', '') for d in dealerships]
                has_dave_sinclair = any('Dave Sinclair' in name for name in dealer_names)
                has_bmw = any('BMW' in name for name in dealer_names)
                
                self.results['web_interface_tests']['dealership_api'] = {
                    'status': 'PASS',
                    'total_dealerships': len(dealerships),
                    'has_dave_sinclair': has_dave_sinclair,
                    'has_bmw': has_bmw,
                    'dealership_names': dealer_names[:5]  # First 5 for sample
                }
                
                print(f"    [PASS] Dealership API returned {len(dealerships)} dealerships")
                if has_dave_sinclair:
                    print(f"    [PASS] Dave Sinclair dealership found")
                if has_bmw:
                    print(f"    [PASS] BMW dealership found")
                    
            else:
                self.results['web_interface_tests']['dealership_api'] = {
                    'status': 'FAIL',
                    'status_code': response.status_code
                }
                print(f"    [FAIL] Dealership API returned {response.status_code}")
                
        except Exception as e:
            self.results['web_interface_tests']['dealership_api'] = {'status': 'FAIL', 'error': str(e)}
            self.results['errors'].append(f"Dealership API: {e}")
            print(f"    [FAIL] Dealership API test failed: {e}")
    
    def test_order_processing_api(self):
        """Test the order processing API endpoint"""
        try:
            print("  [INFO] Testing order processing API...")
            
            # Test the CAO order processing endpoint
            payload = {
                'dealerships': ['Dave Sinclair Lincoln South'],
                'template_type': 'shortcut_pack'
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.web_server_url}/api/orders/process-cao",
                json=payload,
                timeout=60
            )
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                dealer_result = result[0] if result else {}
                
                self.results['web_interface_tests']['order_processing_api'] = {
                    'status': 'PASS' if dealer_result.get('success') else 'FAIL',
                    'processing_time': round(processing_time, 2),
                    'vehicles_processed': dealer_result.get('total_vehicles', 0),
                    'new_vehicles': dealer_result.get('new_vehicles', 0),
                    'csv_generated': bool(dealer_result.get('download_csv')),
                    'download_filename': dealer_result.get('download_csv', '')
                }
                
                if dealer_result.get('success'):
                    print(f"    [PASS] API order processed in {processing_time:.2f}s - {dealer_result.get('new_vehicles', 0)} new vehicles")
                    if dealer_result.get('download_csv'):
                        print(f"    [PASS] CSV generated: {dealer_result.get('download_csv')}")
                else:
                    print(f"    [FAIL] API order processing failed: {dealer_result.get('error', 'Unknown error')}")
                    
            else:
                self.results['web_interface_tests']['order_processing_api'] = {
                    'status': 'FAIL',
                    'status_code': response.status_code,
                    'response_text': response.text[:200]
                }
                print(f"    [FAIL] API returned {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            self.results['web_interface_tests']['order_processing_api'] = {'status': 'FAIL', 'error': str(e)}
            self.results['errors'].append(f"Order processing API: {e}")
            print(f"    [FAIL] Order processing API test failed: {e}")
    
    def test_end_to_end_processing(self):
        """Test complete end-to-end processing workflow"""
        try:
            print("  [PROC] Testing end-to-end processing workflow...")
            
            # This simulates: Frontend → API → Backend → File Generation → Download
            workflow_steps = {
                'dealership_selection': False,
                'order_creation': False,
                'processing': False,
                'file_generation': False,
                'download_available': False
            }
            
            # Step 1: Get dealerships (simulates frontend dropdown)
            dealerships_response = requests.get(f"{self.web_server_url}/api/dealerships", timeout=10)
            if dealerships_response.status_code == 200:
                workflow_steps['dealership_selection'] = True
            
            # Step 2: Process order (simulates queue processing)
            if workflow_steps['dealership_selection']:
                payload = {
                    'dealerships': ['Dave Sinclair Lincoln South'],
                    'template_type': 'shortcut_pack'
                }
                
                order_response = requests.post(
                    f"{self.web_server_url}/api/orders/process-cao",
                    json=payload,
                    timeout=60
                )
                
                if order_response.status_code == 200:
                    workflow_steps['order_creation'] = True
                    result = order_response.json()
                    dealer_result = result[0] if result else {}
                    
                    if dealer_result.get('success'):
                        workflow_steps['processing'] = True
                        
                        if dealer_result.get('download_csv'):
                            workflow_steps['file_generation'] = True
                            
                            # Step 3: Test download availability
                            download_url = f"{self.web_server_url}/download_csv/{dealer_result['download_csv']}"
                            download_response = requests.head(download_url, timeout=10)
                            
                            if download_response.status_code == 200:
                                workflow_steps['download_available'] = True
            
            all_steps_passed = all(workflow_steps.values())
            
            self.results['integration_tests']['end_to_end'] = {
                'status': 'PASS' if all_steps_passed else 'PARTIAL',
                'workflow_steps': workflow_steps,
                'completion_rate': f"{sum(workflow_steps.values())}/{len(workflow_steps)}"
            }
            
            print(f"    {'[PASS]' if all_steps_passed else '[WARN]'} End-to-end workflow: {sum(workflow_steps.values())}/{len(workflow_steps)} steps completed")
            for step, completed in workflow_steps.items():
                status = "[PASS]" if completed else "[FAIL]"
                print(f"      {status} {step.replace('_', ' ').title()}")
                
        except Exception as e:
            self.results['integration_tests']['end_to_end'] = {'status': 'FAIL', 'error': str(e)}
            self.results['errors'].append(f"End-to-end workflow: {e}")
            print(f"    [FAIL] End-to-end test failed: {e}")
    
    def test_file_generation_and_download(self):
        """Test file generation and download functionality"""
        try:
            print("  📁 Testing file generation and download...")
            
            if not self.order_processor:
                self.order_processor = CorrectOrderProcessor()
            
            # Generate files using backend
            result = self.order_processor.process_cao_order("Dave Sinclair Lincoln South", "shortcut_pack")
            
            file_tests = {
                'csv_generated': False,
                'qr_codes_generated': False,
                'files_downloadable': False
            }
            
            if result.get('success') and result.get('download_csv'):
                file_tests['csv_generated'] = True
                
                if result.get('qr_codes_generated', 0) > 0:
                    file_tests['qr_codes_generated'] = True
                
                # Test download via web interface
                download_url = f"{self.web_server_url}/download_csv/{result['download_csv']}"
                download_response = requests.head(download_url, timeout=10)
                
                if download_response.status_code == 200:
                    file_tests['files_downloadable'] = True
            
            self.results['integration_tests']['file_generation'] = {
                'status': 'PASS' if all(file_tests.values()) else 'PARTIAL',
                'tests': file_tests,
                'csv_filename': result.get('download_csv', '') if result.get('success') else '',
                'qr_count': result.get('qr_codes_generated', 0) if result.get('success') else 0
            }
            
            for test, passed in file_tests.items():
                status = "[PASS]" if passed else "[FAIL]"
                print(f"    {status} {test.replace('_', ' ').title()}")
                
        except Exception as e:
            self.results['integration_tests']['file_generation'] = {'status': 'FAIL', 'error': str(e)}
            self.results['errors'].append(f"File generation: {e}")
            print(f"    [FAIL] File generation test failed: {e}")
    
    def test_concurrent_processing(self):
        """Test concurrent processing capabilities"""
        try:
            print("  ⚡ Testing concurrent processing...")
            
            # Test processing multiple dealerships concurrently
            dealerships = ['Dave Sinclair Lincoln South', 'BMW of West St. Louis']
            
            def process_dealership(dealership_name):
                try:
                    payload = {
                        'dealerships': [dealership_name],
                        'template_type': 'shortcut_pack'
                    }
                    
                    start_time = time.time()
                    response = requests.post(
                        f"{self.web_server_url}/api/orders/process-cao",
                        json=payload,
                        timeout=60
                    )
                    processing_time = time.time() - start_time
                    
                    return {
                        'dealership': dealership_name,
                        'success': response.status_code == 200,
                        'processing_time': processing_time,
                        'status_code': response.status_code
                    }
                    
                except Exception as e:
                    return {
                        'dealership': dealership_name,
                        'success': False,
                        'error': str(e)
                    }
            
            # Run concurrent requests
            threads = []
            results = []
            
            start_time = time.time()
            for dealership in dealerships:
                thread = threading.Thread(target=lambda d=dealership: results.append(process_dealership(d)))
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            total_time = time.time() - start_time
            
            successful_requests = sum(1 for r in results if r.get('success'))
            
            self.results['performance_tests']['concurrent_processing'] = {
                'status': 'PASS' if successful_requests == len(dealerships) else 'PARTIAL',
                'total_requests': len(dealerships),
                'successful_requests': successful_requests,
                'total_time': round(total_time, 2),
                'average_time': round(total_time / len(dealerships), 2),
                'results': results
            }
            
            print(f"    {'[PASS]' if successful_requests == len(dealerships) else '[WARN]'} Concurrent processing: {successful_requests}/{len(dealerships)} successful in {total_time:.2f}s")
            
        except Exception as e:
            self.results['performance_tests']['concurrent_processing'] = {'status': 'FAIL', 'error': str(e)}
            self.results['errors'].append(f"Concurrent processing: {e}")
            print(f"    [FAIL] Concurrent processing test failed: {e}")
    
    def print_test_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 60)
        print("🏆 INTEGRATED SYSTEM STRESS TEST RESULTS")
        print("=" * 60)
        
        # Summary
        total_tests = 0
        passed_tests = 0
        
        for category in self.results:
            if category != 'errors':
                for test_name, test_result in self.results[category].items():
                    total_tests += 1
                    if test_result.get('status') == 'PASS':
                        passed_tests += 1
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n[RESULTS] OVERALL RESULTS:")
        print(f"   Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"   Errors: {len(self.results['errors'])}")
        
        # Category breakdown
        for category, tests in self.results.items():
            if category == 'errors':
                continue
                
            print(f"\n[INFO] {category.upper().replace('_', ' ')}:")
            for test_name, result in tests.items():
                status = result.get('status', 'UNKNOWN')
                emoji = "[PASS]" if status == 'PASS' else "[WARN]" if status == 'PARTIAL' else "[FAIL]"
                print(f"   {emoji} {test_name.replace('_', ' ').title()}: {status}")
        
        # Critical errors
        if self.results['errors']:
            print(f"\n🚨 CRITICAL ERRORS:")
            for error in self.results['errors']:
                print(f"   [FAIL] {error}")
        
        # Recommendations
        print(f"\n[TIPS] RECOMMENDATIONS:")
        if success_rate >= 90:
            print("   🟢 System is ready for production use")
        elif success_rate >= 75:
            print("   🟡 System is functional but needs minor fixes")
        else:
            print("   🔴 System needs significant work before production")
        
        print(f"\n🎯 NEXT STEPS:")
        if passed_tests < total_tests:
            print("   1. Address failed tests before deployment")
        print("   2. Test with additional dealerships")
        print("   3. Monitor performance under production load")
        
        # Save results to file
        results_file = project_root / "integrated_system_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")

def main():
    """Run the integrated system stress test"""
    tester = IntegratedSystemStressTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()