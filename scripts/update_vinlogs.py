"""
Script to clear and update VIN logs for 4 dealerships
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

def import_vinlog_csv(csv_path, table_name, dealership_name):
    """Import VIN log data from CSV with proper order number assignment"""
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV file not found: {csv_path}")
        return False
    
    try:
        records_to_insert = []
        current_order = None
        
        print(f"\nIMPORTING {dealership_name} from {os.path.basename(csv_path)}")
        
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
                
                # Check if table has imported_at column
                if table_name == 'mini_of_st_louis_vin_log':
                    # Mini of St Louis table structure is different
                    record = (
                        vin,
                        current_order,
                        datetime.now().strftime('%Y-%m-%d'),  # processed_date
                        'CAO',  # order_type (default)
                        'Standard',  # template_type (default)
                        datetime.now()   # created_at
                    )
                else:
                    # Standard table structure
                    record = (
                        vin,
                        current_order,
                        datetime.now().strftime('%Y-%m-%d'),  # processed_date
                        'CAO',  # order_type (default)
                        'Standard',  # template_type (default)
                        datetime.now(),  # created_at
                        datetime.now()   # imported_at
                    )
                records_to_insert.append(record)
        
        if records_to_insert:
            # Insert all records
            if table_name == 'mini_of_st_louis_vin_log':
                columns = ['vin', 'order_number', 'processed_date', 'order_type', 'template_type', 'created_at']
            else:
                columns = ['vin', 'order_number', 'processed_date', 'order_type', 'template_type', 'created_at', 'imported_at']
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
    """Main function to update all 4 dealership VIN logs"""
    
    # Define dealership configurations
    dealerships = [
        {
            'name': 'Spirit Lexus',
            'table': 'spirit_lexus_vin_log',
            'csv': 'SPIRIT_LEXUS_VINLOG - LOG (3).csv'
        },
        {
            'name': 'Suntrup Ford Kirkwood',
            'table': 'suntrup_ford_kirkwood_vin_log', 
            'csv': 'SUNTRUP_FORD_KIRKWOOD_VINLOG - LOG.csv'
        },
        {
            'name': 'Mini of St. Louis',
            'table': 'mini_of_st_louis_vin_log',
            'csv': 'Mini_of_St_Louis_VINLOG - LOG.csv'
        },
        {
            'name': 'Bommarito West County Pre Owned',
            'table': 'bommarito_west_county_vin_log',
            'csv': 'BOMM_WCPO_VINLOG - LOG.csv'
        }
    ]
    
    base_path = r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\VIN LOGS"
    
    print("=== VIN LOG UPDATE PROCESS ===")
    print(f"Processing {len(dealerships)} dealerships")
    print("=" * 50)
    
    for dealership in dealerships:
        print(f"\nProcessing {dealership['name']}...")
        
        # Step 1: Clear existing records
        if clear_vinlog_table(dealership['table']):
            # Step 2: Import new records
            csv_path = os.path.join(base_path, dealership['csv'])
            import_vinlog_csv(csv_path, dealership['table'], dealership['name'])
        
        print("-" * 30)
    
    print("\n=== VIN LOG UPDATE COMPLETE ===")
    
    # Final summary
    print("\nFinal record counts:")
    for dealership in dealerships:
        try:
            result = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {dealership['table']}")
            count = result[0]['count'] if result else 0
            print(f"  {dealership['name']}: {count} records")
        except Exception as e:
            print(f"  {dealership['name']}: ERROR - {e}")

if __name__ == "__main__":
    main()