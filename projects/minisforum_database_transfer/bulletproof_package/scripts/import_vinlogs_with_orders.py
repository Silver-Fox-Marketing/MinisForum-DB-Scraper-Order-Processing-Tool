"""
Import VIN logs with proper order number mapping
Each VIN gets associated with the most recent order number from above
"""

import sys
import os
import pandas as pd

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_connection import db_manager

def import_vinlogs_with_orders():
    """Import VIN logs with order number mapping for Thoroughbred Ford and Glendale CDJR"""
    
    print("="*60)
    print("VIN LOG IMPORT WITH ORDER NUMBER MAPPING")
    print("="*60)
    
    # Test database connection
    if not db_manager.test_connection():
        print("[ERROR] Database connection failed")
        return False
    print("[OK] Database connection successful")
    
    # Define the dealerships and their file mappings
    dealership_files = {
        'Thoroughbred Ford': {
            'file': r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\Vinlogs\TBRED_FORD_VINLOG - LOG (1).csv',
            'table': 'thoroughbred_ford_vin_log',
            'vin_column': 'VINS'
        },
        'Glendale CDJR': {
            'file': r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\Vinlogs\GLENDALE_VINLOG - LOG (1).csv',
            'table': 'glendale_cdjr_vin_log', 
            'vin_column': 'VIN'
        }
    }
    
    for dealership, info in dealership_files.items():
        file_path = info['file']
        table_name = info['table']
        vin_column = info['vin_column']
        
        print(f"\n{'='*60}")
        print(f"Processing: {dealership}")
        print(f"Table: {table_name}")
        print(f"File: {file_path}")
        print(f"VIN Column: {vin_column}")
        print('='*60)
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"[ERROR] File not found: {file_path}")
            continue
        
        # Step 1: Drop and recreate table with order_number field
        print(f"\n[STEP 1] Creating table with order_number field...")
        try:
            # Drop existing table
            db_manager.execute_query(f"DROP TABLE IF EXISTS {table_name}")
            
            # Create new table with order_number field
            create_query = f"""
            CREATE TABLE {table_name} (
                id SERIAL PRIMARY KEY,
                vin VARCHAR(17) NOT NULL,
                dealership VARCHAR(255),
                order_date DATE,
                order_type VARCHAR(50),
                order_number VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(vin)
            )
            """
            db_manager.execute_query(create_query)
            print(f"   [OK] Created table with order_number field")
        except Exception as e:
            print(f"   [ERROR] Failed to create table: {str(e)}")
            continue
        
        # Step 2: Read and process CSV file
        print(f"\n[STEP 2] Reading CSV and mapping order numbers...")
        try:
            df = pd.read_csv(file_path)
            print(f"   [OK] Read {len(df)} rows from CSV")
            print(f"   [INFO] Columns: {list(df.columns)}")
            
            # Process the data to map VINs to order numbers
            processed_data = []
            current_order_number = None
            
            for index, row in df.iterrows():
                order_value = str(row['ORDER']).strip() if pd.notna(row['ORDER']) else ""
                vin_value = str(row[vin_column]).strip() if pd.notna(row[vin_column]) else ""
                
                # Skip rows with no VIN
                if not vin_value or len(vin_value) < 11 or vin_value.lower() == 'nan':
                    continue
                
                # If this row has an order number, update current_order_number
                if order_value and order_value != "" and order_value.lower() != 'nan':
                    current_order_number = order_value
                    print(f"   [INFO] Found order number: {current_order_number}")
                
                # Add VIN with current order number
                processed_data.append({
                    'vin': vin_value,
                    'order_number': current_order_number,
                    'dealership': dealership,
                    'order_date': '2025-09-04',
                    'order_type': 'baseline'
                })
            
            print(f"   [INFO] Processed {len(processed_data)} VINs with order numbers")
            
            # Show distribution by order number
            order_counts = {}
            for item in processed_data:
                order_num = item['order_number']
                order_counts[order_num] = order_counts.get(order_num, 0) + 1
            
            print(f"   [INFO] Order number distribution:")
            for order_num, count in sorted(order_counts.items()):
                print(f"     - Order {order_num}: {count} VINs")
            
        except Exception as e:
            print(f"   [ERROR] Failed to process CSV: {str(e)}")
            continue
        
        # Step 3: Import VINs with order numbers
        print(f"\n[STEP 3] Importing VINs with order numbers...")
        try:
            success_count = 0
            error_count = 0
            
            for item in processed_data:
                try:
                    insert_query = f"""
                    INSERT INTO {table_name} (vin, dealership, order_date, order_type, order_number)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (vin) DO UPDATE SET
                        order_number = EXCLUDED.order_number,
                        order_date = EXCLUDED.order_date,
                        order_type = EXCLUDED.order_type
                    """
                    
                    db_manager.execute_query(insert_query, (
                        item['vin'],
                        item['dealership'], 
                        item['order_date'],
                        item['order_type'],
                        item['order_number']
                    ))
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    if error_count <= 3:
                        print(f"   [ERROR] Failed to insert VIN {item['vin']}: {str(e)}")
            
            print(f"   [OK] Successfully imported {success_count} VINs")
            if error_count > 0:
                print(f"   [WARNING] {error_count} VINs failed to import")
            
            # Verify final count and show samples by order
            final_result = db_manager.execute_query(f"SELECT COUNT(*) FROM {table_name}")
            final_count = final_result[0]['count'] if final_result else 0
            print(f"   [VERIFY] Final count in {table_name}: {final_count}")
            
            # Show sample records by order number
            sample_result = db_manager.execute_query(f"""
                SELECT order_number, COUNT(*) as vin_count
                FROM {table_name}
                GROUP BY order_number
                ORDER BY order_number
            """)
            
            if sample_result:
                print(f"   [VERIFY] VINs by order number:")
                for record in sample_result:
                    print(f"     - Order {record['order_number']}: {record['vin_count']} VINs")
            
        except Exception as e:
            print(f"   [ERROR] Failed to import VINs: {str(e)}")
            continue
    
    print(f"\n{'='*60}")
    print("VIN LOG IMPORT WITH ORDER NUMBERS COMPLETE")
    print('='*60)
    
    # Final summary with order mapping
    print("\nFINAL SUMMARY:")
    for dealership, info in dealership_files.items():
        table_name = info['table']
        try:
            # Total count
            result = db_manager.execute_query(f"SELECT COUNT(*) FROM {table_name}")
            count = result[0]['count'] if result else 0
            print(f"\n  {dealership}: {count} VINs total")
            
            # Order breakdown
            order_result = db_manager.execute_query(f"""
                SELECT order_number, COUNT(*) as count, 
                       MIN(vin) as sample_vin
                FROM {table_name}
                GROUP BY order_number
                ORDER BY order_number
            """)
            
            if order_result:
                for record in order_result:
                    print(f"    Order {record['order_number']}: {record['count']} VINs (e.g., {record['sample_vin']})")
            
        except Exception as e:
            print(f"  - {dealership}: Error - {str(e)}")
    
    return True

if __name__ == "__main__":
    success = import_vinlogs_with_orders()
    
    if success:
        print(f"\n{'='*60}")
        print("[SUCCESS] VIN logs imported with order number mapping!")
        print('='*60)
    else:
        print(f"\n{'='*60}")
        print("[ERROR] VIN log import failed!")
        print('='*60)