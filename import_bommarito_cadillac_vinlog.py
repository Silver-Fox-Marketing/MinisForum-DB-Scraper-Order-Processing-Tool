#!/usr/bin/env python3
"""
Import Bommarito Cadillac VIN Log from Downloaded CSV
Follows VINLOG_IMPORT_HANDOVER.md documentation exactly.
"""

import csv
import sys
import os
from datetime import datetime

# Add the scripts directory to Python path
scripts_path = r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts'
sys.path.append(scripts_path)

from database_connection import DatabaseManager

def import_bommarito_cadillac_vinlog():
    """
    Import VIN log for Bommarito Cadillac, preserving ALL records including duplicates
    """
    dealership_name = "Bommarito Cadillac"
    csv_path = r"C:\Users\Workstation_1\Downloads\BOMM_CADILLAC_VINLOG - LOG (1).csv"
    default_order_date = '2025-09-14'  # User specified 9/14
    order_type = 'Historical'  # User specified Historical

    print("=== Bommarito Cadillac VIN Log Import ===")
    print(f"Dealership: {dealership_name}")
    print(f"CSV File: {csv_path}")
    print(f"Default Date: {default_order_date}")
    print(f"Order Type: {order_type}")

    # Initialize database manager
    try:
        db = DatabaseManager()
        print("OK Database connection established")
    except Exception as e:
        print(f"ERROR Database connection failed: {e}")
        return False

    # Find correct table name
    table_result = db.execute_query(f"""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name LIKE '%{dealership_name.lower().replace(' ', '_')}%vin_log%'
    """)

    if not table_result:
        print(f"ERROR No VIN log table found for {dealership_name}")
        return False

    table_name = table_result[0]['table_name']
    print(f"OK Using table: {table_name}")

    # Read CSV and process - ONLY column 2 (VIN), ignore all other columns
    processed_data = []
    current_order_number = None

    print(f"Reading CSV file...")

    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as file:
            csv_reader = csv.reader(file)
            headers = next(csv_reader)  # Skip header
            print(f"CSV headers: {headers}")

            row_count = 0
            for row in csv_reader:
                row_count += 1

                if len(row) < 2:
                    continue

                # Column 1: Order number (may be empty)
                # Column 2: VIN (focus only on this)
                order_num = row[0].strip() if row[0] else ''
                vin = row[1].strip() if row[1] else ''

                # Skip if no VIN in column 2
                if not vin:
                    continue

                # Handle order number propagation
                if order_num:
                    current_order_number = order_num
                    print(f"Row {row_count}: New order number {order_num}")

                # Use order number 66666 if no order number available
                final_order_number = current_order_number if current_order_number else "66666"

                processed_data.append({
                    'vin': vin,
                    'dealership': dealership_name,
                    'order_number': final_order_number,
                    'order_date': default_order_date,
                    'order_type': order_type,
                    'row': row_count
                })

                if row_count <= 10 or row_count % 100 == 0:
                    print(f"Row {row_count}: VIN={vin}, Order={final_order_number}")

    except Exception as e:
        print(f"ERROR Reading CSV: {e}")
        return False

    print(f"OK Extracted {len(processed_data)} VIN records from CSV")

    # CRITICAL: Insert ALL records, don't skip duplicates!
    # This follows the VINLOG_IMPORT_HANDOVER.md requirement to preserve duplicates
    print(f"Importing {len(processed_data)} VIN records to {table_name}...")

    success_count = 0
    error_count = 0

    for record in processed_data:
        try:
            # IMPORTANT: NO ON CONFLICT clause - we want ALL records including duplicates
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

            if success_count <= 5 or success_count % 100 == 0:
                print(f"OK Imported {success_count}: {record['vin']} (Order: {record['order_number']})")

        except Exception as e:
            error_count += 1
            print(f"ERROR Row {record['row']}, VIN {record['vin']}: {e}")

    print(f"IMPORT COMPLETE: {success_count} successful, {error_count} errors")

    # Verify import following VINLOG_IMPORT_HANDOVER.md verification checklist
    print(f"\n=== VERIFICATION ===")

    # 1. Total record count
    total_result = db.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
    total_count = total_result[0]['count'] if total_result else 0
    print(f"Total records in {table_name}: {total_count}")

    # 2. Order numbers present
    order_result = db.execute_query(f"""
        SELECT DISTINCT order_number, COUNT(*) as count
        FROM {table_name}
        GROUP BY order_number
        ORDER BY order_number
    """)
    print(f"Order numbers found: {len(order_result) if order_result else 0}")
    for order in (order_result or [])[:10]:  # Show first 10
        print(f"  Order {order['order_number']}: {order['count']} VINs")

    # 3. Duplicate VINs preserved (this is EXPECTED and CORRECT)
    duplicate_result = db.execute_query(f"""
        SELECT vin, COUNT(*) as order_count
        FROM {table_name}
        GROUP BY vin
        HAVING COUNT(*) > 1
        ORDER BY order_count DESC
        LIMIT 10
    """)

    if duplicate_result:
        print(f"\nDuplicate VINs found: {len(duplicate_result)} (this is correct!)")
        for dup in duplicate_result:
            print(f"  {dup['vin']}: {dup['order_count']} orders")
    else:
        print("No duplicate VINs found")

    # 4. Dealership name consistent
    dealership_result = db.execute_query(f"SELECT DISTINCT dealership FROM {table_name}")
    print(f"Dealership names: {[d['dealership'] for d in (dealership_result or [])]}")

    return success_count > 0

def main():
    """Main function"""
    success = import_bommarito_cadillac_vinlog()
    if success:
        print("\nSUCCESS: Bommarito Cadillac VIN log import completed")
        return 0
    else:
        print("\nERROR: VIN log import failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())