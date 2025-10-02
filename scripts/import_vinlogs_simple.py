"""
Simple VIN log import using existing database manager
"""

import sys
import os
import pandas as pd

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_connection import db_manager

def import_vinlogs():
    """Import VIN logs for Thoroughbred Ford and Glendale CDJR"""
    
    # Test database connection first
    print("Testing database connection...")
    if not db_manager.test_connection():
        print("[ERROR] Database connection failed")
        return False
    print("[OK] Database connection successful")
    
    # Define the dealerships and their file mappings
    dealership_files = {
        'Thoroughbred Ford': {
            'file': r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\Vinlogs\TBRED_FORD_VINLOG - LOG (1).csv',
            'table': 'thoroughbred_ford_vin_log'
        },
        'Glendale CDJR': {
            'file': r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\Vinlogs\GLENDALE_VINLOG - LOG (1).csv',
            'table': 'glendale_cdjr_vin_log'
        }
    }
    
    for dealership, info in dealership_files.items():
        file_path = info['file']
        table_name = info['table']
        
        print(f"\n{'='*60}")
        print(f"Processing: {dealership}")
        print(f"Table: {table_name}")
        print(f"File: {file_path}")
        print('='*60)
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"[ERROR] File not found: {file_path}")
            continue
        
        # Step 1: Create table if it doesn't exist
        print(f"\n[STEP 1] Creating table if needed...")
        try:
            create_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
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
            print(f"   [OK] Table {table_name} ready")
        except Exception as e:
            print(f"   [ERROR] Failed to create table: {str(e)}")
            continue
        
        # Step 2: Clear existing data
        print(f"\n[STEP 2] Clearing existing data...")
        try:
            # Get current count
            count_result = db_manager.execute_query(f"SELECT COUNT(*) FROM {table_name}")
            existing_count = count_result[0]['count'] if count_result else 0
            print(f"   [INFO] Found {existing_count} existing records")
            
            # Clear the table
            db_manager.execute_query(f"DELETE FROM {table_name}")
            print(f"   [OK] Cleared all existing records")
        except Exception as e:
            print(f"   [ERROR] Failed to clear existing data: {str(e)}")
            continue
        
        # Step 3: Read CSV file
        print(f"\n[STEP 3] Reading CSV file...")
        try:
            df = pd.read_csv(file_path)
            print(f"   [OK] Read {len(df)} rows from CSV")
            print(f"   [INFO] Columns: {list(df.columns)}")
            
            # Find VIN column
            vin_column = None
            for col in df.columns:
                if 'vin' in col.lower():
                    vin_column = col
                    break
            
            if not vin_column:
                vin_column = df.columns[0]
                print(f"   [WARNING] Using first column as VIN: {vin_column}")
            else:
                print(f"   [INFO] Using VIN column: {vin_column}")
            
            # Get clean VINs
            vins = df[vin_column].dropna().astype(str).str.strip()
            # Remove empty and invalid VINs
            vins = [v for v in vins if v and len(v) >= 11 and v.lower() != 'nan']
            vins = list(set(vins))  # Remove duplicates
            
            print(f"   [INFO] Found {len(vins)} unique valid VINs")
            
        except Exception as e:
            print(f"   [ERROR] Failed to read CSV: {str(e)}")
            continue
        
        # Step 4: Import VINs
        print(f"\n[STEP 4] Importing VINs...")
        try:
            success_count = 0
            error_count = 0
            
            for vin in vins:
                try:
                    insert_query = f"""
                    INSERT INTO {table_name} (vin, dealership, order_date, order_type)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (vin) DO NOTHING
                    """
                    
                    db_manager.execute_query(insert_query, (vin, dealership, '2025-09-04', 'baseline'))
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    if error_count <= 3:
                        print(f"   [ERROR] Failed to insert VIN {vin}: {str(e)}")
            
            print(f"   [OK] Successfully imported {success_count} VINs")
            if error_count > 0:
                print(f"   [WARNING] {error_count} VINs failed to import")
            
            # Verify final count
            final_result = db_manager.execute_query(f"SELECT COUNT(*) FROM {table_name}")
            final_count = final_result[0]['count'] if final_result else 0
            print(f"   [VERIFY] Final count in {table_name}: {final_count}")
            
        except Exception as e:
            print(f"   [ERROR] Failed to import VINs: {str(e)}")
            continue
    
    print(f"\n{'='*60}")
    print("VIN LOG IMPORT COMPLETE")
    print('='*60)
    
    # Final summary
    print("\nFINAL SUMMARY:")
    for dealership, info in dealership_files.items():
        table_name = info['table']
        try:
            result = db_manager.execute_query(f"SELECT COUNT(*) FROM {table_name}")
            count = result[0]['count'] if result else 0
            print(f"  - {dealership}: {count} VINs")
            
            # Show sample records
            sample_result = db_manager.execute_query(f"""
                SELECT vin, order_date, order_type 
                FROM {table_name} 
                LIMIT 3
            """)
            
            if sample_result:
                print(f"    Sample VINs:")
                for record in sample_result:
                    print(f"      - {record['vin']} | {record['order_date']} | {record['order_type']}")
            
        except Exception as e:
            print(f"  - {dealership}: Error - {str(e)}")
    
    return True

if __name__ == "__main__":
    print("="*60)
    print("VIN LOG IMPORT - THOROUGHBRED FORD & GLENDALE CDJR")
    print("Order Type: baseline | Order Date: 2025-09-04")
    print("="*60)
    
    success = import_vinlogs()
    
    if success:
        print("\n[SUCCESS] VIN log import completed successfully!")
    else:
        print("\n[ERROR] VIN log import failed!")