#!/usr/bin/env python3
"""
Test if expected VINs are now available after the fix
"""

import sys
from pathlib import Path

current_file = Path(__file__).resolve()
sys.path.insert(0, str(current_file.parent / 'scripts'))

from database_connection import db_manager

def test_expected_vins():
    expected_vins = [
        'YV4062JE7T1434433', 'YV4062JE8T1435316', 'YV4062PF7T1453502',
        'YV4H60RC2T1343158', 'YV4H60RM2T1325073', 'YV4M12RC3T1336034',
        'YV4M12RC4T1335930', 'YV4M12RC5T1329666', 'YV4M12RC8T1331153',
        'YV4M12RC8T1342069', 'YV4M12RM9T1335429'
    ]

    print('=== TEST: EXPECTED VINS AFTER FIX ===')

    try:
        # Test 1: Check if expected VINs now exist in normalized data linked to Import 12
        print('1. Check expected VINs in normalized data from Import 12...')
        test_query = """
            SELECT nvd.vin, nvd.on_lot_status, nvd.vehicle_condition, si.import_id, si.status
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE nvd.location = 'Volvo Cars West County'
            AND si.status = 'active'
            AND nvd.vin = ANY(%s)
            ORDER BY nvd.vin
        """
        
        results = db_manager.execute_query(test_query, [expected_vins])
        print(f'Expected VINs found in active normalized data: {len(results)}/11')
        
        for result in results:
            print(f"  - {result['vin']} | Status: {result['on_lot_status']} | Condition: {result['vehicle_condition']} | Import: {result['import_id']}")
        
        # Test 2: Check total active normalized data for Import 12
        print('\n2. Check total active normalized data...')
        total_query = """
            SELECT COUNT(*) as total_normalized
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE nvd.location = 'Volvo Cars West County'
            AND si.status = 'active'
            AND nvd.on_lot_status = 'onlot'
        """
        
        total_result = db_manager.execute_query(total_query)
        if total_result:
            print(f'Total active onlot normalized vehicles: {total_result[0]["total_normalized"]}')
        
        # Test 3: Simulate CAO query
        print('\n3. Simulate CAO query (should now return expected VINs)...')
        cao_query = """
            SELECT nvd.vin, nvd.on_lot_status, nvd.vehicle_condition
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE nvd.location = 'Volvo Cars West County'
            AND nvd.on_lot_status IN ('onlot', 'on lot')
            AND si.status = 'active'
            ORDER BY nvd.vin
            LIMIT 20
        """
        
        cao_results = db_manager.execute_query(cao_query)
        print(f'CAO query returns {len(cao_results)} vehicles')
        
        # Check how many expected VINs are in CAO results
        cao_vins = [r['vin'] for r in cao_results]
        expected_in_cao = [vin for vin in expected_vins if vin in cao_vins]
        print(f'Expected VINs in CAO results: {len(expected_in_cao)}/11')
        
        if len(expected_in_cao) == len(results):
            print('SUCCESS: All expected VINs found in normalized data are also returned by CAO query!')
            
            if len(expected_in_cao) == 11:
                print('PERFECT: All 11 expected VINs are now available for CAO processing!')
            else:
                print(f'PARTIAL: {len(expected_in_cao)} expected VINs available, {11-len(expected_in_cao)} still missing')
        else:
            print('WARNING: Mismatch between normalized data and CAO query results')
            
        print('\n=== SUMMARY ===')
        if len(expected_in_cao) >= 10:  # Allow for 1 offlot vehicle
            print('FIX SUCCESSFUL: Expected VINs are now available for CAO processing!')
            return True
        else:
            print(f'FIX INCOMPLETE: Only {len(expected_in_cao)}/11 expected VINs available')
            return False
            
    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_expected_vins()
    if success:
        print('\nVIN FILTERING ISSUE RESOLVED!')
    else:
        print('\nVIN FILTERING ISSUE STILL EXISTS')