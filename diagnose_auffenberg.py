"""
Diagnostic script for Auffenberg Hyundai maintenance order issue
"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
os.chdir(os.path.join(os.path.dirname(__file__), 'web_gui'))

from database_connection import db_manager

print("=" * 80)
print("AUFFENBERG HYUNDAI MAINTENANCE ORDER DIAGNOSTIC")
print("=" * 80)
print()

# 1. Check dealership configuration
print("1. DEALERSHIP CONFIGURATION")
print("-" * 80)
config = db_manager.execute_query(
    "SELECT * FROM dealership_configs WHERE name = %s",
    ('Auffenberg Hyundai',),
    fetch='one'
)
if config:
    print(f"  Dealership Name: {config['name']}")
    print(f"  Filtering Rules: {config.get('filtering_rules', 'N/A')}")
    print(f"  Output Rules: {config.get('output_rules', 'N/A')}")
    print(f"  QR Code Path: {config.get('qr_output_path', 'N/A')}")
    print(f"  Is Active: {config.get('is_active', 'N/A')}")
else:
    print("  [ERROR] No configuration found for Auffenberg Hyundai!")
print()

# 2. Check active scraper import
print("2. ACTIVE SCRAPER IMPORT")
print("-" * 80)
active_import = db_manager.execute_query("""
    SELECT import_id, import_date, dealership_name, status, row_count
    FROM scraper_imports
    WHERE dealership_name = 'Auffenberg Hyundai'
    AND status = 'active'
    ORDER BY import_date DESC
    LIMIT 1
""", fetch='one')
if active_import:
    print(f"  Import ID: {active_import['import_id']}")
    print(f"  Import Date: {active_import['import_date']}")
    print(f"  Status: {active_import['status']}")
    print(f"  Row Count: {active_import['row_count']}")
else:
    print("  [ERROR] No active import found for Auffenberg Hyundai!")
print()

# 3. Check raw vehicle data count
print("3. RAW VEHICLE DATA (Active Import)")
print("-" * 80)
if active_import:
    raw_count = db_manager.execute_query("""
        SELECT COUNT(*) as count
        FROM raw_vehicle_data
        WHERE location = 'Auffenberg Hyundai'
        AND import_id = %s
    """, (active_import['import_id'],), fetch='one')
    if raw_count:
        print(f"  Total vehicles in active import: {raw_count['count']}")

    # Check by condition
    by_condition = db_manager.execute_query("""
        SELECT vehicle_condition, COUNT(*) as count
        FROM raw_vehicle_data
        WHERE location = 'Auffenberg Hyundai'
        AND import_id = %s
        GROUP BY vehicle_condition
    """, (active_import['import_id'],))
    print(f"  Breakdown by condition:")
    for row in by_condition:
        print(f"    - {row['vehicle_condition']}: {row['count']}")
else:
    print("  [SKIPPED] No active import to check")
print()

# 4. Check VIN log
print("4. VIN LOG STATUS")
print("-" * 80)
vin_log_count = db_manager.execute_query(
    "SELECT COUNT(*) as count FROM auffenberg_hyundai_vin_log",
    fetch='one'
)
if vin_log_count:
    print(f"  Total VINs in log: {vin_log_count['count']}")

# Recent VINs
recent_vins = db_manager.execute_query("""
    SELECT vin, order_date, order_type, template_type
    FROM auffenberg_hyundai_vin_log
    ORDER BY order_date DESC
    LIMIT 5
""")
print(f"  Recent 5 VINs in log:")
for row in recent_vins:
    print(f"    - {row['vin']} | {row['order_date']} | {row['order_type']} | {row['template_type']}")
print()

# 5. Test maintenance order query
print("5. MAINTENANCE ORDER QUERY TEST")
print("-" * 80)
if active_import and config:
    print("  Testing maintenance order logic...")

    # Get vehicle types from config
    import json
    filtering_rules = config.get('filtering_rules', {})
    if isinstance(filtering_rules, str):
        filtering_rules = json.loads(filtering_rules)

    vehicle_types = filtering_rules.get('vehicle_types', [])
    if isinstance(vehicle_types, str):
        try:
            vehicle_types = json.loads(vehicle_types)
        except:
            vehicle_types = [vehicle_types]

    print(f"  Configured vehicle types: {vehicle_types}")

    # Build condition list for SQL
    if 'used' in vehicle_types:
        conditions = ['used', 'po', 'cpo', 'certified', 'pre-owned']
    elif 'new' in vehicle_types:
        conditions = ['new']
    else:
        conditions = vehicle_types

    print(f"  SQL conditions to check: {conditions}")

    # Test the actual maintenance query
    maintenance_query = """
        SELECT COUNT(*) as count
        FROM raw_vehicle_data rvd
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE rvd.location = %s
        AND si.status = 'active'
        AND rvd.vehicle_condition = ANY(%s)
        AND rvd.vin IN (
            SELECT vin FROM auffenberg_hyundai_vin_log
            WHERE order_type = 'cao'
        )
    """

    maintenance_count = db_manager.execute_query(
        maintenance_query,
        ('Auffenberg Hyundai', conditions),
        fetch='one'
    )

    if maintenance_count:
        print(f"  [RESULT] Vehicles matching maintenance criteria: {maintenance_count['count']}")

    # Also check CAO query (what worked yesterday)
    cao_query = """
        SELECT COUNT(*) as count
        FROM raw_vehicle_data rvd
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE rvd.location = %s
        AND si.status = 'active'
        AND rvd.vehicle_condition = ANY(%s)
        AND rvd.vin NOT IN (
            SELECT vin FROM auffenberg_hyundai_vin_log
        )
    """

    cao_count = db_manager.execute_query(
        cao_query,
        ('Auffenberg Hyundai', conditions),
        fetch='one'
    )

    if cao_count:
        print(f"  [COMPARISON] CAO query result (NOT IN log): {cao_count['count']}")
else:
    print("  [SKIPPED] Missing active import or config")
print()

print("=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
