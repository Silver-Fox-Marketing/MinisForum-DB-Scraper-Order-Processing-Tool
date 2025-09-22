#!/usr/bin/env python3
"""
CRITICAL: Comprehensive dealership name mapping analysis
Ensures perfect name consistency across all system components
"""

import sys
import os
import csv
sys.path.append(os.path.join(os.path.dirname(__file__), 'projects/minisforum_database_transfer/bulletproof_package/scripts'))

from database_connection import db_manager
import json

def analyze_name_mappings():
    """Comprehensive analysis of dealership name mappings across all components"""

    print("=== COMPREHENSIVE DEALERSHIP NAME MAPPING ANALYSIS ===\n")

    # Step 1: Get all unique dealership names from raw scraper CSV
    print("[STEP 1] EXTRACTING DEALERSHIP NAMES FROM RAW SCRAPER CSV...")
    csv_path = r"C:\Users\Workstation_1\Downloads\complete_data - 9.8.csv"

    scraper_dealerships = set()
    row_count = 0

    with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            row_count += 1
            location = row.get('Location', '').strip()
            if location:
                scraper_dealerships.add(location)

    scraper_dealerships = sorted(list(scraper_dealerships))
    print(f"    Found {len(scraper_dealerships)} unique dealerships in {row_count} rows")
    print("\n    SCRAPER CSV DEALERSHIP NAMES:")
    for i, name in enumerate(scraper_dealerships, 1):
        print(f"    {i:2}. '{name}'")

    # Step 2: Get all dealership names from dealership_configs table
    print("\n[STEP 2] GETTING DEALERSHIP NAMES FROM CONFIGS TABLE...")

    config_results = db_manager.execute_query("""
        SELECT name, is_active
        FROM dealership_configs
        ORDER BY name
    """)

    config_dealerships = []
    for config in config_results:
        config_dealerships.append({
            'name': config['name'],
            'active': config['is_active']
        })

    print(f"    Found {len(config_dealerships)} dealerships in config table")
    print("\n    CONFIG TABLE DEALERSHIP NAMES:")
    for i, dealer in enumerate(config_dealerships, 1):
        status = "ACTIVE" if dealer['active'] else "INACTIVE"
        print(f"    {i:2}. '{dealer['name']}' [{status}]")

    # Step 3: Get the name mapping from correct_order_processing.py
    print("\n[STEP 3] NAME MAPPINGS FROM correct_order_processing.py:")

    # Hardcoded from the actual file - these are the current mappings
    code_name_mapping = {
        'Dave Sinclair Lincoln South': 'Dave Sinclair Lincoln',
        'BMW of West St. Louis': 'BMW of West St Louis',
        'Columbia Honda': 'Columbia Honda',
        'South County DCJR': 'South County Dodge Chrysler Jeep RAM',
        'Glendale CDJR': 'Glendale Chrysler Jeep Dodge Ram',
        'HW Kia': 'HW Kia of West County'
    }

    print("    Current hardcoded mappings (Config -> Scraper):")
    for config_name, scraper_name in code_name_mapping.items():
        print(f"    '{config_name}' -> '{scraper_name}'")

    # Step 4: Compare and find mismatches
    print("\n[STEP 4] CRITICAL COMPARISON ANALYSIS:")
    print("=" * 60)

    # Find scraper names that don't have a config
    print("\n    A. SCRAPER NAMES WITHOUT CONFIG MATCH:")
    unmapped_scraper = []
    for scraper_name in scraper_dealerships:
        # Check if this scraper name has a direct config match
        has_config = any(c['name'] == scraper_name for c in config_dealerships)

        # Check if this scraper name is a mapping target
        is_mapping_target = scraper_name in code_name_mapping.values()

        # Check if there's a config that maps TO this scraper name
        mapped_config = None
        for config_name, mapped_scraper in code_name_mapping.items():
            if mapped_scraper == scraper_name:
                mapped_config = config_name
                break

        if not has_config and not mapped_config:
            unmapped_scraper.append(scraper_name)
            print(f"        [ERROR] '{scraper_name}' - NO CONFIG FOUND")
        elif mapped_config:
            print(f"        [OK] '{scraper_name}' <- mapped from config '{mapped_config}'")
        elif has_config:
            print(f"        [OK] '{scraper_name}' - direct match in config")

    # Find config names that don't have scraper data
    print("\n    B. CONFIG NAMES WITHOUT SCRAPER DATA:")
    for config in config_dealerships:
        config_name = config['name']

        # Check if config name directly matches scraper
        direct_match = config_name in scraper_dealerships

        # Check if config name has a mapping
        has_mapping = config_name in code_name_mapping
        mapped_name = code_name_mapping.get(config_name)

        # Check if mapped name exists in scraper data
        mapped_exists = mapped_name in scraper_dealerships if mapped_name else False

        if not direct_match and not mapped_exists:
            print(f"        [WARNING] Config '{config_name}' - NO SCRAPER DATA")
        elif has_mapping and mapped_exists:
            print(f"        [OK] Config '{config_name}' -> maps to '{mapped_name}' in scraper")
        elif direct_match:
            print(f"        [OK] Config '{config_name}' - direct match in scraper")

    # Step 5: Check VIN log tables
    print("\n[STEP 5] VIN LOG TABLE VERIFICATION:")

    vin_log_tables = db_manager.execute_query("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name LIKE '%_vin_log'
        ORDER BY table_name
    """)

    print(f"    Found {len(vin_log_tables)} VIN log tables")

    # Map config names to expected VIN log table names
    for config in config_dealerships[:31]:  # Focus on the 31 in scraper CSV
        config_name = config['name']

        # Generate expected VIN log table name
        expected_table = config_name.lower()
        expected_table = expected_table.replace(' ', '_')
        expected_table = expected_table.replace('&', 'and')
        expected_table = expected_table.replace('.', '')
        expected_table = expected_table.replace(',', '')
        expected_table = expected_table.replace("'", '')
        expected_table = expected_table.replace('-', '_')
        expected_table = expected_table.replace('/', '_')
        expected_table = expected_table.replace('__', '_')
        expected_table = f'{expected_table}_vin_log'

        # Check if table exists
        table_exists = any(t['table_name'] == expected_table for t in vin_log_tables)

        if table_exists:
            print(f"        [OK] '{config_name}' -> table '{expected_table}' EXISTS")
        else:
            print(f"        [MISSING] '{config_name}' -> table '{expected_table}' NOT FOUND")

    # Step 6: Recommendations
    print("\n[STEP 6] CRITICAL RECOMMENDATIONS:")
    print("=" * 60)

    if unmapped_scraper:
        print("\n    URGENT: These scraper dealerships need config entries or mappings:")
        for name in unmapped_scraper:
            print(f"        - '{name}'")

    # Find potential mapping issues
    print("\n    POTENTIAL NAME VARIATIONS TO MAP:")
    for scraper_name in scraper_dealerships:
        for config in config_dealerships:
            config_name = config['name']
            # Look for partial matches that might need mapping
            if (scraper_name != config_name and
                config_name not in code_name_mapping and
                (scraper_name.lower() in config_name.lower() or
                 config_name.lower() in scraper_name.lower())):
                print(f"        Config: '{config_name}' <-> Scraper: '{scraper_name}'")

    print("\n=== ANALYSIS COMPLETE ===")

    return {
        'scraper_dealerships': scraper_dealerships,
        'config_dealerships': config_dealerships,
        'unmapped_scraper': unmapped_scraper,
        'code_mappings': code_name_mapping
    }

if __name__ == "__main__":
    results = analyze_name_mappings()