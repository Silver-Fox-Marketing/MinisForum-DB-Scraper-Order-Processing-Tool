#!/usr/bin/env python3
"""
Verify Frank Leta Honda configuration was actually updated
"""

import sys
import json

# Add the scripts directory to Python path
scripts_path = r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts'
sys.path.append(scripts_path)

from database_connection import DatabaseManager

def verify_frank_leta_update():
    """Verify Frank Leta Honda configuration update"""
    print("=== Verifying Frank Leta Honda Configuration Update ===")

    # Initialize database
    try:
        db = DatabaseManager()
        print("OK Database connection established")
    except Exception as e:
        print(f"ERROR Database connection failed: {e}")
        return False

    # Get Frank Leta Honda config directly
    print("\n--- Current Database Configuration ---")
    result = db.execute_query("""
        SELECT name, filtering_rules::text as filtering_rules_text, updated_at
        FROM dealership_configs
        WHERE name = 'Frank Leta Honda' AND is_active = true
    """)

    if result:
        config = result[0]
        print(f"Name: {config['name']}")
        print(f"Last Updated: {config['updated_at']}")

        # Parse the JSON text
        try:
            rules = json.loads(config['filtering_rules_text'])
            print("\n--- Configuration Structure ---")
            print(json.dumps(rules, indent=2))

            # Verify all required fields exist
            print("\n--- Field Verification ---")
            required_fields = [
                "notes",
                "order_type",
                "days_on_lot",
                "price_range",
                "require_stock",
                "vehicle_types",
                "exclude_status",
                "exclude_in_transit",
                "allowed_vehicle_types",
                "exclude_missing_stock_number"
            ]

            all_present = True
            for field in required_fields:
                if field in rules:
                    print(f"[OK] {field}: PRESENT")
                else:
                    print(f"[MISSING] {field}: NOT FOUND")
                    all_present = False

            # Check for old fields that should NOT exist
            print("\n--- Old Fields Check (Should NOT Exist) ---")
            old_fields = ["exclude_conditions", "exclude_missing_stock", "seasoning_days"]
            old_found = False
            for field in old_fields:
                if field in rules:
                    print(f"[PROBLEM] {field}: STILL EXISTS (should be removed)")
                    old_found = True
                else:
                    print(f"[OK] {field}: REMOVED")

            # Verify specific values
            print("\n--- Value Verification ---")
            if "allowed_vehicle_types" in rules:
                avt = rules["allowed_vehicle_types"]
                if avt == ["cpo", "po", "certified", "pre-owned"]:
                    print("[OK] allowed_vehicle_types: Correct for used-only")
                else:
                    print(f"[WRONG] allowed_vehicle_types: {avt}")

            if "exclude_status" in rules:
                es = rules["exclude_status"]
                if set(es) == {"In-Transit", "Sold", "Allocated"}:
                    print("[OK] exclude_status: Has all required values")
                else:
                    print(f"[WRONG] exclude_status: {es}")

            print("\n--- FINAL VERDICT ---")
            if all_present and not old_found:
                print("[SUCCESS] Configuration is FULLY UPDATED to template standard!")
                print("Frank Leta Honda is ready for testing.")
                return True
            else:
                print("[WARNING] Configuration may need additional updates")
                return False

        except Exception as e:
            print(f"Error parsing JSON: {e}")
            print(f"Raw data: {config['filtering_rules_text']}")
            return False
    else:
        print("ERROR No Frank Leta Honda configuration found")
        return False

def main():
    """Main function"""
    success = verify_frank_leta_update()
    if success:
        print("\nVerification completed - Configuration is correct!")
        return 0
    else:
        print("\nVerification shows issues - Check configuration")
        return 1

if __name__ == "__main__":
    sys.exit(main())