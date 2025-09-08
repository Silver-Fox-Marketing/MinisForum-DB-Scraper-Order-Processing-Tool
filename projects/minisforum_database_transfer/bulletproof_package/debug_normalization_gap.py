import sys
sys.path.insert(0, 'scripts')
from database_connection import db_manager

print('=== CRITICAL: FIND NORMALIZATION GAP ===')

expected_vins = [
    'YV4062JE7T1434433', 'YV4062JE8T1435316', 'YV4062PF7T1453502',
    'YV4H60RC2T1343158', 'YV4H60RM2T1325073', 'YV4M12RC3T1336034',
    'YV4M12RC4T1335930', 'YV4M12RC5T1329666', 'YV4M12RC8T1331153',
    'YV4M12RC8T1342069', 'YV4M12RM9T1335429'
]

dealership_name = 'Volvo Cars West County'
active_import_id = 12

try:
    # Check expected VINs in raw_vehicle_data for Import 12
    print('1. Check expected VINs in RAW data for Import 12...')
    raw_query = """
        SELECT vin, location, import_id, type
        FROM raw_vehicle_data 
        WHERE import_id = %s 
        AND location = %s
        AND vin = ANY(%s)
        ORDER BY vin
    """
    
    raw_results = db_manager.execute_query(raw_query, [active_import_id, dealership_name, expected_vins])
    print(f'Expected VINs in RAW Import 12: {len(raw_results)}/11')
    
    for result in raw_results:
        print(f'  - {result["vin"]} | Type: {result["type"]}')
    
    # Check expected VINs in normalized_vehicle_data for Import 12
    print('\n2. Check expected VINs in NORMALIZED data for Import 12...')
    normalized_query = """
        SELECT nvd.vin, nvd.location, nvd.on_lot_status, nvd.vehicle_condition, rvd.import_id
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        WHERE rvd.import_id = %s 
        AND nvd.location = %s
        AND nvd.vin = ANY(%s)
        ORDER BY nvd.vin
    """
    
    normalized_results = db_manager.execute_query(normalized_query, [active_import_id, dealership_name, expected_vins])
    print(f'Expected VINs in NORMALIZED Import 12: {len(normalized_results)}/11')
    
    for result in normalized_results:
        print(f'  - {result["vin"]} | Status: {result["on_lot_status"]} | Condition: {result["vehicle_condition"]}')
    
    # Find the normalization gap
    raw_vins = [r['vin'] for r in raw_results]
    normalized_vins = [r['vin'] for r in normalized_results]
    missing_from_normalized = [vin for vin in raw_vins if vin not in normalized_vins]
    
    if missing_from_normalized:
        print(f'\n3. NORMALIZATION GAP FOUND: {len(missing_from_normalized)} VINs')
        print('VINs in RAW but missing from NORMALIZED:')
        for vin in missing_from_normalized:
            print(f'  - {vin}')
            
        # Get the raw_data_id for missing VINs
        print('\n4. Check raw_data_id for missing VINs...')
        raw_id_query = """
            SELECT id as raw_data_id, vin, type
            FROM raw_vehicle_data 
            WHERE import_id = %s 
            AND location = %s
            AND vin = ANY(%s)
            ORDER BY vin
        """
        
        raw_ids = db_manager.execute_query(raw_id_query, [active_import_id, dealership_name, missing_from_normalized])
        print(f'Raw data IDs for missing VINs: {len(raw_ids)}')
        
        for result in raw_ids:
            print(f'  - {result["vin"]} | raw_data_id: {result["raw_data_id"]} | Type: {result["type"]}')
            
            # Check if normalized record exists with this raw_data_id
            check_normalized_query = """
                SELECT id, vin, on_lot_status, vehicle_condition
                FROM normalized_vehicle_data
                WHERE raw_data_id = %s
            """
            
            norm_check = db_manager.execute_query(check_normalized_query, [result["raw_data_id"]])
            if norm_check:
                print(f'    -> Normalized record EXISTS: {norm_check[0]["vin"]} | Status: {norm_check[0]["on_lot_status"]}')
            else:
                print(f'    -> NO normalized record for raw_data_id {result["raw_data_id"]}')
    else:
        print('\n3. NO NORMALIZATION GAP: All raw VINs have normalized records')
        
    # Check total normalization coverage for Import 12
    print('\n5. Check total normalization coverage for Import 12...')
    coverage_query = """
        SELECT 
            COUNT(rvd.id) as total_raw,
            COUNT(nvd.id) as total_normalized,
            COUNT(rvd.id) - COUNT(nvd.id) as missing_normalized
        FROM raw_vehicle_data rvd
        LEFT JOIN normalized_vehicle_data nvd ON rvd.id = nvd.raw_data_id
        WHERE rvd.import_id = %s 
        AND rvd.location = %s
    """
    
    coverage = db_manager.execute_query(coverage_query, [active_import_id, dealership_name])
    if coverage:
        cov = coverage[0]
        print(f'Import 12 Volvo normalization coverage:')
        print(f'  Total RAW records: {cov["total_raw"]}')
        print(f'  Total NORMALIZED records: {cov["total_normalized"]}')
        print(f'  Missing NORMALIZED records: {cov["missing_normalized"]}')
        
        if cov["missing_normalized"] > 0:
            print(f'  PROBLEM: {cov["missing_normalized"]} raw records are not normalized!')
        else:
            print('  SUCCESS: All raw records have normalized records')
        
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()