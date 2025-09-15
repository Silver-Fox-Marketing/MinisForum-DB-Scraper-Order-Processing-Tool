"""
Complete fix for Pappas Toyota VIN log issue
"""
import sys
import os
import csv
from datetime import datetime

# Add project path
sys.path.append(r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts')

from database_connection import DatabaseManager

def fix_pappas_vin_log_structure():
    """Fix the pappas_toyota_vin_log table structure"""
    db = DatabaseManager()
    
    print("=== FIXING PAPPAS TOYOTA VIN LOG TABLE STRUCTURE ===")
    
    # First, add the missing dealership column if it doesn't exist
    try:
        db.execute_query("""
            ALTER TABLE pappas_toyota_vin_log 
            ADD COLUMN IF NOT EXISTS dealership VARCHAR(255)
        """)
        print("Added dealership column to pappas_toyota_vin_log")
    except Exception as e:
        print(f"Note: {e}")
    
    # Update all existing records to have the correct dealership name
    db.execute_query("""
        UPDATE pappas_toyota_vin_log 
        SET dealership = 'Pappas Toyota'
        WHERE dealership IS NULL
    """)
    print("Updated existing records with dealership name")
    
    # Add order_date column if missing
    try:
        db.execute_query("""
            ALTER TABLE pappas_toyota_vin_log 
            ADD COLUMN IF NOT EXISTS order_date DATE
        """)
        print("Added order_date column")
    except Exception as e:
        print(f"Note: {e}")
    
    # Update processed_date to order_date for existing records
    db.execute_query("""
        UPDATE pappas_toyota_vin_log 
        SET order_date = processed_date::date
        WHERE order_date IS NULL AND processed_date IS NOT NULL
    """)
    print("Updated order_date from processed_date")

def clear_and_import_vinlog(csv_path):
    """Clear existing data and import new VIN log"""
    db = DatabaseManager()
    
    print("\n=== CLEARING EXISTING VIN LOG DATA ===")
    
    # Clear the table
    db.execute_query("DELETE FROM pappas_toyota_vin_log")
    print("Cleared all existing records from pappas_toyota_vin_log")
    
    print("\n=== IMPORTING NEW VIN LOG DATA ===")
    print(f"CSV file: {csv_path}")
    
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
            print(f"  Processing order group: {current_order_number}")
        
        # Add to processed data with propagated order number
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
    
    # Insert data into database
    if processed_data:
        print("\nInserting data into database...")
        
        inserted_count = 0
        for batch_start in range(0, len(processed_data), 100):
            batch = processed_data[batch_start:batch_start + 100]
            
            # Build insert query with all columns
            values = []
            for item in batch:
                values.append(f"""(
                    '{item['vin']}',
                    '{item['order_number']}',
                    '{item['processed_date']}',
                    '{item['order_type']}',
                    '{item['template_type']}',
                    '{item['created_at']}',
                    '{item['imported_at']}',
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
            print(f"  Inserted batch {batch_start//100 + 1}/{(len(processed_data)-1)//100 + 1} ({inserted_count} total)")
    
    # Verify import
    final_count = db.execute_query("SELECT COUNT(*) as count FROM pappas_toyota_vin_log")
    print(f"\nFinal record count: {final_count[0]['count']}")
    
    # Show sample of imported data
    sample = db.execute_query("""
        SELECT vin, order_number, order_date, dealership 
        FROM pappas_toyota_vin_log 
        LIMIT 5
    """)
    print("\nSample of imported data:")
    for row in sample:
        print(f"  VIN: {row['vin']}, Order: {row['order_number']}, Date: {row['order_date']}, Dealership: {row['dealership']}")

def verify_fix():
    """Verify the fix worked"""
    db = DatabaseManager()
    
    print("\n=== VERIFYING FIX ===")
    
    # Check dealership values
    dealerships = db.execute_query("""
        SELECT DISTINCT dealership, COUNT(*) as count
        FROM pappas_toyota_vin_log
        GROUP BY dealership
    """)
    
    print("Dealership values in VIN log:")
    for d in dealerships:
        print(f"  '{d['dealership']}': {d['count']} records")
    
    # Check order distribution
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
    
    # Check total stats
    stats = db.execute_query("""
        SELECT 
            COUNT(DISTINCT vin) as unique_vins,
            COUNT(DISTINCT order_number) as unique_orders,
            MIN(order_date) as earliest_date,
            MAX(order_date) as latest_date
        FROM pappas_toyota_vin_log
    """)
    
    print("\nOverall statistics:")
    print(f"  Total unique VINs: {stats[0]['unique_vins']}")
    print(f"  Total unique orders: {stats[0]['unique_orders']}")
    print(f"  Date range: {stats[0]['earliest_date']} to {stats[0]['latest_date']}")

def main():
    # Step 1: Fix table structure
    fix_pappas_vin_log_structure()
    
    # Step 2: Clear and import new data
    csv_path = r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\VIN LOGS\PAPPAS_TOYOTA_VINLOG - LOG (1).csv"
    
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV file not found at {csv_path}")
        return
    
    clear_and_import_vinlog(csv_path)
    
    # Step 3: Verify the fix
    verify_fix()
    
    print("\n=== PROCESS COMPLETE ===")
    print("Successfully fixed and updated Pappas Toyota VIN log!")
    print("The dealership panel should now show the correct VIN history.")

if __name__ == "__main__":
    main()