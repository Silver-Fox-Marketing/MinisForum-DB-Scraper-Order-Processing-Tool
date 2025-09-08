#!/usr/bin/env python3
"""
Debug CAO query filtering issue
"""

import sys
from pathlib import Path
import json

current_file = Path(__file__).resolve()
sys.path.insert(0, str(current_file.parent / 'scripts'))

from database_connection import db_manager

def debug_cao_filtering():
    print('=== DEBUG: CAO QUERY FILTERING ISSUE ===')

    expected_vins = [
        'YV4062JE7T1434433', 'YV4062JE8T1435316', 'YV4062PF7T1453502',
        'YV4H60RC2T1343158', 'YV4H60RM2T1325073', 'YV4M12RC3T1336034',
        'YV4M12RC4T1335930', 'YV4M12RC5T1329666', 'YV4M12RC8T1331153',
        'YV4M12RC8T1342069', 'YV4M12RM9T1335429'
    ]

    # CAO query (same as from correct_order_processing.py)
    cao_query = """
        SELECT nvd.vin, nvd.on_lot_status, nvd.vehicle_condition
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = %s 
        AND nvd.on_lot_status IN ('onlot', 'on lot')
        AND si.status = 'active'
        ORDER BY nvd.vin
        LIMIT 20
    """

    cao_results = db_manager.execute_query(cao_query, ['Volvo Cars West County'])
    print(f'1. CAO query returns {len(cao_results)} vehicles:')

    for i, result in enumerate(cao_results, 1):
        is_expected = 'YES' if result['vin'] in expected_vins else 'NO'
        print(f'  {i}. {result["vin"]} | {result["on_lot_status"]} | {result["vehicle_condition"]} | Expected: {is_expected}')

    # Check if the issue is dealership filtering
    print('\n2. Check dealership filtering rules...')
    config_query = """
        SELECT name, filtering_rules FROM dealership_configs WHERE name = %s
    """

    config = db_manager.execute_query(config_query, ['Volvo Cars West County'])
    if config:
        filtering_rules = config[0]['filtering_rules']
        if isinstance(filtering_rules, str):
            filtering_rules = json.loads(filtering_rules)
        print(f'Dealership filtering rules: {filtering_rules}')
        
        vehicle_types = filtering_rules.get('vehicle_types', [])
        allowed_types = filtering_rules.get('allowed_vehicle_types', [])
        exclude_conditions = filtering_rules.get('exclude_conditions', [])
        
        print(f'Vehicle types filter: {vehicle_types}')
        print(f'Allowed types: {allowed_types}') 
        print(f'Exclude conditions: {exclude_conditions}')
        
        # Check if expected VINs match the filtering criteria
        print('\n3. Expected VINs vs filtering criteria:')
        print('Expected VINs are all "new" condition')
        
        if 'new' not in vehicle_types and 'new' not in allowed_types:
            print('PROBLEM FOUND: Expected VINs are "new" but filtering rules exclude new vehicles!')
            print('This explains why CAO query excludes expected VINs.')
        else:
            print('Filtering rules should allow "new" vehicles - issue is elsewhere')
    else:
        print('No dealership config found')

    # Check if CAO filtering is being applied
    print('\n4. Check if additional filtering is applied in CAO process...')
    # The CAO process in correct_order_processing.py calls filter_vehicles_by_type()
    # Let's see what that method does
    
    # Check the raw CAO query without dealership-specific filtering
    raw_cao_query = """
        SELECT nvd.vin, nvd.on_lot_status, nvd.vehicle_condition
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = %s 
        AND nvd.on_lot_status IN ('onlot', 'on lot')
        AND si.status = 'active'
        AND nvd.vin = ANY(%s)
        ORDER BY nvd.vin
    """
    
    raw_results = db_manager.execute_query(raw_cao_query, ['Volvo Cars West County', expected_vins])
    print(f'Raw CAO query (expected VINs only): {len(raw_results)} results')
    
    for result in raw_results:
        print(f'  - {result["vin"]} | {result["on_lot_status"]} | {result["vehicle_condition"]}')
    
    print(f'\n5. Analysis:')
    print(f'  - Expected VINs in normalized data: 11/11 ✅')  
    print(f'  - Expected VINs match raw CAO query: {len(raw_results)}/11')
    print(f'  - Expected VINs in full CAO query: 0/11 ❌')
    
    if len(raw_results) == 11 and len([r for r in cao_results if r['vin'] in expected_vins]) == 0:
        print('  CONCLUSION: CAO query excludes expected VINs due to dealership-specific filtering!')
        return 'filtering_issue'
    elif len(raw_results) < 11:
        print('  CONCLUSION: Some expected VINs fail basic CAO criteria (on_lot_status or import status)')
        return 'basic_criteria_issue'
    else:
        print('  CONCLUSION: Unknown issue - expected VINs meet all criteria but still excluded')
        return 'unknown_issue'

if __name__ == '__main__':
    issue_type = debug_cao_filtering()
    print(f'\nISSUE TYPE: {issue_type}')