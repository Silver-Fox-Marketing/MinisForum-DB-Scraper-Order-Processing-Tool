#!/usr/bin/env python3
"""
Check price values for Glendale CDJR vehicles to diagnose filtering issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_connection import DatabaseManager

def check_glendale_prices():
    """Check price values for specific VINs"""
    db = DatabaseManager()

    # The VINs that shouldn't be returning
    problem_vins = [
        '1C4BJWEG8FL764636',
        '1C4HJXDG5MW826989',
        '1C4HJXDN2KW679221',
        '1C4HJXDN4MW766847',
        '1C4JJXP66NW109376',
        '1C4JJXR67NW171379',
        '1C4JJXR6XPW516567',
        '1C4PJMDS8GW174601',
        '1C4RJYB63N8748237',
        '1GNERKKW7MJ244230',
        '5XYRKDLFXPG212594',
        'KNDJT2A68C7436696',
        'SALE3ERU7M2045455',
        'WA1LFAFP4EA104542'
    ]

    print("[INFO] Checking price values for Glendale CDJR vehicles with asterisk prices...")
    print("=" * 80)

    for vin in problem_vins[:5]:  # Check first 5 VINs
        print(f"\nVIN: {vin}")
        print("-" * 40)

        # Check normalized data
        nvd_result = db.execute_query("""
            SELECT vin, price, stock, vehicle_condition
            FROM normalized_vehicle_data nvd
            WHERE nvd.vin = %s
            AND nvd.location = 'Glendale Chrysler Jeep'
            AND EXISTS (
                SELECT 1 FROM raw_vehicle_data rvd
                JOIN scraper_imports si ON rvd.import_id = si.import_id
                WHERE rvd.vin = nvd.vin
                AND rvd.location = nvd.location
                AND si.status = 'active'
            )
        """, (vin,))

        if nvd_result:
            print(f"  Normalized Data:")
            print(f"    - Price: {nvd_result[0]['price']} (type: {type(nvd_result[0]['price']).__name__})")
            print(f"    - Stock: {nvd_result[0]['stock']}")
            print(f"    - Condition: {nvd_result[0]['vehicle_condition']}")

        # Check raw data
        rvd_result = db.execute_query("""
            SELECT rvd.vin, rvd.price, rvd.stock, rvd.status
            FROM raw_vehicle_data rvd
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE rvd.vin = %s
            AND rvd.location = 'Glendale Chrysler Jeep'
            AND si.status = 'active'
        """, (vin,))

        if rvd_result:
            print(f"  Raw Data:")
            print(f"    - Price: '{rvd_result[0]['price']}' (type: {type(rvd_result[0]['price']).__name__})")
            print(f"    - Stock: {rvd_result[0]['stock']}")
            print(f"    - Status: {rvd_result[0]['status']}")

        # Test the filter condition
        filter_test = db.execute_query("""
            SELECT
                rvd.vin,
                rvd.price as raw_price,
                nvd.price as norm_price,
                CASE
                    WHEN nvd.price IS NOT NULL AND nvd.price > 0 THEN 'PASS nvd.price check'
                    ELSE 'FAIL nvd.price check'
                END as nvd_check,
                CASE
                    WHEN rvd.price IS NOT NULL AND rvd.price NOT IN ('*', '', 'Call', 'TBD', 'N/A', '0', '$0') THEN 'PASS rvd.price IN check'
                    ELSE 'FAIL rvd.price IN check'
                END as rvd_in_check,
                CASE
                    WHEN rvd.price NOT LIKE '%*%' THEN 'PASS rvd.price LIKE check'
                    ELSE 'FAIL rvd.price LIKE check'
                END as rvd_like_check
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.vin = rvd.vin AND nvd.location = rvd.location
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE nvd.vin = %s
            AND nvd.location = 'Glendale Chrysler Jeep'
            AND si.status = 'active'
        """, (vin,))

        if filter_test:
            print(f"  Filter Test Results:")
            print(f"    - {filter_test[0]['nvd_check']}")
            print(f"    - {filter_test[0]['rvd_in_check']}")
            print(f"    - {filter_test[0]['rvd_like_check']}")

    print("\n" + "=" * 80)
    print("[DIAGNOSIS] If nvd.price is passing but rvd.price is failing, the issue is in normalization")
    print("[DIAGNOSIS] The normalized price might be converting '*' to 0 or another value")

if __name__ == "__main__":
    check_glendale_prices()