#!/usr/bin/env python3
"""
Deep investigation of CAO processing for Auffenberg Hyundai
- Config retrieval with timestamps
- VIN log table verification
- Vehicle data filtering step-by-step
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'projects/minisforum_database_transfer/bulletproof_package/scripts'))

from database_connection import db_manager
import json

def investigate_config_caching(dealership_name):
    """Investigate config caching and retrieval timestamps"""
    print(f"\n=== CONFIG CACHING INVESTIGATION: {dealership_name} ===")

    # Check ALL configurations in the database for this dealership
    print(f"\n[1] ALL CONFIGURATIONS FOR '{dealership_name}':")
    all_configs = db_manager.execute_query("""
        SELECT name, filtering_rules, updated_at, created_at, is_active,
               extract(epoch from updated_at) as updated_timestamp,
               extract(epoch from created_at) as created_timestamp
        FROM dealership_configs
        WHERE name = %s
        ORDER BY updated_at DESC NULLS LAST, created_at DESC
    """, (dealership_name,))

    for i, config in enumerate(all_configs):
        print(f"  Config {i+1}:")
        print(f"    Active: {config['is_active']}")
        print(f"    Created: {config['created_at']} (timestamp: {config['created_timestamp']})")
        print(f"    Updated: {config['updated_at']} (timestamp: {config['updated_timestamp']})")

        if isinstance(config['filtering_rules'], str):
            rules = json.loads(config['filtering_rules'])
        else:
            rules = config['filtering_rules']

        print(f"    Rules count: {len(rules)}")
        # Show key filtering rules
        key_rules = ['exclude_missing_stock_number', 'vehicle_types', 'allowed_vehicle_types', 'exclude_status']
        for key in key_rules:
            if key in rules:
                print(f"    {key}: {rules[key]}")
        print()

    # Test the EXACT query used by CAO processing
    print(f"\n[2] EXACT CAO QUERY SIMULATION:")
    print("Query: SELECT filtering_rules FROM dealership_configs WHERE name = %s AND is_active = true ORDER BY updated_at DESC NULLS LAST")

    cao_result = db_manager.execute_query("""
        SELECT filtering_rules, updated_at, created_at,
               extract(epoch from updated_at) as updated_timestamp
        FROM dealership_configs
        WHERE name = %s AND is_active = true
        ORDER BY updated_at DESC NULLS LAST
    """, (dealership_name,))

    if cao_result:
        config = cao_result[0]
        print(f"    Found active config:")
        print(f"    Updated: {config['updated_at']} (timestamp: {config['updated_timestamp']})")

        if isinstance(config['filtering_rules'], str):
            rules = json.loads(config['filtering_rules'])
        else:
            rules = config['filtering_rules']

        print(f"    Rules: {json.dumps(rules, indent=6)}")
        return rules
    else:
        print("    [ERROR] No active config found!")
        return None

def investigate_vin_log_table(dealership_name):
    """Investigate VIN log table name generation and contents"""
    print(f"\n=== VIN LOG INVESTIGATION: {dealership_name} ===")

    # Generate VIN log table name using the same logic as CAO processing
    slug = dealership_name.lower()
    slug = slug.replace(' ', '_')
    slug = slug.replace('&', 'and')
    slug = slug.replace('.', '')
    slug = slug.replace(',', '')
    slug = slug.replace("'", '')
    slug = slug.replace('-', '_')
    slug = slug.replace('/', '_')
    slug = slug.replace('__', '_')
    vin_log_table = f'{slug}_vin_log'

    print(f"[1] VIN LOG TABLE NAME GENERATION:")
    print(f"    Dealership: '{dealership_name}'")
    print(f"    Generated table: '{vin_log_table}'")

    # Check if table exists
    print(f"\n[2] TABLE EXISTENCE CHECK:")
    table_check = db_manager.execute_query("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = %s
    """, (vin_log_table,))

    if table_check:
        print(f"    [OK] Table '{vin_log_table}' EXISTS")

        # Get table contents summary
        print(f"\n[3] VIN LOG CONTENTS:")
        vin_count = db_manager.execute_query(f"""
            SELECT COUNT(*) as total_vins,
                   COUNT(DISTINCT vin) as unique_vins,
                   MIN(created_at) as earliest_entry,
                   MAX(created_at) as latest_entry
            FROM {vin_log_table}
        """)

        if vin_count:
            stats = vin_count[0]
            print(f"    Total entries: {stats['total_vins']}")
            print(f"    Unique VINs: {stats['unique_vins']}")
            print(f"    Earliest entry: {stats['earliest_entry']}")
            print(f"    Latest entry: {stats['latest_entry']}")

        # Show recent VIN log entries
        print(f"\n[4] RECENT VIN LOG ENTRIES (last 10):")
        recent_vins = db_manager.execute_query(f"""
            SELECT vin, vehicle_type, order_date, created_at
            FROM {vin_log_table}
            ORDER BY created_at DESC
            LIMIT 10
        """)

        for vin_entry in recent_vins:
            print(f"    {vin_entry['vin']} | {vin_entry['vehicle_type']} | {vin_entry['order_date']} | {vin_entry['created_at']}")
    else:
        print(f"    [ERROR] Table '{vin_log_table}' DOES NOT EXIST")
        print(f"    This means no VINs have been processed for this dealership yet")

    return vin_log_table

