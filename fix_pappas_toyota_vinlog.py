"""
Fix Pappas Toyota VIN log issue and import new data
"""
import sys
import os
import csv
from datetime import datetime

# Add project path
sys.path.append(r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts')

from database_connection import DatabaseManager

def investigate_pappas_toyota():
    """Check current state of Pappas Toyota data"""
    db = DatabaseManager()
    
    print("=== INVESTIGATING PAPPAS TOYOTA ===")
    
    # Check dealership_configs
    configs = db.execute_query("""
        SELECT location, actual_location_name, vin_log_table 
        FROM dealership_configs 
        WHERE LOWER(location) LIKE '%pappas%' OR LOWER(actual_location_name) LIKE '%pappas%'
    """)
    
    if configs:
        print(f"\nFound {len(configs)} Pappas Toyota configs:")
        for config in configs:
            print(f"  Location: {config['location']}")
            print(f"  Actual name: {config['actual_location_name']}")
            print(f"  VIN log table: {config['vin_log_table']}")
            
            # Check VIN log contents
            vin_log_table = config['vin_log_table']
            count_result = db.execute_query(f"SELECT COUNT(*) as count FROM {vin_log_table}")
            print(f"  Current records in {vin_log_table}: {count_result[0]['count']}")
            
            # Check dealership names in VIN log
            dealership_names = db.execute_query(f"""
                SELECT DISTINCT dealership, COUNT(*) as count 
                FROM {vin_log_table} 
                GROUP BY dealership
            """)
            if dealership_names:
                print(f"  Dealership names in VIN log:")
                for name in dealership_names:
                    print(f"    '{name['dealership']}': {name['count']} records")
    
    # Check raw_vehicle_data
    raw_locations = db.execute_query("""
        SELECT DISTINCT location, COUNT(*) as count
        FROM raw_vehicle_data 
        WHERE LOWER(location) LIKE '%pappas%'
        GROUP BY location
    """)
    
    if raw_locations:
        print(f"\nPappas locations in raw_vehicle_data:")
        for loc in raw_locations:
            print(f"  '{loc['location']}': {loc['count']} vehicles")
    
    return configs[0] if configs else None

def clear_pappas_vinlog(vin_log_table):
    """Clear existing Pappas Toyota VIN log"""
    db = DatabaseManager()
    
    print(f"\n=== CLEARING {vin_log_table} ===")
    
    # Get count before clearing
    count_before = db.execute_query(f"SELECT COUNT(*) as count FROM {vin_log_table}")
    print(f"Records before clearing: {count_before[0]['count']}")
    
    # Clear the table
    db.execute_query(f"DELETE FROM {vin_log_table}")
    print(f"Cleared all records from {vin_log_table}")
    
    # Verify it's empty
    count_after = db.execute_query(f"SELECT COUNT(*) as count FROM {vin_log_table}")
    print(f"Records after clearing: {count_after[0]['count']}")

def import_pappas_vinlog(csv_path, vin_log_table, dealership_name):
    """Import new VIN log data with order date and number propagation"""
    db = DatabaseManager()
    
    print(f"\n=== IMPORTING NEW VIN LOG DATA ===")
    print(f"CSV file: {csv_path}")
    print(f"Target table: {vin_log_table}")
    
    # Read CSV file
    with open(csv_path, 'r', encoding='utf-8-sig') as file:
        csv_reader = csv.DictReader(file)
        rows = list(csv_reader)
    
    print(f"Found {len(rows)} rows in CSV")
    
    # Process rows and propagate order numbers
    processed_data = []
    current_order_number = None
    order_date = '2024-08-09'  # August 9 as requested
    
    for row in rows:
        # Get VIN
        vin = row.get('VIN', '').strip()
        if not vin:
            continue
            
        # Check for order number in this row
        order_num = row.get('Order Number', '').strip()
        if order_num:
            # New order group starts
            current_order_number = order_num
            print(f"  New order group: {current_order_number}")
        
        # Add to processed data with propagated order number
        if current_order_number and vin:
            processed_data.append({
                'vin': vin,
                'dealership': dealership_name,
                'order_number': current_order_number,
                'order_date': order_date,
                'order_type': 'CAO',  # Assuming CAO type
                'created_at': datetime.now()
            })
    
    print(f"\nProcessed {len(processed_data)} VINs with order numbers")
    
    # Count unique order numbers
    unique_orders = set(item['order_number'] for item in processed_data)
    print(f"Found {len(unique_orders)} unique order numbers")
    
    # Insert data into database
    if processed_data:
        print("\nInserting data into database...")
        
        for batch_start in range(0, len(processed_data), 100):
            batch = processed_data[batch_start:batch_start + 100]
            
            # Build insert query
            values = []
            for item in batch:
                values.append(f"""(
                    '{item['vin']}',
                    '{item['dealership']}',
                    '{item['order_number']}',
                    '{item['order_date']}',
                    '{item['order_type']}',
                    '{item['created_at']}'
                )""")
            
            insert_query = f"""
                INSERT INTO {vin_log_table} 
                (vin, dealership, order_number, order_date, order_type, created_at)
                VALUES {','.join(values)}
                ON CONFLICT (vin) DO NOTHING
            """
            
            db.execute_query(insert_query)
            print(f"  Inserted batch {batch_start//100 + 1}/{(len(processed_data)-1)//100 + 1}")
    
    # Verify import
    final_count = db.execute_query(f"SELECT COUNT(*) as count FROM {vin_log_table}")
    print(f"\nFinal record count: {final_count[0]['count']}")
    
    # Show sample of imported data
    sample = db.execute_query(f"""
        SELECT vin, order_number, order_date 
        FROM {vin_log_table} 
        LIMIT 5
    """)
    print("\nSample of imported data:")
    for row in sample:
        print(f"  VIN: {row['vin']}, Order: {row['order_number']}, Date: {row['order_date']}")

def main():
    # Step 1: Investigate current state
    config = investigate_pappas_toyota()
    
    if not config:
        print("\nERROR: Could not find Pappas Toyota configuration!")
        return
    
    vin_log_table = config['vin_log_table']
    location_name = config['location']
    
    # Step 2: Clear existing VIN log
    clear_pappas_vinlog(vin_log_table)
    
    # Step 3: Import new VIN log
    csv_path = r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\VIN LOGS\PAPPAS_TOYOTA_VINLOG - LOG (1).csv"
    
    # Use the location name from dealership_configs for consistency
    import_pappas_vinlog(csv_path, vin_log_table, location_name)
    
    print("\n=== PROCESS COMPLETE ===")
    print(f"Successfully updated VIN log for {location_name}")

if __name__ == "__main__":
    main()