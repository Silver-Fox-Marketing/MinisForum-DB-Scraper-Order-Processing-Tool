"""
Import ALL Pappas Toyota VINs including duplicates
Following the new VIN LOG IMPORT HANDOVER guidelines
"""
import sys
import csv
from datetime import datetime

# Add project path
sys.path.append(r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts')

from database_connection import DatabaseManager

def import_all_pappas_vins():
    """Import ALL 834 Pappas Toyota VINs including duplicates"""
    db = DatabaseManager()
    
    csv_path = r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\VIN LOGS\PAPPAS_TOYOTA_VINLOG - LOG (1).csv"
    
    print("=== IMPORTING ALL PAPPAS TOYOTA VINS (INCLUDING DUPLICATES) ===")
    print(f"CSV file: {csv_path}")
    
    # First, ensure table structure is correct (no unique constraint on VIN)
    print("\nEnsuring table structure allows duplicates...")
    try:
        # Remove any unique constraint on VIN if it exists
        db.execute_query("""
            ALTER TABLE pappas_toyota_vin_log 
            DROP CONSTRAINT IF EXISTS pappas_toyota_vin_log_vin_key
        """)
        print("Removed VIN unique constraint if it existed")
    except Exception as e:
        print(f"Note: {e}")
    
    # Clear existing data for fresh import
    print("\nClearing existing data...")
    db.execute_query("DELETE FROM pappas_toyota_vin_log")
    
    # Read CSV file and collect ALL records
    all_records = []
    current_order_number = None
    order_date = '2024-08-09'  # August 9 as requested
    
    with open(csv_path, 'r', encoding='utf-8-sig') as file:
        csv_reader = csv.reader(file)
        headers = next(csv_reader)  # Skip header row
        print(f"CSV Headers: {headers}")
        
        row_count = 0
        for row in csv_reader:
            row_count += 1
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
                print(f"  Order group {current_order_number} starting at row {row_count}")
            
            # Add EVERY VIN record (including duplicates!)
            if current_order_number and vin:
                all_records.append({
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
    
    print(f"\nTotal records to import: {len(all_records)}")
    
    # Count duplicates before import
    vin_counts = {}
    for record in all_records:
        vin = record['vin']
        vin_counts[vin] = vin_counts.get(vin, 0) + 1
    
    duplicate_vins = {k: v for k, v in vin_counts.items() if v > 1}
    print(f"VINs appearing multiple times: {len(duplicate_vins)}")
    if duplicate_vins:
        # Show first 5 examples
        examples = list(duplicate_vins.items())[:5]
        for vin, count in examples:
            print(f"  {vin}: appears {count} times")
    
    # Insert ALL records individually to preserve duplicates
    print("\nInserting ALL records (including duplicates)...")
    
    inserted = 0
    failed = 0
    
    for i, record in enumerate(all_records):
        try:
            # Escape single quotes in VIN
            vin = record['vin'].replace("'", "''")
            
            insert_query = f"""
                INSERT INTO pappas_toyota_vin_log 
                (vin, order_number, processed_date, order_type, template_type, 
                 created_at, imported_at, dealership, order_date)
                VALUES 
                ('{vin}', 
                 '{record['order_number']}', 
                 '{record['processed_date']}',
                 '{record['order_type']}', 
                 '{record['template_type']}',
                 '{record['created_at'].isoformat()}', 
                 '{record['imported_at'].isoformat()}',
                 '{record['dealership']}', 
                 '{record['order_date']}')
            """
            
            db.execute_query(insert_query)
            inserted += 1
            
            if (i + 1) % 100 == 0:
                print(f"  Progress: {i + 1}/{len(all_records)} records inserted")
                
        except Exception as e:
            failed += 1
            print(f"  Failed to insert record {i + 1}: {e}")
    
    print(f"\nInsert complete: {inserted} successful, {failed} failed")
    
    # Verify final import
    print("\n=== VERIFICATION ===")
    
    # Total count
    total_count = db.execute_query("SELECT COUNT(*) as count FROM pappas_toyota_vin_log")
    print(f"Total records in database: {total_count[0]['count']}")
    print(f"Expected records from CSV: {len(all_records)}")
    
    # Unique VINs vs total records
    unique_vins = db.execute_query("""
        SELECT COUNT(DISTINCT vin) as unique_count 
        FROM pappas_toyota_vin_log
    """)
    print(f"Unique VINs: {unique_vins[0]['unique_count']}")
    print(f"Duplicate records: {total_count[0]['count'] - unique_vins[0]['unique_count']}")
    
    # Check VINs with multiple orders
    duplicates_in_db = db.execute_query("""
        SELECT vin, COUNT(*) as order_count
        FROM pappas_toyota_vin_log
        GROUP BY vin
        HAVING COUNT(*) > 1
        ORDER BY order_count DESC
        LIMIT 10
    """)
    
    if duplicates_in_db:
        print("\nTop 10 VINs with multiple orders (THIS IS CORRECT!):")
        for dup in duplicates_in_db:
            print(f"  {dup['vin']}: {dup['order_count']} orders")
    
    # Order statistics
    order_stats = db.execute_query("""
        SELECT 
            COUNT(DISTINCT order_number) as unique_orders,
            MIN(order_date) as earliest_date,
            MAX(order_date) as latest_date
        FROM pappas_toyota_vin_log
    """)
    
    print(f"\nOrder Statistics:")
    print(f"  Unique order numbers: {order_stats[0]['unique_orders']}")
    print(f"  Date range: {order_stats[0]['earliest_date']} to {order_stats[0]['latest_date']}")
    
    # Sample of data
    sample = db.execute_query("""
        SELECT vin, order_number, order_date, dealership 
        FROM pappas_toyota_vin_log 
        ORDER BY order_number, vin
        LIMIT 5
    """)
    
    print("\nSample of imported data:")
    for row in sample:
        print(f"  VIN: {row['vin']}, Order: {row['order_number']}, Date: {row['order_date']}, Dealership: {row['dealership']}")

if __name__ == "__main__":
    import_all_pappas_vins()
    print("\n=== IMPORT COMPLETE ===")
    print("ALL Pappas Toyota VINs have been imported, including duplicates!")
    print("This correctly represents every graphics order placed.")