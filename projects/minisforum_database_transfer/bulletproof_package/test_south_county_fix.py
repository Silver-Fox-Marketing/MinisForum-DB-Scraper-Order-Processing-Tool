#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
from database_connection import DatabaseManager
from correct_order_processing import CorrectOrderProcessor

def main():
    print("=== TESTING SOUTH COUNTY DCJR NAME MAPPING FIX ===")
    
    db_manager = DatabaseManager()
    processor = CorrectOrderProcessor()
    
    # Test the CAO processing with the fixed name mapping
    print("\n1. TESTING CAO ORDER PROCESSING FOR SOUTH COUNTY DCJR:")
    try:
        # Test the name mapping first
        actual_location_name = processor.dealership_name_mapping.get('South County DCJR', 'South County DCJR')
        print(f"Config name 'South County DCJR' maps to: '{actual_location_name}'")
        
        # Check if we can find vehicles with the mapped name
        vehicle_count = db_manager.execute_query("""
            SELECT COUNT(*) as count
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE nvd.location = %s
            AND si.status = 'active'
            AND nvd.vehicle_condition IN ('used', 'po', 'cpo', 'certified', 'pre-owned', 'new')
            AND nvd.stock IS NOT NULL 
            AND nvd.stock != ''
            AND nvd.stock != '*'
        """, (actual_location_name,))
        
        if vehicle_count:
            print(f"Found {vehicle_count[0]['count']} vehicles in database for mapped location")
        
        # Check VIN log entries
        vin_log_count = db_manager.execute_query("""
            SELECT COUNT(*) as count FROM south_county_dcjr_vin_log
        """)
        
        if vin_log_count:
            print(f"VIN log contains {vin_log_count[0]['count']} previously processed vehicles")
        
        # Simulate what CAO would return (vehicles not in VIN log)
        cao_simulation = db_manager.execute_query("""
            SELECT COUNT(*) as count
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            LEFT JOIN south_county_dcjr_vin_log vlog ON nvd.vin = vlog.vin
            WHERE nvd.location = %s
            AND si.status = 'active'
            AND nvd.vehicle_condition IN ('used', 'po', 'cpo', 'certified', 'pre-owned', 'new')
            AND nvd.stock IS NOT NULL 
            AND nvd.stock != ''
            AND nvd.stock != '*'
            AND vlog.vin IS NULL
        """, (actual_location_name,))
        
        if cao_simulation:
            expected_cao_count = cao_simulation[0]['count']
            print(f"Expected CAO result: {expected_cao_count} vehicles needing graphics")
            
            if expected_cao_count > 0:
                print("✅ NAME MAPPING FIX SUCCESSFUL - CAO should now return vehicles!")
            else:
                print("ℹ️  All vehicles already processed - check if VIN log needs clearing")
        
        # Test actual CAO processing
        print("\n2. RUNNING ACTUAL CAO TEST:")
        result = processor.process_cao_order(
            dealership_name="South County DCJR",
            vin_history_table_suffix="south_county_dcjr_vin_log"
        )
        
        print(f"CAO Processing Result:")
        print(f"  - Success: {result.get('success', False)}")
        print(f"  - Total vehicles: {result.get('total_vehicles', 0)}")
        print(f"  - New vehicles needing graphics: {result.get('new_vehicles', 0)}")
        print(f"  - Files generated: {result.get('files_generated', 0)}")
        
        if result.get('error'):
            print(f"  - Error: {result['error']}")
        else:
            print("✅ CAO PROCESSING COMPLETED SUCCESSFULLY!")
            
    except Exception as e:
        print(f"Error during CAO testing: {e}")
        import traceback
        traceback.print_exc()
    
    db_manager.close()

if __name__ == "__main__":
    main()