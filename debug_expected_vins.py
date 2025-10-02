import sys
sys.path.insert(0, 'scripts')
from database_connection import db_manager

print('=== CRITICAL: FIND EXPECTED VINS ROOT CAUSE ===')

expected_vins = [
    'YV4062JE7T1434433', 'YV4062JE8T1435316', 'YV4062PF7T1453502',
    'YV4H60RC2T1343158', 'YV4H60RM2T1325073', 'YV4M12RC3T1336034',
    'YV4M12RC4T1335930', 'YV4M12RC5T1329666', 'YV4M12RC8T1331153',
    'YV4M12RC8T1342069', 'YV4M12RM9T1335429'
]

try:
    # Find expected VINs in raw_vehicle_data
    print('1. Find expected VINs in RAW vehicle data...')
    raw_vins_query = """
        SELECT vin, location, import_id, type as raw_type
        FROM raw_vehicle_data 
        WHERE vin = ANY(%s)
        ORDER BY import_id DESC, vin
    """
    
    raw_results = db_manager.execute_query(raw_vins_query, [expected_vins])
    print(f'Expected VINs in raw_vehicle_data: {len(raw_results)}')
    
    raw_import_counts = {}
    for result in raw_results:
        import_id = result['import_id']
        if import_id not in raw_import_counts:
            raw_import_counts[import_id] = {'location': result['location'], 'count': 0, 'vins': []}
        raw_import_counts[import_id]['count'] += 1
        raw_import_counts[import_id]['vins'].append(result['vin'])
    
    for import_id, data in raw_import_counts.items():
        print(f'  Import {import_id}: {data["count"]} expected VINs')
        print(f'    Location: {data["location"]}')
    
    # Check import status for the import containing expected VINs
    if raw_import_counts:
        main_import_id = list(raw_import_counts.keys())[0]
        print(f'\n2. Check status of Import {main_import_id} containing expected VINs...')
        
        import_status_query = """
            SELECT import_id, status, import_date, total_vehicles
            FROM scraper_imports 
            WHERE import_id = %s
        """
        
        import_status = db_manager.execute_query(import_status_query, [main_import_id])
        if import_status:
            status_info = import_status[0]
            print(f'  Import {main_import_id}: status={status_info["status"]} | date={status_info["import_date"]} | vehicles={status_info["total_vehicles"]}')
            
            if status_info['status'] != 'active':
                print('  PROBLEM: This import is NOT active - expected VINs will not show in CAO!')
                print('  This is the root cause of the VIN filtering issue.')
            else:
                print('  Import is ACTIVE - VINs should be available.')
        
    # Find which import is currently active
    print('\n3. Find current ACTIVE import...')
    active_query = """
        SELECT import_id, status, import_date, total_vehicles
        FROM scraper_imports 
        WHERE status = 'active'
        ORDER BY import_id DESC
    """
    
    active_imports = db_manager.execute_query(active_query)
    print(f'Active imports: {len(active_imports)}')
    for imp in active_imports:
        print(f'  Import {imp["import_id"]}: status={imp["status"]} | vehicles={imp["total_vehicles"]} | date={imp["import_date"]}')
        
    print('\n=== SOLUTION ===')
    if raw_import_counts and active_imports:
        expected_import = list(raw_import_counts.keys())[0] 
        active_import = active_imports[0]['import_id']
        
        if expected_import != active_import:
            print(f'PROBLEM IDENTIFIED: Expected VINs are in Import {expected_import} but active import is {active_import}')
            print(f'SOLUTION: Either mark Import {expected_import} as active, or use data from Import {active_import}')
        else:
            print('Expected VINs are in the active import - issue is elsewhere')
        
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()