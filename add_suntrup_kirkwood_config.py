#!/usr/bin/env python3

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
from database_connection import DatabaseManager

def main():
    print("=== ADDING SUNTRUP FORD KIRKWOOD DEALERSHIP CONFIGURATION ===")
    
    db_manager = DatabaseManager()
    
    # Check if Suntrup Ford Kirkwood config already exists
    print("\n1. CHECKING FOR EXISTING SUNTRUP FORD KIRKWOOD CONFIG:")
    try:
        existing_config = db_manager.execute_query('''
            SELECT * FROM dealership_configs 
            WHERE name ILIKE '%suntrup%' AND name ILIKE '%kirkwood%'
        ''')
        
        if existing_config:
            print(f"Found existing config: {existing_config[0]}")
            config_id = existing_config[0]['id']
            update_mode = True
        else:
            print("No existing Suntrup Ford Kirkwood config found - will create new one")
            update_mode = False
            
    except Exception as e:
        print(f"Error checking existing config: {e}")
        update_mode = False
    
    # Define the filtering rules for Suntrup Ford Kirkwood (USED ONLY)
    filtering_rules = {
        "vehicle_types": ["used"],
        "allowed_vehicle_types": ["used", "po", "cpo", "certified", "pre-owned"],
        "exclude_conditions": ["new"],
        "exclude_new_vehicles": True,
        "require_stock": True,
        "exclude_missing_stock": True,
        "notes": "Suntrup Ford Kirkwood only processes USED vehicles for graphics orders",
        "rationale": "Based on user requirement that this dealership should only get used cars for graphics",
        "business_rule": "Filter out ALL new vehicles, process only used/pre-owned/certified vehicles"
    }
    
    output_rules = {
        "format": "csv"
    }
    
    qr_output_path = "C:\\dealership_database\\qr_codes\\Suntrup_Ford_Kirkwood"
    
    if update_mode:
        print(f"\n2. UPDATING EXISTING CONFIG (ID: {config_id}):")
        try:
            result = db_manager.execute_query('''
                UPDATE dealership_configs 
                SET filtering_rules = %s,
                    output_rules = %s,
                    qr_output_path = %s,
                    is_active = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, name
            ''', (
                json.dumps(filtering_rules),
                json.dumps(output_rules),
                qr_output_path,
                True,
                config_id
            ))
            
            if result:
                print(f"SUCCESSFULLY UPDATED config for {result[0]['name']} (ID: {result[0]['id']})")
            else:
                print("UPDATE failed - no rows affected")
                
        except Exception as e:
            print(f"Error updating config: {e}")
            return False
            
    else:
        print("\n2. CREATING NEW SUNTRUP FORD KIRKWOOD CONFIG:")
        try:
            result = db_manager.execute_query('''
                INSERT INTO dealership_configs 
                (name, filtering_rules, output_rules, qr_output_path, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id, name
            ''', (
                "Suntrup Ford Kirkwood",
                json.dumps(filtering_rules),
                json.dumps(output_rules),
                qr_output_path,
                True
            ))
            
            if result:
                print(f"SUCCESSFULLY CREATED config for {result[0]['name']} (ID: {result[0]['id']})")
            else:
                print("INSERT failed - no rows affected")
                
        except Exception as e:
            print(f"Error creating config: {e}")
            return False
    
    # Verify the configuration was saved correctly
    print("\n3. VERIFYING SAVED CONFIGURATION:")
    try:
        saved_config = db_manager.execute_query('''
            SELECT name, filtering_rules, is_active, updated_at
            FROM dealership_configs 
            WHERE name = 'Suntrup Ford Kirkwood'
        ''')
        
        if saved_config:
            config = saved_config[0]
            print(f"Name: {config['name']}")
            print(f"Active: {config['is_active']}")
            print(f"Updated: {config['updated_at']}")
            print(f"Filtering Rules:")
            
            rules = config['filtering_rules']
            for key, value in rules.items():
                print(f"  - {key}: {value}")
                
            print("\nCONFIGURATION SAVED SUCCESSFULLY!")
            return True
        else:
            print("ERROR: Configuration not found after save")
            return False
            
    except Exception as e:
        print(f"Error verifying config: {e}")
        return False
    
    finally:
        db_manager.close()

if __name__ == "__main__":
    success = main()
    if success:
        print("\n=== SUNTRUP FORD KIRKWOOD CONFIGURATION COMPLETE ===")
        print("The dealership will now only process USED vehicles in CAO orders")
        print("NEW vehicles will be automatically filtered out")
    else:
        print("\n=== CONFIGURATION FAILED ===")
        print("Please check the errors above and try again")