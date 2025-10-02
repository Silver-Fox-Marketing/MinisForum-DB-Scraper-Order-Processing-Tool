#!/usr/bin/env python3
"""
CRITICAL VIN LOG STANDARDIZATION AND CLEANUP SCRIPT
Silver Fox Order Processing System - Complete VIN Log Standardization

This script will:
1. Standardize the 36 official dealership VIN log tables
2. Remove ALL other VIN log tables (43 unauthorized tables)
3. Ensure consistent schema across all 36 tables

NO UNICODE CHARACTERS - Windows compatible output only
"""

import sys
import os

# Set working directory and add scripts to path
os.chdir('C:/Users/Workstation_1/Documents/Tools/ClaudeCode/projects/minisforum_database_transfer/bulletproof_package')
sys.path.insert(0, './scripts')

from database_connection import db_manager

# Official 36 dealerships from DEALERSHIP_ORDER_PROCESSING_METHODS.md
OFFICIAL_DEALERSHIPS = [
    # CAO-SCHEDULED (15 Total)
    "Auffenberg Hyundai",
    "Frank Leta Honda", 
    "Glendale CDJR",
    "Honda of Frontenac",
    "HW Kia",
    "Pappas Toyota",
    "Porsche St. Louis",
    "Serra Honda O'Fallon",
    "South County DCJR", 
    "Spirit Lexus",
    "Suntrup Buick GMC",
    "Suntrup Ford Kirkwood",
    "Suntrup Ford West",
    "Thoroughbred Ford",
    "Weber Chevrolet",
    
    # MANUAL/LIST (21 Total)
    "BMW of Columbia",
    "BMW West St. Louis",
    "Bommarito Cadillac", 
    "Bommarito West County",
    "Columbia Honda",
    "Dave Sinclair Lincoln",
    "Dave Sinclair Lincoln St. Peters",
    "Joe Machens CDJR",
    "Joe Machens Hyundai",
    "Joe Machens Nissan", 
    "Joe Machens Toyota",
    "Indigo Auto Group",
    "Jaguar Rancho Mirage",
    "KIA of Columbia",
    "Land Rover Rancho Mirage",
    "Mini of St. Louis",
    "Pundmann Ford",
    "Rusty Drewing Chevy BGMC",
    "Rusty Drewing Cadillac", 
    "Suntrup Hyundai South",
    "Suntrup Kia South"
]

def dealership_to_table_name(dealership_name):
    """Convert dealership name to standardized table name"""
    return dealership_name.lower().replace(' ', '_').replace('.', '').replace("'", '') + '_vin_log'

def standardize_table_schema(table_name, dealership_name):
    """Ensure table has standardized schema"""
    try:
        # Add missing columns
        db_manager.execute_query(f'ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS order_date DATE')
        db_manager.execute_query(f'ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS dealership VARCHAR(255)')
        db_manager.execute_query(f'ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS order_number VARCHAR(50)')
        db_manager.execute_query(f'ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS template_type VARCHAR(50)')
        
        # Update dealership name if null
        db_manager.execute_query(f"""
            UPDATE {table_name} 
            SET dealership = %s 
            WHERE dealership IS NULL
        """, (dealership_name,))
        
        # Update order_date from processed_date if null
        db_manager.execute_query(f"""
            UPDATE {table_name} 
            SET order_date = CAST(processed_date AS DATE) 
            WHERE order_date IS NULL AND processed_date IS NOT NULL
        """)
        
        return True
    except Exception as e:
        print(f"    ERROR standardizing {table_name}: {e}")
        return False

