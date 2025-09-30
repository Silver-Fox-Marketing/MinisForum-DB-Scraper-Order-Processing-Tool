#!/usr/bin/env python3
"""
Update Glendale CDJR configuration to enable missing price filter
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_connection import DatabaseManager

def update_glendale_filter():
    """Enable missing price filter for Glendale CDJR"""
    db = DatabaseManager()

    try:
        # First, get the current configuration
        result = db.execute_query("""
            SELECT filtering_rules
            FROM dealership_configs
            WHERE name = %s
        """, ('Glendale CDJR',))

        if not result:
            print("[ERROR] Glendale CDJR not found in dealership_configs")
            return False

        # Parse current filtering rules
        current_rules = result[0]['filtering_rules']
        if isinstance(current_rules, str):
            filtering_rules = json.loads(current_rules)
        else:
            filtering_rules = current_rules if current_rules else {}

        print(f"[INFO] Current filtering rules: {filtering_rules}")

        # Add the missing price filter
        filtering_rules['exclude_missing_price'] = True

        print(f"[INFO] Updated filtering rules: {filtering_rules}")

        # Update the database
        update_result = db.execute_query("""
            UPDATE dealership_configs
            SET filtering_rules = %s
            WHERE name = %s
        """, (json.dumps(filtering_rules), 'Glendale CDJR'))

        print("[SUCCESS] Glendale CDJR configuration updated with missing price filter")

        # Verify the update
        verify_result = db.execute_query("""
            SELECT name, filtering_rules
            FROM dealership_configs
            WHERE name = %s
        """, ('Glendale CDJR',))

        if verify_result:
            updated_rules = json.loads(verify_result[0]['filtering_rules'])
            print(f"[VERIFY] Updated configuration: {updated_rules}")
            print(f"[VERIFY] exclude_missing_price = {updated_rules.get('exclude_missing_price', False)}")

        return True

    except Exception as e:
        print(f"[ERROR] Failed to update configuration: {e}")
        return False

if __name__ == "__main__":
    update_glendale_filter()