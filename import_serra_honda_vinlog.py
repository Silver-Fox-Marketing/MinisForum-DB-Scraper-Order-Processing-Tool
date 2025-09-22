#!/usr/bin/env python3
"""
Import Serra Honda VIN Log from CSV
Clear existing VIN log and import updated CSV with proper order number grouping
"""

import sys
import csv
import re
from datetime import datetime

# Add the scripts directory to Python path
scripts_path = r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts'
sys.path.append(scripts_path)

from database_connection import DatabaseManager

def import_serra_honda_vinlog():
    """Import Serra Honda VIN log from CSV with proper order grouping"""
    print("=== Importing Serra Honda VIN Log ===")

    # Initialize database
    try:
        db = DatabaseManager()
        print("OK Database connection established")
    except Exception as e:
        print(f"ERROR Database connection failed: {e}")
        return False

    csv_path = r'C:\Users\Workstation_1\Downloads\SERRAHONDA_VINLOG - LOG.csv'

    # Clear existing Serra Honda VIN log
    print("\n--- Clearing Current Serra Honda VIN Log ---")
    try:
        clear_query = "DELETE FROM serra_honda_ofallon_vin_log"
        db.execute_query(clear_query)
        print("OK Cleared existing Serra Honda VIN log")
    except Exception as e:
        print(f"ERROR Failed to clear VIN log: {e}")
        return False

    # Read and process CSV
    print("\n--- Processing CSV File ---")
    print(f"CSV Path: {csv_path}")

    processed_vins = []
    current_order_number = "Missing Order Number"
    line_count = 0

    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)

            for row in csv_reader:
                line_count += 1

                # Skip header
                if line_count == 1:
                    continue

                # Skip empty rows (order group separators)
                if not row or (len(row) == 2 and not row[0] and not row[1]):
                    continue

                if len(row) >= 2:
                    order_col = row[0].strip()
                    vin_col = row[1].strip()

                    # Check if this is an order number line (has order number in first column)
                    if order_col and vin_col:
                        # This line has both order number and VIN
                        current_order_number = order_col
                        if len(vin_col) == 17:  # Valid VIN length
                            processed_vins.append({
                                'vin': vin_col,
                                'order_number': current_order_number,
                                'order_type': 'Historical',
                                'order_date': '2025-09-15'
                            })
                            print(f"  VIN: {vin_col} -> Order: {current_order_number}")

                    elif not order_col and vin_col:
                        # This is a VIN-only line, use current order number
                        if len(vin_col) == 17:  # Valid VIN length
                            processed_vins.append({
                                'vin': vin_col,
                                'order_number': current_order_number,
                                'order_type': 'Historical',
                                'order_date': '2025-09-15'
                            })
                            print(f"  VIN: {vin_col} -> Order: {current_order_number}")

        print(f"\nProcessed {len(processed_vins)} VINs from {line_count} lines")

    except Exception as e:
        print(f"ERROR Failed to read CSV: {e}")
        return False

    # Insert VINs into database
    print("\n--- Inserting VINs into Database ---")
    try:
        insert_query = """
            INSERT INTO serra_honda_ofallon_vin_log (vin, order_number, order_type, order_date, created_at)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (vin) DO UPDATE SET
                order_number = EXCLUDED.order_number,
                order_type = EXCLUDED.order_type,
                order_date = EXCLUDED.order_date,
                created_at = CURRENT_TIMESTAMP
        """

        for vin_data in processed_vins:
            db.execute_query(insert_query, [
                vin_data['vin'],
                vin_data['order_number'],
                vin_data['order_type'],
                vin_data['order_date']
            ])

        print(f"OK Inserted {len(processed_vins)} VINs into serra_honda_ofallon_vin_log")

        # Verify the import
        verify_result = db.execute_query("""
            SELECT COUNT(*) as total_vins,
                   COUNT(DISTINCT order_number) as unique_orders
            FROM serra_honda_ofallon_vin_log
        """)

        if verify_result:
            stats = verify_result[0]
            print(f"\nVerification:")
            print(f"  Total VINs: {stats['total_vins']}")
            print(f"  Unique Orders: {stats['unique_orders']}")

        # Show sample of imported data
        sample_result = db.execute_query("""
            SELECT vin, order_number, order_type, order_date, created_at
            FROM serra_honda_ofallon_vin_log
            ORDER BY created_at DESC
            LIMIT 10
        """)

        if sample_result:
            print(f"\nSample of imported data:")
            for record in sample_result:
                print(f"  {record['vin']} | {record['order_number']} | {record['order_type']} | {record['order_date']}")

        return True

    except Exception as e:
        print(f"ERROR Failed to insert VINs: {e}")
        return False

def main():
    """Main function"""
    success = import_serra_honda_vinlog()
    if success:
        print("\nSerra Honda VIN log import completed successfully!")
        print("All historical VINs have been imported with order groupings.")
        print("Serra Honda CAO processing should now show significantly fewer VINs.")
        return 0
    else:
        print("\nVIN log import failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())