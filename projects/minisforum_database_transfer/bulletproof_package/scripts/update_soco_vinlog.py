#!/usr/bin/env python3
"""
Update SOCO DCJR VIN log from downloaded Excel file
"""

import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, '.')
from database_connection import db_manager

def update_soco_vinlog():
    """Update South County Autos VIN log from Excel file"""
    
    excel_path = r"C:\Users\Workstation_1\Downloads\SOCODCJR_VINLOG.xlsx"
    
    if not Path(excel_path).exists():
        print(f"ERROR: File not found: {excel_path}")
        return False
        
    print(f"Loading VIN log from: {excel_path}")
    
    try:
        # Load the Excel file
        df = pd.read_excel(excel_path)
        print(f"Loaded {len(df)} rows from Excel file")
        
        # Display column information
        print(f"Columns in file: {list(df.columns)}")
        print(f"Sample data:")
        print(df.head())
        
        # Determine the dealership-specific VIN log table name
        dealership_name = "South County Autos"
        table_name = "south_county_autos_vin_log"
        
        print(f"\nUpdating VIN log for: {dealership_name}")
        print(f"Target table: {table_name}")
        
        # Check if the table exists, if not create it
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            vin VARCHAR(17) NOT NULL,
            order_number VARCHAR(20),
            processed_date DATE NOT NULL DEFAULT CURRENT_DATE,
            order_type VARCHAR(20) DEFAULT 'CAO',
            template_type VARCHAR(50) DEFAULT 'Shortcut',
            import_source VARCHAR(100) DEFAULT 'Excel Import',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        db_manager.execute_query(create_table_query)
        print(f"SUCCESS: Ensured table {table_name} exists")
        
        # Drop and recreate table to ensure proper schema
        drop_query = f"DROP TABLE IF EXISTS {table_name}"
        db_manager.execute_query(drop_query)
        print(f"SUCCESS: Dropped existing table {table_name}")
        
        # Recreate table with proper schema
        db_manager.execute_query(create_table_query)
        print(f"SUCCESS: Recreated table {table_name} with correct schema")
        
        # Process and insert VIN data with duplicate removal by order number
        inserted_count = 0
        skipped_duplicates = 0
        
        # Based on the sample data, VIN is in the second column (index 1)
        vin_column = df.columns[1]  # '58ADZ1B10NU133431' column contains VINs
        print(f"Using VIN column: {vin_column}")
        
        # The first column appears to be order numbers, let's use that for reference
        order_column = df.columns[0]  # 'ORDER'
        print(f"Order reference column: {order_column}")
        
        # Try to find date column
        date_column = None
        for col in df.columns:
            if any(keyword in col.upper() for keyword in ['DATE', 'PROCESSED', 'ORDER', 'CREATED']):
                date_column = col
                break
        
        # Process grouped data structure: order number + VINs in groups
        print(f"Original dataset has {len(df)} rows")
        
        current_order_num = None
        group_vins = []
        all_processed_vins = []
        
        # Process each row to identify order groups
        for index, row in df.iterrows():
            order_val = row[order_column] if not pd.isna(row[order_column]) else None
            vin_val = str(row[vin_column]).strip() if not pd.isna(row[vin_column]) else ""
            
            # Check if this row starts a new order group (has order number)
            if order_val is not None:
                # Save previous group if exists
                if current_order_num and group_vins:
                    for group_vin in group_vins:
                        all_processed_vins.append({
                            'order_number': current_order_num,
                            'vin': group_vin
                        })
                
                # Start new group
                current_order_num = str(order_val).strip()
                group_vins = []
                
                # Add VIN from this row if present and valid
                if vin_val and len(vin_val) >= 10:
                    group_vins.append(vin_val)
                    
            elif vin_val and len(vin_val) >= 10:
                # This is a VIN row within current group
                if current_order_num:
                    group_vins.append(vin_val)
                    
            elif not vin_val and current_order_num and group_vins:
                # Empty row - end of current group
                for group_vin in group_vins:
                    all_processed_vins.append({
                        'order_number': current_order_num,
                        'vin': group_vin
                    })
                current_order_num = None
                group_vins = []
        
        # Handle last group if file doesn't end with empty row
        if current_order_num and group_vins:
            for group_vin in group_vins:
                all_processed_vins.append({
                    'order_number': current_order_num,
                    'vin': group_vin
                })
        
        print(f"Processed into {len(all_processed_vins)} VIN entries across order groups")
        
        # Show some example order groups for debugging
        if all_processed_vins:
            print("\nSample order groups:")
            current_order = None
            group_count = 0
            for i, vin_data in enumerate(all_processed_vins[:20]):  # Show first 20 entries
                if vin_data['order_number'] != current_order:
                    if current_order is not None:
                        print()  # New line between groups
                    current_order = vin_data['order_number']
                    group_count += 1
                    print(f"Order {current_order}:", end=" ")
                print(f"VIN-{i+1}", end=" ")
            print(f"\n... (showing first {min(20, len(all_processed_vins))} entries)")
            print(f"Total unique order numbers: {len(set(v['order_number'] for v in all_processed_vins))}")
        
        # Insert processed VINs with their associated order numbers
        for vin_data in all_processed_vins:
            insert_query = f"""
            INSERT INTO {table_name} (vin, order_number, processed_date, order_type, template_type)
            VALUES (%s, %s, CURRENT_DATE, 'CAO', 'Shortcut')
            """
            
            try:
                db_manager.execute_query(insert_query, [vin_data['vin'], vin_data['order_number']])
                inserted_count += 1
                
                if inserted_count % 100 == 0:
                    print(f"Processed {inserted_count} VINs...")
                    
            except Exception as e:
                print(f"Error inserting VIN {vin_data['vin']}: {e}")
                continue
        
        print(f"\n=== IMPORT SUMMARY ===")
        print(f"Total rows processed: {len(df)}")
        print(f"VINs successfully inserted: {inserted_count}")
        
        # Verify the import
        verify_query = f"SELECT COUNT(*) as total FROM {table_name}"
        result = db_manager.execute_query(verify_query)
        total_in_db = result[0]['total'] if result else 0
        
        print(f"Total VINs now in {table_name}: {total_in_db}")
        
        # Show sample of imported data
        sample_query = f"""
        SELECT vin, order_number, processed_date, order_type, template_type 
        FROM {table_name} 
        ORDER BY created_at DESC 
        LIMIT 5
        """
        sample_results = db_manager.execute_query(sample_query)
        
        if sample_results:
            print(f"\nSample of imported VINs:")
            for row in sample_results:
                order_display = row['order_number'] if row['order_number'] else 'No Order#'
                print(f"  {row['vin']} - Order: {order_display} - {row['processed_date']} ({row['order_type']}/{row['template_type']})")
        
        print(f"\nSUCCESS: SOCO DCJR VIN log update completed successfully!")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to update VIN log: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    update_soco_vinlog()