"""
Database Registration Script: BMW of West St. Louis
Adds BMW of West St. Louis scraper to dealership_configs table
"""

import sys
import os
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent / "scripts"
sys.path.append(str(scripts_dir))

from database_connection import db_manager
import json

def add_bmw_of_west_st_louis():
    """Add BMW of West St. Louis to dealership_configs table"""
    
    dealership_name = 'BMW of West St. Louis'
    
    # BMW configuration with filtering rules
    filtering_rules = {
        'vehicle_types': ['new', 'used', 'certified'],
        'min_price': 0,
        'max_price': None,
        'min_year': 2015,  # BMW typically focuses on newer vehicles
        'scraper_module': 'bmwofweststlouis_real_working',
        'scraper_config': {
            'algolia_url': 'https://sewjn80htn-dsn.algolia.net/1/indexes/*/queries',
            'api_key': '179608f32563367799314290254e3e44',
            'application_id': 'SEWJN80HTN',
            'location_filter': 'BMW of West St. Louis, Manchester, MO',
            'indexes': {
                'new': 'bmwofweststlouis-sbm0125_production_inventory_sort_image_type_price_lh',
                'used': 'bmwofweststlouis-sbm0125_production_inventory_specials_oem_price',
                'certified': 'bmwofweststlouis-sbm0125_production_inventory_specials_oem_price'
            }
        }
    }
    
    # BMW output rules  
    output_rules = {
        'include_qr': True,
        'format': 'premium',
        'sort_by': ['model', 'year'],
        'fields': ['vin', 'stock', 'year', 'make', 'model', 'trim', 'price', 'vehicle_type'],
        'qr_output_path': './output_data/qr_codes/bmw_west_st_louis/'
    }
    
    try:
        # Check if dealership already exists
        check_query = "SELECT COUNT(*) FROM dealership_configs WHERE name = %s"
        result = db_manager.execute_query(check_query, (dealership_name,), fetch='one')
        
        if result and result['count'] > 0:
            print(f"BMW of West St. Louis already exists in database")
            # Update existing record
            update_query = """
                UPDATE dealership_configs 
                SET filtering_rules = %s, output_rules = %s, updated_at = CURRENT_TIMESTAMP 
                WHERE name = %s
            """
            db_manager.execute_non_query(update_query, (
                json.dumps(filtering_rules), 
                json.dumps(output_rules), 
                dealership_name
            ))
            print(f"Updated existing BMW of West St. Louis configuration")
        else:
            # Insert new dealership
            insert_query = """
                INSERT INTO dealership_configs (name, filtering_rules, output_rules, is_active) 
                VALUES (%s, %s, %s, %s)
            """
            db_manager.execute_non_query(insert_query, (
                dealership_name, 
                json.dumps(filtering_rules), 
                json.dumps(output_rules), 
                True
            ))
            print(f"Added BMW of West St. Louis to dealership_configs")
        
        print(f"[SUCCESS] BMW of West St. Louis scraper registered successfully!")
        
        # Verify the addition
        verify_query = "SELECT name, is_active FROM dealership_configs WHERE name = %s"
        result = db_manager.execute_query(verify_query, (dealership_name,), fetch='one')
        if result:
            print(f"Verification: {result['name']} - Active: {result['is_active']}")
        
        return True
        
    except Exception as e:
        print(f"Error adding BMW of West St. Louis: {e}")
        return False

if __name__ == "__main__":
    print("Adding BMW of West St. Louis to database...")
    success = add_bmw_of_west_st_louis()
    if success:
        print("BMW of West St. Louis scraper ready for use!")
    else:
        print("Failed to add BMW of West St. Louis")