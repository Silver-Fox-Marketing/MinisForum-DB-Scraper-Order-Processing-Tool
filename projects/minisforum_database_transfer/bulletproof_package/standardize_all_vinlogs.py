#!/usr/bin/env python3
"""
CRITICAL VIN LOG STANDARDIZATION SCRIPT
Silver Fox Order Processing System - Complete VIN Log Standardization

This script will:
1. Get the official 36 dealerships from DEALERSHIP_ORDER_PROCESSING_METHODS.md
2. Standardize ALL VIN log tables to: dealership_name_vin_log format
3. Add missing columns (order_date, dealership) to ensure consistent schema
4. Migrate data from OLD convention tables to NEW convention tables
5. Remove duplicate/unauthorized VIN log tables

STANDARD SCHEMA:
- id (SERIAL PRIMARY KEY)
- vin (VARCHAR(17) NOT NULL)
- dealership (VARCHAR(255))
- order_date (DATE) 
- processed_date (VARCHAR) - legacy compatibility
- order_type (VARCHAR(50))
- order_number (VARCHAR(50))
- template_type (VARCHAR(50))
- created_at (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
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

def main():
    print("=" * 80)
    print("CRITICAL VIN LOG STANDARDIZATION - SILVER FOX ORDER PROCESSING SYSTEM")
    print("=" * 80)
    
    # Step 1: Get all existing VIN log tables
    print("\nSTEP 1: CATALOGING ALL EXISTING VIN LOG TABLES")
    tables = db_manager.execute_query("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = %s 
        AND table_name LIKE %s 
        ORDER BY table_name
    """, ('public', '%vin_log%'))
    
    existing_tables = [table['table_name'] for table in tables]
    print(f"Found {len(existing_tables)} existing VIN log tables")
    
    # Step 2: Create standardized table names for official dealerships
    print("\nSTEP 2: CREATING OFFICIAL DEALERSHIP TABLE MAPPING")
    official_tables = {}
    for dealership in OFFICIAL_DEALERSHIPS:
        table_name = dealership_to_table_name(dealership)
        official_tables[dealership] = table_name
        print(f"  {dealership} -> {table_name}")
    
    # Step 3: Standardize each official dealership's VIN log
    print("\nSTEP 3: STANDARDIZING OFFICIAL DEALERSHIP VIN LOGS")
    
    for dealership, target_table in official_tables.items():
        print(f"\n--- PROCESSING: {dealership} ---")
        
        # Find related tables for this dealership
        dealership_key = dealership.lower().replace(' ', '_').replace('.', '').replace("'", '')
        old_table = f"vin_log_{dealership_key}"
        new_table = target_table
        
        print(f"Target table: {new_table}")
        print(f"Looking for OLD: {old_table}")
        
        # Check if target table exists
        target_exists = new_table in existing_tables
        old_exists = old_table in existing_tables
        
        if target_exists:
            print(f"  ✓ Target table {new_table} exists")
            
            # Ensure target table has all required columns
            print(f"  Adding missing columns to {new_table}...")
            
            # Add missing columns with error handling
            try:
                db_manager.execute_query(f'ALTER TABLE {new_table} ADD COLUMN IF NOT EXISTS order_date DATE')
                db_manager.execute_query(f'ALTER TABLE {new_table} ADD COLUMN IF NOT EXISTS dealership VARCHAR(255)')
                db_manager.execute_query(f'ALTER TABLE {new_table} ADD COLUMN IF NOT EXISTS order_number VARCHAR(50)')
                db_manager.execute_query(f'ALTER TABLE {new_table} ADD COLUMN IF NOT EXISTS template_type VARCHAR(50)')
                
                # Update dealership name if null
                db_manager.execute_query(f"""
                    UPDATE {new_table} 
                    SET dealership = %s 
                    WHERE dealership IS NULL
                """, (dealership,))
                
                # Update order_date from processed_date if null
                db_manager.execute_query(f"""
                    UPDATE {new_table} 
                    SET order_date = CAST(processed_date AS DATE) 
                    WHERE order_date IS NULL AND processed_date IS NOT NULL
                """)
                
                print(f"  ✓ Standardized {new_table}")
                
            except Exception as e:
                print(f"  ⚠ Error standardizing {new_table}: {e}")
        
        elif old_exists:
            print(f"  Found OLD table {old_table}, migrating to {new_table}...")
            
            try:
                # Create new table with standard schema
                db_manager.execute_query(f"""
                    CREATE TABLE {new_table} (
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
                
                # Migrate data from old table to new table
                db_manager.execute_query(f"""
                    INSERT INTO {new_table} (vin, dealership, order_date, processed_date, order_type, order_number, template_type, created_at)
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
                
                print(f"  ✓ Migrated data from {old_table} to {new_table}")
                
            except Exception as e:
                print(f"  ⚠ Error migrating {old_table}: {e}")
        
        else:
            print(f"  ⚠ No existing table found for {dealership}")
    
    # Step 4: Show final status
    print("\nSTEP 4: FINAL STATUS CHECK")
    
    for dealership, target_table in official_tables.items():
        try:
            count = db_manager.execute_query(f'SELECT COUNT(*) as total FROM {target_table}')
            total = count[0]['total'] if count else 0
            print(f"  {dealership}: {total} records in {target_table}")
        except:
            print(f"  {dealership}: TABLE NOT FOUND - {target_table}")
    
    print("\n" + "=" * 80)
    print("VIN LOG STANDARDIZATION COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Test VIN log API endpoints")
    print("2. Verify dealership settings modals show correct data")
    print("3. Remove unauthorized VIN log tables")

if __name__ == "__main__":
    main()