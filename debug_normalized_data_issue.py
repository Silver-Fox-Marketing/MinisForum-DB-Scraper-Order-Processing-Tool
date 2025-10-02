#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
from database_connection import DatabaseManager

def main():
    print("=== DEBUGGING SUNTRUP FORD KIRKWOOD NORMALIZED DATA FILTERING ===")
    
    db_manager = DatabaseManager()
    
    # Check normalized_vehicle_data schema
    print("\n1. CHECKING NORMALIZED VEHICLE DATA SCHEMA:")
    schema = db_manager.execute_query('''
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'normalized_vehicle_data'
        ORDER BY ordinal_position
    ''')
    
    for col in schema:
        print(f"  - {col['column_name']} ({col['data_type']})")
    
    # Check how vehicles are normalized for Suntrup Ford Kirkwood
    print("\n2. CHECKING NORMALIZED VEHICLES FOR SUNTRUP FORD KIRKWOOD:")
    normalized_data = db_manager.execute_query('''
        SELECT nvd.vin, nvd.vehicle_condition, rvd.type as raw_type, nvd.make, nvd.model, nvd.year
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = 'Suntrup Ford Kirkwood'
        AND si.status = 'active'
        ORDER BY nvd.vehicle_condition, rvd.type
        LIMIT 20
    ''')
    
    print(f"Found {len(normalized_data)} normalized vehicles:")
    new_count = 0
    used_count = 0
    
    for vehicle in normalized_data:
        vin = vehicle['vin']
        normalized_condition = vehicle['vehicle_condition']
        raw_type = vehicle['raw_type']
        
        if normalized_condition == 'new':
            new_count += 1
        else:
            used_count += 1
            
        print(f"  {vin} | Raw: {raw_type} | Normalized: {normalized_condition} | {vehicle['year']} {vehicle['make']} {vehicle['model']}")
    
    print(f"\nNormalized vehicle summary:")
    print(f"  - NEW vehicles: {new_count}")
    print(f"  - USED vehicles: {used_count}")
    
    # Check what the CAO query would return with current filtering
    print(f"\n3. TESTING CAO QUERY WITH CURRENT FILTERING:")
    
    # This mirrors the exact query from correct_order_processing.py
    cao_query = '''
        SELECT nvd.vin, nvd.vehicle_condition, rvd.type as raw_type, nvd.make, nvd.model, nvd.year
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = %s
        AND si.status = 'active'
        AND nvd.vehicle_condition IN (%s, %s, %s, %s, %s)
        ORDER BY nvd.created_at DESC
        LIMIT 50
    '''
    
    # Test with the allowed_vehicle_types from our config: ['used', 'po', 'cpo', 'certified', 'pre-owned']
    cao_result = db_manager.execute_query(cao_query, (
        'Suntrup Ford Kirkwood',
        'used', 'po', 'cpo', 'certified', 'pre-owned'
    ))
    
    print(f"CAO query would return {len(cao_result)} vehicles:")
    new_in_cao = 0
    used_in_cao = 0
    
    for vehicle in cao_result:
        condition = vehicle['vehicle_condition']
        if condition == 'new':
            new_in_cao += 1
            print(f"  [WARNING] NEW: {vehicle['vin']} | {condition} | {vehicle['year']} {vehicle['make']} {vehicle['model']}")
        else:
            used_in_cao += 1
            
    print(f"\nCAO query result summary:")
    print(f"  - NEW vehicles in results: {new_in_cao}")
    print(f"  - USED vehicles in results: {used_in_cao}")
    
    if new_in_cao == 0:
        print("  SUCCESS: CAO filtering is working correctly!")
    else:
        print(f"  ISSUE: {new_in_cao} new vehicles would be included in CAO processing")
    
    # Check if there's an issue with the normalized data
    print(f"\n4. CHECKING FOR NORMALIZATION ISSUES:")
    
    # Look for vehicles where raw_type is "New" but normalized condition is not "new"
    normalization_issues = db_manager.execute_query('''
        SELECT nvd.vin, rvd.type as raw_type, nvd.vehicle_condition, nvd.make, nvd.model, nvd.year
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = 'Suntrup Ford Kirkwood'
        AND si.status = 'active'
        AND (
            (rvd.type ILIKE '%new%' AND nvd.vehicle_condition != 'new')
            OR (rvd.type NOT ILIKE '%new%' AND nvd.vehicle_condition = 'new')
        )
        LIMIT 10
    ''')
    
    if normalization_issues:
        print(f"Found {len(normalization_issues)} normalization inconsistencies:")
        for issue in normalization_issues:
            print(f"  {issue['vin']} | Raw: {issue['raw_type']} | Normalized: {issue['vehicle_condition']} | {issue['year']} {issue['make']} {issue['model']}")
    else:
        print("No normalization inconsistencies found")
    
    db_manager.close()

if __name__ == "__main__":
    main()