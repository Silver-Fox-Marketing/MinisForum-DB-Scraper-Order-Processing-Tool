#!/usr/bin/env python3
"""
Test Script for Automated Normalization Manager
Tests the complete normalization pipeline with existing data
"""
import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from automated_normalization_manager import (
    AutomatedNormalizationManager, 
    normalize_active_import, 
    validate_normalization_status
)
from database_connection import db_manager

def test_validation_status():
    """Test validation of current normalization status"""
    print("\n" + "="*60)
    print("TESTING NORMALIZATION VALIDATION")
    print("="*60)
    
    result = validate_normalization_status()
    
    if 'error' in result:
        print(f"❌ ERROR: {result['error']}")
        return False
    
    print(f"Normalization Status: {'✅ COMPLETE' if result['is_complete'] else '❌ INCOMPLETE'}")
    print(f"Raw Records: {result['raw_records']}")
    print(f"Normalized Records: {result['normalized_records']}")
    print(f"Completion Rate: {result['completion_rate']}%")
    
    if result.get('dealership_consistency'):
        dc = result['dealership_consistency']
        print(f"Dealership Consistency: {dc['consistent_dealerships']}/{dc['total_dealerships']} consistent")
        
        if not dc['all_consistent']:
            print("\nInconsistent Dealerships:")
            for dealer, stats in dc['dealership_details'].items():
                if not stats['is_consistent']:
                    print(f"  - {dealer}: {stats['raw_count']} raw → {stats['normalized_count']} normalized (missing {stats['missing_records']})")
    
    return result['is_complete']

def test_normalization_run():
    """Test running the automated normalization"""
    print("\n" + "="*60)
    print("TESTING AUTOMATED NORMALIZATION RUN")
    print("="*60)
    
    result = normalize_active_import()
    
    if result['success']:
        print(f"✅ SUCCESS: Normalized {result['normalized_records']} records")
        print(f"Import ID: {result['import_id']}")
        print(f"Dealerships Processed: {result['dealerships_processed']}")
        
        if result.get('validation'):
            val = result['validation']
            print(f"Final Completion Rate: {val['completion_rate']}%")
            print(f"Raw → Normalized: {val['raw_records']} → {val['normalized_records']}")
            
            if val.get('dealership_consistency'):
                dc = val['dealership_consistency']
                print(f"All Dealerships Consistent: {'✅ YES' if dc['all_consistent'] else '❌ NO'}")
    else:
        print(f"❌ FAILED: {result['error']}")
        if result['stats']['errors']:
            print("\nErrors:")
            for error in result['stats']['errors'][:5]:
                print(f"  - {error}")
    
    return result['success']

def test_active_import_info():
    """Test getting active import information"""
    print("\n" + "="*60)
    print("ACTIVE IMPORT INFORMATION")
    print("="*60)
    
    try:
        active_import = db_manager.execute_query(
            """
            SELECT 
                import_id, 
                import_date, 
                total_vehicles, 
                dealerships_count,
                dealerships_list,
                import_source,
                file_name
            FROM scraper_imports 
            WHERE status = 'active' 
            LIMIT 1
            """, fetch='one'
        )
        
        if active_import:
            print(f"Import ID: {active_import['import_id']}")
            print(f"Import Date: {active_import['import_date']}")
            print(f"Total Vehicles: {active_import['total_vehicles']}")
            print(f"Dealerships: {active_import['dealerships_count']}")
            print(f"Source File: {active_import.get('file_name', 'Unknown')}")
            print(f"Import Source: {active_import.get('import_source', 'Unknown')}")
            
            if active_import.get('dealerships_list'):
                print(f"Dealership List: {active_import['dealerships_list'][:5]}...")  # Show first 5
            
            return active_import['import_id']
        else:
            print("❌ No active import found")
            return None
            
    except Exception as e:
        print(f"❌ Error getting active import info: {e}")
        return None

def main():
    """Run all normalization tests"""
    print("🔄 AUTOMATED NORMALIZATION MANAGER - TEST SUITE")
    print("=" * 70)
    
    # Test 1: Get active import info
    import_id = test_active_import_info()
    if not import_id:
        print("\n❌ Cannot proceed without an active import")
        return
    
    # Test 2: Check current validation status
    is_complete_before = test_validation_status()
    
    # Test 3: Run normalization (even if complete, to test the system)
    print(f"\nRunning normalization for Import ID {import_id}...")
    success = test_normalization_run()
    
    # Test 4: Check final validation status
    if success:
        print("\n" + "="*60)
        print("FINAL VALIDATION CHECK")
        print("="*60)
        is_complete_after = test_validation_status()
        
        if is_complete_after:
            print("\n✅ NORMALIZATION SYSTEM TEST: SUCCESS")
            print("✅ All data properly normalized and ready for CAO processing")
        else:
            print("\n❌ NORMALIZATION SYSTEM TEST: INCOMPLETE")
            print("❌ Some records may not be properly normalized")
    else:
        print("\n❌ NORMALIZATION SYSTEM TEST: FAILED")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")

if __name__ == "__main__":
    main()