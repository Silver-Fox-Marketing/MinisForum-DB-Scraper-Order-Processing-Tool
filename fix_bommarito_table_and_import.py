#!/usr/bin/env python3
"""
Fix Bommarito Cadillac VIN Log Table Structure and Import Data
Removes unique constraint and imports all VINs including duplicates
"""

import csv
import sys
import os
from datetime import datetime

# Add the scripts directory to Python path
scripts_path = r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts'
sys.path.append(scripts_path)

from database_connection import DatabaseManager

def fix_table_structure(db):
    """
    Fix the table structure by removing unique constraint on VIN
    Following VINLOG_IMPORT_HANDOVER.md requirements
    """
    table_name = "bommarito_cadillac_vin_log"

    print(f"=== FIXING TABLE STRUCTURE: {table_name} ===")

    # Check current table structure
    print("Checking current table constraints...")
    constraints_result = db.execute_query(f"""
        SELECT conname, contype
        FROM pg_constraint
        WHERE conrelid = '{table_name}'::regclass
    """)

    if constraints_result:
        print("Current constraints:")
        for constraint in constraints_result:
            print(f"  {constraint['conname']}: {constraint['contype']}")

    # Remove primary key constraint (which enforces uniqueness on VIN)
    try:
        print("Removing primary key constraint...")
        db.execute_query(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS bommarito_cadillac_vin_log_pkey")
        print("OK Primary key constraint removed")
    except Exception as e:
        print(f"NOTE: {e}")

    # Remove any unique constraints on VIN
    try:
        print("Removing unique constraint on VIN...")
        db.execute_query(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS unique_vin")
        print("OK Unique constraint removed")
    except Exception as e:
        print(f"NOTE: {e}")

    # Add ID column as primary key if it doesn't exist
    try:
        print("Adding ID column as primary key...")
        db.execute_query(f"""
            ALTER TABLE {table_name}
            ADD COLUMN IF NOT EXISTS id SERIAL PRIMARY KEY
        """)
        print("OK ID column added as primary key")
    except Exception as e:
        print(f"NOTE: {e}")

    # Add missing columns if needed
    try:
        print("Adding missing columns...")
        db.execute_query(f"""
            ALTER TABLE {table_name}
            ADD COLUMN IF NOT EXISTS dealership VARCHAR(255),
            ADD COLUMN IF NOT EXISTS order_date DATE,
            ADD COLUMN IF NOT EXISTS template_type VARCHAR(50),
            ADD COLUMN IF NOT EXISTS imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """)
        print("OK Missing columns added")
    except Exception as e:
        print(f"NOTE: {e}")

    # Create indexes for performance (non-unique)
    try:
        print("Creating performance indexes...")
        db.execute_query(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_vin ON {table_name} (vin)")
        db.execute_query(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_order_number ON {table_name} (order_number)")
        print("OK Indexes created")
    except Exception as e:
        print(f"NOTE: {e}")

    print("Table structure fix completed!")
    return True

def import_vins(db):
    """Import VINs from CSV - now that constraints are fixed"""
    dealership_name = "Bommarito Cadillac"
    csv_path = r"C:\Users\Workstation_1\Downloads\BOMM_CADILLAC_VINLOG - LOG (1).csv"
    default_order_date = '2025-09-14'
    order_type = 'Historical'
    table_name = "bommarito_cadillac_vin_log"

    print(f"\n=== IMPORTING VINS ===")
    print(f"Dealership: {dealership_name}")
    print(f"Date: {default_order_date}, Type: {order_type}")

    # Read CSV and process
    processed_data = []
    current_order_number = None

    with open(csv_path, 'r', encoding='utf-8-sig') as file:
        csv_reader = csv.reader(file)
        headers = next(csv_reader)  # Skip header

        for row_count, row in enumerate(csv_reader, 1):
            if len(row) < 2:
                continue

            order_num = row[0].strip() if row[0] else ''
            vin = row[1].strip() if row[1] else ''

            if not vin:
                continue

            if order_num:
                current_order_number = order_num

            final_order_number = current_order_number if current_order_number else "66666"

            processed_data.append({
                'vin': vin,
                'dealership': dealership_name,
                'order_number': final_order_number,
                'order_date': default_order_date,
                'order_type': order_type,
                'row': row_count
            })

    print(f"OK Extracted {len(processed_data)} VIN records")

    # Import ALL records - no more constraint conflicts!
    print(f"Importing {len(processed_data)} VIN records...")

    success_count = 0
    error_count = 0

    for record in processed_data:
        try:
            # Simple insert - no ON CONFLICT needed now
            insert_query = f"""
                INSERT INTO {table_name}
                (vin, dealership, order_number, order_date, order_type, template_type, processed_date, created_at, imported_at)
                VALUES
                (%(vin)s, %(dealership)s, %(order_number)s, %(order_date)s, %(order_type)s, %(template_type)s, %(processed_date)s, NOW(), NOW())
            """

            db.execute_query(insert_query, {
                'vin': record['vin'],
                'dealership': record['dealership'],
                'order_number': record['order_number'],
                'order_date': record['order_date'],
                'order_type': record['order_type'],
                'template_type': 'Historical Import',
                'processed_date': record['order_date']
            })

            success_count += 1

            if success_count <= 5 or success_count % 200 == 0:
                print(f"OK Imported {success_count}: {record['vin']} (Order: {record['order_number']})")

        except Exception as e:
            error_count += 1
            print(f"ERROR Row {record['row']}, VIN {record['vin']}: {e}")

    print(f"\nIMPORT COMPLETE: {success_count} successful, {error_count} errors")
    return success_count

def verify_import(db):
    """Verify the import following VINLOG_IMPORT_HANDOVER.md"""
    table_name = "bommarito_cadillac_vin_log"

    print(f"\n=== VERIFICATION ===")

    # Total record count
    total_result = db.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
    total_count = total_result[0]['count'] if total_result else 0
    print(f"Total records in {table_name}: {total_count}")

    # Records from this import (today's import)
    today_result = db.execute_query(f"""
        SELECT COUNT(*) as count FROM {table_name}
        WHERE order_type = 'Historical' AND order_date = '2025-09-14'
    """)
    today_count = today_result[0]['count'] if today_result else 0
    print(f"Historical records imported today: {today_count}")

    # Order numbers
    order_result = db.execute_query(f"""
        SELECT DISTINCT order_number, COUNT(*) as count
        FROM {table_name}
        WHERE order_type = 'Historical'
        GROUP BY order_number
        ORDER BY order_number
        LIMIT 10
    """)
    print(f"Sample order numbers from import:")
    for order in (order_result or []):
        print(f"  Order {order['order_number']}: {order['count']} VINs")

    # Duplicate VINs (this is expected and correct!)
    duplicate_result = db.execute_query(f"""
        SELECT vin, COUNT(*) as order_count
        FROM {table_name}
        GROUP BY vin
        HAVING COUNT(*) > 1
        ORDER BY order_count DESC
        LIMIT 5
    """)

    if duplicate_result:
        print(f"\nDuplicate VINs (this is correct!):")
        for dup in duplicate_result:
            print(f"  {dup['vin']}: {dup['order_count']} orders")
    else:
        print("No duplicate VINs found")

    return total_count, today_count

def main():
    """Main function"""
    print("=== Bommarito Cadillac VIN Log Fix and Import ===")

    # Initialize database
    try:
        db = DatabaseManager()
        print("OK Database connection established")
    except Exception as e:
        print(f"ERROR Database connection failed: {e}")
        return 1

    # Step 1: Fix table structure
    if not fix_table_structure(db):
        print("ERROR Failed to fix table structure")
        return 1

    # Step 2: Import VINs
    success_count = import_vins(db)
    if success_count == 0:
        print("ERROR No VINs imported")
        return 1

    # Step 3: Verify
    total_count, today_count = verify_import(db)

    print(f"\nSUCCESS: Import completed!")
    print(f"  Total VINs in database: {total_count}")
    print(f"  VINs imported today: {today_count}")
    print(f"  Import success rate: {success_count}/{today_count}")

    return 0

if __name__ == "__main__":
    sys.exit(main())