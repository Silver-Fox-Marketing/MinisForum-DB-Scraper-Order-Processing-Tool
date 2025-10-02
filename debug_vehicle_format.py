#!/usr/bin/env python3
"""
Debug vehicle data format for filtering
"""

import sys
from pathlib import Path

current_file = Path(__file__).resolve()
sys.path.insert(0, str(current_file.parent / 'scripts'))

from database_connection import db_manager

def debug_vehicle_format():
    print('=== DEBUG: VEHICLE DATA FORMAT FOR FILTERING ===')
    
    expected_vins = ['YV4M12RM7S1225123', 'LVY062AEXSP456045', 'YV4H60RM4S1189429']

    # Check the exact format of vehicles returned by CAO query
    cao_query = """
        SELECT nvd.vin, nvd.on_lot_status, nvd.vehicle_condition, nvd.status as raw_status
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = %s 
        AND nvd.on_lot_status IN ('onlot', 'on lot')
        AND si.status = 'active'
        AND nvd.vehicle_condition = 'new'
        AND nvd.vin = ANY(%s)
        ORDER BY nvd.created_at DESC
        LIMIT 3
    """

    results = db_manager.execute_query(cao_query, ['Volvo Cars West County', expected_vins])

    print(f'Found {len(results)} vehicles:')

    for vehicle in results:
        print(f'\nVehicle: {vehicle["vin"]}')
        print(f'Data keys: {list(vehicle.keys())}')
        print(f'Data values:')
        for key, value in vehicle.items():
            print(f'  {key}: {repr(value)}')
        
        # Test the filtering logic paths
        vehicle_type = vehicle.get('type', '').lower()
        vehicle_condition = vehicle.get('vehicle_condition', '').lower() 
        raw_status = vehicle.get('raw_status', '').lower()
        
        print(f'Filtering checks:')
        print(f'  vehicle.get("type"): "{vehicle_type}"')
        print(f'  vehicle.get("vehicle_condition"): "{vehicle_condition}"')
        print(f'  vehicle.get("raw_status"): "{raw_status}"')
        
        # The filtering logic checks: vehicle.get('type', '').lower()
        # But our data has: vehicle_condition = 'new'
        # This is the mismatch!
        
    # Check what the _get_dealership_vehicles method actually returns
    print(f'\n=== CHECK _get_dealership_vehicles RETURN FORMAT ===')
    
    vehicles_query = """
        SELECT nvd.* FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = %s 
        AND nvd.on_lot_status IN ('onlot', 'on lot')
        AND si.status = 'active'
        AND nvd.vehicle_condition = 'new'
        AND nvd.vin = ANY(%s)
        LIMIT 1
    """
    
    full_vehicles = db_manager.execute_query(vehicles_query, ['Volvo Cars West County', expected_vins])
    
    if full_vehicles:
        vehicle = full_vehicles[0]
        print(f'Full vehicle record has these keys:')
        for key in sorted(vehicle.keys()):
            print(f'  {key}: {repr(vehicle[key])}')
            
        # Check if there's a 'type' field vs 'vehicle_condition'
        type_value = vehicle.get('type', 'NOT FOUND')
        condition_value = vehicle.get('vehicle_condition', 'NOT FOUND')
        
        print(f'\nCRITICAL COMPARISON:')
        print(f'  vehicle["type"]: {repr(type_value)}')
        print(f'  vehicle["vehicle_condition"]: {repr(condition_value)}')
        
        if type_value == 'NOT FOUND' and condition_value != 'NOT FOUND':
            print(f'\nPROBLEM IDENTIFIED: Filtering logic checks "type" but vehicles have "vehicle_condition"!')
            return 'field_name_mismatch'
        elif type_value != condition_value:
            print(f'\nPROBLEM: "type" and "vehicle_condition" have different values!')
            return 'field_value_mismatch'
        else:
            print(f'\nFields match - issue is elsewhere')
            return 'unknown'

if __name__ == '__main__':
    issue_type = debug_vehicle_format()
    print(f'\nISSUE TYPE: {issue_type}')