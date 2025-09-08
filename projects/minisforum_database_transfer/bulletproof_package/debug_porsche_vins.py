#!/usr/bin/env python3

import sys
import os
sys.path.append('scripts')
from database_connection import DatabaseManager

def main():
    db_manager = DatabaseManager()

    print('DIRECT VIN COMPARISON: Normalized Vehicle Data vs Porsche VIN Log')
    print('=' * 70)

    # Get VINs from current normalized vehicle data for Porsche (onlot vehicles)
    print('Step 1: Getting VINs from current normalized vehicle data (onlot only)...')
    normalized_vins_query = '''
        SELECT DISTINCT nvd.vin, nvd.vehicle_condition, nvd.on_lot_status
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = 'Porsche St. Louis'
        AND si.status = 'active'
        AND nvd.on_lot_status = 'onlot'
        ORDER BY nvd.vin
    '''

    normalized_result = db_manager.execute_query(normalized_vins_query)
    if normalized_result:
        normalized_vins = [row['vin'] for row in normalized_result]
        print(f'Found {len(normalized_vins)} onlot VINs in normalized data')
        print('First 5 VINs:', normalized_vins[:5])
    else:
        print('ERROR getting normalized VINs')
        normalized_vins = []

    print()

    # Get VINs from Porsche VIN log
    print('Step 2: Getting VINs from Porsche VIN log...')
    vinlog_query = '''
        SELECT DISTINCT vin 
        FROM porsche_st_louis_vin_log 
        ORDER BY vin
    '''

    vinlog_result = db_manager.execute_query(vinlog_query)
    if vinlog_result:
        vinlog_vins = [row['vin'] for row in vinlog_result]
        print(f'Found {len(vinlog_vins)} VINs in Porsche VIN log')
        print('First 5 VINs:', vinlog_vins[:5])
    else:
        print('ERROR getting VIN log VINs')
        vinlog_vins = []

    print()

    # Find VINs in normalized data but NOT in VIN log
    print('Step 3: Finding VINs in normalized data but NOT in VIN log...')
    normalized_set = set(normalized_vins)
    vinlog_set = set(vinlog_vins)

    missing_from_vinlog = normalized_set - vinlog_set
    print(f'VINs in normalized data but NOT in VIN log: {len(missing_from_vinlog)}')

    if missing_from_vinlog:
        print('These VINs should trigger CAO processing:')
        for i, vin in enumerate(sorted(missing_from_vinlog)[:10]):  # Show first 10
            print(f'  {i+1}. {vin}')
        if len(missing_from_vinlog) > 10:
            print(f'  ... and {len(missing_from_vinlog) - 10} more')
    else:
        print('All VINs in normalized data already exist in VIN log')

    print()

    # Also check reverse - VINs in VIN log but not in current normalized data
    missing_from_normalized = vinlog_set - normalized_set
    print(f'VINs in VIN log but NOT in current normalized data: {len(missing_from_normalized)}')

    print()
    print('SUMMARY:')
    print(f'- Normalized onlot VINs: {len(normalized_vins)}')
    print(f'- VIN log VINs: {len(vinlog_vins)}')
    print(f'- Missing from VIN log (should process): {len(missing_from_vinlog)}')
    print(f'- Missing from normalized (archived): {len(missing_from_normalized)}')

    # If we found discrepancies, show detailed breakdown
    if missing_from_vinlog:
        print()
        print('DETAILED BREAKDOWN OF MISSING VINS:')
        print('-' * 50)
        
        # Get detailed info about missing VINs
        missing_vins_list = list(missing_from_vinlog)
        placeholders = ','.join(['%s'] * len(missing_vins_list))
        
        detailed_query = f'''
            SELECT nvd.vin, nvd.vehicle_condition, nvd.on_lot_status, nvd.make, nvd.model, nvd.year
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE nvd.location = 'Porsche St. Louis'
            AND si.status = 'active'
            AND nvd.on_lot_status = 'onlot'
            AND nvd.vin IN ({placeholders})
            ORDER BY nvd.vin
            LIMIT 20
        '''
        
        detailed_result = db_manager.execute_query(detailed_query, tuple(missing_vins_list))
        if detailed_result:
            print('Sample of VINs that should be processed:')
            for row in detailed_result:
                vin = row['vin']
                condition = row['vehicle_condition']
                status = row['on_lot_status']
                make = row['make']
                model = row['model']
                year = row['year']
                print(f'  {vin} - {year} {make} {model} ({condition}, {status})')
    
    db_manager.close_connection()

if __name__ == "__main__":
    main()