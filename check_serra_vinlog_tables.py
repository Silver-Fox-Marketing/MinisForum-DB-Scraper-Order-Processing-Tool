"""
Check what VIN log tables exist for Serra dealerships
"""
import sys
sys.path.insert(0, r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts')

from database_connection import db_manager

# Get all VIN log tables
query = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name LIKE '%serra%vin_log%'
    ORDER BY table_name
"""

results = db_manager.execute_query(query)

print("\nSerra VIN Log Tables Found:")
print("="*60)
if results:
    for row in results:
        print(f"  - {row['table_name']}")
else:
    print("  [NONE FOUND]")

# Also check Serra dealership configs
print("\n\nSerra Dealership Configs:")
print("="*60)

config_query = """
    SELECT name, filtering_rules
    FROM dealership_configs
    WHERE name LIKE '%Serra%'
    ORDER BY name
"""

configs = db_manager.execute_query(config_query)
if configs:
    for config in configs:
        print(f"\n  Dealership: {config['name']}")
        print(f"    Filtering Rules: {config['filtering_rules']}")

        # Generate expected VIN log table name
        table_name = config['name'].lower().replace(' ', '_').replace("'", '') + '_vin_log'
        print(f"    Expected VIN Log Table: {table_name}")
else:
    print("  [NONE FOUND]")

# Check what location names exist in raw_vehicle_data for Serra
print("\n\nSerra Locations in raw_vehicle_data (active import):")
print("="*60)

location_query = """
    SELECT DISTINCT rvd.location
    FROM raw_vehicle_data rvd
    JOIN scraper_imports si ON rvd.import_id = si.import_id
    WHERE rvd.location LIKE '%Serra%'
    AND si.status = 'active'
    ORDER BY rvd.location
"""

locations = db_manager.execute_query(location_query)
if locations:
    for loc in locations:
        print(f"  - {loc['location']}")
        table_name = loc['location'].lower().replace(' ', '_').replace("'", '') + '_vin_log'
        print(f"    -> VIN log would be: {table_name}")
else:
    print("  [NONE FOUND]")
