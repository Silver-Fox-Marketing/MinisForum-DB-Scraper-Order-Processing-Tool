"""
Script to clear and update VIN log for Suntrup Ford Westport
"""
import csv
import os
from database_connection import db_manager
from datetime import datetime

def clear_vinlog_table(table_name):
    """Clear all records from a VIN log table"""
    try:
        # First drop the primary key constraint to allow duplicates
        try:
            db_manager.execute_non_query(f"ALTER TABLE {table_name} DROP CONSTRAINT {table_name}_pkey")
            print(f"DROPPED primary key constraint on {table_name}")
        except:
            pass  # Constraint might not exist
            
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
                order = row['ORDER'].strip()
                vin = row['VINS'].strip()
                
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
                        vin,
                        current_order,
                        datetime.now().strftime('%Y-%m-%d'),  # processed_date
                        'CAO',  # order_type (default)
                        'Standard',  # template_type (default)
                        datetime.now(),  # created_at
                        datetime.now()   # imported_at
                    )
                else:
                    record = (
                        vin,
                        current_order,
                        datetime.now().strftime('%Y-%m-%d'),  # processed_date
                        'CAO',  # order_type (default)
                        'Standard',  # template_type (default)
                        datetime.now()   # created_at
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
    """Main function to update Suntrup Ford Westport VIN log"""
    
    dealership = {
        'name': 'Suntrup Ford Westport',
        'table': 'suntrup_ford_westport_vin_log',
        'csv': 'SUNTRUP_FORD_WESTPORT_VINLOG - LOG (3).csv'
    }
    
    base_path = r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\VIN LOGS"
    
    print("=== SUNTRUP FORD WESTPORT VIN LOG UPDATE ===")
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
        print(f"Records imported: {after_count - 0}")  # Since we cleared first, imported = final count
    except Exception as e:
        print(f"Error getting final count: {e}")

if __name__ == "__main__":
    main()