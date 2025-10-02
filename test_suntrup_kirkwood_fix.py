#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
from database_connection import DatabaseManager
from correct_order_processing import CorrectOrderProcessor

def main():
    print("=== TESTING SUNTRUP FORD KIRKWOOD CAO FILTER FIX ===")
    
    db_manager = DatabaseManager()
    processor = CorrectOrderProcessor()
    
    # Test the CAO processing with the new filter
    print("\n1. TESTING CAO ORDER PROCESSING:")
    try:
        # Run CAO for Suntrup Ford Kirkwood
        result = processor.process_cao_order(
            dealership_name="Suntrup Ford Kirkwood",
            vin_history_table_suffix="suntrup_ford_kirkwood_vin_log"
        )
        
        print(f"CAO Processing Result:")
        print(f"  - Total vehicles processed: {result.get('total_vehicles', 0)}")
        print(f"  - New vehicles needing graphics: {result.get('new_vehicles', 0)}")
        print(f"  - Files generated: {result.get('files_generated', 0)}")
        print(f"  - Success: {result.get('success', False)}")
        
        if result.get('error'):
            print(f"  - Error: {result['error']}")
        
        # Check the vehicle details to verify no NEW vehicles are included
        if 'processed_vehicles' in result:
            print(f"\n2. ANALYZING PROCESSED VEHICLES:")
            new_count = 0
            used_count = 0
            
            for vehicle in result['processed_vehicles']:
                vehicle_type = vehicle.get('type', '').lower()
                vehicle_condition = vehicle.get('vehicle_condition', '').lower()
                
                if 'new' in vehicle_type or vehicle_condition == 'new':
                    new_count += 1
                    print(f"  [WARNING] NEW vehicle found: {vehicle.get('vin')} - {vehicle.get('year')} {vehicle.get('make')} {vehicle.get('model')} - Type: {vehicle_type}")
                else:
                    used_count += 1
                    
            print(f"\nVehicle Type Summary:")
            print(f"  - Used vehicles: {used_count}")
            print(f"  - New vehicles: {new_count}")
            
            if new_count == 0:
                print("  SUCCESS: No new vehicles were processed!")
            else:
                print(f"  ISSUE: {new_count} new vehicles were incorrectly processed")
                
        # Check if orders folder was created
        print(f"\n3. CHECKING OUTPUT FILES:")
        orders_path = "C:\\Users\\Workstation_1\\Documents\\Tools\\ClaudeCode\\projects\\minisforum_database_transfer\\bulletproof_package\\orders\\Suntrup_Ford_Kirkwood"
        
        if os.path.exists(orders_path):
            # Find the latest order folder
            order_folders = [f for f in os.listdir(orders_path) if os.path.isdir(os.path.join(orders_path, f))]
            if order_folders:
                latest_folder = sorted(order_folders)[-1]
                full_path = os.path.join(orders_path, latest_folder)
                print(f"  Latest order folder: {full_path}")
                
                # List files in the order folder
                files = os.listdir(full_path)
                print(f"  Generated files: {files}")
                
                # Check CSV file for vehicle types
                csv_files = [f for f in files if f.endswith('.csv')]
                if csv_files:
                    csv_path = os.path.join(full_path, csv_files[0])
                    print(f"\n4. ANALYZING CSV CONTENT:")
                    
                    with open(csv_path, 'r', encoding='utf-8-sig') as f:
                        lines = f.readlines()
                        
                    print(f"  Total lines in CSV: {len(lines)}")
                    
                    # Count vehicle types in CSV
                    new_in_csv = 0
                    used_in_csv = 0
                    
                    for line in lines[1:]:  # Skip header
                        if 'New' in line:
                            new_in_csv += 1
                        if 'Used' in line:
                            used_in_csv += 1
                    
                    print(f"  Vehicles in CSV - New: {new_in_csv}, Used: {used_in_csv}")
                    
                    if new_in_csv == 0:
                        print("  SUCCESS: CSV contains no new vehicles!")
                    else:
                        print(f"  ISSUE: CSV contains {new_in_csv} new vehicles")
            else:
                print("  No order folders found")
        else:
            print("  Orders folder not found")
            
    except Exception as e:
        print(f"Error during CAO testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db_manager.close()

if __name__ == "__main__":
    main()