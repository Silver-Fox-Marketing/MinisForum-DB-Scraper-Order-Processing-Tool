"""
Import CDJR of Columbia VIN log from CSV
All VINs imported with date 10/2/25 and order_type 'manual'
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

def import_vinlog():
    """Import all VINs from CSV including duplicates"""

    print(f"\n{'='*80}")
    print(f"CDJR of Columbia VIN Log Import")
    print(f"{'='*80}\n")

    # Read CSV file
    vins_to_import = []
    with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):  # Start at 2 because of header
            vin = row.get('VIN', '').strip()

            # Skip empty VINs
            if not vin:
                print(f"[SKIP] Row {row_num}: Empty VIN")
                continue

            vins_to_import.append(vin)
            print(f"[QUEUE] Row {row_num}: {vin}")

    print(f"\n[INFO] Total VINs to import: {len(vins_to_import)}")
    print(f"[INFO] Unique VINs: {len(set(vins_to_import))}")
    print(f"[INFO] Duplicates: {len(vins_to_import) - len(set(vins_to_import))}")

    # Check for duplicates already in database
    check_query = f"""
        SELECT vin, COUNT(*) as count
        FROM {TABLE_NAME}
        WHERE vin = ANY(%s)
        GROUP BY vin
    """

    existing = db_manager.execute_query(check_query, (vins_to_import,))

    if existing:
        print(f"\n[WARNING] Found {len(existing)} VINs already in database:")
        for row in existing[:10]:  # Show first 10
            print(f"  - {row['vin']}: {row['count']} existing records")
        if len(existing) > 10:
            print(f"  ... and {len(existing) - 10} more")

    # Confirm import
    response = input(f"\n[CONFIRM] Import {len(vins_to_import)} VINs to {TABLE_NAME}? (yes/no): ")
    if response.lower() != 'yes':
        print("[CANCELLED] Import cancelled by user")
        return

    # Import VINs
    print(f"\n[IMPORT] Starting import...")

    insert_query = f"""
        INSERT INTO {TABLE_NAME} (vin, order_type, created_at)
        VALUES (%s, %s, %s)
    """

    imported = 0
    errors = 0

    for vin in vins_to_import:
        try:
            db_manager.execute_non_query(
                insert_query,
                (vin, ORDER_TYPE, IMPORT_DATE)
            )
            imported += 1
            if imported % 50 == 0:
                print(f"[PROGRESS] Imported {imported}/{len(vins_to_import)} VINs...")
        except Exception as e:
            errors += 1
            print(f"[ERROR] Failed to import {vin}: {e}")

    print(f"\n{'='*80}")
    print(f"[SUCCESS] Import Complete!")
    print(f"{'='*80}")
    print(f"Total VINs processed: {len(vins_to_import)}")
    print(f"Successfully imported: {imported}")
    print(f"Errors: {errors}")
    print(f"Import date: {IMPORT_DATE}")
    print(f"Order type: {ORDER_TYPE}")

    # Verify import
    count_query = f"SELECT COUNT(*) as total FROM {TABLE_NAME} WHERE created_at = %s"
    result = db_manager.execute_query(count_query, (IMPORT_DATE,), fetch='one')

    if result:
        print(f"\n[VERIFY] Total records in {TABLE_NAME} with date {IMPORT_DATE}: {result['total']}")

if __name__ == "__main__":
    import_vinlog()
