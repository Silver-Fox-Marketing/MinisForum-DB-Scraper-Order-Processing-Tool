import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
os.chdir(os.path.join(os.path.dirname(__file__), 'web_gui'))

from database_connection import db_manager
import json

# Fix Serra Honda O'Fallon config
config = db_manager.execute_query(
    "SELECT * FROM dealership_configs WHERE name = %s",
    ("Serra Honda O'Fallon",),
    fetch='one'
)

if config:
    filtering_rules = config['filtering_rules']

    print("BEFORE:")
    print(f"  exclude_conditions: {filtering_rules.get('exclude_conditions', [])}")

    # Remove po and cpo from exclude_conditions
    filtering_rules['exclude_conditions'] = []

    # Update the database
    db_manager.execute_non_query(
        "UPDATE dealership_configs SET filtering_rules = %s WHERE name = %s",
        (json.dumps(filtering_rules), "Serra Honda O'Fallon")
    )

    print("\nAFTER:")
    print(f"  exclude_conditions: {filtering_rules['exclude_conditions']}")
    print("\n[OK] Updated Serra Honda O'Fallon: removed contradictory exclude_conditions")
else:
    print("No config found for Serra Honda O'Fallon")
