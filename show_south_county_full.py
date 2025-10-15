import sys
import os
import json

script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
sys.path.insert(0, script_dir)

from database_connection import db_manager

result = db_manager.execute_query("SELECT filtering_rules FROM dealership_configs WHERE name = 'South County DCJR'")
config = result[0]['filtering_rules'] if result else {}

print('=' * 80)
print('FULL South County DCJR filtering_rules CONFIG')
print('=' * 80)
print(json.dumps(config, indent=2, sort_keys=True))
print('\n' + '=' * 80)
print('ALL FIELDS (alphabetical):')
print('=' * 80)
for key in sorted(config.keys()):
    print(f'{key}: {config[key]}')
