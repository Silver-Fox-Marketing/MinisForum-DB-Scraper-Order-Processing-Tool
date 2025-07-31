#!/usr/bin/env python3
"""
Backend Stress Test
==================

Test just the backend components without requiring web server.
Validates the core order processing system works correctly.

Author: Silver Fox Assistant
Created: 2025-07-30
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "scripts"))

class BackendStressTester:
    """Test backend order processing system"""
    
    def __init__(self):
        self.results = {}
        self.errors = []
        
    def run_backend_tests(self):
        """Run backend-only stress tests"""
        print("*** Backend System Stress Test ***")
        print("=" * 50)
        
        self.test_imports()
        self.test_database_connectivity()
        self.test_dealership_data()
        self.test_order_processor()
        self.test_name_mapping()
        self.test_order_processing()
        self.test_file_generation()
        
        self.print_results()
        
    def test_imports(self):
        """Test all required imports"""
        try:
            print("[1/7] Testing imports...")
            
            from database_connection import db_manager
            print("  [OK] database_connection imported")
            
            from correct_order_processing import CorrectOrderProcessor
            print("  [OK] correct_order_processing imported")
            
            self.results['imports'] = {'status': 'PASS'}
            
        except Exception as e:
            self.results['imports'] = {'status': 'FAIL', 'error': str(e)}
            self.errors.append(f"Imports: {e}")
            print(f"  [ERROR] Import failed: {e}")
    
    def test_database_connectivity(self):
        """Test database connection"""
        try:
            print("[2/7] Testing database...")
            
            from database_connection import db_manager
            
            # Test basic query
            result = db_manager.execute_query("SELECT 1 as test")
            assert result[0]['test'] == 1
            
            # Count dealership configs
            configs = db_manager.execute_query("SELECT COUNT(*) as count FROM dealership_configs")
            config_count = configs[0]['count']
            
            # Count vehicle data
            vehicles = db_manager.execute_query("SELECT COUNT(*) as count FROM raw_vehicle_data")
            vehicle_count = vehicles[0]['count']
            
            self.results['database'] = {
                'status': 'PASS',
                'dealership_configs': config_count,
                'total_vehicles': vehicle_count
            }
            
            print(f"  [OK] Database connected")
            print(f"  [INFO] {config_count} dealership configs")
            print(f"  [INFO] {vehicle_count} total vehicles")
            
        except Exception as e:
            self.results['database'] = {'status': 'FAIL', 'error': str(e)}
            self.errors.append(f"Database: {e}")
            print(f"  [ERROR] Database test failed: {e}")
    
    def test_dealership_data(self):
        """Test dealership data availability"""
        try:
            print("[3/7] Testing dealership data...")
            
            from database_connection import db_manager
            
            # Check key dealerships
            dealerships = {
                'Dave Sinclair Lincoln': 0,
                'BMW of West St. Louis': 0,
                'Columbia Honda': 0
            }
            
            for dealer in dealerships.keys():
                result = db_manager.execute_query(
                    "SELECT COUNT(*) as count FROM raw_vehicle_data WHERE location = %s",
                    (dealer,)
                )
                dealerships[dealer] = result[0]['count']
                
                status = "[OK]" if dealerships[dealer] > 0 else "[WARN]"
                print(f"  {status} {dealer}: {dealerships[dealer]} vehicles")
            
            self.results['dealership_data'] = {
                'status': 'PASS' if all(count > 0 for count in dealerships.values()) else 'PARTIAL',
                'dealerships': dealerships
            }
            
        except Exception as e:
            self.results['dealership_data'] = {'status': 'FAIL', 'error': str(e)}
            self.errors.append(f"Dealership data: {e}")
            print(f"  [ERROR] Dealership data test failed: {e}")
    
    def test_order_processor(self):
        """Test order processor initialization"""
        try:
            print("[4/7] Testing CorrectOrderProcessor...")
            
            from correct_order_processing import CorrectOrderProcessor
            
            processor = CorrectOrderProcessor()
            
            # Check mapping exists
            assert hasattr(processor, 'dealership_name_mapping')
            mapping_count = len(processor.dealership_name_mapping)
            
            # Check output directory
            assert processor.output_base.exists()
            
            self.results['order_processor'] = {
                'status': 'PASS',
                'mapping_count': mapping_count,
                'output_path': str(processor.output_base)
            }
            
            print(f"  [OK] Order processor initialized")
            print(f"  [INFO] {mapping_count} name mappings")
            print(f"  [INFO] Output path: {processor.output_base}")
            
        except Exception as e:
            self.results['order_processor'] = {'status': 'FAIL', 'error': str(e)}
            self.errors.append(f"Order processor: {e}")
            print(f"  [ERROR] Order processor test failed: {e}")
    
    def test_name_mapping(self):
        """Test critical name mapping fix"""
        try:
            print("[5/7] Testing name mapping fix...")
            
            from correct_order_processing import CorrectOrderProcessor
            
            processor = CorrectOrderProcessor()
            
            # Test the critical mapping
            config_name = "Dave Sinclair Lincoln South"
            mapped_name = processor.dealership_name_mapping.get(config_name)
            
            print(f"  [INFO] Mapping: {config_name} -> {mapped_name}")
            
            # Test that mapping works
            vehicles = processor._get_dealership_vehicles(config_name)
            vehicle_count = len(vehicles) if vehicles else 0
            
            self.results['name_mapping'] = {
                'status': 'PASS' if mapped_name and vehicle_count > 0 else 'FAIL',
                'original_name': config_name,
                'mapped_name': mapped_name,
                'vehicles_found': vehicle_count
            }
            
            if mapped_name and vehicle_count > 0:
                print(f"  [OK] Name mapping works: found {vehicle_count} vehicles")
            else:
                print(f"  [ERROR] Name mapping failed: {vehicle_count} vehicles found")
                self.errors.append(f"Name mapping returned {vehicle_count} vehicles")
            
        except Exception as e:
            self.results['name_mapping'] = {'status': 'FAIL', 'error': str(e)}
            self.errors.append(f"Name mapping: {e}")
            print(f"  [ERROR] Name mapping test failed: {e}")
    
    def test_order_processing(self):
        """Test actual order processing"""
        try:
            print("[6/7] Testing order processing...")
            
            from correct_order_processing import CorrectOrderProcessor
            
            processor = CorrectOrderProcessor()
            
            # Process Dave Sinclair Lincoln South
            start_time = time.time()
            result = processor.process_cao_order("Dave Sinclair Lincoln South", "shortcut_pack")
            processing_time = time.time() - start_time
            
            self.results['order_processing'] = {
                'status': 'PASS' if result.get('success') else 'FAIL',
                'processing_time': round(processing_time, 2),
                'result': result
            }
            
            if result.get('success'):
                print(f"  [OK] Order processed in {processing_time:.2f}s")
                print(f"  [INFO] Total vehicles: {result.get('total_vehicles', 0)}")
                print(f"  [INFO] New vehicles: {result.get('new_vehicles', 0)}")
                print(f"  [INFO] QR codes: {result.get('qr_codes_generated', 0)}")
                print(f"  [INFO] CSV file: {result.get('download_csv', 'None')}")
            else:
                error = result.get('error', 'Unknown error')
                print(f"  [ERROR] Order processing failed: {error}")
                self.errors.append(f"Order processing: {error}")
            
        except Exception as e:
            self.results['order_processing'] = {'status': 'FAIL', 'error': str(e)}
            self.errors.append(f"Order processing: {e}")
            print(f"  [ERROR] Order processing test failed: {e}")
    
    def test_file_generation(self):
        """Test file generation"""
        try:
            print("[7/7] Testing file generation...")
            
            # Check if files were generated from previous test
            orders_dir = Path("scripts/orders")
            
            csv_files = list(orders_dir.glob("**/*.csv"))
            qr_dirs = list(orders_dir.glob("**/qr_codes"))
            
            # Also check current directory
            current_orders = Path("orders")
            if current_orders.exists():
                csv_files.extend(list(current_orders.glob("**/*.csv")))
                qr_dirs.extend(list(current_orders.glob("**/qr_codes")))
            
            self.results['file_generation'] = {
                'status': 'PASS' if csv_files else 'PARTIAL',
                'csv_files_found': len(csv_files),
                'qr_directories_found': len(qr_dirs),
                'latest_csv': str(csv_files[-1]) if csv_files else None
            }
            
            if csv_files:
                print(f"  [OK] Found {len(csv_files)} CSV files")
                print(f"  [INFO] Found {len(qr_dirs)} QR directories")
                print(f"  [INFO] Latest: {csv_files[-1].name}")
            else:
                print(f"  [WARN] No CSV files found")
            
        except Exception as e:
            self.results['file_generation'] = {'status': 'FAIL', 'error': str(e)}
            self.errors.append(f"File generation: {e}")
            print(f"  [ERROR] File generation test failed: {e}")
    
    def print_results(self):
        """Print test results summary"""
        print("\n" + "=" * 50)
        print("*** BACKEND STRESS TEST RESULTS ***")
        print("=" * 50)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r.get('status') == 'PASS')
        partial_tests = sum(1 for r in self.results.values() if r.get('status') == 'PARTIAL')
        
        print(f"[SUMMARY] {passed_tests} passed, {partial_tests} partial, {total_tests - passed_tests - partial_tests} failed")
        print(f"[SUCCESS RATE] {passed_tests/total_tests*100:.1f}%")
        
        for test_name, result in self.results.items():
            status = result.get('status', 'UNKNOWN')
            emoji = "[PASS]" if status == 'PASS' else "[PARTIAL]" if status == 'PARTIAL' else "[FAIL]"
            print(f"{emoji} {test_name.replace('_', ' ').title()}: {status}")
        
        if self.errors:
            print(f"\n[ERRORS] ({len(self.errors)}):")
            for error in self.errors:
                print(f"  [ERROR] {error}")
        
        if passed_tests == total_tests:
            print(f"\n[SUCCESS] All backend tests passed! System ready for web interface testing.")
        elif passed_tests >= total_tests * 0.8:
            print(f"\n[WARNING] Most tests passed. Minor issues need attention.")
        else:
            print(f"\n[CRITICAL] Significant issues found. Backend needs fixes before proceeding.")

def main():
    """Run backend stress tests"""
    tester = BackendStressTester()
    tester.run_backend_tests()

if __name__ == "__main__":
    main()