import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
os.chdir(os.path.join(os.path.dirname(__file__), 'web_gui'))

from database_connection import db_manager
import json

dealership = "Serra Honda O'Fallon"
actual_location = "Serra Honda O'Fallon"  # Location name in raw data

print("=" * 80)
print(f"MAINTENANCE ORDER ANALYSIS: {dealership}")
print("=" * 80)
print()

# 1. Check active scraper import
print("1. ACTIVE SCRAPER DATA")
print("-" * 80)
active_import = db_manager.execute_query("""
    SELECT import_id, import_date, total_vehicles
    FROM scraper_imports
    WHERE %s = ANY(dealerships_list)
    AND status = 'active'
    ORDER BY import_date DESC
    LIMIT 1
""", (dealership,), fetch='one')

if active_import:
    print(f"  Active Import ID: {active_import['import_id']}")
    print(f"  Import Date: {active_import['import_date']}")
    print(f"  Total Vehicles: {active_import['total_vehicles']}")

    # Count vehicles in active import
    vehicle_count = db_manager.execute_query("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN type IN ('new') THEN 1 END) as new_count,
            COUNT(CASE WHEN type IN ('used', 'po', 'cpo', 'certified', 'pre-owned') THEN 1 END) as used_count
        FROM raw_vehicle_data
        WHERE location = %s
        AND import_id = %s
    """, (actual_location, active_import['import_id']), fetch='one')

    if vehicle_count:
        print(f"\n  Total vehicles in active import for Serra Honda: {vehicle_count['total']}")
        print(f"    NEW vehicles: {vehicle_count['new_count']}")
        print(f"    USED vehicles (including po/cpo): {vehicle_count['used_count']}")
else:
    print("  [ERROR] No active import found!")
print()

# 2. Check VIN log
print("2. VIN LOG STATUS")
print("-" * 80)
vin_log_count = db_manager.execute_query(
    "SELECT COUNT(*) as count FROM serra_honda_ofallon_vin_log",
    fetch='one'
)
print(f"  Total VINs in log: {vin_log_count['count']}")

# Count by order type
vin_log_breakdown = db_manager.execute_query("""
    SELECT order_type, COUNT(*) as count
    FROM serra_honda_ofallon_vin_log
    GROUP BY order_type
""")
print(f"  Breakdown by order type:")
for row in vin_log_breakdown:
    print(f"    - {row['order_type']}: {row['count']}")
print()

# 3. CAO query simulation (what maintenance order CAO portion does)
print("3. CAO PORTION (vehicles NOT in VIN log)")
print("-" * 80)
cao_count = None
if active_import:
    cao_count = db_manager.execute_query("""
        SELECT COUNT(*) as count
        FROM raw_vehicle_data rvd
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE rvd.location = %s
        AND si.status = 'active'
        AND rvd.type IN ('new', 'used', 'po', 'cpo', 'certified', 'pre-owned')
        AND rvd.vin NOT IN (SELECT vin FROM serra_honda_ofallon_vin_log)
    """, (actual_location,), fetch='one')

    if cao_count:
        print(f"  CAO would return: {cao_count['count']} vehicles")
        print(f"  (Vehicles in active import NOT in VIN log)")
else:
    print("  [SKIPPED] No active import")
print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print("For a maintenance order:")
print("  - CAO portion finds vehicles not yet processed (from active scraper data)")
print("  - LIST portion should only process VINs that:")
print("    1. Are in the provided list")
print("    2. Are in active scraper data")
print("    3. Were previously processed (in VIN log)")
print()
if active_import and cao_count:
    print(f"If you got 81 VINs total, this is likely from:")
    print(f"  - CAO: {cao_count['count']} vehicles (new vehicles not in VIN log)")
    print(f"  - Plus any LIST VINs that match all 3 criteria")
else:
    print("Analysis incomplete - check active import status")
