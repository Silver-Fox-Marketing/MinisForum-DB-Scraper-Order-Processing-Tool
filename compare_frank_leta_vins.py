#!/usr/bin/env python3
"""
Compare Frank Leta Honda VINs - check if expected 24 VINs are in the 38 received,
and identify the 14 extra VINs to check against current system VIN log
"""

import sys
import csv

# Add the scripts directory to Python path
scripts_path = r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts'
sys.path.append(scripts_path)

from database_connection import DatabaseManager

def compare_frank_leta_vins():
    """Compare Frank Leta Honda VINs"""
    print("=== Comparing Frank Leta Honda VINs ===")

    # Expected 24 VINs from user
    expected_vins = {
        "5FNRL5H93DB081775",
        "19XFC2F57JE017774",
        "19XFC1F34GE012131",
        "2HGFC2F50JH561023",
        "5J6RM4H95GL113838",
        "7FARW2H85ME007324",
        "7FARW2H85NE045234",
        "5FPYK3F53PB017671",
        "7FARS6H90SE079329",
        "5FNYF6H22NB064866",
        "1HGCV1F40NA092485",
        "1HGCR2F70GA223292",
        "1HGCM56313A070056",
        "JM1BM1U75E1121683",
        "KNALN4D79F5168824",
        "5FRYD4H41GB056657",
        "3C4NJDAN7RT140552",
        "3KPF44AC2RE821328",
        "4T1G11AK3RU891520",
        "3GNKBJR41RS168581",
        "JM3KFBDMXR0388407",
        "JTHBZ1B13K2000378",
        "W1KZF5KB8NB007250",
        "1GT49RE72MF263479"
    }

    # Extract VINs from the CSV file we received
    csv_file = r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\orders\Frank_Leta_Honda\20250917_155322\FRANKLETAHONDA_09-17 - BILLING.csv"

    received_vins = set()
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            # Skip first line (headers)
            next(f)
            for line in f:
                if line.strip() and ',' in line:
                    # Extract VIN from the line (format: "description - VIN")
                    parts = line.split(' - ')
                    if len(parts) >= 2:
                        vin_part = parts[-1].split(',')[0].strip()
                        if len(vin_part) == 17:  # VIN length check
                            received_vins.add(vin_part)
    except Exception as e:
        print(f"ERROR reading CSV: {e}")
        return False

    print(f"Expected VINs: {len(expected_vins)}")
    print(f"Received VINs: {len(received_vins)}")

    # Check if all expected VINs are in received VINs
    print("\n--- Expected VINs Check ---")
    missing_expected = expected_vins - received_vins
    if missing_expected:
        print(f"[PROBLEM] Missing expected VINs ({len(missing_expected)}):")
        for vin in sorted(missing_expected):
            print(f"  {vin}")
    else:
        print("[OK] All 24 expected VINs are present in the 38 received")

    # Identify extra VINs
    extra_vins = received_vins - expected_vins
    print(f"\n--- Extra VINs ({len(extra_vins)}) ---")
    for vin in sorted(extra_vins):
        print(f"  {vin}")

    # Check if extra VINs are in our current VIN log
    print(f"\n--- Checking Extra VINs Against VIN Log ---")
    try:
        db = DatabaseManager()
        print("OK Database connection established")

        for vin in sorted(extra_vins):
            result = db.execute_query(
                "SELECT vin, order_number, order_date FROM frank_leta_honda_vin_log WHERE vin = %s",
                [vin]
            )

            if result:
                log_entry = result[0]
                print(f"[IN LOG] {vin} - Order: {log_entry['order_number']} - Date: {log_entry['order_date']}")
            else:
                print(f"[NOT IN LOG] {vin} - This VIN should be new")

        return True

    except Exception as e:
        print(f"ERROR checking VIN log: {e}")
        return False

def main():
    """Main function"""
    success = compare_frank_leta_vins()
    if success:
        print("\nVIN comparison completed")
        return 0
    else:
        print("\nVIN comparison failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())