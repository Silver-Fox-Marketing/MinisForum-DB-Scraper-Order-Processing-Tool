"""
Script to rename 'West County Volvo Cars' to 'Volvo Cars West County' across all database tables
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_connection import db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OLD_NAME = "West County Volvo Cars"
NEW_NAME = "Volvo Cars West County"

def rename_dealership():
    """Rename dealership across all relevant tables"""
    
    print("=== RENAMING DEALERSHIP FROM 'West County Volvo Cars' TO 'Volvo Cars West County' ===")
    
    # 1. Update dealership_configs table
    print("\n1. Updating dealership_configs table...")
    try:
        result = db_manager.execute_query("""
            UPDATE dealership_configs 
            SET dealership_name = %s 
            WHERE dealership_name = %s
            RETURNING id, dealership_name
        """, [NEW_NAME, OLD_NAME])
        
        if result:
            print(f"   SUCCESS: Updated dealership_configs - {len(result)} record(s)")
            print(f"   New name: {result[0]['dealership_name']}")
        else:
            print("   INFO: No records found in dealership_configs")
    except Exception as e:
        print(f"   ERROR updating dealership_configs: {e}")
    
    # 2. Update raw_vehicle_data table
    print("\n2. Updating raw_vehicle_data table...")
    try:
        result = db_manager.execute_query("""
            UPDATE raw_vehicle_data 
            SET location = %s 
            WHERE location = %s
            RETURNING id
        """, [NEW_NAME, OLD_NAME])
        
        if result:
            print(f"   SUCCESS: Updated {len(result)} records in raw_vehicle_data")
        else:
            print("   INFO: No records found in raw_vehicle_data")
    except Exception as e:
        print(f"   ERROR updating raw_vehicle_data: {e}")
    
    # 3. Update normalized_vehicle_data table
    print("\n3. Updating normalized_vehicle_data table...")
    try:
        result = db_manager.execute_query("""
            UPDATE normalized_vehicle_data 
            SET location = %s 
            WHERE location = %s
            RETURNING id
        """, [NEW_NAME, OLD_NAME])
        
        if result:
            print(f"   SUCCESS: Updated {len(result)} records in normalized_vehicle_data")
        else:
            print("   INFO: No records found in normalized_vehicle_data")
    except Exception as e:
        print(f"   ERROR updating normalized_vehicle_data: {e}")
    
    # 4. Update order_queue table
    print("\n4. Updating order_queue table...")
    try:
        result = db_manager.execute_query("""
            UPDATE order_queue 
            SET dealership_name = %s 
            WHERE dealership_name = %s
            RETURNING id
        """, [NEW_NAME, OLD_NAME])
        
        if result:
            print(f"   SUCCESS: Updated {len(result)} records in order_queue")
        else:
            print("   INFO: No records found in order_queue")
    except Exception as e:
        print(f"   ERROR updating order_queue: {e}")
    
    # 5. Check for VIN log table (might be named differently)
    print("\n5. Checking for VIN log tables...")
    try:
        # Check if there's a generic vin_history table
        result = db_manager.execute_query("""
            UPDATE vin_history 
            SET dealership_name = %s 
            WHERE dealership_name = %s
            RETURNING id
        """, [NEW_NAME, OLD_NAME])
        
        if result:
            print(f"   SUCCESS: Updated {len(result)} records in vin_history")
        else:
            print("   INFO: No records found in vin_history")
    except Exception as e:
        print(f"   INFO: vin_history table update: {e}")
    
    # Check for dealership-specific VIN log table
    try:
        # First check if old table exists
        old_table_check = db_manager.execute_query("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_name = 'west_county_volvo_cars_vin_log'
        """)
        
        if old_table_check and old_table_check[0]['count'] > 0:
            print("   Found 'west_county_volvo_cars_vin_log' table")
            # Rename the table
            db_manager.execute_query("""
                ALTER TABLE west_county_volvo_cars_vin_log 
                RENAME TO volvo_cars_west_county_vin_log
            """)
            print("   SUCCESS: Renamed VIN log table to 'volvo_cars_west_county_vin_log'")
    except Exception as e:
        print(f"   INFO: Dealership-specific VIN log table: {e}")
    
    # 6. Update scraper_imports table
    print("\n6. Updating scraper_imports table...")
    try:
        result = db_manager.execute_query("""
            UPDATE scraper_imports 
            SET dealership_name = %s 
            WHERE dealership_name = %s
            RETURNING import_id
        """, [NEW_NAME, OLD_NAME])
        
        if result:
            print(f"   SUCCESS: Updated {len(result)} records in scraper_imports")
        else:
            print("   INFO: No records found in scraper_imports")
    except Exception as e:
        print(f"   ERROR updating scraper_imports: {e}")
    
    # 7. Verify the changes
    print("\n=== VERIFICATION ===")
    print("Checking for any remaining references to old name...")
    
    tables_to_check = [
        'dealership_configs',
        'raw_vehicle_data',
        'normalized_vehicle_data', 
        'order_queue',
        'vin_history',
        'scraper_imports'
    ]
    
    for table in tables_to_check:
        try:
            # Check for old name
            old_check = db_manager.execute_query(f"""
                SELECT COUNT(*) as count 
                FROM {table} 
                WHERE dealership_name = %s OR location = %s
            """, [OLD_NAME, OLD_NAME])
            
            # Check for new name
            new_check = db_manager.execute_query(f"""
                SELECT COUNT(*) as count 
                FROM {table} 
                WHERE dealership_name = %s OR location = %s
            """, [NEW_NAME, NEW_NAME])
            
            old_count = old_check[0]['count'] if old_check else 0
            new_count = new_check[0]['count'] if new_check else 0
            
            if old_count > 0:
                print(f"   WARNING: {table} still has {old_count} records with old name")
            if new_count > 0:
                print(f"   SUCCESS: {table} has {new_count} records with new name")
        except:
            pass
    
    print("\n=== DATABASE UPDATE COMPLETE ===")
    print(f"Dealership renamed from '{OLD_NAME}' to '{NEW_NAME}'")

if __name__ == "__main__":
    rename_dealership()