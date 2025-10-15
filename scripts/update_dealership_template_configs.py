"""
Update dealership configurations to include template type settings for SHORTCUTS vs SHORTCUT PACKS.

Based on business requirements:
- Porsche: SHORTCUTS for both new and used
- Volvo Cars West County: SHORTCUTS for both new and used
- CDJR of Columbia: SHORTCUTS for new, SHORTCUT PACKS for used
- All others: Default to SHORTCUT PACKS for both
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.database_connection import db_manager

def update_dealership_template_configs():
    """Update dealership configs with template type settings."""

    print("=== UPDATING DEALERSHIP TEMPLATE CONFIGURATIONS ===")

    # Define template configurations for specific dealerships
    template_configs = {
        'Porsche St. Louis': {
            'template_types': {
                'new': 'shortcut',
                'used': 'shortcut',
                'default': 'shortcut'
            }
        },
        'Volvo Cars West County': {
            'template_types': {
                'new': 'shortcut',
                'used': 'shortcut',
                'default': 'shortcut'
            }
        },
        'CDJR of Columbia': {
            'template_types': {
                'new': 'shortcut',
                'used': 'shortcut_pack',
                'default': 'shortcut_pack'
            }
        }
    }

    # Update each dealership's configuration
    for dealership_name, template_config in template_configs.items():
        print(f"\nUpdating {dealership_name}...")

        # First, check if dealership config exists
        existing_config = db_manager.execute_query("""
            SELECT id, name, output_rules
            FROM dealership_configs
            WHERE name = %s
        """, (dealership_name,))

        if existing_config:
            # Update existing config
            config_id = existing_config[0]['id']
            current_output_rules = existing_config[0]['output_rules'] or {}

            if isinstance(current_output_rules, str):
                current_output_rules = json.loads(current_output_rules)

            # Merge template config into output_rules
            current_output_rules.update(template_config)

            # Update the database
            result = db_manager.execute_query("""
                UPDATE dealership_configs
                SET output_rules = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, name
            """, (json.dumps(current_output_rules), config_id))

            if result:
                print(f"  [OK] Updated {dealership_name} with template configuration")
                print(f"       New: {template_config['template_types']['new']}")
                print(f"       Used: {template_config['template_types']['used']}")
            else:
                print(f"  [ERROR] Failed to update {dealership_name}")
        else:
            print(f"  [WARNING] {dealership_name} not found in dealership_configs table")
            print(f"           Creating new configuration...")

            # Create new config with template settings
            output_rules = template_config
            filtering_rules = {
                'vehicle_types': ['new', 'used'],
                'notes': f'Auto-created config for {dealership_name}'
            }

            result = db_manager.execute_query("""
                INSERT INTO dealership_configs
                (name, filtering_rules, output_rules, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id, name
            """, (
                dealership_name,
                json.dumps(filtering_rules),
                json.dumps(output_rules)
            ))

            if result:
                print(f"  [OK] Created configuration for {dealership_name}")
                print(f"       New: {template_config['template_types']['new']}")
                print(f"       Used: {template_config['template_types']['used']}")
            else:
                print(f"  [ERROR] Failed to create config for {dealership_name}")

    # Set default template type for all other dealerships (shortcut_pack)
    print("\n\nUpdating all other dealerships to default SHORTCUT PACKS...")

    # Get all dealerships without template_types in their output_rules
    other_dealerships = db_manager.execute_query("""
        SELECT id, name, output_rules
        FROM dealership_configs
        WHERE name NOT IN %s
        AND is_active = true
    """, (tuple(template_configs.keys()),))

    for dealership in other_dealerships:
        output_rules = dealership['output_rules'] or {}
        if isinstance(output_rules, str):
            output_rules = json.loads(output_rules)

        # Only update if template_types not already set
        if 'template_types' not in output_rules:
            output_rules['template_types'] = {
                'new': 'shortcut_pack',
                'used': 'shortcut_pack',
                'default': 'shortcut_pack'
            }

            result = db_manager.execute_query("""
                UPDATE dealership_configs
                SET output_rules = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING name
            """, (json.dumps(output_rules), dealership['id']))

            if result:
                print(f"  [OK] Set default template type for {dealership['name']}")

    print("\n=== TEMPLATE CONFIGURATION UPDATE COMPLETE ===")

    # Verify the updates
    print("\n=== VERIFICATION ===")
    all_configs = db_manager.execute_query("""
        SELECT name, output_rules
        FROM dealership_configs
        WHERE is_active = true
        ORDER BY name
    """)

    for config in all_configs:
        output_rules = config['output_rules'] or {}
        if isinstance(output_rules, str):
            output_rules = json.loads(output_rules)

        if 'template_types' in output_rules:
            template_types = output_rules['template_types']
            print(f"{config['name']}: New={template_types.get('new', 'N/A')}, Used={template_types.get('used', 'N/A')}")

if __name__ == "__main__":
    update_dealership_template_configs()