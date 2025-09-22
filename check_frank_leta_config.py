#!/usr/bin/env python3
"""
Check Frank Leta Honda's dealership configuration
"""

import sys
import json

# Add the scripts directory to Python path
scripts_path = r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts'
sys.path.append(scripts_path)

from database_connection import DatabaseManager

def check_frank_leta_config():
    """Check Frank Leta Honda configuration"""
    print("=== Checking Frank Leta Honda Configuration ===")

    # Initialize database
    try:
        db = DatabaseManager()
        print("OK Database connection established")
    except Exception as e:
        print(f"ERROR Database connection failed: {e}")
        return False

    # Get Frank Leta Honda config
    print("\n--- Frank Leta Honda Configuration ---")
    frank_result = db.execute_query("""
        SELECT name, filtering_rules, is_active, updated_at
        FROM dealership_configs
        WHERE name ILIKE '%frank%leta%' AND is_active = true
    """)

    if frank_result:
        for config in frank_result:
            print(f"Name: {config['name']}")
            print(f"Active: {config['is_active']}")
            print(f"Updated: {config['updated_at']}")
            print("\nCurrent Filtering Rules:")
            try:
                rules = json.loads(config['filtering_rules'])
                print(json.dumps(rules, indent=2))

                # Check which filters are missing compared to template
                print("\n--- Template Comparison ---")
                template_filters = {
                    "notes": "Check",
                    "order_type": "Check",
                    "days_on_lot": "Check",
                    "price_range": "Check",
                    "require_stock": "Check",
                    "vehicle_types": "Check",
                    "exclude_status": "Check",
                    "exclude_in_transit": "Check",
                    "allowed_vehicle_types": "Check",
                    "exclude_missing_stock_number": "Check"
                }

                print("Filter Status:")
                for filter_name in template_filters:
                    if filter_name in rules:
                        print(f"  [EXISTS] {filter_name}: {rules[filter_name]}")
                    else:
                        print(f"  [MISSING] {filter_name}: NOT FOUND")

                # Check for old format fields
                print("\n--- Old Format Fields Check ---")
                old_fields = ["exclude_conditions", "seasoning_days", "exclude_vins", "special_rules"]
                for field in old_fields:
                    if field in rules:
                        print(f"  [OLD FORMAT] {field}: {rules[field]}")

            except Exception as e:
                print(f"Error parsing JSON: {e}")
                print(f"Raw filtering_rules: {config['filtering_rules']}")
    else:
        print("ERROR No Frank Leta Honda config found")

    # Get all dealership names with 'frank' or 'leta' for reference
    print("\n--- All Frank Leta Related Dealerships ---")
    all_frank = db.execute_query("""
        SELECT name, is_active
        FROM dealership_configs
        WHERE name ILIKE '%frank%' OR name ILIKE '%leta%'
        ORDER BY name
    """)

    if all_frank:
        for dealer in all_frank:
            status = "ACTIVE" if dealer['is_active'] else "INACTIVE"
            print(f"  [{status}] {dealer['name']}")

    return True

def main():
    """Main function"""
    success = check_frank_leta_config()
    if success:
        print("\nConfig check completed")
        return 0
    else:
        print("\nConfig check failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())