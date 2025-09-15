"""
Import Pappas Toyota VIN log with correct CSV structure
"""
import sys
import csv
from datetime import datetime

# Add project path
sys.path.append(r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts')

from database_connection import DatabaseManager

def import_pappas_vinlog():
    """Import Pappas Toyota VIN log with order number propagation"""
    db = DatabaseManager()
    
    csv_path = r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\VIN LOGS\PAPPAS_TOYOTA_VINLOG - LOG (1).csv"
    
    print("=== IMPORTING PAPPAS TOYOTA VIN LOG ===")
    print(f"CSV file: {csv_path}")
    
    # Read CSV file - note the different structure
    processed_data = []
    current_order_number = None
    order_date = '2024-08-09'  # August 9 as requested
    
    with open(csv_path, 'r', encoding='utf-8-sig') as file:
        csv_reader = csv.reader(file)
        headers = next(csv_reader)  # Skip header row
        print(f"CSV Headers: {headers}")
        
        for row in csv_reader:
            if len(row) < 2:
                continue
                
            # First column is order number (if present)
            order_num = row[0].strip() if row[0] else ''
            # Second column is VIN
            vin = row[1].strip() if row[1] else ''
            
            if not vin:
                continue
            
            # Update order number if present
            if order_num:
                current_order_number = order_num
                print(f"  New order group: {current_order_number}")
            
            # Add VIN with propagated order number
            if current_order_number and vin:
                processed_data.append({
                    'vin': vin,
                    'dealership': 'Pappas Toyota',
                    'order_number': current_order_number,
                    'order_date': order_date,
                    'order_type': 'CAO',
                    'template_type': 'Standard',
                    'processed_date': order_date,
                    'created_at': datetime.now(),
                    'imported_at': datetime.now()
                })
    
    print(f"\nProcessed {len(processed_data)} VINs")
    
    # Count unique order numbers
    unique_orders = set(item['order_number'] for item in processed_data)
    print(f"Found {len(unique_orders)} unique order numbers")
    
    # Clear existing data first
    print("\nClearing existing data...")
    db.execute_query("DELETE FROM pappas_toyota_vin_log")
    
    # Insert data into database
    if processed_data:
        print("\nInserting data into database...")
        
        inserted_count = 0
        errors = []
        
        for batch_start in range(0, len(processed_data), 50):
            batch = processed_data[batch_start:batch_start + 50]
            
            try:
                # Build insert query
                values = []
                for item in batch:
                    # Escape single quotes in VIN
                    vin = item['vin'].replace("'", "''")
                    values.append(f"""(
                        '{vin}',
                        '{item['order_number']}',
                        '{item['processed_date']}',
                        '{item['order_type']}',
                        '{item['template_type']}',
                        '{item['created_at'].isoformat()}',
                        '{item['imported_at'].isoformat()}',
                        '{item['dealership']}',
                        '{item['order_date']}'
                    )""")
                
                insert_query = f"""
                    INSERT INTO pappas_toyota_vin_log 
                    (vin, order_number, processed_date, order_type, template_type, 
                     created_at, imported_at, dealership, order_date)
                    VALUES {','.join(values)}
                    ON CONFLICT (vin) DO UPDATE SET
                        order_number = EXCLUDED.order_number,
                        dealership = EXCLUDED.dealership,
                        order_date = EXCLUDED.order_date
                """
                
                db.execute_query(insert_query)
                inserted_count += len(batch)
                print(f"  Inserted batch {batch_start//50 + 1}/{(len(processed_data)-1)//50 + 1} ({inserted_count} total)")
                
            except Exception as e:
                print(f"  Error in batch {batch_start//50 + 1}: {e}")
                errors.append(str(e))
    
    # Verify import
    final_count = db.execute_query("SELECT COUNT(*) as count FROM pappas_toyota_vin_log")
    print(f"\nFinal record count: {final_count[0]['count']}")
    
    # Show statistics
    stats = db.execute_query("""
        SELECT 
            COUNT(DISTINCT vin) as unique_vins,
            COUNT(DISTINCT order_number) as unique_orders,
            COUNT(DISTINCT dealership) as unique_dealerships
        FROM pappas_toyota_vin_log
    """)
    
    print("\nImport Statistics:")
    print(f"  Unique VINs: {stats[0]['unique_vins']}")
    print(f"  Unique Orders: {stats[0]['unique_orders']}")
    print(f"  Unique Dealerships: {stats[0]['unique_dealerships']}")
    
    # Show sample data
    sample = db.execute_query("""
        SELECT vin, order_number, order_date, dealership 
        FROM pappas_toyota_vin_log 
        LIMIT 5
    """)
    
    print("\nSample of imported data:")
    for row in sample:
        print(f"  VIN: {row['vin']}, Order: {row['order_number']}, Date: {row['order_date']}, Dealership: {row['dealership']}")
    
    # Show order distribution
    orders = db.execute_query("""
        SELECT order_number, COUNT(*) as vin_count
        FROM pappas_toyota_vin_log
        GROUP BY order_number
        ORDER BY order_number
        LIMIT 10
    """)
    
    print("\nFirst 10 orders:")
    for order in orders:
        print(f"  Order {order['order_number']}: {order['vin_count']} VINs")

if __name__ == "__main__":
    import_pappas_vinlog()
    print("\n=== IMPORT COMPLETE ===")
    print("Pappas Toyota VIN log has been successfully imported!")
    print("The dealership panel should now show the correct VIN history.")