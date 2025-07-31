#!/usr/bin/env python3
"""
Quick Stress Test
=================

Focused stress test after fixing critical issues.

Author: Silver Fox Assistant
Created: 2025-07-29
"""

import os
import sys
import time
import concurrent.futures
from pathlib import Path

# Add project paths
current_file = Path(__file__).resolve()
scripts_dir = current_file.parent
sys.path.insert(0, str(scripts_dir))

from real_scraper_integration import RealScraperIntegration

def test_concurrent_scrapers():
    """Test concurrent scraper execution"""
    print("\n" + "="*60)
    print("[QUICK STRESS] CONCURRENT SCRAPER TEST")
    print("="*60)
    
    integration = RealScraperIntegration()
    scrapers = list(integration.real_scraper_mapping.keys())
    print(f"[TEST] Running {len(scrapers)} scrapers concurrently")
    
    def run_scraper(name):
        try:
            result = integration.run_real_scraper(name)
            if result['success']:
                # Test database import
                import_result = integration.import_vehicles_to_database(result['vehicles'], name)
                return {
                    'name': name,
                    'success': True,
                    'vehicles': result['vehicle_count'],
                    'imported': import_result.get('total_processed', 0),
                    'real_data': result.get('is_real_data', False)
                }
            else:
                return {'name': name, 'success': False, 'error': result.get('error', 'Unknown')}
        except Exception as e:
            return {'name': name, 'success': False, 'error': str(e)}
    
    start_time = time.time()
    
    # Run all scrapers concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(run_scraper, scraper): scraper for scraper in scrapers}
        results = []
        
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result(timeout=30)
                results.append(result)
                if result['success']:
                    print(f"[SUCCESS] {result['name']}: {result['vehicles']} vehicles, {result['imported']} imported")
                else:
                    print(f"[FAILED] {result['name']}: {result['error']}")
            except Exception as e:
                print(f"[ERROR] {futures[future]}: {e}")
                results.append({'name': futures[future], 'success': False, 'error': str(e)})
    
    duration = time.time() - start_time
    successful = sum(1 for r in results if r['success'])
    total_vehicles = sum(r.get('vehicles', 0) for r in results if r['success'])
    total_imported = sum(r.get('imported', 0) for r in results if r['success'])
    real_data_count = sum(1 for r in results if r.get('real_data', False))
    
    print("\n[RESULTS]")
    print(f"Duration: {duration:.2f}s")
    print(f"Success rate: {successful}/{len(scrapers)} ({successful/len(scrapers)*100:.1f}%)")
    print(f"Total vehicles scraped: {total_vehicles}")
    print(f"Total vehicles imported: {total_imported}")
    print(f"Real data sources: {real_data_count}/{successful}")
    
    return successful > 0

def test_rapid_execution():
    """Test rapid sequential execution"""
    print("\n" + "="*60)
    print("[QUICK STRESS] RAPID EXECUTION TEST")
    print("="*60)
    
    integration = RealScraperIntegration()
    test_scraper = 'Test Integration Dealer'
    
    print(f"[TEST] Running {test_scraper} 5 times rapidly")
    
    start_time = time.time()
    results = []
    
    for i in range(5):
        try:
            result = integration.run_real_scraper(test_scraper)
            if result['success']:
                import_result = integration.import_vehicles_to_database(result['vehicles'], test_scraper)
                results.append({
                    'run': i+1,
                    'success': True,
                    'vehicles': result['vehicle_count'],
                    'imported': import_result.get('total_processed', 0)
                })
                print(f"[RUN {i+1}] SUCCESS: {result['vehicle_count']} vehicles")
            else:
                results.append({'run': i+1, 'success': False, 'error': result.get('error')})
                print(f"[RUN {i+1}] FAILED: {result.get('error')}")
        except Exception as e:
            results.append({'run': i+1, 'success': False, 'error': str(e)})
            print(f"[RUN {i+1}] ERROR: {e}")
    
    duration = time.time() - start_time
    successful = sum(1 for r in results if r['success'])
    avg_time = duration / len(results)
    
    print(f"\n[RESULTS]")
    print(f"Duration: {duration:.2f}s")
    print(f"Average per run: {avg_time:.2f}s")
    print(f"Success rate: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
    
    return successful >= 4  # At least 4/5 should succeed

def main():
    """Run quick stress tests"""
    print("\n" + "="*80)
    print("[QUICK STRESS] SILVER FOX SCRAPER SYSTEM - QUICK STRESS TEST")
    print("="*80)
    
    tests = [
        ("Concurrent Scrapers", test_concurrent_scrapers),
        ("Rapid Execution", test_rapid_execution)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n[STRESS] Starting: {test_name}")
        try:
            result = test_func()
            status = "PASSED" if result else "FAILED"
            print(f"[STRESS] {test_name}: {status}")
            if result:
                passed += 1
        except Exception as e:
            print(f"[STRESS] {test_name}: EXCEPTION - {e}")
    
    print("\n" + "="*80)
    print("[FINAL] QUICK STRESS TEST RESULTS")
    print("="*80)
    print(f"Tests passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("[SUCCESS] All quick stress tests passed! System is robust.")
    elif passed >= total * 0.5:
        print("[WARNING] Most tests passed. System is mostly stable.")
    else:
        print("[FAILED] Multiple failures. System needs attention.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)