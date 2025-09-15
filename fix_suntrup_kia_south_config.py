"""
Fix Suntrup Kia South Configuration
Changes vehicle types from ['new', 'used'] to ['used'] to match scraper data
CRITICAL: Only affects Suntrup Kia South - leaves all other dealerships unchanged
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

def fix_suntrup_kia_south_config():
    """Update ONLY Suntrup Kia South configuration to match its scraper data"""
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print('=' * 60)
        print('FIXING SUNTRUP KIA SOUTH CONFIGURATION')
        print('=' * 60)
        
        # First, show current configuration
        print('BEFORE: Current Suntrup Kia South Configuration')
        cursor.execute("""
            SELECT name, filtering_rules, is_active 
            FROM dealership_configs 
            WHERE name = 'Suntrup Kia South'
        """)
        
        current_config = cursor.fetchone()
        if current_config:
            print(f'Name: {current_config[0]}')
            print(f'Active: {current_config[2]}')
            print('Current Filtering Rules:')
            if current_config[1]:
                print(json.dumps(current_config[1], indent=2))
            else:
                print('  (No filtering rules found)')
        else:
            print('ERROR: Suntrup Kia South not found in dealership_configs!')
            return False
        
        print()
        print('PROBLEM IDENTIFIED:')
        print('- Scraper collects: Certified Pre-Owned + Pre-Owned vehicles only (~37 vehicles)')
        print('- Current config processes: [new, used] (ALL 377 vehicles)')  
        print('- Solution: Change to [used] to match scraper data')
        print()
        
        # Create the corrected filtering rules
        # Match Porsche St. Louis successful pattern (used vehicles only)
        corrected_filtering_rules = {
            "allowed_vehicle_types": ["used"],  # This will include both 'po' and 'cpo'
            "exclude_new_vehicles": True,
            "price_required": True,
            "exclude_price_placeholders": ["*", "Call", "TBD", "Market", "Contact"],
            "min_price": 1000
        }
        
        print('APPLYING FIX:')
        print('New Filtering Rules:')
        print(json.dumps(corrected_filtering_rules, indent=2))
        print()
        
        # Update ONLY Suntrup Kia South configuration
        cursor.execute("""
            UPDATE dealership_configs 
            SET filtering_rules = %s
            WHERE name = 'Suntrup Kia South'
        """, (json.dumps(corrected_filtering_rules),))
        
        # Verify the update
        cursor.execute("""
            SELECT name, filtering_rules, is_active 
            FROM dealership_configs 
            WHERE name = 'Suntrup Kia South'
        """)
        
        updated_config = cursor.fetchone()
        
        print('AFTER: Updated Suntrup Kia South Configuration')
        print(f'Name: {updated_config[0]}')
        print(f'Active: {updated_config[2]}')
        print('Updated Filtering Rules:')
        if updated_config[1]:
            print(json.dumps(updated_config[1], indent=2))
        
        # Commit the changes
        conn.commit()
        
        print()
        print('=' * 60)
        print('SUCCESS: SUNTRUP KIA SOUTH CONFIGURATION FIXED')
        print('=' * 60)
        print('EXPECTED RESULT:')
        print('- CAO orders should now return ~37 vehicles instead of 377')
        print('- Only processes used vehicles (po, cpo) matching scraper data')
        print('- Matches successful Porsche St. Louis pattern')
        print()
        print('VERIFICATION:')
        print('1. Test CAO order for Suntrup Kia South')
        print('2. Should return ~37 vehicles (used only)')
        print('3. All other dealerships remain unchanged')
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f'Database error: {e}')
        print('Make sure the Flask server is running and database is accessible')
        return False

if __name__ == "__main__":
    success = fix_suntrup_kia_south_config()
    if success:
        print('\n[SUCCESS] Suntrup Kia South configuration updated successfully!')
        print('Ready to test CAO processing with corrected filtering.')
    else:
        print('\n[ERROR] Failed to update configuration.')
        print('Check database connection and try again.')