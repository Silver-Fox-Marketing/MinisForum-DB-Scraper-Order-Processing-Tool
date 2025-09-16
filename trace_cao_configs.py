#!/usr/bin/env python3
"""
Trace CAO configuration retrieval for South County DCJR vs Auffenberg Hyundai
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'projects/minisforum_database_transfer/bulletproof_package/scripts'))

from database_connection import db_manager
import json

def trace_config_retrieval(dealership_name):
    """Trace exactly what configuration is being retrieved for a dealership"""
    print(f"\n=== TRACING CONFIG RETRIEVAL: {dealership_name} ===")

    # Step 1: Check what configs exist for this dealership
    print(f"\n[STEP 1] All configs for '{dealership_name}':")
    all_configs = db_manager.execute_query("""
        SELECT name, filtering_rules, updated_at, is_active
        FROM dealership_configs
        WHERE name = %s
        ORDER BY updated_at DESC NULLS LAST
    """, (dealership_name,))

    for i, config in enumerate(all_configs):
        print(f"  Config {i+1}:")
        print(f"    Name: {config['name']}")
        print(f"    Active: {config['is_active']}")
        print(f"    Updated: {config['updated_at']}")
        if isinstance(config['filtering_rules'], str):
            rules = json.loads(config['filtering_rules'])
        else:
            rules = config['filtering_rules']
        print(f"    Rules: {json.dumps(rules, indent=6)}")

    # Step 2: What the CAO processing code actually retrieves
    print(f"\n[STEP 2] What CAO processing retrieves (exact same query):")
    cao_config = db_manager.execute_query("""
        SELECT filtering_rules FROM dealership_configs
        WHERE name = %s AND is_active = true
        ORDER BY updated_at DESC NULLS LAST
    """, (dealership_name,))

    if cao_config:
        config_data = cao_config[0]
        if isinstance(config_data['filtering_rules'], str):
            cao_rules = json.loads(config_data['filtering_rules'])
        else:
            cao_rules = config_data['filtering_rules']
        print(f"    CAO Rules: {json.dumps(cao_rules, indent=6)}")

        # Count the rules
        print(f"\n[ANALYSIS] Configuration has {len(cao_rules)} filter rules:")
        for rule_name, rule_value in cao_rules.items():
            print(f"    - {rule_name}: {rule_value}")
    else:
        print("    [ERROR] No active config found!")
        cao_rules = None

    return cao_rules

def compare_configs():
    """Compare the exact configurations being retrieved by CAO processing"""
    print("=== CAO CONFIGURATION COMPARISON ===")
    print("Tracing the exact same config retrieval used in CAO processing...")

    # Get configs exactly as CAO processing does
    south_county_config = trace_config_retrieval("South County DCJR")
    auffenberg_config = trace_config_retrieval("Auffenberg Hyundai")

    # Compare
    print(f"\n=== COMPARISON RESULTS ===")
    if south_county_config and auffenberg_config:
        south_county_rules = set(south_county_config.keys())
        auffenberg_rules = set(auffenberg_config.keys())

        missing_from_auffenberg = south_county_rules - auffenberg_rules
        extra_in_auffenberg = auffenberg_rules - south_county_rules

        print(f"South County DCJR has {len(south_county_rules)} rules")
        print(f"Auffenberg Hyundai has {len(auffenberg_rules)} rules")

        if missing_from_auffenberg:
            print(f"\n[ERROR] Auffenberg MISSING these rules from South County:")
            for rule in missing_from_auffenberg:
                print(f"    - {rule}: {south_county_config[rule]}")

        if extra_in_auffenberg:
            print(f"\n[INFO] Auffenberg has these EXTRA rules:")
            for rule in extra_in_auffenberg:
                print(f"    - {rule}: {auffenberg_config[rule]}")

        if not missing_from_auffenberg and not extra_in_auffenberg:
            print(f"\n[OK] Both dealerships have identical rule sets!")

            # Check for value differences
            print(f"\n[DETAILED] Rule value comparison:")
            for rule in sorted(south_county_rules):
                south_val = south_county_config[rule]
                auff_val = auffenberg_config[rule]
                if south_val == auff_val:
                    print(f"    ✓ {rule}: IDENTICAL")
                else:
                    print(f"    ✗ {rule}: DIFFERENT")
                    print(f"        South County: {south_val}")
                    print(f"        Auffenberg:   {auff_val}")
    else:
        print("[ERROR] Could not retrieve one or both configurations")

if __name__ == "__main__":
    compare_configs()