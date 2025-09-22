#!/usr/bin/env python3
"""
Check Serra Honda's dealership configuration and compare with South County DCJR
"""

import sys
import json
from datetime import datetime

# Add the scripts directory to Python path
scripts_path = r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts'
sys.path.append(scripts_path)

from database_connection import DatabaseManager

def check_dealership_configs():
    """Check and compare dealership configurations"""
    print("=== Checking Dealership Configurations ===")

    # Initialize database
    try:
        db = DatabaseManager()
        print("OK Database connection established")
    except Exception as e:
        print(f"ERROR Database connection failed: {e}")
        return False

    # Get Serra Honda config
    print("\n--- Serra Honda Configuration ---")
    serra_result = db.execute_query("""
        SELECT name, filtering_rules, is_active, updated_at
        FROM dealership_configs
        WHERE name ILIKE '%serra%honda%' AND is_active = true
    """)

    if serra_result:
        for config in serra_result:
            print(f"Name: {config['name']}")
            print(f"Active: {config['is_active']}")
            print(f"Updated: {config['updated_at']}")
            print("Filtering Rules:")
            try:
                rules = json.loads(config['filtering_rules'])
                print(json.dumps(rules, indent=2))
            except:
                print(config['filtering_rules'])
    else:
        print("ERROR No Serra Honda config found")

    # Get South County DCJR config for comparison
    print("\n--- South County DCJR Configuration (Reference) ---")
    south_county_result = db.execute_query("""
        SELECT name, filtering_rules, is_active, updated_at
        FROM dealership_configs
        WHERE name ILIKE '%south%county%dcjr%' AND is_active = true
    """)

    if south_county_result:
        for config in south_county_result:
            print(f"Name: {config['name']}")
            print(f"Active: {config['is_active']}")
            print(f"Updated: {config['updated_at']}")
            print("Filtering Rules:")
            try:
                rules = json.loads(config['filtering_rules'])
                print(json.dumps(rules, indent=2))
            except:
                print(config['filtering_rules'])
    else:
        print("ERROR No South County DCJR config found")

    # Show all dealership names for reference
    print("\n--- All Active Dealership Names ---")
    all_dealerships = db.execute_query("""
        SELECT name FROM dealership_configs
        WHERE is_active = true
        ORDER BY name
    """)

    if all_dealerships:
        for dealer in all_dealerships:
            print(f"  {dealer['name']}")

    return True

def main():
    """Main function"""
    success = check_dealership_configs()
    if success:
        print("\nConfig check completed")
        return 0
    else:
        print("\nConfig check failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())