"""
Test database connection and import VIN logs for Thoroughbred Ford and Glendale CDJR
"""

import sys
import os
import pandas as pd
from datetime import datetime
import psycopg2
from psycopg2 import sql

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_db_connection():
    """Get a direct database connection"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="minisforum_cao_db",
            user="silveradmin",
            password="$ilverF0x2024DB!"
        )
        return conn
    except Exception as e:
        print(f"[ERROR] Failed to connect to database: {str(e)}")
        return None

def clear_and_import_vinlogs():
    """Clear existing VIN logs and import updated ones for specified dealerships"""
    
    conn = get_db_connection()
    if not conn:
        print("[ERROR] Could not establish database connection")
        return
    
    cursor = conn.cursor()
    
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
        
        # Step 1: Check if table exists, if not create it
        print(f"\n[STEP 1] Checking/Creating table {table_name}...")
        try:
            # Check if table exists
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            """, (table_name,))
            
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                # Get count before deletion
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                existing_count = cursor.fetchone()[0]
                print(f"   [INFO] Table exists with {existing_count} records")
                
                # Delete all existing records
                cursor.execute(f"DELETE FROM {table_name}")
                conn.commit()
                print(f"   [OK] Cleared {existing_count} existing records")
            else:
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
                cursor.execute(create_query)
                conn.commit()
                print(f"   [OK] Created new table {table_name}")
                
        except Exception as e:
            print(f"   [ERROR] Table operations failed: {str(e)}")
            conn.rollback()
            continue
        
        # Step 2: Read the CSV file
        print(f"\n[STEP 2] Reading CSV file...")
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            print(f"   [OK] Read {len(df)} rows from CSV")
            
            # Display first few rows to understand structure
            print(f"   [INFO] CSV columns: {list(df.columns)}")
            print(f"   [INFO] First 3 rows:")
            print(df.head(3))
            
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
            print(f"   [INFO] Found {len(vins)} unique VINs to import")
            
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
                    if not vin or len(vin) < 11 or vin.lower() == 'nan':
                        continue
                    
                    cursor.execute(f"""
                        INSERT INTO {table_name} (vin, dealership, order_date, order_type)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (vin) DO NOTHING
                    """, (vin, dealership, '2025-09-04', 'baseline'))
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    if error_count <= 3:  # Only show first 3 errors
                        print(f"   [ERROR] Failed to insert VIN {vin}: {str(e)}")
            
            conn.commit()
            print(f"   [OK] Successfully imported {success_count} VINs")
            if error_count > 0:
                print(f"   [WARNING] Failed to import {error_count} VINs")
            
            # Verify the import
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            final_count = cursor.fetchone()[0]
            print(f"   [VERIFY] Final count in {table_name}: {final_count} records")
            
        except Exception as e:
            print(f"   [ERROR] Failed to import VINs: {str(e)}")
            conn.rollback()
            continue
    
    print(f"\n{'='*60}")
    print("VIN LOG IMPORT COMPLETE")
    print('='*60)
    
    # Summary
    print("\nFINAL SUMMARY:")
    for dealership in dealership_files.keys():
        table_name = table_mappings[dealership]
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {dealership}: {count} VINs in {table_name}")
            
            # Show sample VINs
            cursor.execute(f"SELECT vin, order_date, order_type FROM {table_name} LIMIT 3")
            samples = cursor.fetchall()
            if samples:
                print(f"    Sample VINs:")
                for sample in samples:
                    print(f"      - {sample[0]} | {sample[1]} | {sample[2]}")
        except Exception as e:
            print(f"  - {dealership}: Error checking count - {str(e)}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    print("="*60)
    print("VIN LOG IMPORT SCRIPT - WITH DIRECT DB CONNECTION")
    print("Clearing and importing updated VIN logs")
    print("Order Type: baseline")
    print("Order Date: 2025-09-04")
    print("="*60)
    
    clear_and_import_vinlogs()