"""
Script to clear and update VIN log for South County DCJR
"""
import csv
import os
from database_connection import db_manager
from datetime import datetime

def clear_vinlog_table(table_name):
    """Clear all records from a VIN log table"""
    try:
        # Drop primary key constraint to allow duplicates
        try:
            db_manager.execute_non_query(f"ALTER TABLE {table_name} DROP CONSTRAINT {table_name}_pkey")
            print(f"DROPPED primary key constraint on {table_name}")
        except:
            # Try alternative constraint name patterns
            alt_names = [
                f"{table_name.replace('_vin_log', '')}_vin_log_pkey",
                f"south_county_dcjr_vin_log_pkey",
                f"south_county_autos_vin_log_pkey"
            ]
            for alt_name in alt_names:
                try:
                    db_manager.execute_non_query(f"ALTER TABLE {table_name} DROP CONSTRAINT {alt_name}")
                    print(f"DROPPED constraint {alt_name}")
                    break
                except:
                    continue
            
        count = db_manager.execute_non_query(f"DELETE FROM {table_name}")
        print(f"CLEARED {table_name}: Removed {count} records")
        return True
    except Exception as e:
        print(f"ERROR clearing {table_name}: {e}")
        return False

def check_table_structure(table_name):
    """Check if table has imported_at column"""
    result = db_manager.execute_query(
        f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}' AND column_name = 'imported_at'"
    )
    return len(result) > 0

def import_vinlog_csv(csv_path, table_name, dealership_name):
    """Import VIN log data from CSV with proper order number assignment"""
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV file not found: {csv_path}")
        return False
    
    try:
        records_to_insert = []
        current_order = None
        has_imported_at = check_table_structure(table_name)
        
        print(f"\nIMPORTING {dealership_name} from {os.path.basename(csv_path)}")
        print(f"Table has imported_at column: {has_imported_at}")
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            # Read first line to determine structure
            first_line = file.readline().strip()
            file.seek(0)
            
            if ',' in first_line:
                # Check if first line has ORDER,VIN format or ORDER,VINS
                if first_line.startswith('ORDER,'):
                    parts = first_line.split(',', 1)
                    if len(parts) == 2 and parts[1] not in ['VINS', 'VIN']:
                        # First line contains ORDER,actual_vin - process as data
                        print("Processing file with ORDER,VIN format (no header)")
                        for line_num, line in enumerate(file, 1):
                            if not line.strip():
                                continue
                                
                            parts = line.strip().split(',', 1)
                            if len(parts) == 2:
                                order = parts[0].strip()
                                vin = parts[1].strip()
                            else:
                                order = ''
                                vin = line.strip()
                            
                            if not vin:
                                continue
                            
                            # If ORDER field has value, use it as current order
                            if order:
                                current_order = order
                            
                            if not current_order:
                                print(f"WARNING: No order number found for VIN {vin} at line {line_num}")
                                continue
                            
                            # Prepare record for insertion based on table structure
                            if has_imported_at:
                                record = (
                                    vin, current_order, datetime.now().strftime('%Y-%m-%d'),
                                    'CAO', 'Standard', datetime.now(), datetime.now()
                                )
                            else:
                                record = (
                                    vin, current_order, datetime.now().strftime('%Y-%m-%d'),
                                    'CAO', 'Standard', datetime.now()
                                )
                            records_to_insert.append(record)
                    else:
                        # Normal CSV with header
                        reader = csv.DictReader(file)
                        for row_num, row in enumerate(reader, 1):
                            order = row.get('ORDER', '').strip()
                            vin = row.get('VINS', row.get('VIN', '')).strip()
                            
                            if not vin:
                                continue
                            
                            if order:
                                current_order = order
                            
                            if not current_order:
                                print(f"WARNING: No order number found for VIN {vin} at row {row_num}")
                                continue
                            
                            if has_imported_at:
                                record = (
                                    vin, current_order, datetime.now().strftime('%Y-%m-%d'),
                                    'CAO', 'Standard', datetime.now(), datetime.now()
                                )
                            else:
                                record = (
                                    vin, current_order, datetime.now().strftime('%Y-%m-%d'),
                                    'CAO', 'Standard', datetime.now()
                                )
                            records_to_insert.append(record)
        
        if records_to_insert:
            # Insert all records with appropriate columns
            if has_imported_at:
                columns = ['vin', 'order_number', 'processed_date', 'order_type', 'template_type', 'created_at', 'imported_at']
            else:
                columns = ['vin', 'order_number', 'processed_date', 'order_type', 'template_type', 'created_at']
                
            rows_inserted = db_manager.execute_batch_insert(table_name, columns, records_to_insert)
            
            print(f"SUCCESS: Inserted {rows_inserted} records into {table_name}")
            
            # Show sample of inserted data
            sample = db_manager.execute_query(f"SELECT vin, order_number FROM {table_name} LIMIT 5")
            print("Sample inserted records:")
            for record in sample:
                print(f"  VIN: {record['vin']} -> Order: {record['order_number']}")
                
            return True
        else:
            print(f"WARNING: No valid records found in {csv_path}")
            return False
            
    except Exception as e:
        print(f"ERROR importing {csv_path}: {e}")
        return False

def main():
    """Main function to update South County DCJR VIN log"""
    
    dealership = {
        'name': 'South County DCJR',
        'table': 'south_county_dcjr_vin_log',  # Most likely table name
        'csv': 'SOCODCJR_VINLOG - LOG (4).csv'
    }
    
    # Check if table exists, try alternative names if needed
    table_check = db_manager.execute_query(
        "SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%south%county%' AND table_name LIKE '%vin_log%'"
    )
    
    if table_check:
        actual_table = table_check[0]['table_name']
        print(f"Found table: {actual_table}")
        dealership['table'] = actual_table
    else:
        print(f"Table not found, using default: {dealership['table']}")
    
    base_path = r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\VIN LOGS"
    
    print("=== SOUTH COUNTY DCJR VIN LOG UPDATE ===")
    print("=" * 50)
    
    # Step 1: Check current count before clearing
    try:
        result = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {dealership['table']}")
        before_count = result[0]['count'] if result else 0
        print(f"Current records in table: {before_count}")
    except Exception as e:
        print(f"Table might not exist yet: {e}")
        before_count = 0
    
    # Step 2: Clear existing records
    print(f"\nClearing {dealership['name']} VIN log...")
    if clear_vinlog_table(dealership['table']):
        # Step 3: Import new records
        csv_path = os.path.join(base_path, dealership['csv'])
        import_vinlog_csv(csv_path, dealership['table'], dealership['name'])
    
    print("-" * 50)
    
    # Final summary
    print("\n=== VIN LOG UPDATE COMPLETE ===")
    try:
        result = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {dealership['table']}")
        after_count = result[0]['count'] if result else 0
        print(f"Final record count: {after_count} records")
    except Exception as e:
        print(f"Error getting final count: {e}")

if __name__ == "__main__":
    main()