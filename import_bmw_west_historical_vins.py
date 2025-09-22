#!/usr/bin/env python3
"""
BMW West St. Louis Historical VIN Import Script

This script imports VIN data from a CSV file with ORDER,VINS format into the
bmw_west_st_louis_vin_log table. All VINs are imported including duplicates
with order_date set to 9/17 and order_type set to "Historical".
"""

import sys
import csv
import os
from datetime import datetime, date
from typing import List, Dict, Tuple

# Add the scripts directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(script_dir, 'projects', 'minisforum_database_transfer', 'bulletproof_package', 'scripts')
sys.path.append(scripts_dir)

from database_connection import db_manager

def parse_csv_file(csv_path: str) -> List[Tuple[str, str]]:
    """
    Parse the BMW West VIN log CSV file and return list of (order_number, vin) tuples.

    Args:
        csv_path: Path to the CSV file

    Returns:
        List of (order_number, vin) tuples
    """
    vin_data = []
    current_order = None

    print(f"[INFO] Reading CSV file: {csv_path}")

    with open(csv_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)

        # Skip header row
        next(csv_reader)

        for row_num, row in enumerate(csv_reader, start=2):
            if len(row) < 2:
                continue

            order_col = row[0].strip()
            vin_col = row[1].strip()

            # Check if this is a new order (non-empty order column)
            if order_col:
                current_order = order_col
                print(f"[INFO] Found order: {current_order}")

            # If we have a VIN and a current order, add it
            if vin_col and current_order:
                vin_data.append((current_order, vin_col))

            # Check for end of order group (empty row)
            elif not order_col and not vin_col:
                print(f"[INFO] End of order group for: {current_order}")
                # Don't reset current_order here, it will be set by next order

    print(f"[INFO] Parsed {len(vin_data)} VIN records from {csv_path}")
    return vin_data

def import_vins_to_database(vin_data: List[Tuple[str, str]]) -> bool:
    """
    Import VIN data into the bmw_west_st_louis_vin_log table.

    Args:
        vin_data: List of (order_number, vin) tuples

    Returns:
        True if successful, False otherwise
    """
    try:
        # Prepare data for insertion
        processed_date = datetime.now().strftime('%Y-%m-%d')  # Today's date as string
        order_date = date(2025, 9, 17)  # September 17, 2025
        order_type = "Historical"
        dealership = "BMW West St. Louis"
        created_at = datetime.now()

        print(f"[INFO] Preparing to import {len(vin_data)} VINs into database")
        print(f"[INFO] Order date: {order_date}")
        print(f"[INFO] Order type: {order_type}")
        print(f"[INFO] Processed date: {processed_date}")

        # Prepare insert data as tuples (matching exact table structure)
        columns = ['vin', 'dealership', 'order_date', 'processed_date', 'order_type', 'order_number', 'created_at']
        insert_data = []

        for order_number, vin in vin_data:
            insert_data.append((
                vin,
                dealership,
                order_date,
                processed_date,
                order_type,
                order_number,
                created_at
            ))

        # Insert into database using batch insert
        print(f"[INFO] Inserting {len(insert_data)} records into bmw_west_st_louis_vin_log table...")

        rows_inserted = db_manager.execute_batch_insert('bmw_west_st_louis_vin_log', columns, insert_data)
        print(f"[INFO] Batch insert completed: {rows_inserted} rows inserted")

        print(f"[SUCCESS] Successfully imported {len(insert_data)} VIN records!")

        # Verify the import
        count_result = db_manager.execute_query("""
            SELECT COUNT(*) as count FROM bmw_west_st_louis_vin_log
            WHERE order_type = 'Historical' AND order_date = %s
        """, (order_date,))

        if count_result:
            total_count = count_result[0]['count']
            print(f"[VERIFICATION] Total historical VINs in database: {total_count}")

        return True

    except Exception as e:
        print(f"[ERROR] Database import failed: {e}")
        return False

def main():
    """Main execution function"""
    csv_file_path = r"C:\Users\Workstation_1\Downloads\BMW_WEST_STL_VINLOG - LOG (2).csv"

    print("="*70)
    print("BMW West St. Louis Historical VIN Import Script")
    print("="*70)

    # Check if CSV file exists
    if not os.path.exists(csv_file_path):
        print(f"[ERROR] CSV file not found: {csv_file_path}")
        return False

    try:
        # Parse CSV file
        print(f"[STEP 1] Parsing CSV file...")
        vin_data = parse_csv_file(csv_file_path)

        if not vin_data:
            print("[ERROR] No VIN data found in CSV file")
            return False

        # Show summary
        print(f"\n[SUMMARY] Parsed data:")
        orders = set(order for order, vin in vin_data)
        print(f"  - Total VINs: {len(vin_data)}")
        print(f"  - Total Orders: {len(orders)}")
        print(f"  - Orders: {sorted(orders)}")

        # Confirmation (auto-proceed for automated execution)
        print(f"\n[CONFIRMATION] About to import {len(vin_data)} VINs into database")
        print(f"  - Order Date: September 17, 2025")
        print(f"  - Order Type: Historical")
        print(f"  - Target Table: bmw_west_st_louis_vin_log")
        print(f"  - Include Duplicates: YES")
        print(f"\n[AUTO-PROCEEDING] Proceeding with import...")

        # Import to database
        print(f"\n[STEP 2] Importing to database...")
        success = import_vins_to_database(vin_data)

        if success:
            print(f"\n[COMPLETE] Import completed successfully!")
            print(f"  - Imported: {len(vin_data)} VIN records")
            print(f"  - Status: ALL DUPLICATES INCLUDED")
            return True
        else:
            print(f"\n[FAILED] Import failed!")
            return False

    except Exception as e:
        print(f"[ERROR] Script execution failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)