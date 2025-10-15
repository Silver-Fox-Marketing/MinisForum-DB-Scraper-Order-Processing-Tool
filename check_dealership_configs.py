"""
Check and display dealership configs - specifically looking at South County DCJR
and all List order type dealerships to standardize their templates
"""

import sys
import os
import json

# Add scripts directory to path for imports
script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
sys.path.insert(0, script_dir)

from database_connection import db_manager

def check_configs():
    """Check dealership configurations"""

    print("="*80)
    print("DEALERSHIP CONFIG ANALYSIS")
    print("="*80)

    # Test database connection
    if not db_manager.test_connection():
        print("[ERROR] Database connection failed")
        return False

    # First, get South County DCJR config (the template)
    print("\n[STEP 1] South County DCJR Config (Template):")
    print("-"*80)

    soco_query = """
        SELECT name, filtering_rules, output_rules, is_active
        FROM dealership_configs
        WHERE name = 'South County DCJR'
    """

    soco_result = db_manager.execute_query(soco_query)

    if soco_result:
        soco_config = soco_result[0]
        print(f"Name: {soco_config['name']}")
        print(f"Active: {soco_config['is_active']}")
        print(f"\nFiltering Rules:")
        print(json.dumps(soco_config['filtering_rules'], indent=2))
        print(f"\nOutput Rules:")
        print(json.dumps(soco_config['output_rules'], indent=2))

        # Save for comparison
        template_filters = soco_config['filtering_rules']
    else:
        print("[ERROR] South County DCJR config not found!")
        return False

    # Now get all dealerships and show which have order_type='list'
    print("\n"*2)
    print("[STEP 2] ALL Dealership Configs:")
    print("-"*80)

    all_query = """
        SELECT name, filtering_rules, output_rules, is_active
        FROM dealership_configs
        ORDER BY name
    """

    all_results = db_manager.execute_query(all_query)

    list_dealerships = []
    cao_dealerships = []
    other_dealerships = []

    for config in all_results:
        filters = config['filtering_rules']
        order_type = filters.get('order_type', 'NONE')

        if order_type == 'list':
            list_dealerships.append(config)
        elif order_type == 'cao':
            cao_dealerships.append(config)
        else:
            other_dealerships.append(config)

    print(f"\nTotal Dealerships: {len(all_results)}")
    print(f"  - CAO Order Type: {len(cao_dealerships)}")
    print(f"  - LIST Order Type: {len(list_dealerships)}")
    print(f"  - No Order Type Set: {len(other_dealerships)}")

    # Show LIST dealerships in detail
    print("\n"*2)
    print("[STEP 3] LIST Order Type Dealerships:")
    print("-"*80)

    for i, config in enumerate(list_dealerships, 1):
        print(f"\n{i}. {config['name']}")
        print(f"   Active: {config['is_active']}")

        filters = config['filtering_rules']

        # Check for important fields
        print(f"   Order Type: {filters.get('order_type', 'MISSING')}")
        print(f"   Vehicle Types: {filters.get('vehicle_types', 'MISSING')}")
        print(f"   Allowed Vehicle Types: {filters.get('allowed_vehicle_types', 'MISSING')}")
        print(f"   Price Range: ${filters.get('price_range', {}).get('min', 'N/A')} - ${filters.get('price_range', {}).get('max', 'N/A')}")
        print(f"   Days on Lot: {filters.get('days_on_lot', {}).get('min', 'N/A')} - {filters.get('days_on_lot', {}).get('max', 'N/A')}")
        print(f"   Exclude Status: {filters.get('exclude_status', 'MISSING')}")
        print(f"   Exclude In-Transit: {filters.get('exclude_in_transit', 'MISSING')}")
        print(f"   Require Stock: {filters.get('require_stock', 'MISSING')}")
        print(f"   Exclude Missing Stock Number: {filters.get('exclude_missing_stock_number', 'MISSING')}")

        # Check if template field exists
        if 'template' in filters:
            print(f"   Template: {filters['template']}")
        else:
            print(f"   Template: MISSING")

        # Check for any notes
        if 'notes' in filters:
            print(f"   Notes: {filters['notes']}")

    # Show CAO dealerships summary
    print("\n"*2)
    print("[STEP 4] CAO Order Type Dealerships (Summary):")
    print("-"*80)

    for i, config in enumerate(cao_dealerships, 1):
        filters = config['filtering_rules']
        print(f"{i}. {config['name']}")
        print(f"   Vehicle Types: {filters.get('vehicle_types', 'MISSING')}")
        print(f"   Allowed Vehicle Types: {filters.get('allowed_vehicle_types', 'MISSING')}")

    # Show dealerships with no order_type
    if other_dealerships:
        print("\n"*2)
        print("[STEP 5] Dealerships WITHOUT order_type field:")
        print("-"*80)
        for i, config in enumerate(other_dealerships, 1):
            print(f"{i}. {config['name']}")

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)

    return True

if __name__ == "__main__":
    success = check_configs()

    if success:
        print(f"\n[SUCCESS] Config analysis completed!")
    else:
        print(f"\n[ERROR] Config analysis failed!")
