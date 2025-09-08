"""
Fix Thoroughbred Ford VIN log table and import data
"""

import sys
import os
import pandas as pd

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_connection import db_manager

def fix_thoroughbred_ford_vinlog():
    """Fix the Thoroughbred Ford VIN log table structure and import data"""
    
    print("="*60)
    print("FIXING THOROUGHBRED FORD VIN LOG TABLE")
    print("="*60)
    
    # Test database connection
    if not db_manager.test_connection():
        print("[ERROR] Database connection failed")
        return False
    
    table_name = 'thoroughbred_ford_vin_log'
    file_path = r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\Vinlogs\TBRED_FORD_VINLOG - LOG (1).csv'
    
    print(f"\nTable: {table_name}")
    print(f"File: {file_path}")
    
    # Step 1: Check current table structure
    print(f"\n[STEP 1] Checking current table structure...")
    try:
        structure_query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = %s
        ORDER BY ordinal_position
        """
        
        columns = db_manager.execute_query(structure_query, (table_name,))
        
        if columns:
            print(f"   [INFO] Current table structure:")
            for col in columns:
                print(f"     - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
        else:
            print(f"   [INFO] Table {table_name} does not exist")
            
    except Exception as e:
        print(f"   [ERROR] Failed to check table structure: {str(e)}")
        return False
    
    # Step 2: Drop and recreate the table with correct structure
    print(f"\n[STEP 2] Recreating table with correct structure...")
    try:
        # Drop existing table
        db_manager.execute_query(f"DROP TABLE IF EXISTS {table_name}")
        print(f"   [OK] Dropped existing table")
        
        # Create new table with correct structure
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
        print(f"   [OK] Created new table with correct structure")
        
    except Exception as e:
        print(f"   [ERROR] Failed to recreate table: {str(e)}")
        return False
    
    # Step 3: Read CSV file
    print(f"\n[STEP 3] Reading CSV file...")
    try:
        df = pd.read_csv(file_path)
        print(f"   [OK] Read {len(df)} rows from CSV")
        print(f"   [INFO] Columns: {list(df.columns)}")
        
        # Find VIN column (should be 'VINS' based on previous output)
        vin_column = 'VINS'  # We know from previous run it's 'VINS'
        
        if vin_column not in df.columns:
            print(f"   [ERROR] Expected VIN column '{vin_column}' not found")
            return False
        
        print(f"   [INFO] Using VIN column: {vin_column}")
        
        # Get clean VINs
        vins = df[vin_column].dropna().astype(str).str.strip()
        vins = [v for v in vins if v and len(v) >= 11 and v.lower() != 'nan']
        vins = list(set(vins))  # Remove duplicates
        
        print(f"   [INFO] Found {len(vins)} unique valid VINs to import")
        
        # Show first few VINs for verification
        print(f"   [INFO] Sample VINs: {vins[:3]}")
        
    except Exception as e:
        print(f"   [ERROR] Failed to read CSV: {str(e)}")
        return False
    
    # Step 4: Import VINs
    print(f"\n[STEP 4] Importing VINs...")
    try:
        success_count = 0
        
        for vin in vins:
            try:
                insert_query = f"""
                INSERT INTO {table_name} (vin, dealership, order_date, order_type)
                VALUES (%s, %s, %s, %s)
                """
                
                db_manager.execute_query(insert_query, (
                    vin,
                    'Thoroughbred Ford',
                    '2025-09-04',
                    'baseline'
                ))
                success_count += 1
                
            except Exception as e:
                print(f"   [ERROR] Failed to insert VIN {vin}: {str(e)}")
        
        print(f"   [OK] Successfully imported {success_count} VINs")
        
        # Verify final count
        count_result = db_manager.execute_query(f"SELECT COUNT(*) FROM {table_name}")
        final_count = count_result[0]['count'] if count_result else 0
        print(f"   [VERIFY] Final count in {table_name}: {final_count}")
        
        # Show sample records
        sample_result = db_manager.execute_query(f"""
            SELECT vin, dealership, order_date, order_type 
            FROM {table_name} 
            LIMIT 5
        """)
        
        if sample_result:
            print(f"   [VERIFY] Sample records:")
            for record in sample_result:
                print(f"     - {record['vin']} | {record['dealership']} | {record['order_date']} | {record['order_type']}")
        
        return True
        
    except Exception as e:
        print(f"   [ERROR] Failed to import VINs: {str(e)}")
        return False

if __name__ == "__main__":
    success = fix_thoroughbred_ford_vinlog()
    
    if success:
        print(f"\n{'='*60}")
        print("[SUCCESS] Thoroughbred Ford VIN log fixed and imported!")
        print('='*60)
    else:
        print(f"\n{'='*60}")
        print("[ERROR] Failed to fix Thoroughbred Ford VIN log!")
        print('='*60)