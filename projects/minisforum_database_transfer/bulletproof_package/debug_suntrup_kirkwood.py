#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
from database_connection import DatabaseManager

# Connect to database
db_manager = DatabaseManager()

# Expected 9 VINs that should be in results
expected_vins = [
    '1C4HJXDG2JW305627',
    '3FA6P0H74FR234230', 
    '4S4WMAMD0N3469009',
    '1C4HJXCG7JW174387',
    '1FMCU0F75EUD29617',
    '1GCPYBEHXMZ173012',
    '3VV3B7AX6KM196670',
    '5TDKDRAH3PS008347',
    'KNMAT2MT3LP513444'
]

print('=== CHECKING SCRAPER_IMPORTS TABLE SCHEMA ===')
schema = db_manager.execute_query('''
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'scraper_imports'
    ORDER BY ordinal_position
''')
print('Available columns:')
for col in schema:
    print(f'  - {col}')

print('\n=== CHECKING ACTIVE IMPORT FOR SUNTRUP FORD KIRKWOOD ===')
active_import = db_manager.execute_query('''
    SELECT import_id, dealerships_list, status, total_vehicles, import_date
    FROM scraper_imports 
    WHERE 'Suntrup Ford Kirkwood' = ANY(dealerships_list)
    AND status = 'active'
    ORDER BY import_date DESC
    LIMIT 1
''')

if active_import:
    import_record = active_import[0]
    import_id = import_record['import_id']
    print(f'Active Import ID: {import_id}')
    print(f'Dealerships: {import_record["dealerships_list"]}')
    print(f'Vehicle Count: {import_record["total_vehicles"]}')
    
    # Check dealership filter settings 
    print('\n=== DEALERSHIP FILTER SETTINGS ===')
    try:
        dealership_config = db_manager.execute_query('''
            SELECT * FROM dealership_configs 
            WHERE dealership_name LIKE '%Suntrup Ford Kirkwood%'
            OR name LIKE '%Suntrup Ford Kirkwood%'
            LIMIT 1
        ''')
        
        if dealership_config:
            print(f'Found dealership config: {dealership_config[0]}')
        else:
            print('No dealership config found - this might explain the filtering issue')
    except Exception as e:
        print(f'Error checking dealership config: {e}')
        
    # Check raw_vehicle_data schema first
    print(f'\n=== RAW VEHICLE DATA SCHEMA ===')
    vehicle_schema = db_manager.execute_query('''
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'raw_vehicle_data'
        ORDER BY ordinal_position
    ''')
    for col in vehicle_schema[:10]:  # Show first 10 columns
        print(f'  - {col["column_name"]} ({col["data_type"]})')
    
    # Get all vehicles from active import for Suntrup Ford Kirkwood
    print(f'\n=== ALL SUNTRUP FORD KIRKWOOD VEHICLES IN ACTIVE IMPORT {import_id} ===')
    all_vehicles = db_manager.execute_query('''
        SELECT vin, type, stock, status, price, year, make, model, location
        FROM raw_vehicle_data
        WHERE import_id = %s
        AND location = 'Suntrup Ford Kirkwood'
        ORDER BY type, vin
    ''', (import_id,))
    
    print(f'Total vehicles in active import: {len(all_vehicles)}')
    
    # Separate expected vs unexpected vehicles
    unexpected_vehicles = []
    expected_found = []
    
    for vehicle in all_vehicles:
        vin = vehicle['vin']
        v_type = vehicle['type']
        stock_num = vehicle['stock'] 
        status = vehicle['status']
        price = vehicle['price']
        year = vehicle['year']
        make = vehicle['make']
        model = vehicle['model']
        
        if vin in expected_vins:
            expected_found.append(vehicle)
        else:
            unexpected_vehicles.append(vehicle)
    
    print(f'\nExpected VINs found: {len(expected_found)}/9')
    print(f'Unexpected vehicles: {len(unexpected_vehicles)}')
    
    # Analyze unexpected vehicles
    print(f'\n=== ANALYZING {len(unexpected_vehicles)} UNEXPECTED VEHICLES ===')
    new_count = 0
    missing_stock = 0
    in_transit = 0
    other_issues = 0
    
    for vehicle in unexpected_vehicles:
        vin = vehicle['vin']
        v_type = vehicle['type']
        stock_num = vehicle['stock'] 
        status = vehicle['status']
        price = vehicle['price']
        year = vehicle['year']
        make = vehicle['make']
        model = vehicle['model']
        
        issues = []
        if v_type and 'new' in v_type.lower():
            new_count += 1
            issues.append('NEW')
        if not stock_num or stock_num.strip() == '':
            missing_stock += 1
            issues.append('NO_STOCK')
        if status and ('transit' in status.lower() or 'pending' in status.lower()):
            in_transit += 1 
            issues.append('IN_TRANSIT')
        
        if not issues:
            other_issues += 1
            issues.append('OTHER')
            
        print(f'{vin} | {v_type} | {stock_num} | {status} | ${price} | {year} {make} {model} | ISSUES: {", ".join(issues)}')
    
    print(f'\n=== SUMMARY OF UNEXPECTED VEHICLES ===')
    print(f'NEW vehicles (should be filtered out): {new_count}')
    print(f'Missing stock numbers: {missing_stock}')
    print(f'In-transit/Pending: {in_transit}')
    print(f'Other issues: {other_issues}')
    print(f'Total unexpected: {len(unexpected_vehicles)}')
    
else:
    print('No active import found for Suntrup Ford Kirkwood')

db_manager.close()