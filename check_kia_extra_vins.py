import sys
sys.path.insert(0, 'projects/minisforum_database_transfer/bulletproof_package/scripts')
from database_connection import db_manager

# The 15 extra VINs that shouldn't be in CAO results
extra_vins = [
    '3VV2B7AX6KM191657',
    'KM8K3CAB9NU805217',
    '5XXG14J25MG062369',
    'JA4AZ3A34FZ012946',
    '1V2EP2CA5JC598747',
    '3CZRE48579G705574',
    '1C4RJFAGXHC963646',
    '3LN6L5C96HR615183',
    '2HGFE2F52RH593526',
    '5XYK33DF2SG304041',
    '3KPFU4DE8SE033219',
    'KNDJ23AU2P7877527',
    '5XYK7CDF0RG193343',
    '3KPFT4DE3SE101106',
    '5XXG64J21RG241372'
]

print('=== INVESTIGATING WHY 15 EXTRA VINS ARE IN CAO RESULTS ===')
print(f'Checking {len(extra_vins)} VINs that should not be in CAO results')
print()

# Step 1: Check if these VINs exist in normalized_vehicle_data for Kia of Columbia
print('STEP 1: Checking normalized_vehicle_data table (what CAO uses)')
print('-' * 60)

for vin in extra_vins:
    # Check in normalized_vehicle_data - exactly what CAO queries
    query = '''
        SELECT nvd.vin, nvd.location, nvd.vehicle_condition, nvd.stock,
               nvd.on_lot_status, rvd.import_id, si.status
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.vin = %s 
        AND nvd.location = 'Kia of Columbia'
        AND si.status = 'active'
        AND nvd.on_lot_status IN ('onlot', 'on lot')
    '''
    
    result = db_manager.execute_query(query, [vin])
    
    if result:
        r = result[0]
        print(f'VIN: {vin}')
        print(f'  [FOUND IN NORMALIZED DATA]')
        print(f'  Location: {r["location"]}')
        print(f'  Condition: {r["vehicle_condition"]}')
        print(f'  Stock: {r["stock"]}')
        print(f'  On-lot status: {r["on_lot_status"]}')
        print(f'  Import ID: {r["import_id"]} (Status: {r["status"]})')
    else:
        print(f'VIN: {vin}')
        print(f'  [NOT IN NORMALIZED DATA] - Should NOT be in CAO results!')
    print()

print()
print('STEP 2: Checking VIN log (what CAO compares against)')
print('-' * 60)

# Step 2: Check if these VINs are in the VIN log
not_in_vinlog = []
in_vinlog = []

for vin in extra_vins:
    vinlog_check = db_manager.execute_query(
        'SELECT vin, order_type, order_number FROM kia_of_columbia_vin_log WHERE vin = %s', 
        [vin]
    )
    
    if vinlog_check:
        in_vinlog.append((vin, vinlog_check[0]))
        print(f'VIN: {vin}')
        print(f'  [IN VIN LOG] Order type: {vinlog_check[0]["order_type"]}, Order #: {vinlog_check[0]["order_number"]}')
        print(f'  ERROR: This VIN should NOT be in CAO results!')
    else:
        not_in_vinlog.append(vin)
        print(f'VIN: {vin}')
        print(f'  [NOT IN VIN LOG] - Correctly included in CAO if in normalized data')
    print()

print()
print('=== SUMMARY ===')
print(f'Extra VINs not in VIN log (correct for CAO): {len(not_in_vinlog)}')
for vin in not_in_vinlog:
    print(f'  - {vin}')

if in_vinlog:
    print(f'\nExtra VINs IN VIN log (SHOULD NOT BE IN CAO): {len(in_vinlog)}')
    for vin, record in in_vinlog:
        print(f'  - {vin} (Order: {record["order_number"]})')
    print('\n[PROBLEM IDENTIFIED] These VINs are in the VIN log but still appearing in CAO results!')

# Step 3: Double-check by simulating the exact CAO query
print()
print('STEP 3: Simulating exact CAO query for Kia of Columbia')
print('-' * 60)

cao_query = '''
    SELECT nvd.vin
    FROM normalized_vehicle_data nvd
    JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
    JOIN scraper_imports si ON rvd.import_id = si.import_id
    WHERE nvd.location = %s 
    AND nvd.on_lot_status IN ('onlot', 'on lot')
    AND si.status = 'active'
    AND nvd.vehicle_condition IN (%s, %s)
    AND nvd.stock IS NOT NULL 
    AND nvd.stock != %s 
    AND nvd.stock != %s
'''

cao_vehicles = db_manager.execute_query(
    cao_query, 
    ['Kia of Columbia', 'po', 'cpo', '', '*']
)

cao_vins = [v['vin'] for v in cao_vehicles] if cao_vehicles else []
print(f'Total vehicles from CAO query: {len(cao_vins)}')

# Check which extra VINs are in CAO query results
extra_in_cao = [vin for vin in extra_vins if vin in cao_vins]
print(f'\nExtra VINs found in CAO query: {len(extra_in_cao)}')
for vin in extra_in_cao:
    print(f'  - {vin}')