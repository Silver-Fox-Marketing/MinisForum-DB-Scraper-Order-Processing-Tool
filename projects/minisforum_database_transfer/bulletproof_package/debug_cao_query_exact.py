#!/usr/bin/env python3
"""
DEBUG: Exact CAO Query Analysis
Investigate why CAO returned 20 VINs instead of 11 expected for Volvo
"""

import sys
from pathlib import Path

current_file = Path(__file__).resolve()
sys.path.insert(0, str(current_file.parent / 'scripts'))

from database_connection import db_manager

def debug_cao_query():
    """Debug the exact CAO query that returned 20 VINs"""
    
    print('=== DEBUGGING EXACT CAO QUERY LOGIC ===')
    
    # Expected VINs from original handover
    expected_vins = [
        'YV4M12RM7S1225123',
        'LVY062AEXSP456045', 
        'YV4H60RM4S1189429',
        '7JDEV3KKXSG009880',
        'YV4L12WK6S2148446',
        'YV4M12JB4S1376169',
        'YV4M12RC2T1336011',
        'YV4M12RM1T1337062',
        'YV4M12RC5T1329666',
        'YV4M12RC8T1342069',
        'YV4H60RM2T1325073'
    ]

    # Step 1: Check current inventory from active import (as CAO does)
    print('\n1. CURRENT INVENTORY FROM ACTIVE IMPORT 12:')
    current_inventory = db_manager.execute_query("""
        SELECT COUNT(*) as total_vehicles,
               COUNT(CASE WHEN nvd.vehicle_condition = 'new' THEN 1 END) as new_vehicles,
               COUNT(CASE WHEN nvd.on_lot_status = 'onlot' THEN 1 END) as onlot_vehicles
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = 'Volvo Cars West County'
        AND si.status = 'active'
    """)
    
    if current_inventory:
        result = current_inventory[0]
        print(f'   Total vehicles: {result["total_vehicles"]}')
        print(f'   New vehicles: {result["new_vehicles"]}')
        print(f'   On-lot vehicles: {result["onlot_vehicles"]}')

    # Step 2: Apply dealership filtering (new vehicles only for Volvo)
    print('\n2. AFTER DEALERSHIP FILTERING (new vehicles only):')
    filtered_inventory = db_manager.execute_query("""
        SELECT COUNT(*) as filtered_count,
               COUNT(CASE WHEN nvd.on_lot_status = 'onlot' THEN 1 END) as onlot_count
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = 'Volvo Cars West County'
        AND si.status = 'active'
        AND nvd.vehicle_condition = 'new'
    """)
    
    if filtered_inventory:
        result = filtered_inventory[0]
        print(f'   Filtered vehicles (new only): {result["filtered_count"]}')
        print(f'   On-lot vehicles: {result["onlot_count"]}')

    # Step 3: Check VIN log for Volvo Cars West County
    print('\n3. VOLVO VIN LOG STATUS:')
    vin_log_count = db_manager.execute_query("""
        SELECT COUNT(*) as log_count
        FROM volvo_cars_west_county_vin_log
    """)
    
    if vin_log_count:
        result = vin_log_count[0]
        print(f'   VIN log entries: {result["log_count"]}')

    # Step 4: Replicate exact CAO comparison (new vehicles not in VIN log)
    print('\n4. EXACT CAO COMPARISON - NEW VEHICLES NOT IN VIN LOG:')
    cao_query = db_manager.execute_query("""
        SELECT nvd.vin, nvd.year, nvd.make, nvd.model, nvd.on_lot_status
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = 'Volvo Cars West County'
        AND si.status = 'active'
        AND nvd.vehicle_condition = 'new'
        AND nvd.vin NOT IN (SELECT vin FROM volvo_cars_west_county_vin_log)
        ORDER BY nvd.vin
    """)
    
    if cao_query:
        print(f'   CAO result count: {len(cao_query)} vehicles')
        print('   Sample VINs from CAO query:')
        for i, vehicle in enumerate(cao_query[:10]):  # Show first 10
            status = '[EXPECTED]' if vehicle['vin'] in expected_vins else '[CONTAMINATION]'
            print(f'     {i+1}. {vehicle["vin"]} - {vehicle["year"]} {vehicle["make"]} {vehicle["model"]} ({vehicle["on_lot_status"]}) {status}')
        
        if len(cao_query) > 10:
            print(f'     ... and {len(cao_query) - 10} more vehicles')

    # Step 5: Identify contamination sources
    print('\n5. CONTAMINATION ANALYSIS:')
    cao_vins = [v['vin'] for v in cao_query] if cao_query else []
    expected_missing = [vin for vin in expected_vins if vin not in cao_vins]
    contamination_vins = [vin for vin in cao_vins if vin not in expected_vins]
    
    print(f'   Expected VINs missing: {len(expected_missing)}')
    if expected_missing:
        print('   Missing VINs:')
        for vin in expected_missing:
            print(f'     {vin}')
    
    print(f'   Contamination VINs: {len(contamination_vins)}')
    if contamination_vins:
        print('   Contaminated VINs (should not be in results):')
        for i, vin in enumerate(contamination_vins[:5]):  # Show first 5
            print(f'     {i+1}. {vin}')

    # Step 6: Check if missing expected VINs exist in normalized data
    if expected_missing:
        print('\n6. WHY ARE EXPECTED VINs MISSING?')
        for vin in expected_missing:
            vin_check = db_manager.execute_query("""
                SELECT nvd.vin, nvd.vehicle_condition, nvd.on_lot_status, 
                       si.import_id, si.status
                FROM normalized_vehicle_data nvd
                JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                JOIN scraper_imports si ON rvd.import_id = si.import_id
                WHERE nvd.vin = %s
                AND nvd.location = 'Volvo Cars West County'
            """, [vin])
            
            if vin_check:
                v = vin_check[0]
                print(f'   {vin}: condition={v["vehicle_condition"]}, lot={v["on_lot_status"]}, import={v["import_id"]} ({v["status"]})')
            else:
                print(f'   {vin}: NOT FOUND in normalized data')

if __name__ == '__main__':
    debug_cao_query()