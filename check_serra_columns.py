import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
os.chdir(os.path.join(os.path.dirname(__file__), 'web_gui'))

from database_connection import db_manager

# Get one record to see all columns
result = db_manager.execute_query(
    "SELECT * FROM raw_vehicle_data WHERE location = %s AND import_id = 87 LIMIT 1",
    ("Serra Honda O'Fallon",)
)

if result:
    print("Columns in raw_vehicle_data for Serra Honda O'Fallon:")
    print("=" * 80)
    for key, value in result[0].items():
        print(f"  {key:30} = {value}")

    print("\n" + "=" * 80)
    print("\nNow checking DISTINCT values for key fields:")
    print("=" * 80)

    # Check type field
    types = db_manager.execute_query("""
        SELECT type, COUNT(*) as count
        FROM raw_vehicle_data
        WHERE location = %s AND import_id = 87
        GROUP BY type
        ORDER BY count DESC
    """, ("Serra Honda O'Fallon",))

    print("\ntype values:")
    for row in types:
        print(f"  - '{row['type']}': {row['count']}")

    # Check how many are NOT in vin log
    not_in_log = db_manager.execute_query("""
        SELECT COUNT(*) as count
        FROM raw_vehicle_data
        WHERE location = %s AND import_id = 87
        AND vin NOT IN (SELECT vin FROM serra_honda_ofallon_vin_log)
    """, ("Serra Honda O'Fallon",), fetch='one')

    print(f"\nVehicles NOT in VIN log: {not_in_log['count']}")
else:
    print("No data found for Serra Honda O'Fallon in import 87")
