#!/usr/bin/env python3
"""
Update Weber Chevrolet configuration to add exclude_missing_stock_number filter
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.database_connection import get_db_connection
import json

def update_weber_config():
    """Update Weber Chevrolet to use standardized configuration"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # New configuration matching South County DCJR
    new_config = {
        "notes": "Standardized configuration based on Porsche St. Louis template",
        "order_type": "cao",
        "days_on_lot": {"max": 999, "min": 0},
        "price_range": {"max": 999999, "min": 0},
        "require_stock": True,
        "vehicle_types": ["new", "used"],
        "exclude_status": ["In-Transit", "Sold", "Allocated"],
        "exclude_in_transit": True,
        "allowed_vehicle_types": ["new", "cpo", "po", "certified", "pre-owned"],
        "exclude_missing_stock_number": True
    }

    print("Updating Weber Chevrolet configuration...")

    # Update the configuration
    cursor.execute("""
        UPDATE dealership_configs
        SET filtering_rules = %s
        WHERE name = 'Weber Chevrolet'
    """, (json.dumps(new_config),))

    conn.commit()

    # Verify the update
    cursor.execute("SELECT name, filtering_rules FROM dealership_configs WHERE name = 'Weber Chevrolet'")
    result = cursor.fetchone()

    if result:
        print(f"\n✅ Successfully updated Weber Chevrolet configuration:")
        print(f"Name: {result[0]}")
        print(f"Config: {json.dumps(result[1], indent=2)}")
    else:
        print("❌ Weber Chevrolet not found in database")

    conn.close()

if __name__ == "__main__":
    update_weber_config()