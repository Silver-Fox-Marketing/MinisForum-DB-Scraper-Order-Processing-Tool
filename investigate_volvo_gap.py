#!/usr/bin/env python3
"""
Investigate why Volvo test returned 20 VINs instead of 52 from CAO query
Critical investigation into the gap between expected results
"""

import sys
from pathlib import Path

current_file = Path(__file__).resolve()
sys.path.insert(0, str(current_file.parent / 'scripts'))

from database_connection import db_manager

def investigate_volvo_gap():
    """Investigate the gap between CAO query results and test results"""
    
    print('=== CRITICAL: WHY DID TEST RETURN ONLY 20 VINS INSTEAD OF 52? ===')

    # Expected VINs from original handover
    expected_vins = [
        'YV4M12RM7S1225123',
        'LVY062AEXSP456045', 
        'YV4H60RM4S1189429',
        '7JDEV3KKXSG009880',
        'YV4L12WK6S2148446',
        'YV4M12JB4S1376169',
        'YV4M12RC2T1336011',
        'YV4M12RM1T1337062',
        'YV4M12RC5T1329666',
        'YV4M12RC8T1342069',
        'YV4H60RM2T1325073'
    ]

    # VINs actually returned in test
    actual_test_vins = [
        'YV4M12RM7S1225123',
        'LVY062AEXSP456045',
        'YV4H60RM4S1189429',
        '7JDEV3KKXSG009880',
        'YV4L12WK6S2148446',
        'YV4M12JB4S1376169',
        'YV4M12RC2T1336011',
        'YV4M12RM1T1337062',
        'YV4M12RC5T1329666',
        'YV4M12RC8T1342069',
        'YV4H60RM2T1325073',
        'YV4M12RC3T1336034',
        'YV4062JE8T1435316',
        'YV4M12RC5T1341350',
        'YV4H60RC2T1343158',
        'YV4M12RC4T1335930',
        'YV4M12RM9T1335429',
        'YV4M12RC4T1337578',
        'YV4062JE7T1434433',
        'YV4M12RC8T1331153'
    ]

    print(f'Expected VINs: {len(expected_vins)}')
    print(f'Test returned: {len(actual_test_vins)}')
    print(f'CAO query found: 52 VINs (from previous debug)')

    # Check VIN log status for expected VINs
    print('\n=== VIN LOG STATUS FOR EXPECTED VINs ===')
    found_in_log = 0
    not_in_log = []
    
    for vin in expected_vins:
        vin_check = db_manager.execute_query("""
            SELECT vin FROM volvo_cars_west_county_vin_log WHERE vin = %s
        """, [vin])
        
        if vin_check:
            found_in_log += 1
            print(f'{vin}: IN VIN LOG (should not appear in CAO)')
        else:
            not_in_log.append(vin)
            print(f'{vin}: NOT IN VIN LOG (should appear in CAO)')

    print(f'\nSUMMARY: {found_in_log}/11 expected VINs are already in VIN log')
    print(f'Expected CAO results: {len(not_in_log)} VINs (those not in log)')

    # Check on-lot status filtering
    print('\n=== ON-LOT STATUS FILTERING ===')
    onlot_only = db_manager.execute_query("""
        SELECT COUNT(*) as onlot_count
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = 'Volvo Cars West County'
        AND si.status = 'active'
        AND nvd.vehicle_condition = 'new'
        AND nvd.on_lot_status = 'onlot'
        AND nvd.vin NOT IN (SELECT vin FROM volvo_cars_west_county_vin_log)
    """)

    if onlot_only:
        result = onlot_only[0]
        print(f'CAO with ON-LOT only filtering: {result["onlot_count"]} vehicles')
        
        if result["onlot_count"] == 20:
            print('*** FOUND THE CAUSE: ON-LOT filtering reduces 52 to 20 VINs ***')

    # Verify test VINs are all on-lot
    print('\n=== VERIFYING TEST VINS ARE ON-LOT ===')
    for vin in actual_test_vins[:5]:  # Check first 5
        lot_status = db_manager.execute_query("""
            SELECT nvd.vin, nvd.on_lot_status
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE nvd.vin = %s
            AND nvd.location = 'Volvo Cars West County'
            AND si.status = 'active'
        """, [vin])
        
        if lot_status:
            status = lot_status[0]["on_lot_status"]
            print(f'{vin}: {status}')

    # Check if there are off-lot vehicles that CAO found but test didn't return
    print('\n=== OFF-LOT VEHICLES EXCLUDED FROM TEST ===')
    offlot_vins = db_manager.execute_query("""
        SELECT nvd.vin, nvd.on_lot_status
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = 'Volvo Cars West County'
        AND si.status = 'active'
        AND nvd.vehicle_condition = 'new'
        AND nvd.on_lot_status = 'offlot'
        AND nvd.vin NOT IN (SELECT vin FROM volvo_cars_west_county_vin_log)
        LIMIT 5
    """)

    if offlot_vins:
        print('Sample OFF-LOT VINs excluded from test results:')
        for vehicle in offlot_vins:
            print(f'  {vehicle["vin"]} ({vehicle["on_lot_status"]})')
        print(f'These explain the gap: 52 total - 20 on-lot = 32 off-lot vehicles')

if __name__ == '__main__':
    investigate_volvo_gap()