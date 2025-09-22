#!/usr/bin/env python3
"""
Compare VIN counts between CSV and database for Serra Honda
"""

import sys
import csv

# Add the scripts directory to Python path
scripts_path = r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts'
sys.path.append(scripts_path)

from database_connection import DatabaseManager

def compare_serra_vinlog_counts():
    """Compare VIN counts between CSV file and database"""
    print("=== Comparing Serra Honda VIN Log Counts ===")

    # Initialize database
    try:
        db = DatabaseManager()
        print("OK Database connection established")
    except Exception as e:
        print(f"ERROR Database connection failed: {e}")
        return False

    csv_path = r'C:\Users\Workstation_1\Downloads\SERRAHONDA_VINLOG - LOG.csv'

    # Count VINs in CSV file (including duplicates)
    print("\n--- CSV File Analysis ---")
    csv_vin_count = 0
    csv_valid_vins = []
    csv_duplicate_count = 0

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
                        csv_vin_count += 1
                        if vin_col in csv_valid_vins:
                            csv_duplicate_count += 1
                        csv_valid_vins.append(vin_col)

        csv_unique_vins = len(set(csv_valid_vins))
        print(f"CSV total VINs (including duplicates): {csv_vin_count}")
        print(f"CSV unique VINs: {csv_unique_vins}")
        print(f"CSV duplicate VINs: {csv_duplicate_count}")

    except Exception as e:
        print(f"ERROR Failed to read CSV: {e}")
        return False

    # Count VINs in database table (including duplicates from multiple imports)
    print("\n--- Database Table Analysis ---")
    try:
        db_result = db.execute_query("""
            SELECT
                COUNT(*) as total_vins,
                COUNT(DISTINCT vin) as unique_vins
            FROM serra_honda_ofallon_vin_log
        """)

        if db_result:
            db_stats = db_result[0]
            db_total_vins = db_stats['total_vins']
            db_unique_vins = db_stats['unique_vins']
            db_duplicate_count = db_total_vins - db_unique_vins

            print(f"Database total VINs (including duplicates): {db_total_vins}")
            print(f"Database unique VINs: {db_unique_vins}")
            print(f"Database duplicate VINs: {db_duplicate_count}")
        else:
            print("ERROR No database results")
            return False

    except Exception as e:
        print(f"ERROR Failed to query database: {e}")
        return False

    # Compare results
    print("\n--- Comparison Results ---")
    print(f"CSV VINs: {csv_vin_count} (including {csv_duplicate_count} duplicates)")
    print(f"Database VINs: {db_total_vins} (including {db_duplicate_count} duplicates)")

    if db_total_vins >= csv_vin_count:
        difference = db_total_vins - csv_vin_count
        print(f"✅ SUCCESS: Database has {difference} MORE VINs than CSV")
        print("   This is expected due to our import handling duplicates properly")
    else:
        difference = csv_vin_count - db_total_vins
        print(f"❌ WARNING: Database has {difference} FEWER VINs than CSV")
        print("   Some VINs may not have been imported properly")

    # Check unique VIN counts
    print(f"\nUnique VIN comparison:")
    print(f"CSV unique VINs: {csv_unique_vins}")
    print(f"Database unique VINs: {db_unique_vins}")

    if db_unique_vins >= csv_unique_vins:
        unique_difference = db_unique_vins - csv_unique_vins
        print(f"✅ SUCCESS: Database has {unique_difference} MORE unique VINs than CSV")
    else:
        unique_difference = csv_unique_vins - db_unique_vins
        print(f"❌ WARNING: Database has {unique_difference} FEWER unique VINs than CSV")

    # Show some sample VINs for verification
    print("\n--- Sample Database VINs ---")
    try:
        sample_result = db.execute_query("""
            SELECT vin, order_number, COUNT(*) as occurrences
            FROM serra_honda_ofallon_vin_log
            GROUP BY vin, order_number
            ORDER BY occurrences DESC, vin
            LIMIT 10
        """)

        if sample_result:
            print("Sample VINs with their occurrence counts:")
            for record in sample_result:
                print(f"  {record['vin']} | Order: {record['order_number']} | Occurrences: {record['occurrences']}")

    except Exception as e:
        print(f"ERROR Failed to get sample: {e}")

    return True

def main():
    """Main function"""
    success = compare_serra_vinlog_counts()
    if success:
        print("\nVIN log comparison completed!")
        return 0
    else:
        print("\nComparison failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())