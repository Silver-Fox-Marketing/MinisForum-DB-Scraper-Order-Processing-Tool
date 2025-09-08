#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
from database_connection import DatabaseManager

def main():
    print("=== INVESTIGATING SOUTH COUNTY DCJR NAME MAPPING ISSUE ===")
    
    db_manager = DatabaseManager()
    
    # Check all possible name variations in different tables
    print("\n1. CHECKING NAME VARIATIONS IN RAW_VEHICLE_DATA:")
    raw_locations = db_manager.execute_query("""
        SELECT DISTINCT location, COUNT(*) as vehicle_count
        FROM raw_vehicle_data rvd
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE (location ILIKE '%south%county%' 
               OR location ILIKE '%soco%' 
               OR location ILIKE '%dcjr%')
        AND si.status = 'active'
        GROUP BY location
        ORDER BY location
    """)
    
    print("Found locations in raw_vehicle_data:")
    for loc in raw_locations:
        print(f"  '{loc['location']}' - {loc['vehicle_count']} vehicles")
    
    print("\n2. CHECKING NAME VARIATIONS IN NORMALIZED_VEHICLE_DATA:")
    norm_locations = db_manager.execute_query("""
        SELECT DISTINCT nvd.location, COUNT(*) as vehicle_count
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE (nvd.location ILIKE '%south%county%' 
               OR nvd.location ILIKE '%soco%' 
               OR nvd.location ILIKE '%dcjr%')
        AND si.status = 'active'
        GROUP BY nvd.location
        ORDER BY nvd.location
    """)
    
    print("Found locations in normalized_vehicle_data:")
    for loc in norm_locations:
        print(f"  '{loc['location']}' - {loc['vehicle_count']} vehicles")
    
    print("\n3. CHECKING DEALERSHIP_CONFIGS TABLE:")
    configs = db_manager.execute_query("""
        SELECT id, name, filtering_rules->>'vehicle_types' as vehicle_types, is_active
        FROM dealership_configs
        WHERE name ILIKE '%south%county%' 
           OR name ILIKE '%soco%'
           OR name ILIKE '%dcjr%'
        ORDER BY name
    """)
    
    print("Found dealership configs:")
    for config in configs:
        print(f"  ID: {config['id']}, Name: '{config['name']}', Active: {config['is_active']}, Types: {config['vehicle_types']}")
    
    print("\n4. CHECKING VIN LOG TABLES:")
    vin_logs = db_manager.execute_query("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND (table_name ILIKE '%south%county%vin%'
             OR table_name ILIKE '%soco%vin%'
             OR table_name ILIKE '%dcjr%vin%')
        ORDER BY table_name
    """)
    
    print("Found VIN log tables:")
    for table in vin_logs:
        print(f"  {table['table_name']}")
        # Count entries
        count_result = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {table['table_name']}")
        if count_result:
            print(f"    - Contains {count_result[0]['count']} entries")
    
    print("\n5. CHECKING SCRAPER_IMPORTS FOR DEALERSHIP NAMES:")
    imports = db_manager.execute_query("""
        SELECT import_id, dealerships_list, status, total_vehicles, import_date
        FROM scraper_imports
        WHERE status = 'active'
        ORDER BY import_date DESC
        LIMIT 1
    """)
    
    if imports:
        dealerships = imports[0]['dealerships_list']
        print(f"Active import ID: {imports[0]['import_id']}")
        print(f"Import date: {imports[0]['import_date']}")
        print(f"Total vehicles: {imports[0]['total_vehicles']}")
        print("\nDealerships in active import:")
        for d in dealerships:
            if 'south' in d.lower() or 'dcjr' in d.lower() or 'soco' in d.lower():
                print(f"  >>> '{d}' <<<")
            else:
                print(f"  {d}")
    
    # Check what the CAO query would see
    print("\n6. SIMULATING CAO QUERY FOR DIFFERENT NAME VARIATIONS:")
    
    test_names = [
        'South County DCJR',
        'South County Dodge Chrysler Jeep RAM',
        'South County Autos',
        'SOCODCJR'
    ]
    
    for test_name in test_names:
        print(f"\nTesting CAO with name: '{test_name}'")
        
        # Check raw data
        raw_count = db_manager.execute_query("""
            SELECT COUNT(*) as count
            FROM raw_vehicle_data rvd
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE rvd.location = %s
            AND si.status = 'active'
        """, (test_name,))
        
        # Check normalized data
        norm_count = db_manager.execute_query("""
            SELECT COUNT(*) as count
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE nvd.location = %s
            AND si.status = 'active'
        """, (test_name,))
        
        print(f"  Raw vehicles: {raw_count[0]['count'] if raw_count else 0}")
        print(f"  Normalized vehicles: {norm_count[0]['count'] if norm_count else 0}")
    
    # Check the actual location in the active import
    print("\n7. CHECKING EXACT LOCATION NAME IN ACTIVE IMPORT:")
    actual_location = db_manager.execute_query("""
        SELECT DISTINCT rvd.location, COUNT(*) as count
        FROM raw_vehicle_data rvd
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE si.status = 'active'
        AND (rvd.location ILIKE '%south%county%' 
             OR rvd.location ILIKE '%dcjr%')
        GROUP BY rvd.location
    """)
    
    if actual_location:
        print(f"FOUND ACTUAL LOCATION NAME IN DATABASE:")
        for loc in actual_location:
            print(f"  >>> '{loc['location']}' with {loc['count']} vehicles <<<")
            print(f"  This is the EXACT name that must be used or mapped!")
    
    db_manager.close()

if __name__ == "__main__":
    main()