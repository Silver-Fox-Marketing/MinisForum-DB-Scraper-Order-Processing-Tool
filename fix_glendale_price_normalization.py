#!/usr/bin/env python3
"""
Fix Glendale Price Normalization
Applies price normalization to convert NULL/invalid prices to 0
This ensures exclude_missing_price filter works correctly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'projects/minisforum_database_transfer/bulletproof_package/scripts'))

from database_connection import db_manager
from scraper_data_normalizer import ScraperDataNormalizer

def fix_glendale_price_normalization():
    """Fix price normalization for Glendale dealership data"""

    print("=== FIXING GLENDALE PRICE NORMALIZATION ===")

    # Initialize normalizer
    normalizer = ScraperDataNormalizer()

    # Step 1: Get the active import ID
    active_import = db_manager.execute_query("""
        SELECT import_id, status, dealerships_count
        FROM scraper_imports
        WHERE status = 'active'
        ORDER BY import_id DESC
        LIMIT 1
    """)

    if not active_import:
        print("[ERROR] No active import found!")
        return False

    import_id = active_import[0]['import_id']
    print(f"[STEP 1] Active import ID: {import_id}")

    # Step 2: Get all Glendale vehicles from normalized data
    print(f"\n[STEP 2] FETCHING GLENDALE NORMALIZED DATA...")

    glendale_data = db_manager.execute_query("""
        SELECT nvd.id, nvd.raw_data_id, nvd.vin, nvd.price, rvd.price as raw_price
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = %s AND si.status = 'active'
    """, ('Glendale Chrysler Jeep Dodge Ram',))

    print(f"    Found {len(glendale_data)} Glendale vehicles")

    # Step 3: Count current NULL prices
    null_price_count = sum(1 for v in glendale_data if v['price'] is None)
    print(f"    Vehicles with NULL prices: {null_price_count}")

    if null_price_count == 0:
        print("\n[INFO] No NULL prices found - normalization may already be fixed")
        return True

    # Step 4: Apply price normalization
    print(f"\n[STEP 3] APPLYING PRICE NORMALIZATION...")

    updated_count = 0
    for vehicle in glendale_data:
        if vehicle['price'] is None:
            # Apply the normalize_price logic
            normalized_price = normalizer.normalize_price(vehicle['raw_price'])

            # Update the normalized_vehicle_data table
            db_manager.execute_query("""
                UPDATE normalized_vehicle_data
                SET price = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (normalized_price, vehicle['id']))

            updated_count += 1

            if updated_count % 10 == 0:
                print(f"    Updated {updated_count} vehicles...")

    print(f"    [OK] Updated {updated_count} vehicles with normalized prices")

    # Step 5: Verify the fix
    print(f"\n[STEP 4] VERIFYING NORMALIZATION...")

    # Check how many vehicles now have valid prices vs 0 prices
    verification = db_manager.execute_query("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN nvd.price IS NULL THEN 1 END) as null_prices,
            COUNT(CASE WHEN nvd.price = 0 THEN 1 END) as zero_prices,
            COUNT(CASE WHEN nvd.price > 0 THEN 1 END) as valid_prices
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = %s AND si.status = 'active'
    """, ('Glendale Chrysler Jeep Dodge Ram',))

    result = verification[0]
    print(f"    Total vehicles: {result['total']}")
    print(f"    NULL prices: {result['null_prices']}")
    print(f"    Zero prices (normalized): {result['zero_prices']}")
    print(f"    Valid prices (> 0): {result['valid_prices']}")

    # Step 6: Test the CAO filter
    print(f"\n[STEP 5] TESTING CAO FILTER...")

    # Simulate the CAO query with price filter
    cao_test = db_manager.execute_query("""
        SELECT COUNT(*) as count
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = %s
        AND nvd.on_lot_status IN ('onlot', 'on lot')
        AND si.status = 'active'
        AND nvd.vehicle_condition IN ('po', 'cpo')
        AND nvd.price > 0  -- The exclude_missing_price filter
    """, ('Glendale Chrysler Jeep Dodge Ram',))

    vehicles_with_price = cao_test[0]['count']
    print(f"    Vehicles that would pass price filter: {vehicles_with_price}")

    if vehicles_with_price == 0:
        print(f"\n[SUCCESS] Price normalization fixed!")
        print(f"Glendale will now correctly return 0 vehicles when exclude_missing_price is enabled")
    else:
        print(f"\n[WARNING] Still have {vehicles_with_price} vehicles with prices > 0")
        print(f"These vehicles have valid prices and will be included in CAO orders")

    return True

if __name__ == "__main__":
    fix_glendale_price_normalization()