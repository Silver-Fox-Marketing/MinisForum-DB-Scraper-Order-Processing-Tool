"""
Import updated VIN logs for Thoroughbred Ford and Glendale CDJR
September 2025 update - Clear existing and import fresh baseline VIN logs
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_connection import DatabaseManager

def clear_and_import_vinlogs():
    """Clear existing VIN logs and import updated ones for specified dealerships"""
    
    db_manager = DatabaseManager()
    
    # Define the dealerships and their file mappings
    dealership_files = {
        'Thoroughbred Ford': r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\Vinlogs\TBRED_FORD_VINLOG - LOG (1).csv',
        'Glendale CDJR': r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\Vinlogs\GLENDALE_VINLOG - LOG (1).csv'
    }
    
    # Define the table name mappings
    table_mappings = {
        'Thoroughbred Ford': 'thoroughbred_ford_vin_log',
        'Glendale CDJR': 'glendale_cdjr_vin_log'
    }
    
    for dealership, file_path in dealership_files.items():
        table_name = table_mappings[dealership]
        
        print(f"\n{'='*60}")
        print(f"Processing: {dealership}")
        print(f"Table: {table_name}")
        print(f"File: {file_path}")
        print('='*60)
        
        # Step 1: Clear existing VIN logs
        print(f"\n[STEP 1] Clearing existing VIN logs for {dealership}...")
        try:
            # First, check if the table exists
            check_query = f"""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = '{table_name}'
            """
            
            result = db_manager.execute_query(check_query)
            
            if result and result[0][0] > 0:
                # Table exists, get count before deletion
                count_query = f"SELECT COUNT(*) FROM {table_name}"
                count_result = db_manager.execute_query(count_query)
                existing_count = count_result[0][0] if count_result else 0
                
                # Delete all existing records
                delete_query = f"DELETE FROM {table_name}"
                db_manager.execute_query(delete_query)
                print(f"   [OK] Deleted {existing_count} existing records from {table_name}")
            else:
                print(f"   [INFO] Table {table_name} does not exist, will be created")
                
                # Create the table
                create_query = f"""
                CREATE TABLE {table_name} (
                    id SERIAL PRIMARY KEY,
                    vin VARCHAR(17) NOT NULL,
                    dealership VARCHAR(255),
                    order_date DATE,
                    order_type VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(vin)
                )
                """
                db_manager.execute_query(create_query)
                print(f"   [OK] Created table {table_name}")
                
        except Exception as e:
            print(f"   [ERROR] Failed to clear existing data: {str(e)}")
            continue
        
        # Step 2: Read the CSV file
        print(f"\n[STEP 2] Reading CSV file...")
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            print(f"   [OK] Read {len(df)} rows from CSV")
            
            # Display column names to understand the structure
            print(f"   [INFO] CSV columns: {list(df.columns)}")
            
            # Find the VIN column (case-insensitive)
            vin_column = None
            for col in df.columns:
                if 'vin' in col.lower():
                    vin_column = col
                    break
            
            if not vin_column:
                # If no VIN column found, assume first column
                vin_column = df.columns[0]
                print(f"   [WARNING] No VIN column found, using first column: {vin_column}")
            else:
                print(f"   [INFO] Using VIN column: {vin_column}")
            
            # Get unique VINs
            vins = df[vin_column].dropna().unique()
            print(f"   [INFO] Found {len(vins)} unique VINs")
            
        except Exception as e:
            print(f"   [ERROR] Failed to read CSV file: {str(e)}")
            continue
        
        # Step 3: Import VINs to database
        print(f"\n[STEP 3] Importing VINs to database...")
        try:
            success_count = 0
            error_count = 0
            
            for vin in vins:
                try:
                    # Clean the VIN (remove any whitespace)
                    vin = str(vin).strip()
                    
                    # Skip empty or invalid VINs
                    if not vin or len(vin) < 11:
                        continue
                    
                    insert_query = f"""
                    INSERT INTO {table_name} (vin, dealership, order_date, order_type)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (vin) DO NOTHING
                    """
                    
                    db_manager.execute_query(insert_query, (
                        vin,
                        dealership,
                        '2025-09-04',
                        'baseline'
                    ))
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    if error_count <= 3:  # Only show first 3 errors
                        print(f"   [ERROR] Failed to insert VIN {vin}: {str(e)}")
            
            print(f"   [OK] Successfully imported {success_count} VINs")
            if error_count > 0:
                print(f"   [WARNING] Failed to import {error_count} VINs")
            
            # Verify the import
            count_query = f"SELECT COUNT(*) FROM {table_name}"
            count_result = db_manager.execute_query(count_query)
            final_count = count_result[0][0] if count_result else 0
            print(f"   [VERIFY] Final count in {table_name}: {final_count} records")
            
        except Exception as e:
            print(f"   [ERROR] Failed to import VINs: {str(e)}")
            continue
    
    print(f"\n{'='*60}")
    print("VIN LOG IMPORT COMPLETE")
    print('='*60)
    
    # Summary
    print("\nSUMMARY:")
    for dealership in dealership_files.keys():
        table_name = table_mappings[dealership]
        try:
            count_query = f"SELECT COUNT(*) FROM {table_name}"
            count_result = db_manager.execute_query(count_query)
            count = count_result[0][0] if count_result else 0
            print(f"  - {dealership}: {count} VINs in {table_name}")
        except:
            print(f"  - {dealership}: Error checking count")

if __name__ == "__main__":
    print("="*60)
    print("VIN LOG IMPORT SCRIPT")
    print("Clearing and importing updated VIN logs")
    print("Order Type: baseline")
    print("Order Date: 2025-09-04")
    print("="*60)
    
    clear_and_import_vinlogs()