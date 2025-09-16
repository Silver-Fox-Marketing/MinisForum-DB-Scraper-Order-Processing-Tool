#!/usr/bin/env python3
"""
Compare dealership configurations to identify missing filters
"""

import requests
import json

def get_dealership_config(name):
    """Get configuration for a specific dealership"""
    try:
        response = requests.get('http://127.0.0.1:5000/api/dealerships')
        dealerships = response.json()

        for dealership in dealerships:
            if dealership['name'] == name:
                return dealership
        return None
    except Exception as e:
        print(f"Error fetching dealerships: {e}")
        return None

def compare_configs():
    """Compare South County DCJR vs Auffenberg Hyundai configs"""

    print("=== DEALERSHIP CONFIGURATION COMPARISON ===\n")

    # Get both configurations
    south_county = get_dealership_config("South County DCJR")
    auffenberg = get_dealership_config("Auffenberg Hyundai")

    if not south_county:
        print("[ERROR] Could not find South County DCJR")
        return

    if not auffenberg:
        print("[ERROR] Could not find Auffenberg Hyundai")
        return

    print("[REFERENCE] SOUTH COUNTY DCJR (Template):")
    print(json.dumps(south_county['filtering_rules'], indent=2))

    print("\n[CURRENT] AUFFENBERG HYUNDAI (Current Config):")
    print(json.dumps(auffenberg['filtering_rules'], indent=2))

    # Find missing filters
    south_filters = set(south_county['filtering_rules'].keys())
    auffenberg_filters = set(auffenberg['filtering_rules'].keys())

    missing_filters = south_filters - auffenberg_filters

    print(f"\n[ANALYSIS]:")
    print(f"South County has {len(south_filters)} filter rules")
    print(f"Auffenberg has {len(auffenberg_filters)} filter rules")

    if missing_filters:
        print(f"\n[ERROR] MISSING FILTERS in Auffenberg Hyundai:")
        for filter_name in missing_filters:
            value = south_county['filtering_rules'][filter_name]
            print(f"  - {filter_name}: {value}")

        print(f"\n[SOLUTION] UPDATED CONFIG for Auffenberg Hyundai:")
        updated_config = auffenberg['filtering_rules'].copy()
        for filter_name in missing_filters:
            updated_config[filter_name] = south_county['filtering_rules'][filter_name]

        print(json.dumps(updated_config, indent=2))

    else:
        print("\n[OK] All filters match - no missing configurations")

if __name__ == "__main__":
    compare_configs()