import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
os.chdir(os.path.join(os.path.dirname(__file__), 'web_gui'))

from database_connection import db_manager
import json

# Get Serra config
config = db_manager.execute_query(
    "SELECT filtering_rules FROM dealership_configs WHERE name = %s",
    ("Serra Honda O'Fallon",),
    fetch='one'
)

if config:
    print("Current Serra Honda O'Fallon exclude_conditions:")
    print(config['filtering_rules']['exclude_conditions'])
    print()

    if config['filtering_rules']['exclude_conditions'] == ['po', 'cpo']:
        print("[ISSUE] The fix did not persist or was reverted")
        print("Re-applying fix now...")

        filtering_rules = config['filtering_rules']
        filtering_rules['exclude_conditions'] = []

        db_manager.execute_non_query(
            "UPDATE dealership_configs SET filtering_rules = %s WHERE name = %s",
            (json.dumps(filtering_rules), "Serra Honda O'Fallon")
        )

        print("[FIXED] Updated exclude_conditions to []")
    elif config['filtering_rules']['exclude_conditions'] == []:
        print("[OK] exclude_conditions is already []")
    else:
        print(f"[UNEXPECTED] exclude_conditions is: {config['filtering_rules']['exclude_conditions']}")
