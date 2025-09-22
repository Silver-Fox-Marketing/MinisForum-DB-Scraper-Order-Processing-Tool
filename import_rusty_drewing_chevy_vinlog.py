#!/usr/bin/env python3
"""
Import Rusty Drewing Chevrolet VIN log CSV
- Import ALL VINs including BASELINE and other order types
- Set order_type='cao' and date=9/14/2025 for all entries
"""

import sys
import os
import csv
from datetime import datetime, date
sys.path.append(os.path.join(os.path.dirname(__file__), 'projects/minisforum_database_transfer/bulletproof_package/scripts'))

from database_connection import db_manager

def import_rusty_drewing_vinlog():
    """Import Rusty Drewing Chevrolet VIN log with complete data"""

    csv_path = r"C:\Users\Workstation_1\Downloads\RDCHEVY_VINLOG - LOG (1).csv"
    table_name = "rusty_drewing_chevy_bgmc_vin_log"  # Based on config name "Rusty Drewing Chevy BGMC"
    dealership_name = "Rusty Drewing Chevy BGMC"
    target_date = date(2025, 9, 14)  # 9/14/2025
    order_type = "cao"

    print(f"=== IMPORTING RUSTY DREWING CHEVROLET VIN LOG ===")
    print(f"CSV file: {csv_path}")
    print(f"Target table: {table_name}")
    print(f"Dealership: {dealership_name}")
    print(f"Import date: {target_date}")
    print(f"Order type: {order_type}")

    # Step 1: Clear existing data
    print(f"\n[STEP 1] CHECKING EXISTING DATA...")

    # Get current count
    current_count = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
    print(f"    Current records: {current_count[0]['count']}")

    if current_count[0]['count'] > 0:
        print(f"    Clearing existing records...")
        db_manager.execute_query(f"DELETE FROM {table_name}")
        print(f"    [OK] Cleared all existing records")

    # Step 2: Read and parse CSV
    print(f"\n[STEP 2] READING CSV FILE...")

    vin_data = []
    current_order = None

    with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row_num, row in enumerate(reader, start=2):  # Start at 2 because header is row 1
            # Check both possible column names
            order_value = ''
            vin_value = ''

            # Try different possible column names
            if 'ORDER#' in row:
                order_value = row['ORDER#'].strip()
            elif 'ORDER' in row:
                order_value = row['ORDER'].strip()
            elif 'Order' in row:
                order_value = row['Order'].strip()

            if 'VIN LOG' in row:
                vin_value = row['VIN LOG'].strip()
            elif 'VINS' in row:
                vin_value = row['VINS'].strip()
            elif 'VIN' in row:
                vin_value = row['VIN'].strip()
            elif 'Vins' in row:
                vin_value = row['Vins'].strip()

            # Update current order if a new order is specified
            if order_value:
                current_order = order_value
                print(f"    Found order group: '{current_order}'")

            # Process VIN if it exists
            if vin_value:
                if current_order is None:
                    print(f"    [WARNING] VIN '{vin_value}' at row {row_num} has no order group - assigning 'UNKNOWN'")
                    current_order = "UNKNOWN"

                vin_data.append({
                    'vin': vin_value,
                    'order_number': current_order,
                    'row_num': row_num
                })

    print(f"    [OK] Read {len(vin_data)} VINs from CSV")

    # Show order group summary
    order_groups = {}
    for vin_entry in vin_data:
        order = vin_entry['order_number']
        if order not in order_groups:
            order_groups[order] = 0
        order_groups[order] += 1

    print(f"\n[STEP 3] ORDER GROUP SUMMARY:")
    for order, count in sorted(order_groups.items()):
        print(f"    Order '{order}': {count} VINs")

    # Step 4: Import all VINs into database
    print(f"\n[STEP 4] IMPORTING VINs TO DATABASE...")

    imported_count = 0
    errors = []

    for vin_entry in vin_data:
        try:
            # Insert VIN into table with all required fields
            db_manager.execute_query(f"""
                INSERT INTO {table_name} (
                    vin,
                    order_number,
                    processed_date,
                    order_type,
                    order_date,
                    dealership,
                    created_at,
                    imported_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                vin_entry['vin'],
                vin_entry['order_number'],
                target_date,  # processed_date
                order_type,   # order_type = 'cao'
                target_date,  # order_date
                dealership_name,  # dealership
                datetime.now(),  # created_at
                datetime.now()   # imported_at
            ))

            imported_count += 1

            if imported_count % 50 == 0:
                print(f"    Imported {imported_count} VINs...")

        except Exception as e:
            error_msg = f"Failed to import VIN {vin_entry['vin']} (row {vin_entry['row_num']}): {e}"
            errors.append(error_msg)
            # Don't print duplicate errors to avoid clutter
            if 'duplicate key' not in str(e):
                print(f"    [ERROR] {error_msg}")

    # Step 5: Verify import
    print(f"\n[STEP 5] VERIFICATION...")

    final_count = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
    print(f"    Records after import: {final_count[0]['count']}")
    print(f"    Successfully imported: {imported_count}")

    if errors:
        duplicate_count = len([e for e in errors if 'duplicate key' in e])
        other_errors = len(errors) - duplicate_count
        print(f"    Duplicate VINs skipped: {duplicate_count}")
        if other_errors > 0:
            print(f"    Other errors: {other_errors}")

    # Show sample of imported data
    print(f"\n[STEP 6] SAMPLE IMPORTED DATA (first 10):")
    sample_data = db_manager.execute_query(f"""
        SELECT vin, order_number, processed_date, order_type, dealership
        FROM {table_name}
        ORDER BY order_number, vin
        LIMIT 10
    """)

    for sample in sample_data:
        print(f"    {sample['vin']} | Order: {sample['order_number']} | Type: {sample['order_type']} | Date: {sample['processed_date']}")

    # Final order group verification
    print(f"\n[STEP 7] FINAL ORDER GROUP VERIFICATION:")
    final_groups = db_manager.execute_query(f"""
        SELECT order_number, COUNT(*) as vin_count
        FROM {table_name}
        GROUP BY order_number
        ORDER BY order_number
    """)

    total_orders = 0
    baseline_count = 0
    numeric_orders = 0

    for group in final_groups:
        order_num = group['order_number']
        count = group['vin_count']

        if 'BASELINE' in order_num.upper():
            baseline_count = count
            print(f"    Order '{order_num}': {count} VINs [BASELINE IMPORTED]")
        elif order_num.isdigit():
            numeric_orders += 1
            print(f"    Order '{order_num}': {count} VINs")
        else:
            print(f"    Order '{order_num}': {count} VINs [SPECIAL]")

        total_orders += 1

    print(f"\n=== IMPORT COMPLETE ===")
    print(f"Summary for Rusty Drewing Chevrolet:")
    print(f"  - Total VINs imported: {imported_count}")
    print(f"  - Order groups: {total_orders}")
    if baseline_count > 0:
        print(f"  - BASELINE VINs included: {baseline_count}")
    print(f"  - Numeric orders: {numeric_orders}")
    print(f"  - Import date: {target_date}")
    print(f"  - Order type: {order_type} (for all VINs)")
    print(f"  - Errors: {len(errors)}")

    return {
        'success': len(errors) == 0 or all('duplicate key' in str(e) for e in errors),
        'imported_count': imported_count,
        'total_groups': total_orders,
        'errors': errors
    }

if __name__ == "__main__":
    result = import_rusty_drewing_vinlog()
    if result['success']:
        print(f"\n[SUCCESS] Import completed successfully!")
    else:
        print(f"\n[WARNING] Import completed with {len(result['errors'])} errors")