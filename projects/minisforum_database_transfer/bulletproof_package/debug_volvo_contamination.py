#!/usr/bin/env python3
"""
DEBUG: Volvo Data Contamination Investigation
Critical investigation into why CAO returned 20 VINs instead of 11 expected
"""

import sys
from pathlib import Path

current_file = Path(__file__).resolve()
sys.path.insert(0, str(current_file.parent / 'scripts'))

from database_connection import db_manager

def investigate_contamination():
    """Investigate Volvo data contamination"""
    
    print('=== CRITICAL DATA CONTAMINATION INVESTIGATION ===')

    # Expected vs Actual VINs
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

    actual_vins = [
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
        'YV4M12RC3T1336034',  # CONTAMINATION
        'YV4062JE8T1435316',  # CONTAMINATION
        'YV4M12RC5T1341350',  # CONTAMINATION
        'YV4H60RC2T1343158',  # CONTAMINATION
        'YV4M12RC4T1335930',  # CONTAMINATION
        'YV4M12RM9T1335429',  # CONTAMINATION
        'YV4M12RC4T1337578',  # CONTAMINATION
        'YV4062JE7T1434433',  # CONTAMINATION
        'YV4M12RC8T1331153'   # CONTAMINATION
    ]

    contamination_vins = [vin for vin in actual_vins if vin not in expected_vins]
    print(f'CONTAMINATION DETECTED: {len(contamination_vins)} extra VINs')

    # Check raw Volvo data in Import 12
    print('\n1. RAW VOLVO DATA IN ACTIVE IMPORT 12:')
    raw_volvo = db_manager.execute_query("""
        SELECT COUNT(*) as total, COUNT(DISTINCT vin) as unique_vins
        FROM raw_vehicle_data 
        WHERE location ILIKE '%volvo%'
        AND import_id = 12
    """)

    if raw_volvo:
        result = raw_volvo[0]
        print(f'   Import 12 raw data: {result["total"]} records, {result["unique_vins"]} unique VINs')

    # Check ALL normalized Volvo data regardless of import
    print('\n2. ALL NORMALIZED VOLVO DATA:')
    all_normalized = db_manager.execute_query("""
        SELECT COUNT(*) as total, COUNT(DISTINCT vin) as unique_vins
        FROM normalized_vehicle_data 
        WHERE location ILIKE '%volvo%'
    """)

    if all_normalized:
        result = all_normalized[0]
        print(f'   Total normalized: {result["total"]} records, {result["unique_vins"]} unique VINs')

    # Check which imports have normalized Volvo data
    print('\n3. NORMALIZED VOLVO DATA BY IMPORT:')
    by_import = db_manager.execute_query("""
        SELECT rvd.import_id, si.status, COUNT(*) as records, COUNT(DISTINCT nvd.vin) as unique_vins
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location ILIKE '%volvo%'
        GROUP BY rvd.import_id, si.status
        ORDER BY rvd.import_id DESC
    """)

    if by_import:
        for imp in by_import:
            status_label = 'ACTIVE' if imp['status'] == 'active' else 'ARCHIVED'
            print(f'   Import {imp["import_id"]} ({status_label}): {imp["records"]} records, {imp["unique_vins"]} unique VINs')
            
            if imp['status'] != 'active':
                print(f'   *** CONTAMINATION: Import {imp["import_id"]} is archived but has normalized data ***')

    # Check contaminated VINs specifically
    print('\n4. INVESTIGATING SPECIFIC CONTAMINATED VINs:')
    for vin in contamination_vins[:3]:  # Check first 3
        print(f'\nVIN: {vin}')
        vin_records = db_manager.execute_query("""
            SELECT nvd.vin, rvd.import_id, si.status, si.import_date
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE nvd.vin = %s
            ORDER BY si.import_date DESC
        """, [vin])
        
        if vin_records:
            for rec in vin_records:
                print(f'  Import {rec["import_id"]} ({rec["status"]}): {rec["import_date"]}')
        else:
            print(f'  VIN {vin} NOT FOUND in normalized data!')

    print('\n5. SOLUTION: CLEAN UP CONTAMINATED NORMALIZED DATA')
    print('Need to remove normalized records from archived imports to prevent contamination')
    
    return contamination_vins

if __name__ == '__main__':
    contamination_vins = investigate_contamination()
    
    if contamination_vins:
        print('\n*** DATA CONTAMINATION CONFIRMED ***')
        print('The CAO process is including normalized data from archived imports')
        print('This violates the ACTIVE-ONLY rule for CAO processing')
        print('\nRECOMMENDATION: Run emergency cleanup of normalized data from archived imports')
    else:
        print('\nNo contamination detected - investigate other causes')