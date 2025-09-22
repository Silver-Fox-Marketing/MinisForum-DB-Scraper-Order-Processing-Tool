#!/usr/bin/env python3
"""
Fix Weber Chevrolet Name Mapping
================================
Updates scraper data location from "Weber Creve Coeur" to "Weber Chevrolet"
to ensure proper CAO processing and name consistency across the system.
"""

import os
import sys
from pathlib import Path

# Add project paths
current_file = Path(__file__).resolve()
sys.path.insert(0, str(current_file.parent / "projects" / "minisforum_database_transfer" / "bulletproof_package" / "scripts"))

from database_connection import db_manager

def fix_weber_name_mapping():
    """Fix Weber Chevrolet name mapping in scraper data"""
    
    print("Fixing Weber Chevrolet name mapping...")
    print("=" * 50)
    
    try:
        # 1. Check current Weber data
        print("1. Checking current Weber data in raw_vehicle_data...")
        
        weber_data = db_manager.execute_query("""
            SELECT location, COUNT(*) as vehicle_count
            FROM raw_vehicle_data 
            WHERE location ILIKE '%weber%'
            GROUP BY location
            ORDER BY location
        """)
        
        print("Current Weber entries:")
        for entry in weber_data:
            print(f"  - {entry['location']}: {entry['vehicle_count']} vehicles")
        
        # 2. Update raw_vehicle_data location
        print("\n2. Updating raw_vehicle_data location...")
        
        update_result = db_manager.execute_query("""
            UPDATE raw_vehicle_data 
            SET location = 'Weber Chevrolet'
            WHERE location = 'Weber Creve Coeur'
            RETURNING id
        """)
        
        updated_count = len(update_result) if update_result else 0
        print(f"Updated {updated_count} records from 'Weber Creve Coeur' to 'Weber Chevrolet'")
        
        # 3. Update normalized_vehicle_data location
        print("\n3. Updating normalized_vehicle_data location...")
        
        normalized_update = db_manager.execute_query("""
            UPDATE normalized_vehicle_data 
            SET location = 'Weber Chevrolet'
            WHERE location = 'Weber Creve Coeur'
            RETURNING id
        """)
        
        normalized_count = len(normalized_update) if normalized_update else 0
        print(f"Updated {normalized_count} normalized records")
        
        # 4. Check if VIN log table exists with correct name
        print("\n4. Checking VIN log table...")
        
        # Check for existing tables
        vin_tables = db_manager.execute_query("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%weber%vin_log'
            ORDER BY table_name
        """)
        
        print("Existing Weber VIN log tables:")
        for table in vin_tables:
            print(f"  - {table['table_name']}")
        
        # Check if we need to rename or create VIN log table
        correct_table = 'weber_chevrolet_vin_log'
        old_table = 'weber_creve_coeur_vin_log'
        
        table_exists = any(t['table_name'] == correct_table for t in vin_tables)
        old_table_exists = any(t['table_name'] == old_table for t in vin_tables)
        
        if old_table_exists and not table_exists:
            print(f"\n5. Renaming VIN log table from {old_table} to {correct_table}...")
            db_manager.execute_query(f"""
                ALTER TABLE {old_table} RENAME TO {correct_table}
            """)
            print("VIN log table renamed successfully")
        elif not table_exists and not old_table_exists:
            print(f"\n5. Creating new VIN log table: {correct_table}...")
            db_manager.execute_query(f"""
                CREATE TABLE {correct_table} (
                    id SERIAL PRIMARY KEY,
                    vin VARCHAR(17) NOT NULL,
                    processed_date DATE NOT NULL,
                    order_number VARCHAR(50),
                    order_type VARCHAR(10) NOT NULL,
                    dealership VARCHAR(100) NOT NULL DEFAULT 'Weber Chevrolet',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    order_date DATE
                )
            """)
            print("VIN log table created successfully")
        else:
            print(f"5. VIN log table {correct_table} already exists correctly")
        
        # 6. Check dealership config
        print("\n6. Checking dealership configuration...")
        
        config_check = db_manager.execute_query("""
            SELECT name, filtering_rules, is_active
            FROM dealership_configs 
            WHERE name ILIKE '%weber%'
        """)
        
        print("Weber configurations found:")
        for config in config_check:
            print(f"  - {config['name']}: active={config['is_active']}")
        
        # Verify final state
        print("\n" + "=" * 50)
        print("VERIFICATION - Final Weber data state:")
        
        final_data = db_manager.execute_query("""
            SELECT location, COUNT(*) as vehicle_count
            FROM raw_vehicle_data 
            WHERE location ILIKE '%weber%'
            GROUP BY location
            ORDER BY location
        """)
        
        for entry in final_data:
            print(f"  - {entry['location']}: {entry['vehicle_count']} vehicles")
        
        print("\nWeber Chevrolet name mapping fix completed successfully!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        raise

if __name__ == "__main__":
    fix_weber_name_mapping()