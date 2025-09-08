import sys
sys.path.insert(0, 'projects/minisforum_database_transfer/bulletproof_package/scripts')
from database_connection import db_manager

# The 15 extra VINs
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

print('=== CHECKING FOR DATA CONTAMINATION IN NORMALIZED DATA ===')
print(f'Investigating {len(extra_vins)} extra VINs')
print()

# Check each VIN in normalized data
for vin in extra_vins:
    # Check in normalized_vehicle_data with active import
    query = '''
        SELECT nvd.vin, nvd.location, nvd.vehicle_condition, 
               rvd.location as raw_location, si.import_id, si.status,
               si.dealership as import_dealership
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.vin = %s 
        AND si.status = 'active'
    '''
    
    result = db_manager.execute_query(query, [vin])
    
    if result:
        r = result[0]
        print(f'VIN: {vin}')
        print(f'  Normalized location: {r["location"]}')
        print(f'  Raw location: {r["raw_location"]}')
        print(f'  Import dealership: {r["import_dealership"]}')
        print(f'  Vehicle condition: {r["vehicle_condition"]}')
        print(f'  Import ID: {r["import_id"]} (Status: {r["status"]})')
        
        # Check if this is contamination
        if r['location'] != 'Kia of Columbia' or r['import_dealership'] != 'Kia of Columbia':
            print(f'  [CONTAMINATION] This VIN is from {r["import_dealership"]} but showing in Kia of Columbia data!')
        else:
            print(f'  [OK] VIN correctly associated with Kia of Columbia')
            
            # Check if it's in the VIN log
            vinlog_check = db_manager.execute_query(
                'SELECT vin, order_type FROM kia_of_columbia_vin_log WHERE vin = %s', 
                [vin]
            )
            if vinlog_check:
                print(f'  [MYSTERY] VIN IS in VIN log as {vinlog_check[0]["order_type"]} - should not be in CAO!')
            else:
                print(f'  [CONFIRMED] VIN is NOT in VIN log - correctly included in CAO')
    else:
        print(f'VIN: {vin}')
        print(f'  [NOT FOUND] Not in active normalized data - should not be in CAO results')
    print()

# Summary check for data contamination
print('=== CONTAMINATION CHECK SUMMARY ===')
contamination_query = '''
    SELECT COUNT(DISTINCT nvd.vin) as total,
           nvd.location,
           si.dealership as import_dealership
    FROM normalized_vehicle_data nvd
    JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
    JOIN scraper_imports si ON rvd.import_id = si.import_id
    WHERE nvd.location = 'Kia of Columbia'
    AND si.status = 'active'
    GROUP BY nvd.location, si.dealership
'''

contamination_results = db_manager.execute_query(contamination_query)
for row in contamination_results:
    print(f'Location: {row["location"]} | Import from: {row["import_dealership"]} | Count: {row["total"]}')
    if row['location'] != row['import_dealership']:
        print('  [WARNING] Potential contamination detected!')