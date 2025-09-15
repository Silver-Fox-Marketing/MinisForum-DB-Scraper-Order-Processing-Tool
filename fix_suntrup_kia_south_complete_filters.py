"""
Complete Fix for Suntrup Kia South Configuration
Adds all the filtering rules that Porsche St. Louis uses successfully:
- Stock number filtering (exclude blank/missing)
- In-transit filtering (exclude vehicles not on lot)  
- Status filtering (exclude off-lot vehicles)
- Price filtering (exclude placeholder values)
"""

import sys
import os

# Add the correct paths for database connection
sys.path.insert(0, r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts')

import psycopg2
import json

# Use the same database configuration as the working system
DB_CONFIG = {
    'host': 'localhost', 
    'database': 'vehicle_inventory',
    'user': 'postgres',
    'password': 'password'
}

def fix_suntrup_kia_south_complete():
    """Apply ALL filtering rules that Porsche St. Louis uses successfully"""
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print('=' * 60)
        print('COMPLETE FIX: SUNTRUP KIA SOUTH CONFIGURATION')
        print('=' * 60)
        
        # First, get Porsche's working configuration for reference
        print('REFERENCE: Porsche St. Louis Configuration (WORKING)')
        cursor.execute("""
            SELECT name, filtering_rules 
            FROM dealership_configs 
            WHERE name = 'Porsche St. Louis'
        """)
        
        porsche_config = cursor.fetchone()
        if porsche_config and porsche_config[1]:
            print('Porsche filtering rules (proven to work):')
            print(json.dumps(porsche_config[1], indent=2))
        else:
            print('WARNING: Could not find Porsche configuration for reference')
        
        print()
        print('APPLYING COMPLETE FILTER SET TO SUNTRUP KIA SOUTH:')
        
        # Create comprehensive filtering rules based on Porsche's success
        # Plus additional filters to handle stock numbers and in-transit issues
        complete_filtering_rules = {
            "allowed_vehicle_types": ["used"],  # Only used vehicles (po, cpo)
            "exclude_new_vehicles": True,       # Explicit new vehicle exclusion
            "price_required": True,             # Require valid price
            "exclude_price_placeholders": ["*", "Call", "TBD", "Market", "Contact", "Please Call", "Call for Price"],
            "min_price": 1000,                  # Minimum price threshold
            
            # ADDITIONAL FILTERS (key differences from before):
            "require_stock": True,              # Require stock number
            "exclude_stock_placeholders": ["", "TBD", "N/A", "*", "Call"],  # Exclude blank/invalid stock numbers
            "exclude_conditions": ["offlot", "in-transit", "sold", "pending"],  # Exclude off-lot vehicles
            "require_status": ["in-stock", "available", "onlot"],  # Only on-lot vehicles
            "exclude_lot_status": ["offlot", "off-lot", "in transit", "sold"]   # Additional lot status exclusions
        }
        
        print('Complete filtering rules:')
        print(json.dumps(complete_filtering_rules, indent=2))
        print()
        
        # Update Suntrup Kia South configuration
        cursor.execute("""
            UPDATE dealership_configs 
            SET filtering_rules = %s
            WHERE name = 'Suntrup Kia South'
        """, (json.dumps(complete_filtering_rules),))
        
        # Verify the update
        cursor.execute("""
            SELECT name, filtering_rules, is_active 
            FROM dealership_configs 
            WHERE name = 'Suntrup Kia South'
        """)
        
        updated_config = cursor.fetchone()
        
        print('UPDATED: Suntrup Kia South Configuration')
        print(f'Name: {updated_config[0]}')
        print(f'Active: {updated_config[2]}')
        print('New filtering rules:')
        if updated_config[1]:
            print(json.dumps(updated_config[1], indent=2))
        
        # Commit the changes
        conn.commit()
        
        print()
        print('=' * 60)
        print('SUCCESS: COMPLETE FILTERING APPLIED')
        print('=' * 60)
        print('FILTERS NOW INCLUDE:')
        print('✓ Vehicle type: Used only (matches scraper)')
        print('✓ Price filtering: Excludes placeholder values') 
        print('✓ Stock number filtering: Requires valid stock numbers')
        print('✓ Lot status filtering: Excludes off-lot/in-transit vehicles')
        print('✓ Condition filtering: Excludes sold/pending vehicles')
        print()
        print('EXPECTED RESULT: 337 → ~37 vehicles')
        print('Ready to test CAO processing with complete filtering.')
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f'Database error: {e}')
        print('Make sure the Flask server is running and database is accessible')
        return False

if __name__ == "__main__":
    success = fix_suntrup_kia_south_complete()
    if success:
        print('\n[SUCCESS] Suntrup Kia South complete filtering applied!')
        print('Test CAO processing - should now return ~37 vehicles instead of 337.')
    else:
        print('\n[ERROR] Failed to apply complete filtering.')
        print('Check database connection and try again.')