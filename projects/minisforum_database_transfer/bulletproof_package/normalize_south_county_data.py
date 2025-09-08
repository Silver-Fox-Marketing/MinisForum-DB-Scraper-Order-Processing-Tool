#!/usr/bin/env python3
"""
Normalize South County DCJR data from raw_vehicle_data to normalized_vehicle_data
"""

import sys
from pathlib import Path
from datetime import datetime

current_file = Path(__file__).resolve()
sys.path.insert(0, str(current_file.parent / 'scripts'))

from database_connection import db_manager
from scraper_data_normalizer import ScraperDataNormalizer

def normalize_south_county_data():
    """Normalize all South County DCJR data from active import"""
    
    print('=== NORMALIZING SOUTH COUNTY DCJR DATA ===')
    
    # Get active import ID
    active_import = db_manager.execute_query("""
        SELECT import_id FROM scraper_imports WHERE status = 'active' LIMIT 1
    """)
    
    if not active_import:
        print('ERROR: No active import found')
        return False
    
    import_id = active_import[0]['import_id']
    print(f'Active import ID: {import_id}')
    
    # Get all South County raw data from active import
    raw_data = db_manager.execute_query("""
        SELECT * FROM raw_vehicle_data
        WHERE location = 'South County DCJR'
        AND import_id = %s
    """, [import_id])
    
    if not raw_data:
        print('No South County DCJR data found in active import')
        return False
    
    print(f'Found {len(raw_data)} raw vehicles to normalize')
    
    # Initialize normalizer
    normalizer = ScraperDataNormalizer()
    
    normalized_count = 0
    error_count = 0
    
    for vehicle in raw_data:
        try:
            # Check if already normalized
            existing = db_manager.execute_query("""
                SELECT id FROM normalized_vehicle_data
                WHERE raw_data_id = %s
            """, [vehicle['id']])
            
            if existing:
                continue
                
            # Normalize the vehicle data
            normalized = {
                'raw_data_id': vehicle['id'],
                'vin': vehicle['vin'],
                'stock': vehicle.get('stock'),
                'vehicle_condition': normalizer.normalize_vehicle_type(vehicle.get('type', '')),
                'year': vehicle.get('year'),
                'make': vehicle.get('make'),
                'model': vehicle.get('model'),
                'trim': vehicle.get('trim'),
                'status': vehicle.get('status'),
                'price': vehicle.get('price'),
                'msrp': vehicle.get('msrp'),
                'date_in_stock': vehicle.get('date_in_stock'),
                'location': 'South County DCJR',  # Ensure standardized name
                'vehicle_url': vehicle.get('vehicle_url'),
                'on_lot_status': normalizer.normalize_lot_status(vehicle.get('on_lot_status', '')),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            # Insert into normalized_vehicle_data
            insert_query = """
                INSERT INTO normalized_vehicle_data (
                    raw_data_id, vin, stock, vehicle_condition, year, make, model, 
                    trim, status, price, msrp, date_in_stock, location, 
                    vehicle_url, on_lot_status, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            params = [
                normalized['raw_data_id'],
                normalized['vin'],
                normalized['stock'],
                normalized['vehicle_condition'],
                normalized['year'],
                normalized['make'],
                normalized['model'],
                normalized['trim'],
                normalized['status'],
                normalized['price'],
                normalized['msrp'],
                normalized['date_in_stock'],
                normalized['location'],
                normalized['vehicle_url'],
                normalized['on_lot_status'],
                normalized['created_at'],
                normalized['updated_at']
            ]
            
            db_manager.execute_query(insert_query, params)
            normalized_count += 1
            
            if normalized_count % 50 == 0:
                print(f'  Normalized {normalized_count} vehicles...')
                
        except Exception as e:
            error_count += 1
            print(f'  Error normalizing VIN {vehicle.get("vin")}: {e}')
    
    print(f'\n=== NORMALIZATION COMPLETE ===')
    print(f'Successfully normalized: {normalized_count} vehicles')
    print(f'Errors: {error_count}')
    
    # Verify the normalization
    verify = db_manager.execute_query("""
        SELECT COUNT(*) as count FROM normalized_vehicle_data
        WHERE location = 'South County DCJR'
    """)
    
    if verify:
        print(f'\nVerification: {verify[0]["count"]} total South County DCJR vehicles in normalized table')
    
    return True

if __name__ == '__main__':
    normalize_south_county_data()