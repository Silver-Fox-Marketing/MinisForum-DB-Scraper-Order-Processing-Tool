#!/usr/bin/env python3
"""
Debug script to check South County DCJR configuration
"""

import sys
import json
from pathlib import Path

# Add the scripts directory to Python path
scripts_dir = Path(__file__).parent / 'projects/minisforum_database_transfer/bulletproof_package/scripts'
sys.path.insert(0, str(scripts_dir))

from database_connection import db_manager

def check_dealership_config(dealership_name):
    """Check a specific dealership's configuration"""
    # First check schema
    schema = db_manager.execute_query("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'dealership_configs'
        ORDER BY ordinal_position
    """)
    print(f'Dealership configs table columns: {[col["column_name"] for col in schema]}')

    config = db_manager.execute_query("""
        SELECT name, output_rules
        FROM dealership_configs
        WHERE name = %s AND is_active = true
        ORDER BY updated_at DESC NULLS LAST
        LIMIT 1
    """, (dealership_name,))

    print(f'=== {dealership_name.upper()} CONFIG ===')
    if config:
        config = config[0]
        print(f'Name: {config["name"]}')
        if config['output_rules']:
            try:
                rules = json.loads(config['output_rules']) if isinstance(config['output_rules'], str) else config['output_rules']
                print(f'Output Rules: {json.dumps(rules, indent=2)}')
            except Exception as e:
                print(f'Output Rules (raw): {config["output_rules"]}')
                print(f'JSON parse error: {e}')
        else:
            print('Output Rules: None')
    else:
        print(f'No config found for {dealership_name}')
    print()

def check_south_county_raw_data():
    """Check if South County DCJR has vehicle data"""
    vehicles = db_manager.execute_query("""
        SELECT COUNT(*) as count, location
        FROM raw_vehicle_data rvd
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE si.status = 'active'
        AND (location = 'South County DCJR' OR location = 'South County Dodge Chrysler Jeep RAM')
        GROUP BY location
    """)

    print('=== SOUTH COUNTY RAW VEHICLE DATA ===')
    if vehicles:
        for vehicle in vehicles:
            print(f'Location: {vehicle["location"]}, Count: {vehicle["count"]}')
    else:
        print('No active vehicle data found for South County DCJR')
    print()

def check_vin_log_table():
    """Check if South County DCJR VIN log table exists"""
    try:
        # Check if table exists
        table_check = db_manager.execute_query("""
            SELECT COUNT(*) as count
            FROM information_schema.tables
            WHERE table_name = 'south_county_dcjr_vin_log'
        """)

        print('=== SOUTH COUNTY VIN LOG TABLE ===')
        if table_check and table_check[0]['count'] > 0:
            print('south_county_dcjr_vin_log table exists')

            # Check VIN count
            vin_count = db_manager.execute_query("""
                SELECT COUNT(*) as count FROM south_county_dcjr_vin_log
            """)
            print(f'VIN log entries: {vin_count[0]["count"] if vin_count else 0}')
        else:
            print('south_county_dcjr_vin_log table does NOT exist')
    except Exception as e:
        print(f'Error checking VIN log table: {e}')
    print()

if __name__ == '__main__':
    print("DEBUGGING SOUTH COUNTY DCJR CONFIGURATION")
    print("=" * 50)

    # Check South County DCJR config
    check_dealership_config('South County DCJR')

    # Compare with working dealership
    check_dealership_config('Thoroughbred Ford')

    # Check raw vehicle data
    check_south_county_raw_data()

    # Check VIN log table
    check_vin_log_table()