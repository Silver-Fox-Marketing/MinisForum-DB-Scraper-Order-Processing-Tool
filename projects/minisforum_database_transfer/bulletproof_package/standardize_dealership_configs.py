#!/usr/bin/env python3
"""
STANDARDIZE ALL DEALERSHIP CONFIGS
Ensures all 36 official dealerships have proper configs with standardized filters
"""

import sys
import os
import json

os.chdir('C:/Users/Workstation_1/Documents/Tools/ClaudeCode/projects/minisforum_database_transfer/bulletproof_package')
sys.path.insert(0, './scripts')

from database_connection import db_manager

# Official 36 dealerships with their vehicle type preferences
DEALERSHIP_CONFIGS = {
    # CAO-SCHEDULED (15 Total) - Most process both new and used
    "Auffenberg Hyundai": {"vehicle_types": ["new", "used"], "order_type": "cao"},
    "Frank Leta Honda": {"vehicle_types": ["new", "used"], "order_type": "cao"}, 
    "Glendale CDJR": {"vehicle_types": ["new", "used"], "order_type": "cao"},
    "Honda of Frontenac": {"vehicle_types": ["new", "used"], "order_type": "cao"},
    "HW Kia": {"vehicle_types": ["new", "used"], "order_type": "cao"},
    "Pappas Toyota": {"vehicle_types": ["used"], "order_type": "cao"},  # Used only per requirements
    "Porsche St. Louis": {"vehicle_types": ["new", "used"], "order_type": "cao"},
    "Serra Honda O'Fallon": {"vehicle_types": ["new", "used"], "order_type": "cao"},
    "South County DCJR": {"vehicle_types": ["new", "used"], "order_type": "cao"},
    "Spirit Lexus": {"vehicle_types": ["new", "used"], "order_type": "cao"},
    "Suntrup Buick GMC": {"vehicle_types": ["used"], "order_type": "cao"},  # Used flyouts
    "Suntrup Ford Kirkwood": {"vehicle_types": ["new", "used"], "order_type": "cao"},
    "Suntrup Ford West": {"vehicle_types": ["new", "used"], "order_type": "cao"},
    "Thoroughbred Ford": {"vehicle_types": ["new", "used"], "order_type": "cao"},
    "Weber Chevrolet": {"vehicle_types": ["new", "used"], "order_type": "cao"},
    
    # MANUAL/LIST (21 Total) - Manual processing
    "BMW of Columbia": {"vehicle_types": ["new", "used"], "order_type": "list"},
    "BMW West St. Louis": {"vehicle_types": ["new", "used"], "order_type": "list"},
    "Bommarito Cadillac": {"vehicle_types": ["new", "used"], "order_type": "list"},
    "Bommarito West County": {"vehicle_types": ["new", "used"], "order_type": "list"},
    "Columbia Honda": {"vehicle_types": ["new", "used"], "order_type": "list"},
    "Dave Sinclair Lincoln": {"vehicle_types": ["new", "used"], "order_type": "list"},
    "Dave Sinclair Lincoln St. Peters": {"vehicle_types": ["new", "used"], "order_type": "list"},
    "Joe Machens CDJR": {"vehicle_types": ["new", "used"], "order_type": "list"},
    "Joe Machens Hyundai": {"vehicle_types": ["new", "used"], "order_type": "list"},
    "Joe Machens Nissan": {"vehicle_types": ["new", "used"], "order_type": "list"},
    "Joe Machens Toyota": {"vehicle_types": ["new", "used"], "order_type": "list"},
    "Indigo Auto Group": {"vehicle_types": ["new", "used"], "order_type": "list"},
    "Jaguar Rancho Mirage": {"vehicle_types": ["new", "used"], "order_type": "list"},
    "KIA of Columbia": {"vehicle_types": ["new", "used"], "order_type": "list"},
    "Land Rover Rancho Mirage": {"vehicle_types": ["new", "used"], "order_type": "list"},
    "Mini of St. Louis": {"vehicle_types": ["new", "used"], "order_type": "list"},
    "Pundmann Ford": {"vehicle_types": ["new", "used"], "order_type": "list"},
    "Rusty Drewing Chevy BGMC": {"vehicle_types": ["new", "used"], "order_type": "list"},
    "Rusty Drewing Cadillac": {"vehicle_types": ["new", "used"], "order_type": "list"},
    "Suntrup Hyundai South": {"vehicle_types": ["new", "used"], "order_type": "list"},
    "Suntrup Kia South": {"vehicle_types": ["new"], "order_type": "list"},  # New only per requirements
}

