#!/usr/bin/env python3
"""
Import updated Auffenberg Hyundai VIN log CSV
- Clear existing VIN log data
- Import ALL VINs including BASELINE and non-numeric order groups
- Set order type to 'cao' and date to 9/11/2025
"""

import sys
import os
import csv
from datetime import datetime, date
sys.path.append(os.path.join(os.path.dirname(__file__), 'projects/minisforum_database_transfer/bulletproof_package/scripts'))

from database_connection import db_manager

def import_vinlog_csv():
    """Import the updated VIN log CSV with complete data"""

    csv_path = r"C:\Users\Workstation_1\Downloads\AUFFENBERG_HYUNDAI_VINLOG - LOG.csv"
    table_name = "auffenberg_hyundai_vin_log"
    dealership_name = "Auffenberg Hyundai"
    target_date = date(2025, 9, 11)  # 9/11/2025
    order_type = "cao"

    print(f"=== IMPORTING UPDATED AUFFENBERG HYUNDAI VIN LOG ===")
    print(f"CSV file: {csv_path}")
    print(f"Target table: {table_name}")
    print(f"Import date: {target_date}")
    print(f"Order type: {order_type}")

    # Step 1: Clear existing data
    print(f"\n[STEP 1] CLEARING EXISTING DATA...")

    # Get current count
    current_count = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
    print(f"    Current records: {current_count[0]['count']}")

    # Clear the table
    db_manager.execute_query(f"DELETE FROM {table_name}")
    print(f"    [OK] Cleared all existing records")

    # Step 2: Read and parse CSV
    print(f"\n[STEP 2] READING CSV FILE...")

    vin_data = []
    current_order = None

    with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row_num, row in enumerate(reader, start=2):  # Start at 2 because header is row 1
            order_value = row['ORDER'].strip()
            vin_value = row['VIN'].strip()

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
    for order, count in order_groups.items():
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
                order_type,   # order_type
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
            print(f"    [ERROR] {error_msg}")

    # Step 5: Verify import
    print(f"\n[STEP 5] VERIFICATION...")

    final_count = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
    print(f"    Records after import: {final_count[0]['count']}")
    print(f"    Successfully imported: {imported_count}")
    print(f"    Import errors: {len(errors)}")

    if errors:
        print(f"\n[ERRORS]:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"    {error}")
        if len(errors) > 5:
            print(f"    ... and {len(errors) - 5} more errors")

    # Show sample of imported data
    print(f"\n[STEP 6] SAMPLE IMPORTED DATA:")
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

    for group in final_groups:
        print(f"    Order '{group['order_number']}': {group['vin_count']} VINs")

    print(f"\n=== IMPORT COMPLETE ===")
    print(f"Summary:")
    print(f"  - Total VINs imported: {imported_count}")
    print(f"  - Order groups: {len(final_groups)}")
    print(f"  - Import date: {target_date}")
    print(f"  - Order type: {order_type}")
    print(f"  - Errors: {len(errors)}")

    return {
        'success': len(errors) == 0,
        'imported_count': imported_count,
        'total_groups': len(final_groups),
        'errors': errors
    }

if __name__ == "__main__":
    result = import_vinlog_csv()
    if result['success']:
        print(f"\n[SUCCESS] Import completed successfully!")
    else:
        print(f"\n[WARNING] Import completed with {len(result['errors'])} errors")