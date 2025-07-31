"""
Add Dave Sinclair Lincoln configuration for testing order processing
"""

import sys
from pathlib import Path

scripts_dir = Path(__file__).parent / "scripts"
sys.path.append(str(scripts_dir))

from database_connection import db_manager
import json

def add_dave_sinclair_lincoln():
    """Add Dave Sinclair Lincoln config for testing"""
    
    dealership_name = 'Dave Sinclair Lincoln'
    
    filtering_rules = {
        'vehicle_types': ['new', 'used', 'certified'],
        'min_price': 0,
        'max_price': None,
        'min_year': 2015,
    }
    
    output_rules = {
        'include_qr': True,
        'format': 'shortcut_pack',
        'sort_by': ['model', 'year'],
        'fields': ['vin', 'stock', 'year', 'make', 'model', 'trim', 'price', 'type'],
        'qr_output_path': './output_data/qr_codes/dave_sinclair_lincoln/'
    }
    
    try:
        # Insert dealership
        db_manager.execute_non_query("""
            INSERT INTO dealership_configs (name, filtering_rules, output_rules, is_active) 
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET
                filtering_rules = EXCLUDED.filtering_rules,
                output_rules = EXCLUDED.output_rules,
                is_active = EXCLUDED.is_active
        """, (
            dealership_name, 
            json.dumps(filtering_rules), 
            json.dumps(output_rules), 
            True
        ))
        
        print(f"[SUCCESS] Added {dealership_name} configuration")
        return True
        
    except Exception as e:
        print(f"Error adding {dealership_name}: {e}")
        return False

if __name__ == "__main__":
    add_dave_sinclair_lincoln()