#!/usr/bin/env python3
"""
Verify all unique VINs from CSV are in the database
"""

import sys
import csv

# Add the scripts directory to Python path
scripts_path = r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts'
sys.path.append(scripts_path)

from database_connection import DatabaseManager

def verify_all_csv_vins_imported():
    """Verify all unique VINs from CSV are in the database"""
    print("=== Verifying All CSV VINs Are Imported ===")

    # Initialize database
    try:
        db = DatabaseManager()
        print("OK Database connection established")
    except Exception as e:
        print(f"ERROR Database connection failed: {e}")
        return False

    csv_path = r'C:\Users\Workstation_1\Downloads\SERRAHONDA_VINLOG - LOG.csv'

    # Get all unique VINs from CSV
    print("\n--- Reading CSV VINs ---")
    csv_vins = set()

    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            line_count = 0

            for row in csv_reader:
                line_count += 1

                # Skip header
                if line_count == 1:
                    continue

                # Skip empty rows
                if not row or (len(row) == 2 and not row[0] and not row[1]):
                    continue

                if len(row) >= 2:
                    vin_col = row[1].strip()

                    # Check if this is a valid VIN (17 characters)
                    if len(vin_col) == 17:
                        csv_vins.add(vin_col)

        print(f"Total unique VINs in CSV: {len(csv_vins)}")

    except Exception as e:
        print(f"ERROR Failed to read CSV: {e}")
        return False

    # Get all unique VINs from database
    print("\n--- Reading Database VINs ---")
    try:
        db_result = db.execute_query("""
            SELECT DISTINCT vin
            FROM serra_honda_ofallon_vin_log
        """)

        if db_result:
            db_vins = set(record['vin'] for record in db_result)
            print(f"Total unique VINs in database: {len(db_vins)}")
        else:
            print("ERROR No database results")
            return False

    except Exception as e:
        print(f"ERROR Failed to query database: {e}")
        return False

    # Compare VIN sets
    print("\n--- Comparison Analysis ---")

    # VINs in CSV but not in database
    missing_from_db = csv_vins - db_vins

    # VINs in database but not in CSV
    extra_in_db = db_vins - csv_vins

    # VINs in both
    in_both = csv_vins & db_vins

    print(f"VINs in both CSV and database: {len(in_both)}")
    print(f"VINs in CSV but NOT in database: {len(missing_from_db)}")
    print(f"VINs in database but NOT in CSV: {len(extra_in_db)}")

    # Show results
    print("\n--- Verification Results ---")
    if len(missing_from_db) == 0:
        print("[SUCCESS] All unique VINs from CSV are in the database!")
        print(f"Database has {len(extra_in_db)} additional VINs (likely from your recent order entry)")
    else:
        print(f"[WARNING] {len(missing_from_db)} VINs from CSV are missing from database:")
        for i, vin in enumerate(list(missing_from_db)[:10], 1):
            print(f"  {i}. {vin}")
        if len(missing_from_db) > 10:
            print(f"  ... and {len(missing_from_db) - 10} more")

    if len(extra_in_db) > 0:
        print(f"\n[INFO] Database has {len(extra_in_db)} VINs not in CSV:")
        print("  (These are likely from the order you entered manually)")
        for i, vin in enumerate(list(extra_in_db)[:10], 1):
            print(f"  {i}. {vin}")
        if len(extra_in_db) > 10:
            print(f"  ... and {len(extra_in_db) - 10} more")

    # Final summary
    print("\n--- Final Summary ---")
    print(f"CSV unique VINs: {len(csv_vins)}")
    print(f"Database unique VINs: {len(db_vins)}")
    print(f"Common VINs: {len(in_both)}")

    if len(missing_from_db) == 0:
        print("\n[CONFIRMED] All CSV VINs successfully imported to database!")
    else:
        print(f"\n[ACTION NEEDED] {len(missing_from_db)} VINs need to be imported")

    return True

def main():
    """Main function"""
    success = verify_all_csv_vins_imported()
    if success:
        print("\nVerification completed!")
        return 0
    else:
        print("\nVerification failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())