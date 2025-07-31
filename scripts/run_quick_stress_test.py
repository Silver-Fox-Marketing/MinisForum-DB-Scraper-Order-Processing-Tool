#!/usr/bin/env python3
"""
Quick Stress Test - Windows Compatible
=====================================

Simplified stress test without emoji characters for Windows compatibility.

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Add the scripts directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("SILVER FOX ORDER PROCESSING STRESS TEST")
print("Windows Compatible Version")
print("=" * 60)

def test_basic_functionality():
    """Test basic system functionality"""
    print("\n[TEST] Basic System Functionality")
    print("-" * 40)
    
    # Test 1: Database Connection
    try:
        from database_connection import db_manager
        result = db_manager.execute_query("SELECT 1 as test")
        if result and result[0]['test'] == 1:
            print("[PASS] Database connection")
        else:
            print("[FAIL] Database query returned unexpected result")
            return False
    except Exception as e:
        print(f"[FAIL] Database connection: {e}")
        return False
    
    # Test 2: Order Processing Workflow
    try:
        from order_processing_workflow import OrderProcessingWorkflow
        workflow = OrderProcessingWorkflow()
        schedule = workflow.get_todays_cao_schedule()
        print(f"[PASS] Order processing workflow - {len(schedule)} scheduled items")
    except Exception as e:
        print(f"[FAIL] Order processing workflow: {e}")
        return False
    
    # Test 3: Real Scraper Integration
    try:
        from real_scraper_integration import RealScraperIntegration
        scraper = RealScraperIntegration()
        scrapers = list(scraper.real_scraper_mapping.keys())
        print(f"[PASS] Real scraper integration - {len(scrapers)} scrapers available")
    except Exception as e:
        print(f"[FAIL] Real scraper integration: {e}")
        return False
    
    return True

def test_order_processing():
    """Test order processing functionality"""
    print("\n[TEST] Order Processing")
    print("-" * 40)
    
    try:
        from order_processing_workflow import OrderProcessingWorkflow
        workflow = OrderProcessingWorkflow()
        
        # Test CAO processing with demo data
        test_dealership = "BMW of West St. Louis"
        print(f"[RUN] Testing CAO order for {test_dealership}")
        
        start_time = time.time()
        result = workflow.process_cao_order(test_dealership, ['new', 'used'])
        duration = time.time() - start_time
        
        if result.get('success'):
            print(f"[PASS] CAO processing completed in {duration:.2f}s")
            print(f"       New vehicles: {result.get('new_vehicles', 0)}")
            print(f"       QR codes: {result.get('qr_codes_generated', 0)}")
            return True
        else:
            print(f"[FAIL] CAO processing: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Order processing test: {e}")
        return False

def test_database_performance():
    """Test database performance"""
    print("\n[TEST] Database Performance")
    print("-" * 40)
    
    try:
        from database_connection import db_manager
        
        # Test multiple quick queries
        start_time = time.time()
        
        for i in range(10):
            result = db_manager.execute_query("SELECT COUNT(*) FROM raw_vehicle_data")
            if not result:
                print(f"[FAIL] Query {i+1} failed")
                return False
        
        duration = time.time() - start_time
        avg_time = duration / 10
        
        print(f"[PASS] Database performance")
        print(f"       10 queries in {duration:.2f}s")
        print(f"       Average: {avg_time*1000:.1f}ms per query")
        
        return avg_time < 0.5  # Should be under 500ms per query
        
    except Exception as e:
        print(f"[FAIL] Database performance test: {e}")
        return False

def test_qr_generation():
    """Test QR code generation"""
    print("\n[TEST] QR Code Generation")
    print("-" * 40)
    
    try:
        from order_processing_workflow import OrderProcessingWorkflow
        workflow = OrderProcessingWorkflow()
        
        # Test QR generation with sample data
        test_vehicles = [
            {
                'vin': 'TESTVIN123456789ABC',
                'url': 'https://example.com/vehicle/1',
                'year': '2024',
                'make': 'Test',
                'model': 'Vehicle'
            }
        ]
        
        from pathlib import Path
        test_output_folder = Path("test_qr_output")
        test_output_folder.mkdir(exist_ok=True)
        
        start_time = time.time()
        qr_paths = workflow.generate_qr_codes(test_vehicles, 'Test Dealership', test_output_folder)
        duration = time.time() - start_time
        
        if isinstance(qr_paths, list) and len(qr_paths) > 0:
            print(f"[PASS] QR generation in {duration:.2f}s")
            print(f"       Generated: {len(qr_paths)} codes")
            print(f"       Output folder: {test_output_folder}")
            return True
        else:
            print(f"[FAIL] QR generation: No QR codes generated")
            return False
            
    except Exception as e:
        print(f"[FAIL] QR generation test: {e}")
        return False

def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("\nStarting comprehensive stress test...")
    start_time = time.time()
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Order Processing", test_order_processing),
        ("Database Performance", test_database_performance),
        ("QR Generation", test_qr_generation)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"[ERROR] Test framework error: {e}")
            failed += 1
    
    total_duration = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 60)
    print("STRESS TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/(passed+failed)*100):.1f}%")
    print(f"Duration: {total_duration:.2f} seconds")
    
    if passed >= len(tests) * 0.8:  # 80% success rate
        print("\n[SUCCESS] System is functioning correctly!")
        return True
    else:
        print("\n[WARNING] System has issues that need attention.")
        return False

if __name__ == "__main__":
    try:
        success = run_comprehensive_test()
        
        print("\n" + "=" * 60)
        if success:
            print("SYSTEM STATUS: OPERATIONAL")
            print("The Silver Fox order processing system is ready for use.")
        else:
            print("SYSTEM STATUS: NEEDS ATTENTION")
            print("Some components require fixes before production use.")
        
        print("\nNext steps:")
        print("1. Start web GUI: python app_windows_safe.py")
        print("2. Access test page: http://127.0.0.1:5001/test")
        print("3. Run order processing: http://127.0.0.1:5001/order-form")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n[STOP] Test interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Test framework error: {e}")
        import traceback
        traceback.print_exc()