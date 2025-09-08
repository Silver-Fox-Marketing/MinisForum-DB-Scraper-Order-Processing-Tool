#!/usr/bin/env python3
"""
Normalize Existing Volvo Data
=============================
Run normalization on the existing Volvo raw data that's already imported
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

def normalize_volvo_data():
    """Normalize all Volvo Cars West County raw data"""
    dealership = "Volvo Cars West County"
    logger.info(f"NORMALIZING ALL {dealership} DATA")
    
    # Get all raw vehicles for this dealership that aren't normalized yet
    query = '''
        SELECT r.id, r.vin, r.type, r.status, r.year, r.make, r.model, r.trim, 
               r.price, r.msrp, r.stock, r.vehicle_url
        FROM raw_vehicle_data r
        LEFT JOIN normalized_vehicle_data n ON r.id = n.raw_data_id
        WHERE r.location = %s AND n.id IS NULL
    '''
    
    raw_vehicles = db_manager.execute_query(query, [dealership])
    logger.info(f"Found {len(raw_vehicles)} vehicles needing normalization")
    
    if len(raw_vehicles) == 0:
        logger.info("No vehicles need normalization")
        return True
    
    # Create normalizer
    normalizer = ScraperDataNormalizer()
    
    # Process each vehicle
    created_count = 0
    onlot_count = 0
    
    for vehicle in raw_vehicles:
        try:
            # Normalize the vehicle data
            raw_type = vehicle.get('type', '')
            raw_status = vehicle.get('status', '')
            
            normalized_type = normalizer.normalize_vehicle_type(raw_type)
            lot_status = normalizer.normalize_lot_status(raw_status)
            
            # Insert normalized record
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
            if lot_status == 'onlot':
                onlot_count += 1
            
            if created_count <= 5:  # Show first 5
                logger.info(f"  {vehicle['vin']}: '{raw_status}' -> '{lot_status}'")
            
        except Exception as e:
            logger.error(f"Error normalizing {vehicle.get('vin', 'unknown')}: {e}")
    
    logger.info(f"NORMALIZED {created_count} VEHICLES")
    logger.info(f"ON-LOT VEHICLES: {onlot_count}")
    
    return onlot_count > 0

if __name__ == "__main__":
    success = normalize_volvo_data()
    if success:
        print("\nSUCCESS: Volvo normalization complete - CAO should now work!")
    else:
        print("\nNo on-lot vehicles found after normalization")