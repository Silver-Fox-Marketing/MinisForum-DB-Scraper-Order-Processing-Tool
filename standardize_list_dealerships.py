"""
Standardize all List order type dealerships to match South County DCJR template
- Ensures all have the same fields/structure
- Preserves their individual vehicle_types settings
"""

import sys
import os
import json

script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
sys.path.insert(0, script_dir)

from database_connection import db_manager

def standardize_list_dealerships():
    """Standardize List dealership configs based on South County DCJR template"""

    print("=" * 80)
    print("STANDARDIZING LIST DEALERSHIP CONFIGS")
    print("=" * 80)

    # Get South County DCJR as template
    template_result = db_manager.execute_query("""
        SELECT filtering_rules, output_rules
        FROM dealership_configs
        WHERE name = 'South County DCJR'
    """)

    if not template_result:
        print("[ERROR] South County DCJR template not found!")
        return False

    template_filters = template_result[0]['filtering_rules']
    template_output = template_result[0]['output_rules']

    print(f"\n[TEMPLATE] South County DCJR filtering_rules:")
    print(json.dumps(template_filters, indent=2))
    print(f"\n[TEMPLATE] South County DCJR output_rules:")
    print(json.dumps(template_output, indent=2))

    # Get all List dealerships
    list_dealerships = db_manager.execute_query("""
        SELECT name, filtering_rules, output_rules
        FROM dealership_configs
        WHERE filtering_rules->>'order_type' = 'list'
        ORDER BY name
    """)

    print(f"\n\n[INFO] Found {len(list_dealerships)} List dealerships")
    print("=" * 80)

    updated_count = 0
    skipped_count = 0

    for dealership in list_dealerships:
        name = dealership['name']
        current_filters = dealership['filtering_rules']
        current_output = dealership['output_rules']

        print(f"\n[PROCESSING] {name}")
        print("-" * 80)

        # Create new filtering_rules with all fields from template
        new_filters = {
            "order_type": "list",  # Keep as list, not cao
            "require_stock": template_filters.get('require_stock', True),
            "vehicle_types": current_filters.get('vehicle_types', ['new', 'used']),  # PRESERVE their setting
            "exclude_conditions": template_filters.get('exclude_conditions', []),
            "allowed_vehicle_types": current_filters.get('allowed_vehicle_types', ['new', 'used']),  # PRESERVE their setting
            "exclude_missing_price": template_filters.get('exclude_missing_price', False),
            "exclude_missing_stock": template_filters.get('exclude_missing_stock', True)
        }

        # Create new output_rules with all fields from template
        # Preserve their custom templates if they have them
        new_output = {
            "price_markup": current_output.get('price_markup', template_output.get('price_markup', 0)),
            "custom_templates": current_output.get('custom_templates', template_output.get('custom_templates', {})),
            "template_variant": current_output.get('template_variant', template_output.get('template_variant', 'standard'))
        }

        # Check if update is needed
        filters_changed = json.dumps(current_filters, sort_keys=True) != json.dumps(new_filters, sort_keys=True)
        output_changed = json.dumps(current_output, sort_keys=True) != json.dumps(new_output, sort_keys=True)

        if filters_changed or output_changed:
            print(f"   [UPDATE NEEDED]")

            if filters_changed:
                print(f"   OLD filtering_rules: {json.dumps(current_filters, sort_keys=True)}")
                print(f"   NEW filtering_rules: {json.dumps(new_filters, sort_keys=True)}")

            if output_changed:
                print(f"   OLD output_rules: {json.dumps(current_output, sort_keys=True)}")
                print(f"   NEW output_rules: {json.dumps(new_output, sort_keys=True)}")

            # Update the database
            update_query = """
                UPDATE dealership_configs
                SET filtering_rules = %s,
                    output_rules = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE name = %s
            """

            db_manager.execute_query(
                update_query,
                (json.dumps(new_filters), json.dumps(new_output), name)
            )

            print(f"   [OK] Updated {name}")
            updated_count += 1
        else:
            print(f"   [SKIP] Already has correct template structure")
            skipped_count += 1

    print("\n" + "=" * 80)
    print(f"STANDARDIZATION COMPLETE")
    print(f"  Updated: {updated_count}")
    print(f"  Skipped (already correct): {skipped_count}")
    print(f"  Total: {len(list_dealerships)}")
    print("=" * 80)

    return True

if __name__ == "__main__":
    success = standardize_list_dealerships()

    if success:
        print(f"\n[SUCCESS] List dealership standardization completed!")
    else:
        print(f"\n[ERROR] List dealership standardization failed!")
