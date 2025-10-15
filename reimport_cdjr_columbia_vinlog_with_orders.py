"""
Re-import CDJR of Columbia VIN log with proper order number grouping
"""
import sys
import csv
from datetime import datetime
sys.path.insert(0, r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts')

from database_connection import db_manager

# Configuration
CSV_FILE = r"C:\Users\Workstation_1\Downloads\CDJR_Columbia_Vin_Log.csv"
TABLE_NAME = "cdjr_of_columbia_vin_log"
IMPORT_DATE = '2025-10-02'
ORDER_TYPE = 'manual'

def parse_order_groups():
    """Parse CSV into order groups"""

    order_groups = []
    current_order = None
    current_vins = []

    with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):
            order_num = row.get('ORDER #', '').strip()
            vin = row.get('VIN', '').strip()

            # Check if this is a blank row (end of order group)
            if not order_num and not vin:
                if current_order and current_vins:
                    order_groups.append({
                        'order_number': current_order,
                        'vins': current_vins.copy()
                    })
                    print(f"[GROUP] Order {current_order}: {len(current_vins)} VINs")
                current_order = None
                current_vins = []
                continue

            # New order number starts new group
            if order_num:
                # Save previous group if exists
                if current_order and current_vins:
                    order_groups.append({
                        'order_number': current_order,
                        'vins': current_vins.copy()
                    })
                    print(f"[GROUP] Order {current_order}: {len(current_vins)} VINs")

                current_order = order_num
                current_vins = []

                # First VIN is in same row as order number
                if vin:
                    current_vins.append(vin)
            else:
                # VIN belongs to current order
                if vin and current_order:
                    current_vins.append(vin)

        # Don't forget last group
        if current_order and current_vins:
            order_groups.append({
                'order_number': current_order,
                'vins': current_vins.copy()
            })
            print(f"[GROUP] Order {current_order}: {len(current_vins)} VINs")

    return order_groups

def reimport_vinlog():
    """Delete previous import and re-import with order numbers"""

    print(f"\n{'='*80}")
    print(f"CDJR of Columbia VIN Log Re-Import with Order Numbers")
    print(f"{'='*80}\n")

    # Parse order groups
    print("[PARSE] Reading CSV and grouping by order number...")
    order_groups = parse_order_groups()

    total_vins = sum(len(g['vins']) for g in order_groups)

    print(f"\n[INFO] Parsed {len(order_groups)} order groups")
    print(f"[INFO] Total VINs: {total_vins}")

    # Show sample
    print(f"\n[SAMPLE] First 5 order groups:")
    for group in order_groups[:5]:
        print(f"  Order {group['order_number']}: {len(group['vins'])} VINs")
        for vin in group['vins'][:3]:
            print(f"    - {vin}")
        if len(group['vins']) > 3:
            print(f"    ... and {len(group['vins']) - 3} more")

    # Delete previous import
    print(f"\n[DELETE] Removing previous import from {IMPORT_DATE}...")
    delete_query = f"DELETE FROM {TABLE_NAME} WHERE created_at = %s"
    deleted = db_manager.execute_non_query(delete_query, (IMPORT_DATE,))
    print(f"[DELETE] Removed {deleted} previous records")

    # Confirm import
    response = input(f"\n[CONFIRM] Import {total_vins} VINs across {len(order_groups)} orders? (yes/no): ")
    if response.lower() != 'yes':
        print("[CANCELLED] Import cancelled by user")
        return

    # Import with order numbers
    print(f"\n[IMPORT] Starting import with order numbers...")

    insert_query = f"""
        INSERT INTO {TABLE_NAME} (vin, order_number, order_type, created_at)
        VALUES (%s, %s, %s, %s)
    """

    imported = 0
    errors = 0

    for group in order_groups:
        order_num = group['order_number']
        vins = group['vins']

        for vin in vins:
            try:
                db_manager.execute_non_query(
                    insert_query,
                    (vin, order_num, ORDER_TYPE, IMPORT_DATE)
                )
                imported += 1
                if imported % 100 == 0:
                    print(f"[PROGRESS] Imported {imported}/{total_vins} VINs...")
            except Exception as e:
                errors += 1
                print(f"[ERROR] Failed to import {vin} for order {order_num}: {e}")

    print(f"\n{'='*80}")
    print(f"[SUCCESS] Import Complete!")
    print(f"{'='*80}")
    print(f"Total VINs processed: {total_vins}")
    print(f"Successfully imported: {imported}")
    print(f"Errors: {errors}")
    print(f"Order groups: {len(order_groups)}")
    print(f"Import date: {IMPORT_DATE}")

    # Verify import
    count_query = f"SELECT COUNT(*) as total FROM {TABLE_NAME} WHERE created_at = %s"
    result = db_manager.execute_query(count_query, (IMPORT_DATE,), fetch='one')

    if result:
        print(f"\n[VERIFY] Total records with date {IMPORT_DATE}: {result['total']}")

    # Show sample with order numbers
    sample_query = f"""
        SELECT vin, order_number
        FROM {TABLE_NAME}
        WHERE created_at = %s
        LIMIT 10
    """
    samples = db_manager.execute_query(sample_query, (IMPORT_DATE,))

    if samples:
        print(f"\n[SAMPLE] Imported records with order numbers:")
        for s in samples:
            print(f"  Order {s['order_number']}: {s['vin']}")

if __name__ == "__main__":
    reimport_vinlog()
