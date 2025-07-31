#!/usr/bin/env python3
"""
Add Dave Sinclair Lincoln South to Database
==========================================

Script to add the imported Dave Sinclair Lincoln South scraper 
to the dealership_configs database table so it appears in the UI.

Author: Silver Fox Assistant
Created: 2025-07-29
"""

import sys
import json
from pathlib import Path

# Add scripts directory to path
script_dir = Path(__file__).parent
sys.path.append(str(script_dir))

from database_connection import db_manager

def add_dave_sinclair_lincoln_south():
    """Add Dave Sinclair Lincoln South to dealership_configs"""
    
    # Configuration for Dave Sinclair Lincoln South
    # Based on actual table schema: id, name, filtering_rules, output_rules, qr_output_path, is_active, created_at, updated_at
    dealership_name = 'Dave Sinclair Lincoln South'
    
    # Create filtering rules (what types of vehicles to include)
    filtering_rules = {
        'vehicle_types': ['new', 'used', 'certified'],
        'min_price': 0,
        'max_price': None,
        'min_year': 2015,
        'scraper_module': 'davesinclairlincolnsouth_real_working',
        'scraper_config': {
            'dealer_id': '18435',
            'page_id': '1730530',
            'api_base': 'https://www.davesinclairlincolnsouth.com/api/vhcliaa/vehicle-pages/cosmos/srp/',
            'location_filter': 'Ballwin, MO'
        }
    }
    
    # Create output rules (how to format the output)
    output_rules = {
        'template_type': 'shortcut_pack',
        'include_new_prefix': True,
        'qr_code_size': 'medium',
        'output_format': 'csv'
    }
    
    qr_output_path = 'C:/qr_codes/dave_sinclair_lincoln_south/'
    
    try:
        # Check if already exists
        existing = db_manager.execute_query(
            'SELECT id FROM dealership_configs WHERE name = %s',
            (dealership_name,)
        )
        
        if existing:
            print(f'Dealership "{dealership_name}" already exists in database')
            return True
        
        # Insert new dealership config using the actual table schema
        db_manager.execute_query('''
            INSERT INTO dealership_configs (
                name, filtering_rules, output_rules, qr_output_path, is_active
            ) VALUES (
                %s, %s, %s, %s, %s
            )
        ''', (
            dealership_name,
            json.dumps(filtering_rules),
            json.dumps(output_rules),
            qr_output_path,
            True  # is_active
        ))
        
        print(f'Successfully added "{dealership_name}" to dealership_configs')
        
        # Verify insertion
        verify = db_manager.execute_query(
            'SELECT name, is_active FROM dealership_configs WHERE name = %s',
            (dealership_name,)
        )
        
        if verify:
            result = verify[0]
            print(f'Verification: Name="{result["name"]}", Active={result["is_active"]}')
            return True
        else:
            print('ERROR: Failed to verify insertion')
            return False
            
    except Exception as e:
        print(f'ERROR adding dealership to database: {e}')
        return False

if __name__ == "__main__":
    print("Adding Dave Sinclair Lincoln South to dealership_configs...")
    success = add_dave_sinclair_lincoln_south()
    if success:
        print("[SUCCESS] Dave Sinclair Lincoln South is now available in the scraper control tab")
    else:
        print("[FAILED] Could not add dealership to database")