"""
Script to clear and update VIN logs for Porsche St. Louis and Suntrup Kia South
"""
import csv
import os
from database_connection import db_manager
from datetime import datetime

def clear_vinlog_table(table_name):
    """Clear all records from a VIN log table"""
    try:
        # Drop primary key constraint to allow duplicates
        constraint_variations = [
            f"{table_name}_pkey",
            f"{table_name.replace('_vin_log', '')}_vin_log_pkey",
            f"porsche_st_louis_vin_log_pkey", 
            f"suntrup_kia_south_vin_log_pkey"
        ]
        
        for constraint_name in constraint_variations:
            try:
                db_manager.execute_non_query(f"ALTER TABLE {table_name} DROP CONSTRAINT {constraint_name}")
                print(f"DROPPED constraint {constraint_name}")
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
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, 1):
                order = row.get('ORDER', '').strip()
                vin = row.get('VIN', row.get('VINS', '')).strip()
                
                if not vin:  # Skip empty VIN rows
                    continue
                
                # If ORDER field has value, use it as current order
                # If ORDER field is empty, use the previous order
                if order:
                    current_order = order
                
                if not current_order:
                    print(f"WARNING: No order number found for VIN {vin} at row {row_num}")
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
    """Main function to update both dealership VIN logs"""
    
    # Define dealership configurations
    dealerships = [
        {
            'name': 'Porsche St. Louis',
            'table': 'porsche_st_louis_vin_log',
            'csv': 'PORSCHESTL_VINLOG - LOG (2).csv'
        },
        {
            'name': 'Suntrup Kia South',
            'table': 'suntrup_kia_south_vin_log',
            'csv': 'SUNTRUP_KIA_VINLOG - LOG.csv'
        }
    ]
    
    base_path = r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\VIN LOGS"
    
    print("=== PORSCHE & SUNTRUP KIA VIN LOG UPDATE ===")
    print("=" * 60)
    
    for dealership in dealerships:
        print(f"\n{'='*20} Processing {dealership['name']} {'='*20}")
        
        # Check if table exists, try to find actual table name
        table_check = db_manager.execute_query(
            f"SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%{dealership['name'].lower().replace(' ', '%')}%vin_log%'"
        )
        
        if table_check:
            actual_table = table_check[0]['table_name']
            print(f"Found table: {actual_table}")
            dealership['table'] = actual_table
        else:
            print(f"Using default table name: {dealership['table']}")
        
        # Step 1: Check current count before clearing
        try:
            result = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {dealership['table']}")
            before_count = result[0]['count'] if result else 0
            print(f"Current records in {dealership['table']}: {before_count}")
        except Exception as e:
            print(f"Table might not exist: {e}")
            before_count = 0
        
        # Step 2: Clear existing records
        if clear_vinlog_table(dealership['table']):
            # Step 3: Import new records
            csv_path = os.path.join(base_path, dealership['csv'])
            import_vinlog_csv(csv_path, dealership['table'], dealership['name'])
        
        # Final count
        try:
            result = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {dealership['table']}")
            after_count = result[0]['count'] if result else 0
            print(f"Final record count for {dealership['name']}: {after_count}")
        except Exception as e:
            print(f"Error getting final count: {e}")
        
        print("-" * 60)
    
    print("\n=== ALL VIN LOG UPDATES COMPLETE ===")

if __name__ == "__main__":
    main()