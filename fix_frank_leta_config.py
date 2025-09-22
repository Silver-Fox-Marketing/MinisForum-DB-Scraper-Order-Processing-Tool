#!/usr/bin/env python3
"""
Fix Frank Leta Honda's dealership configuration to match standardized template
Based on Final_dealership_config_template_9.16.md
"""

import sys
import json
from datetime import datetime

# Add the scripts directory to Python path
scripts_path = r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts'
sys.path.append(scripts_path)

from database_connection import DatabaseManager

def fix_frank_leta_config():
    """Fix Frank Leta Honda's configuration with proper template filters"""
    print("=== Fixing Frank Leta Honda Configuration ===")

    # Initialize database
    try:
        db = DatabaseManager()
        print("OK Database connection established")
    except Exception as e:
        print(f"ERROR Database connection failed: {e}")
        return False

    # Corrected configuration based on template (Used-only dealership)
    corrected_config = {
        "notes": "Standardized configuration for used-only dealership based on template 9.16",
        "order_type": "cao",
        "days_on_lot": {
            "max": 999,
            "min": 0
        },
        "price_range": {
            "max": 999999,
            "min": 0
        },
        "require_stock": True,
        "vehicle_types": ["used"],
        "exclude_status": ["In-Transit", "Sold", "Allocated"],
        "exclude_in_transit": True,
        "allowed_vehicle_types": ["cpo", "po", "certified", "pre-owned"],
        "exclude_missing_stock_number": True
    }

    print("\nCorrected Configuration:")
    print(json.dumps(corrected_config, indent=2))

    # Update the configuration
    try:
        update_query = """
            UPDATE dealership_configs
            SET filtering_rules = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE name = 'Frank Leta Honda' AND is_active = true
        """

        db.execute_query(update_query, [json.dumps(corrected_config)])
        print("\nOK Frank Leta Honda configuration updated successfully")

        # Verify the update
        verify_result = db.execute_query("""
            SELECT name, filtering_rules, updated_at
            FROM dealership_configs
            WHERE name = 'Frank Leta Honda' AND is_active = true
        """)

        if verify_result:
            print("\n--- Verification - Updated Configuration ---")
            config = verify_result[0]
            print(f"Name: {config['name']}")
            print(f"Updated: {config['updated_at']}")
            print("\nFiltering Rules:")
            try:
                rules = json.loads(config['filtering_rules'])
                print(json.dumps(rules, indent=2))
            except Exception as e:
                print(f"Error parsing JSON: {e}")
                print(f"Raw filtering_rules: {config['filtering_rules']}")
                return False

            # Report changes
            print("\n--- Key Fixes Applied ---")
            print("[ADDED] days_on_lot filter (min: 0, max: 999)")
            print("[ADDED] price_range filter (min: 0, max: 999999)")
            print("[ADDED] exclude_status: ['In-Transit', 'Sold', 'Allocated']")
            print("[ADDED] exclude_in_transit: true")
            print("[FIXED] allowed_vehicle_types: ['cpo', 'po', 'certified', 'pre-owned'] (was just ['used'])")
            print("[FIXED] exclude_missing_stock_number: true (was 'exclude_missing_stock')")
            print("[REMOVED] exclude_conditions field (old format)")
            print("[ADDED] notes field for documentation")

        return True

    except Exception as e:
        print(f"ERROR Failed to update configuration: {e}")
        return False

def main():
    """Main function"""
    success = fix_frank_leta_config()
    if success:
        print("\n=== Frank Leta Honda Configuration Fix Completed ===")
        print("The dealership now has:")
        print("- All required filters from the standardized template")
        print("- Proper vehicle type filtering for used vehicles")
        print("- Status exclusions for In-Transit, Sold, Allocated")
        print("- Stock number requirement")
        print("\nThis should reduce the CAO order from 54 to around 24 vehicles.")
        return 0
    else:
        print("\nConfiguration fix failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())