#!/usr/bin/env python3
"""
Fix Serra Honda's dealership configuration with proper seasoning filter and all missing filters
Based on Final_dealership_config_template_9.16.md and South County DCJR reference
"""

import sys
import json
from datetime import datetime

# Add the scripts directory to Python path
scripts_path = r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts'
sys.path.append(scripts_path)

from database_connection import DatabaseManager

def fix_serra_honda_config():
    """Fix Serra Honda's configuration with proper filters"""
    print("=== Fixing Serra Honda Configuration ===")

    # Initialize database
    try:
        db = DatabaseManager()
        print("OK Database connection established")
    except Exception as e:
        print(f"ERROR Database connection failed: {e}")
        return False

    # Corrected configuration based on template with seasoning filter minimum of 7 days
    # User specified: minimum seasoning (7 days), no maximum
    corrected_config = {
        "notes": "Corrected configuration based on Final_dealership_config_template_9.16.md - Added proper seasoning filter (min 7 days) and all missing filters",
        "order_type": "cao",
        "days_on_lot": {
            "max": 999,    # No maximum as user specified
            "min": 7       # Minimum 7 days seasoning as user specified
        },
        "price_range": {
            "max": 999999,
            "min": 0
        },
        "require_stock": True,
        "vehicle_types": ["new", "used"],
        "exclude_status": ["In-Transit", "Sold", "Allocated"],
        "exclude_in_transit": True,
        "allowed_vehicle_types": ["new", "cpo", "po", "certified", "pre-owned"],
        "exclude_missing_stock_number": True
    }

    print("Corrected Configuration:")
    print(json.dumps(corrected_config, indent=2))

    # Update the configuration
    try:
        update_query = """
            UPDATE dealership_configs
            SET filtering_rules = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE name = 'Serra Honda O''Fallon' AND is_active = true
        """

        db.execute_query(update_query, [json.dumps(corrected_config)])
        print("OK Serra Honda configuration updated successfully")

        # Verify the update
        verify_result = db.execute_query("""
            SELECT name, filtering_rules, updated_at
            FROM dealership_configs
            WHERE name = 'Serra Honda O''Fallon' AND is_active = true
        """)

        if verify_result:
            print("\nVerification - Updated Configuration:")
            config = verify_result[0]
            print(f"Name: {config['name']}")
            print(f"Updated: {config['updated_at']}")
            print("Filtering Rules:")
            try:
                rules = json.loads(config['filtering_rules'])
                print(json.dumps(rules, indent=2))
            except Exception as e:
                print(f"Error parsing JSON: {e}")
                print(f"Raw filtering_rules: {config['filtering_rules']}")
                return False

            # Check key fixes
            print("\nKey Fixes Applied:")
            if "days_on_lot" in rules and rules["days_on_lot"]["min"] == 7:
                print("✅ Seasoning filter: Minimum 7 days (was 'seasoning_days': 7)")

            if "exclude_status" in rules:
                print("✅ Status exclusions: Added In-Transit, Sold, Allocated")

            if "exclude_in_transit" in rules:
                print("✅ In-transit exclusion: Added")

            if "allowed_vehicle_types" in rules and "cpo" in rules["allowed_vehicle_types"]:
                print("✅ Vehicle types: Fixed to include cpo, po, certified, pre-owned")

            if "exclude_missing_stock_number" in rules:
                print("✅ Stock number filter: Fixed field name")

        return True

    except Exception as e:
        print(f"ERROR Failed to update configuration: {e}")
        return False

def main():
    """Main function"""
    success = fix_serra_honda_config()
    if success:
        print("\nSerra Honda configuration fix completed!")
        print("The dealership should now properly filter:")
        print("- VINs must be on lot for minimum 7 days (seasoning)")
        print("- Exclude In-Transit, Sold, Allocated vehicles")
        print("- Include proper vehicle types (new, cpo, po, certified, pre-owned)")
        print("- Exclude vehicles without stock numbers")
        return 0
    else:
        print("\nConfiguration fix failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())