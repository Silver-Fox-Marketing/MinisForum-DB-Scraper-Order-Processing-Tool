#!/usr/bin/env python3
"""Debug Suntrup Ford West CAO issue"""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from database_connection import db_manager

# Check if these specific VINs are in current inventory
vins_to_check = [
    '1FMJK1MT8NEA40714',
    '1FTEW1E52LKE37327', 
    '1G6DH5RL0M0144239',
    '2LMPJ6K96NBL18706',
    '5FPYK1F59BB007451',
    'JM1BM1V33F1238384',
    'W1N0G8DB6NG121113'
]

print('=== CHECKING SUNTRUP FORD WEST INVENTORY FOR EXPECTED VINS ===')
found_vins = []
for vin in vins_to_check:
    result = db_manager.execute_query('''
        SELECT vin, type, make, model, year, price 
        FROM raw_vehicle_data 
        WHERE location = %s
        AND vin = %s
    ''', ('Suntrup Ford West', vin))
    
    if result:
        vehicle = result[0]
        print(f'[FOUND] {vin} - {vehicle["type"]} {vehicle["year"]} {vehicle["make"]} {vehicle["model"]} - ${vehicle["price"]}')
        found_vins.append(vin)
    else:
        print(f'[NOT FOUND] {vin}')

print(f'\nFound {len(found_vins)} out of {len(vins_to_check)} VINs in current inventory')

# Check if these VINs are in VIN log
print('\n=== CHECKING VIN LOG FOR THESE VINS ===')
for vin in found_vins:
    result = db_manager.execute_query('''
        SELECT vin, processed_date, order_number 
        FROM suntrup_ford_west_vin_log 
        WHERE vin = %s
    ''', (vin,))
    
    if result:
        print(f'[IN VIN LOG] {vin} - Processed: {result[0]["processed_date"]} - Order: {result[0]["order_number"]}')
    else:
        print(f'[NEW] {vin} - Should be included in CAO')

# Check dealership config
print('\n=== SUNTRUP FORD WEST CONFIGURATION ===')
config = db_manager.execute_query('''
    SELECT * FROM dealership_configs 
    WHERE dealership_name = %s
''', ('Suntrup Ford West',))

if config:
    for key, value in config[0].items():
        print(f'{key}: {value}')
else:
    print('No configuration found for Suntrup Ford West')

# Check total inventory count
print('\n=== INVENTORY STATS ===')
stats = db_manager.execute_query('''
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN type ILIKE %s THEN 1 END) as new_count,
        COUNT(CASE WHEN type ILIKE %s THEN 1 END) as used_count,
        COUNT(CASE WHEN type ILIKE %s OR type ILIKE %s THEN 1 END) as certified_count
    FROM raw_vehicle_data 
    WHERE location = %s
''', ('%new%', '%used%', '%certified%', '%cpo%', 'Suntrup Ford West'))

if stats:
    print(f'Total vehicles: {stats[0]["total"]}')
    print(f'New vehicles: {stats[0]["new_count"]}')  
    print(f'Used vehicles: {stats[0]["used_count"]}')
    print(f'Certified vehicles: {stats[0]["certified_count"]}')

# Get a sample of current inventory
print('\n=== SAMPLE OF CURRENT INVENTORY ===')
sample = db_manager.execute_query('''
    SELECT vin, type, year, make, model, price
    FROM raw_vehicle_data 
    WHERE location = %s
    AND type ILIKE %s
    ORDER BY import_timestamp DESC
    LIMIT 10
''', ('Suntrup Ford West', '%used%'))

for vehicle in sample:
    print(f'{vehicle["vin"]} - {vehicle["type"]} - {vehicle["year"]} {vehicle["make"]} {vehicle["model"]} - ${vehicle["price"]}')