def main():
    print("=" * 80)
    print("CRITICAL VIN LOG STANDARDIZATION AND CLEANUP")
    print("Silver Fox Order Processing System")
    print("=" * 80)
    
    # Step 1: Get all existing VIN log tables
    print("\nSTEP 1: GETTING ALL VIN LOG TABLES")
    tables = db_manager.execute_query("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = %s 
        AND table_name LIKE %s 
        ORDER BY table_name
    """, ('public', '%vin_log%'))
    
    all_tables = [table['table_name'] for table in tables]
    print(f"Found {len(all_tables)} total VIN log tables")
    
    # Step 2: Create mapping for official 36 dealerships
    print(f"\nSTEP 2: MAPPING {len(OFFICIAL_DEALERSHIPS)} OFFICIAL DEALERSHIPS")
    official_tables = {}
    for dealership in OFFICIAL_DEALERSHIPS:
        table_name = dealership_to_table_name(dealership)
        official_tables[dealership] = table_name
        print(f"  {dealership} -> {table_name}")
    
    official_table_names = list(official_tables.values())
    
    # Step 3: Standardize official dealership tables
    print(f"\nSTEP 3: STANDARDIZING {len(official_table_names)} OFFICIAL TABLES")
    
    standardized_count = 0
    for dealership, target_table in official_tables.items():
        print(f"\n--- {dealership} ---")
        
        # Check if target table exists
        if target_table in all_tables:
            print(f"  Found existing table: {target_table}")
            if standardize_table_schema(target_table, dealership):
                print(f"  [OK] Standardized {target_table}")
                standardized_count += 1
        else:
            # Look for old convention table to migrate
            dealership_key = dealership.lower().replace(' ', '_').replace('.', '').replace("'", '')
            old_table = f"vin_log_{dealership_key}"
            
            if old_table in all_tables:
                print(f"  Found OLD table: {old_table}, migrating...")
                try:
                    # Create new standardized table
                    db_manager.execute_query(f"""
                        CREATE TABLE {target_table} (
                            id SERIAL PRIMARY KEY,
                            vin VARCHAR(17) NOT NULL,
                            dealership VARCHAR(255),
                            order_date DATE,
                            processed_date VARCHAR(50),
                            order_type VARCHAR(50),
                            order_number VARCHAR(50),
                            template_type VARCHAR(50),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Migrate all data
                    db_manager.execute_query(f"""
                        INSERT INTO {target_table} (vin, dealership, order_date, processed_date, order_type, order_number, template_type, created_at)
                        SELECT 
                            vin,
                            %s as dealership,
                            CASE 
                                WHEN order_date IS NOT NULL THEN order_date
                                WHEN processed_date IS NOT NULL THEN CAST(processed_date AS DATE)
                                ELSE NULL
                            END as order_date,
                            processed_date,
                            COALESCE(order_type, 'CAO') as order_type,
                            order_number,
                            COALESCE(template_type, 'Standard') as template_type,
                            COALESCE(created_at, CURRENT_TIMESTAMP) as created_at
                        FROM {old_table}
                    """, (dealership,))
                    
                    print(f"  [OK] Migrated {old_table} to {target_table}")
                    standardized_count += 1
                    
                except Exception as e:
                    print(f"  ERROR migrating {old_table}: {e}")
            else:
                print(f"  WARNING: No table found for {dealership}")
    
    # Step 4: Identify tables to remove
    print(f"\nSTEP 4: IDENTIFYING UNAUTHORIZED TABLES TO REMOVE")
    tables_to_remove = [table for table in all_tables if table not in official_table_names]
    
    print(f"Tables to keep: {len(official_table_names)}")
    print(f"Tables to remove: {len(tables_to_remove)}")
    
    if tables_to_remove:
        print("\nTables that will be REMOVED:")
        for table in tables_to_remove:
            count = db_manager.execute_query(f'SELECT COUNT(*) as total FROM {table}')
            total = count[0]['total'] if count else 0
            print(f"  {table}: {total} records")
    
    # Step 5: Remove unauthorized tables
    print(f"\nSTEP 5: REMOVING {len(tables_to_remove)} UNAUTHORIZED TABLES")
    removed_count = 0
    
    for table in tables_to_remove:
        try:
            db_manager.execute_query(f'DROP TABLE {table}')
            print(f"  [REMOVED] {table}")
            removed_count += 1
        except Exception as e:
            print(f"  ERROR removing {table}: {e}")
    
    # Step 6: Final verification
    print(f"\nSTEP 6: FINAL VERIFICATION")
    
    # Get remaining tables
    final_tables = db_manager.execute_query("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = %s 
        AND table_name LIKE %s 
        ORDER BY table_name
    """, ('public', '%vin_log%'))
    
    final_count = len(final_tables)
    print(f"Remaining VIN log tables: {final_count}")
    
    # Show status of each official dealership
    for dealership, target_table in official_tables.items():
        try:
            count = db_manager.execute_query(f'SELECT COUNT(*) as total FROM {target_table}')
            total = count[0]['total'] if count else 0
            print(f"  {dealership}: {total} records")
        except:
            print(f"  {dealership}: TABLE NOT FOUND")
    
    print("\n" + "=" * 80)
    print("VIN LOG STANDARDIZATION AND CLEANUP COMPLETE")
    print("=" * 80)
    print(f"RESULTS:")
    print(f"  Official tables standardized: {standardized_count}")
    print(f"  Unauthorized tables removed: {removed_count}")
    print(f"  Final VIN log table count: {final_count}")
    print(f"  Target: {len(OFFICIAL_DEALERSHIPS)} official dealerships")

if __name__ == "__main__":
    main()