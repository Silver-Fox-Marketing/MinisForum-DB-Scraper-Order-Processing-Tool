#!/usr/bin/env python3
"""
FIX CRITICAL NAME MAPPING ISSUES
Adds missing mappings to correct_order_processing.py
"""

import os

def fix_name_mappings():
    """Add critical missing name mappings"""

    print("=== FIXING DEALERSHIP NAME MAPPINGS ===\n")

    # Path to correct_order_processing.py
    processing_file = r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts\correct_order_processing.py"

    # New mappings needed based on analysis
    new_mappings = {
        # Case mismatches
        'KIA of Columbia': 'Kia of Columbia',  # Config -> Scraper (case fix)
        'Mini of St. Louis': 'MINI OF ST. LOUIS',  # Config -> Scraper (case fix)

        # Name variations
        'Rusty Drewing Chevy BGMC': 'Rusty Drewing Chevrolet Buick GMC',  # Config -> Scraper
        'Weber Chevrolet': 'Weber Creve Coeur',  # Config -> Scraper

        # Missing configs that might exist under different names
        # 'Joe Machens CDJR': 'Joe Machens Chrysler Dodge Jeep Ram',  # If config exists

        # BMW mapping already exists but let's ensure consistency
        'BMW West St. Louis': 'BMW of West St Louis',  # Config -> Scraper (missing "of")
    }

    print("[STEP 1] Reading current file...")
    with open(processing_file, 'r') as f:
        lines = f.readlines()

    # Find the line with dealership_name_mapping
    mapping_start = -1
    mapping_end = -1

    for i, line in enumerate(lines):
        if 'self.dealership_name_mapping = {' in line:
            mapping_start = i
        if mapping_start > -1 and '}' in line and mapping_end == -1:
            mapping_end = i
            break

    if mapping_start == -1:
        print("[ERROR] Could not find dealership_name_mapping in file!")
        return False

    print(f"[STEP 2] Found mapping at lines {mapping_start}-{mapping_end}")

    # Build new mapping lines
    new_mapping_lines = []

    # Add existing mappings
    for i in range(mapping_start + 1, mapping_end):
        line = lines[i].strip()
        if line and not line.startswith('#'):
            new_mapping_lines.append(f"            {line}\n")

    # Add new mappings
    print("\n[STEP 3] Adding new mappings:")
    for config_name, scraper_name in new_mappings.items():
        mapping_line = f"'{config_name}': '{scraper_name}',"
        print(f"    {mapping_line}")
        new_mapping_lines.append(f"            {mapping_line}\n")

    # Sort all mappings alphabetically for consistency
    new_mapping_lines.sort()

    # Rebuild the file with new mappings
    new_lines = []
    new_lines.extend(lines[:mapping_start + 1])
    new_lines.extend(new_mapping_lines)
    new_lines.append(lines[mapping_end])
    new_lines.extend(lines[mapping_end + 1:])

    print("\n[STEP 4] Writing updated file...")
    with open(processing_file, 'w') as f:
        f.writelines(new_lines)

    print("[SUCCESS] Name mappings updated!")

    # Now let's also check if we need to handle Joe Machens CDJR
    print("\n[ADDITIONAL NOTES]:")
    print("1. 'Joe Machens Chrysler Dodge Jeep Ram' in scraper has NO config match")
    print("   - Consider adding 'Joe Machens CDJR' to dealership_configs table")
    print("   - OR it might be the same as 'Joe Machens CDJR' if that exists")

    print("\n2. 'Volvo Cars West County' in scraper has NO config match")
    print("   - This might be 'West County Volvo' or similar in configs")
    print("   - Need to verify if this dealership should be active")

    print("\n3. 'CDJR of Columbia' in config has NO scraper data in this CSV")
    print("   - This might be in a different scraper dataset")
    print("   - OR it might need a different name mapping")

    return True

if __name__ == "__main__":
    success = fix_name_mappings()

    if success:
        print("\n=== NEXT STEPS ===")
        print("1. Review the updated mappings in correct_order_processing.py")
        print("2. Test CAO processing for affected dealerships:")
        print("   - KIA of Columbia")
        print("   - Mini of St. Louis")
        print("   - Rusty Drewing Chevy BGMC")
        print("   - Weber Chevrolet")
        print("3. Resolve remaining unmapped dealerships")
    else:
        print("\n[ERROR] Failed to update mappings!")