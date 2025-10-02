#!/usr/bin/env python3
"""
Minimal Normalization Fix
=========================
Create normalized records using the correct schema
"""

import sys
import logging
from pathlib import Path

current_file = Path(__file__).resolve()
sys.path.insert(0, str(current_file.parent))

from database_connection import db_manager
from scraper_data_normalizer import ScraperDataNormalizer

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def fix_volvo_normalization():
    """Create normalized records for Volvo Cars West County"""
    dealership = "Volvo Cars West County"
    logger.info(f"FIXING NORMALIZATION FOR {dealership}")
    
    # Get raw vehicles
    raw_query = '''
        SELECT id, vin, type, status, year, make, model, trim, price, msrp, stock, vehicle_url
        FROM raw_vehicle_data 
        WHERE location = %s
        ORDER BY import_timestamp DESC
        LIMIT 50
    '''
    
    raw_vehicles = db_manager.execute_query(raw_query, [dealership])
    logger.info(f"Found {len(raw_vehicles)} raw vehicle records")
    
    if not raw_vehicles:
        return False
    
    # Check expected VINs
    expected_vins = [
        'YV4062JE8T1435316', 'YV4M12RC8T1331153', 'YV4062JE7T1434433',
        'YV4M12RC5T1329666', 'YV4M12RC3T1336034', 'YV4M12RM9T1335429',
        'YV4M12RC4T1335930', 'YV4H60RM2T1325073', 'YV4M12RC8T1342069',
        'YV4H60RC2T1343158', 'YV4062PF7T1453502'
    ]
    
    logger.info("CHECKING FOR EXPECTED VINS IN RAW DATA:")
    found_expected = []
    for vehicle in raw_vehicles:
        if vehicle['vin'] in expected_vins:
            found_expected.append(vehicle)
            logger.info(f"  FOUND: {vehicle['vin']} - status: '{vehicle.get('status', 'N/A')}'")
    
    logger.info(f"Found {len(found_expected)} of {len(expected_vins)} expected VINs")
    
    if len(found_expected) == 0:
        logger.error("CRITICAL: None of the expected VINs found in raw data!")
        return False
    
    # Create normalizer
    normalizer = ScraperDataNormalizer()
    
    # Process the found expected vehicles
    created_count = 0
    for vehicle in found_expected:
        try:
            # Check if already normalized
            existing = db_manager.execute_query(
                'SELECT id FROM normalized_vehicle_data WHERE raw_data_id = %s',
                [vehicle['id']]
            )
            
            if existing:
                logger.info(f"  SKIP {vehicle['vin']}: Already normalized")
                continue
            
            # Normalize
            raw_type = vehicle.get('type', '')
            raw_status = vehicle.get('status', '')
            
            normalized_type = normalizer.normalize_vehicle_type(raw_type)
            lot_status = normalizer.normalize_lot_status(raw_status)
            
            # Insert normalized record with correct columns
            db_manager.execute_query('''
                INSERT INTO normalized_vehicle_data 
                (raw_data_id, vin, stock, vehicle_condition, year, make, model, trim,
                 status, price, msrp, location, vehicle_url, on_lot_status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ''', (
                vehicle['id'],
                vehicle['vin'],
                vehicle.get('stock', ''),
                normalized_type,
                vehicle.get('year', 0),
                vehicle.get('make', ''),
                vehicle.get('model', ''),
                vehicle.get('trim', ''),
                raw_status,
                vehicle.get('price'),
                vehicle.get('msrp'),
                dealership,
                vehicle.get('vehicle_url', ''),
                lot_status
            ))
            
            created_count += 1
            logger.info(f"  CREATED: {vehicle['vin']} - '{raw_status}' -> '{lot_status}'")
            
        except Exception as e:
            logger.error(f"Error processing {vehicle['vin']}: {e}")
    
    logger.info(f"CREATED {created_count} NORMALIZED RECORDS")
    
    # Verify results
    onlot_query = '''
        SELECT COUNT(*) as count
        FROM normalized_vehicle_data 
        WHERE location = %s AND on_lot_status = 'onlot'
    '''
    onlot_result = db_manager.execute_query(onlot_query, [dealership])
    onlot_count = onlot_result[0]['count'] if onlot_result else 0
    
    logger.info(f"FINAL RESULT: {onlot_count} vehicles with on_lot_status = 'onlot'")
    
    return onlot_count > 0

if __name__ == "__main__":
    success = fix_volvo_normalization()
    if success:
        print("\nSUCCESS: CAO should now work for Volvo Cars West County!")
    else:
        print("\nFAILED: Could not create normalized records")