def investigate_vehicle_data_filtering(dealership_name):
    """Investigate the actual vehicle data and filtering logic"""
    print(f"\n=== VEHICLE DATA FILTERING INVESTIGATION: {dealership_name} ===")

    # Check name mapping (dealership config name vs data location name)
    name_mapping = {
        'Dave Sinclair Lincoln South': 'Dave Sinclair Lincoln',
        'BMW of West St. Louis': 'BMW of West St Louis',
        'Columbia Honda': 'Columbia Honda',
        'South County DCJR': 'South County Dodge Chrysler Jeep RAM',
        'Glendale CDJR': 'Glendale Chrysler Jeep Dodge Ram',
        'HW Kia': 'HW Kia of West County'
    }

    actual_location_name = name_mapping.get(dealership_name, dealership_name)
    print(f"[1] NAME MAPPING:")
    print(f"    Config name: '{dealership_name}'")
    print(f"    Data location: '{actual_location_name}'")

    # Check raw vehicle data for this location
    print(f"\n[2] RAW VEHICLE DATA CHECK:")
    vehicle_count = db_manager.execute_query("""
        SELECT COUNT(*) as total_vehicles
        FROM raw_vehicle_data rvd
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE rvd.location = %s AND si.status = 'active'
    """, (actual_location_name,))

    if vehicle_count:
        print(f"    Total vehicles in active import: {vehicle_count[0]['total_vehicles']}")

    # Check normalized vehicle data
    print(f"\n[3] NORMALIZED VEHICLE DATA CHECK:")
    normalized_count = db_manager.execute_query("""
        SELECT COUNT(*) as total_vehicles,
               COUNT(CASE WHEN on_lot_status IN ('onlot', 'on lot') THEN 1 END) as on_lot_vehicles,
               COUNT(CASE WHEN stock IS NOT NULL AND stock != '' AND stock != '*' THEN 1 END) as vehicles_with_stock
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = %s AND si.status = 'active'
    """, (actual_location_name,))

    if normalized_count:
        stats = normalized_count[0]
        print(f"    Total normalized vehicles: {stats['total_vehicles']}")
        print(f"    On-lot vehicles: {stats['on_lot_vehicles']}")
        print(f"    Vehicles with stock numbers: {stats['vehicles_with_stock']}")

    # Test the exact CAO filtering query
    print(f"\n[4] CAO FILTERING SIMULATION:")
    print("Simulating the exact query used in _get_dealership_vehicles()...")

    # Build the query exactly as in the CAO code
    query = """
        SELECT COUNT(*) as filtered_count
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = %s
        AND nvd.on_lot_status IN ('onlot', 'on lot')
        AND si.status = 'active'
        AND nvd.vehicle_condition IN ('new', 'po', 'cpo')
        AND nvd.stock IS NOT NULL AND nvd.stock != '' AND nvd.stock != '*'
    """

    filtered_result = db_manager.execute_query(query, (actual_location_name,))
    if filtered_result:
        print(f"    Vehicles after basic CAO filtering: {filtered_result[0]['filtered_count']}")

    # Sample some vehicles to see what we're working with
    print(f"\n[5] SAMPLE VEHICLES (first 5):")
    sample_vehicles = db_manager.execute_query("""
        SELECT nvd.vin, nvd.stock, nvd.vehicle_condition, nvd.on_lot_status,
               rvd.status as raw_status, nvd.year, nvd.make, nvd.model
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = %s
        AND nvd.on_lot_status IN ('onlot', 'on lot')
        AND si.status = 'active'
        AND nvd.vehicle_condition IN ('new', 'po', 'cpo')
        AND nvd.stock IS NOT NULL AND nvd.stock != '' AND nvd.stock != '*'
        LIMIT 5
    """, (actual_location_name,))

    for vehicle in sample_vehicles:
        print(f"    {vehicle['vin']} | {vehicle['stock']} | {vehicle['vehicle_condition']} | {vehicle['year']} {vehicle['make']} {vehicle['model']}")

def main():
    """Main investigation function"""
    dealership_name = "Auffenberg Hyundai"

    print("=== COMPREHENSIVE CAO PROCESSING INVESTIGATION ===")
    print(f"Target dealership: {dealership_name}")
    print("Investigating config caching, VIN logs, and data filtering...")

    # Step 1: Config investigation
    config = investigate_config_caching(dealership_name)

    # Step 2: VIN log investigation
    vin_log_table = investigate_vin_log_table(dealership_name)

    # Step 3: Vehicle data filtering
    investigate_vehicle_data_filtering(dealership_name)

    print(f"\n=== INVESTIGATION COMPLETE ===")
    print("Check the output above for any discrepancies in:")
    print("1. Configuration timestamps and caching")
    print("2. VIN log table name and contents")
    print("3. Vehicle data filtering results")

if __name__ == "__main__":
    main()