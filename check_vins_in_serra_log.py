#!/usr/bin/env python3
"""
Check if Frank Leta Honda's 14 extra VINs are in the Serra Honda VIN log CSV
"""

import csv

def check_vins_in_serra_log():
    """Check if Frank Leta extra VINs are in Serra Honda VIN log"""
    print("=== Checking Frank Leta Extra VINs in Serra Honda VIN Log ===")

    # The 14 extra VINs from Frank Leta Honda
    frank_leta_extra_vins = {
        "19UDE4H26PA010912",
        "19XFL2H86SE023154",
        "1C4RJFBG8KC533216",
        "1C4RJFLT3MC589840",
        "1C4RJHAG3PC593232",
        "1HGCR2F86DA205951",
        "2C4RC1GG7JR274102",
        "2GNAXJEV7J6261474",
        "2HGFC2E82LH600497",
        "2T3RFREV9DW096579",
        "5FNYF6H28NB096169",
        "5NMJBCAE5NH065704",
        "JTJBM7FX5G5123703",
        "KNDNB4H33R6424112"
    }

    # Read Serra Honda VIN log CSV
    serra_csv_path = r"C:\Users\Workstation_1\Downloads\SERRAHONDA_VINLOG - LOG.csv"
    serra_vins = set()

    try:
        with open(serra_csv_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            for row in csv_reader:
                # VIN should be in the second column (index 1)
                if len(row) > 1 and row[1].strip():
                    vin = row[1].strip()
                    if len(vin) == 17:  # Valid VIN length
                        serra_vins.add(vin)

        print(f"Serra Honda VINs in CSV: {len(serra_vins)}")
        print(f"Frank Leta extra VINs to check: {len(frank_leta_extra_vins)}")

        # Check for matches
        matches = frank_leta_extra_vins.intersection(serra_vins)

        print(f"\n--- Results ---")
        if matches:
            print(f"[FOUND] {len(matches)} Frank Leta VINs found in Serra Honda log:")
            for vin in sorted(matches):
                print(f"  {vin}")
        else:
            print("[OK] None of the 14 Frank Leta extra VINs are in Serra Honda VIN log")

        print(f"\n--- All Frank Leta Extra VINs Status ---")
        for vin in sorted(frank_leta_extra_vins):
            status = "FOUND IN SERRA" if vin in serra_vins else "NOT IN SERRA"
            print(f"  {vin}: {status}")

        return True

    except Exception as e:
        print(f"ERROR reading Serra Honda CSV: {e}")
        return False

def main():
    """Main function"""
    success = check_vins_in_serra_log()
    if success:
        print("\nVIN cross-check completed")
        return 0
    else:
        print("\nVIN cross-check failed")
        return 1

if __name__ == "__main__":
    exit(main())