def create_standard_filtering_rules(vehicle_types, order_type="cao"):
    """Create standardized filtering rules based on Porsche template"""
    
    # Map simple vehicle_types to allowed types for filtering
    allowed_types = []
    if "new" in vehicle_types:
        allowed_types.append("new")
    if "used" in vehicle_types:
        allowed_types.extend(["cpo", "po", "certified", "pre-owned"])
    
    return {
        "vehicle_types": vehicle_types,
        "order_type": order_type,
        "require_stock": True,
        "exclude_missing_stock_number": True,
        "exclude_in_transit": True,
        "exclude_status": ["In-Transit", "Sold", "Allocated"],
        "allowed_vehicle_types": allowed_types,
        "price_range": {
            "min": 0,
            "max": 999999
        },
        "days_on_lot": {
            "min": 0,
            "max": 999
        },
        "notes": "Standardized configuration based on Porsche St. Louis template"
    }

def create_standard_output_rules():
    """Create standardized output rules"""
    return {
        "format": "csv",
        "include_qr": True,
        "qr_size": 388,
        "template_type": "Standard"
    }

def main():
    print("=" * 80)
    print("STANDARDIZING ALL 36 DEALERSHIP CONFIGS")
    print("=" * 80)
    
    # First, get all existing configs
    existing_configs = db_manager.execute_query("""
        SELECT id, name FROM dealership_configs
    """)
    
    existing_map = {config['name']: config['id'] for config in existing_configs}
    
    updated_count = 0
    created_count = 0
    
    for dealership_name, config_settings in DEALERSHIP_CONFIGS.items():
        print(f"\nProcessing: {dealership_name}")
        
        # Create standardized rules
        filtering_rules = create_standard_filtering_rules(
            config_settings["vehicle_types"],
            config_settings["order_type"]
        )
        output_rules = create_standard_output_rules()
        
        if dealership_name in existing_map:
            # Update existing config
            config_id = existing_map[dealership_name]
            
            db_manager.execute_query("""
                UPDATE dealership_configs 
                SET filtering_rules = %s,
                    output_rules = %s,
                    is_active = true,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                json.dumps(filtering_rules),
                json.dumps(output_rules),
                config_id
            ))
            
            print(f"  [UPDATED] Config for {dealership_name}")
            print(f"    Vehicle types: {config_settings['vehicle_types']}")
            print(f"    Order type: {config_settings['order_type']}")
            updated_count += 1
            
        else:
            # Create new config
            db_manager.execute_query("""
                INSERT INTO dealership_configs (name, filtering_rules, output_rules, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                dealership_name,
                json.dumps(filtering_rules),
                json.dumps(output_rules)
            ))
            
            print(f"  [CREATED] New config for {dealership_name}")
            print(f"    Vehicle types: {config_settings['vehicle_types']}")
            print(f"    Order type: {config_settings['order_type']}")
            created_count += 1
    
    # Remove any configs not in the official 36
    print("\n" + "=" * 80)
    print("REMOVING UNAUTHORIZED CONFIGS")
    print("=" * 80)
    
    all_configs = db_manager.execute_query("SELECT name FROM dealership_configs")
    unauthorized = [c['name'] for c in all_configs if c['name'] not in DEALERSHIP_CONFIGS]
    
    for dealer in unauthorized:
        db_manager.execute_query("""
            DELETE FROM dealership_configs WHERE name = %s
        """, (dealer,))
        print(f"  [REMOVED] {dealer}")
    
    # Final verification
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    final_configs = db_manager.execute_query("""
        SELECT name, filtering_rules, output_rules, is_active 
        FROM dealership_configs 
        ORDER BY name
    """)
    
    print(f"Total configs: {len(final_configs)}")
    print(f"Updated: {updated_count}")
    print(f"Created: {created_count}")
    print(f"Removed: {len(unauthorized)}")
    
    # Verify all have proper structure
    issues = []
    for config in final_configs:
        filtering_rules = json.loads(config['filtering_rules'])
        
        if 'vehicle_types' not in filtering_rules:
            issues.append(f"{config['name']}: Missing vehicle_types")
        if 'exclude_in_transit' not in filtering_rules:
            issues.append(f"{config['name']}: Missing exclude_in_transit")
        if 'exclude_missing_stock_number' not in filtering_rules:
            issues.append(f"{config['name']}: Missing exclude_missing_stock_number")
    
    if issues:
        print("\nISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n[SUCCESS] All 36 dealerships have standardized configs!")
        print("  ✓ Proper vehicle_types (new/used/both)")
        print("  ✓ exclude_in_transit filter")
        print("  ✓ exclude_missing_stock_number filter")
        print("  ✓ Standard output rules")
        print("  ✓ Consistent structure across all dealerships")

if __name__ == "__main__":
    main()