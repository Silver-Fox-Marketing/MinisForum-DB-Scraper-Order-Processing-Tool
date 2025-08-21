#!/usr/bin/env python3
"""
Import Honda VIN log with proper order number grouping and Baseline date designation
"""

import pandas as pd
from database_connection import db_manager
from datetime import datetime

def import_honda_baseline_vinlog():
    """Import Honda VIN log with order groups and Baseline date"""
    
    try:
        # First, clear the current Honda VIN log
        db_manager.execute_query('DELETE FROM honda_of_frontenac_vin_log')
        print('Cleared existing Honda VIN log data')
        
        # Read the Honda VIN log Excel file
        excel_path = 'C:/Users/Workstation_1/Documents/Tools/ClaudeCode/projects/shared_resources/VIN LOGS/HONDAofFRONTENAC_VINLOG.xlsx'
        df = pd.read_excel(excel_path)
        
        print(f'Read {len(df)} rows from Excel file')
        print(f'Columns: {list(df.columns)}')
        
        # Parse the order groups format
        current_order = None
        imported = 0
        
        for index, row in df.iterrows():
            order_val = row['ORDER']
            vin_val = row['VIN']
            
            # Convert to strings for processing
            order_str = str(order_val).strip() if pd.notna(order_val) else ''
            vin_str = str(vin_val).strip().upper() if pd.notna(vin_val) else ''
            
            # Check if this row has an order number (start of new order group)
            if pd.notna(order_val) and order_str != '' and order_str != 'nan':
                current_order = order_str
                print(f'Found order group: {current_order}')
                
                # This row might also have a VIN, so continue processing
            
            # Check if this row has a VIN and we have a current order
            if pd.notna(vin_val) and vin_str != '' and vin_str != 'NAN' and len(vin_str) >= 10 and current_order:
                try:
                    # Insert VIN with order number and special baseline date (Jan 1, 2020) for both order_date and processed_date
                    baseline_date = datetime(2020, 1, 1).date()
                    db_manager.execute_query('''
                        INSERT INTO honda_of_frontenac_vin_log (vin, order_number, order_date, order_type, processed_date)
                        VALUES (%s, %s, %s, %s, %s)
                    ''', (vin_str, current_order, baseline_date, 'BASELINE_IMPORT', baseline_date))
                    
                    imported += 1
                    
                    if imported % 50 == 0:
                        print(f'Imported {imported} VINs...')
                    
                except Exception as e:
                    if 'duplicate' not in str(e).lower():
                        print(f'Error importing VIN {vin_str} for order {current_order}: {e}')
            
            # Check for blank row (end of order group)
            if pd.isna(order_val) and pd.isna(vin_val):
                if current_order:
                    print(f'End of order group: {current_order}')
                current_order = None
        
        print(f'Successfully imported {imported} VINs with order numbers and Baseline date')
        
        # Check final count
        result = db_manager.execute_query('SELECT COUNT(*) as count FROM honda_of_frontenac_vin_log')
        print(f'Honda of Frontenac VIN log count: {result[0]["count"]}')
        
        # Show sample of imported data
        sample = db_manager.execute_query('''
            SELECT vin, order_number, order_date, order_type 
            FROM honda_of_frontenac_vin_log 
            ORDER BY id 
            LIMIT 5
        ''')
        
        print('Sample imported data:')
        for row in sample:
            print(f'  Order: {row["order_number"]} | VIN: {row["vin"]} | Date: {row["order_date"]}')

    except Exception as e:
        print(f'Error processing Honda VIN log: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    import_honda_baseline_vinlog()