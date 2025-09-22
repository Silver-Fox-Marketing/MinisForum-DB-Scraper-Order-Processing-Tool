#!/usr/bin/env python3
"""
Test Frank Leta Honda CAO filters to see what's being applied
"""

import sys
import json
from datetime import datetime

# Add the scripts directory to Python path
scripts_path = r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts'
sys.path.append(scripts_path)

from database_connection import DatabaseManager

def test_frank_leta_cao_filters():
    """Test Frank Leta Honda CAO filter application"""
    print("=== Testing Frank Leta Honda CAO Filters ===")

    # Initialize database
    try:
        db = DatabaseManager()
        print("OK Database connection established")
    except Exception as e:
        print(f"ERROR Database connection failed: {e}")
        return False

    # Get Frank Leta's current config
    print("\n--- Current Configuration ---")
    config_result = db.execute_query("""
        SELECT filtering_rules::text as rules_text
        FROM dealership_configs
        WHERE name = 'Frank Leta Honda' AND is_active = true
    """)

    if config_result:
        rules = json.loads(config_result[0]['rules_text'])
        print(f"Exclude Status: {rules.get('exclude_status', 'NOT SET')}")
        print(f"Exclude In Transit: {rules.get('exclude_in_transit', 'NOT SET')}")
        print(f"Exclude Missing Stock: {rules.get('exclude_missing_stock_number', 'NOT SET')}")

    # Test 1: Count total vehicles
    print("\n--- Total Vehicles for Frank Leta ---")
    total_result = db.execute_query("""
        SELECT COUNT(*) as total,
               COUNT(DISTINCT nvd.vin) as unique_vins
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = 'Frank Leta Honda'
          AND si.status = 'active'
          AND nvd.vehicle_condition IN ('cpo', 'po', 'certified', 'pre-owned')
    """)

    if total_result:
        print(f"Total vehicles: {total_result[0]['total']}")
        print(f"Unique VINs: {total_result[0]['unique_vins']}")

    # Test 2: Check VIN log exclusions
    print("\n--- VIN Log Exclusions ---")
    vinlog_result = db.execute_query("""
        SELECT COUNT(DISTINCT nvd.vin) as in_vinlog
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = 'Frank Leta Honda'
          AND si.status = 'active'
          AND nvd.vehicle_condition IN ('cpo', 'po', 'certified', 'pre-owned')
          AND nvd.vin IN (SELECT vin FROM frank_leta_honda_vin_log)
    """)

    if vinlog_result:
        print(f"VINs already in VIN log: {vinlog_result[0]['in_vinlog']}")

    # Test 3: Check status exclusions
    print("\n--- Status Breakdown ---")
    status_result = db.execute_query("""
        SELECT nvd.status as lot_status, COUNT(*) as count
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = 'Frank Leta Honda'
          AND si.status = 'active'
          AND nvd.vehicle_condition IN ('cpo', 'po', 'certified', 'pre-owned')
        GROUP BY nvd.status
        ORDER BY count DESC
    """)

    if status_result:
        for status in status_result:
            print(f"  {status['lot_status'] or 'NULL'}: {status['count']} vehicles")

    # Test 4: Check stock number exclusions
    print("\n--- Stock Number Status ---")
    stock_result = db.execute_query("""
        SELECT
            COUNT(CASE WHEN nvd.stock IS NULL OR nvd.stock = '' THEN 1 END) as missing_stock,
            COUNT(CASE WHEN nvd.stock IS NOT NULL AND nvd.stock != '' THEN 1 END) as has_stock
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = 'Frank Leta Honda'
          AND si.status = 'active'
          AND nvd.vehicle_condition IN ('cpo', 'po', 'certified', 'pre-owned')
    """)

    if stock_result:
        print(f"Missing stock number: {stock_result[0]['missing_stock']} vehicles")
        print(f"Has stock number: {stock_result[0]['has_stock']} vehicles")

    # Test 5: Apply all filters manually
    print("\n--- Applying All Filters Manually ---")
    filtered_result = db.execute_query("""
        SELECT COUNT(DISTINCT nvd.vin) as filtered_count
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = 'Frank Leta Honda'
          AND si.status = 'active'
          AND nvd.vehicle_condition IN ('cpo', 'po', 'certified', 'pre-owned')
          AND nvd.vin NOT IN (SELECT vin FROM frank_leta_honda_vin_log)
          AND (nvd.status IS NULL OR nvd.status NOT IN ('In-Transit', 'Sold', 'Allocated'))
          AND nvd.stock IS NOT NULL
          AND nvd.stock != ''
    """)

    if filtered_result:
        print(f"After all filters: {filtered_result[0]['filtered_count']} vehicles")

    # Test 6: Sample the vehicles being included
    print("\n--- Sample of Included Vehicles ---")
    sample_result = db.execute_query("""
        SELECT nvd.vin, nvd.status, nvd.stock, nvd.vehicle_condition
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = 'Frank Leta Honda'
          AND si.status = 'active'
          AND nvd.vehicle_condition IN ('cpo', 'po', 'certified', 'pre-owned')
          AND nvd.vin NOT IN (SELECT vin FROM frank_leta_honda_vin_log)
        LIMIT 5
    """)

    if sample_result:
        for vehicle in sample_result:
            print(f"  VIN: {vehicle['vin']}")
            print(f"    Status: {vehicle['status']}")
            print(f"    Stock: {vehicle['stock']}")
            print(f"    Condition: {vehicle['vehicle_condition']}")

    return True

def main():
    """Main function"""
    success = test_frank_leta_cao_filters()
    if success:
        print("\nFilter test completed")
        return 0
    else:
        print("\nFilter test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())