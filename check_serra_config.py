import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
os.chdir(os.path.join(os.path.dirname(__file__), 'web_gui'))

from database_connection import db_manager
import json

# Check Serra Honda O'Fallon config
config = db_manager.execute_query(
    "SELECT name, filtering_rules FROM dealership_configs WHERE name = %s",
    ("Serra Honda O'Fallon",),
    fetch='one'
)

if config:
    print("Serra Honda filtering_rules:")
    print(json.dumps(config['filtering_rules'], indent=2))

    # Check for contradictory settings
    rules = config['filtering_rules']
    vehicle_types = rules.get('vehicle_types', [])
    exclude_conditions = rules.get('exclude_conditions', [])

    print("\nAnalysis:")
    print(f"  vehicle_types: {vehicle_types}")
    print(f"  exclude_conditions: {exclude_conditions}")

    if 'used' in vehicle_types:
        print("\n  [INFO] 'used' in vehicle_types means system will look for:")
        print("         ['used', 'po', 'cpo', 'certified', 'pre-owned']")

        problematic = []
        if 'po' in exclude_conditions:
            problematic.append('po')
        if 'cpo' in exclude_conditions:
            problematic.append('cpo')
        if 'certified' in exclude_conditions:
            problematic.append('certified')
        if 'pre-owned' in exclude_conditions:
            problematic.append('pre-owned')

        if problematic:
            print(f"\n  [ISSUE] exclude_conditions blocks: {problematic}")
            print(f"  This contradicts 'used' in vehicle_types!")
            print(f"  FIX: Remove {problematic} from exclude_conditions")
        else:
            print("\n  [OK] No contradictory exclude_conditions")
else:
    print("No config found for Serra Honda")
