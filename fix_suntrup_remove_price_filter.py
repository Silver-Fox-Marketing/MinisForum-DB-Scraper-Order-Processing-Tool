#!/usr/bin/env python3
"""
Remove price filtering from Suntrup Kia South dealership config
Only Glendale should have price filtering logic
"""

import sys
import os
sys.path.append('C:\\Users\\Workstation_1\\Documents\\Tools\\ClaudeCode\\projects\\minisforum_database_transfer\\bulletproof_package')
sys.path.append('C:\\Users\\Workstation_1\\Documents\\Tools\\ClaudeCode\\projects\\minisforum_database_transfer\\bulletproof_package\\scripts')

from database_connection import db_manager
import json

def remove_price_filtering():
    """Remove price filtering from Suntrup Kia South config"""
    
    try:
        # Get current config
        result = db_manager.execute_query("""
            SELECT filtering_rules 
            FROM dealership_configs 
            WHERE name = 'Suntrup Kia South'
        """)
        
        if not result:
            print("No config found for Suntrup Kia South")
            return False
            
        print("BEFORE - Current Suntrup Kia South config:")
        current_config = result[0]['filtering_rules']
        print(json.dumps(current_config, indent=2))
        
        # Remove price filtering - keep only vehicle type filtering
        cleaned_config = {
            "allowed_vehicle_types": ["used"],
            "exclude_new_vehicles": True
        }
        
        # Update the config
        db_manager.execute_non_query("""
            UPDATE dealership_configs 
            SET filtering_rules = %s
            WHERE name = 'Suntrup Kia South'
        """, (json.dumps(cleaned_config),))
        
        # Verify the update
        result = db_manager.execute_query("""
            SELECT filtering_rules 
            FROM dealership_configs 
            WHERE name = 'Suntrup Kia South'
        """)
        
        print("\nAFTER - Updated Suntrup Kia South config:")
        print(json.dumps(result[0]['filtering_rules'], indent=2))
        
        print("\nSUCCESS: Removed price filtering from Suntrup Kia South")
        print("Only vehicle type filtering remains: used vehicles only")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("=== REMOVING PRICE FILTERING FROM SUNTRUP KIA SOUTH ===")
    print("Only Glendale should have price filtering logic")
    print()
    
    success = remove_price_filtering()
    
    if success:
        print("\n=== READY FOR TESTING ===")
        print("Suntrup Kia South should now process without price comparison errors")
    else:
        print("\n=== FAILED ===")
        print("Manual intervention required")