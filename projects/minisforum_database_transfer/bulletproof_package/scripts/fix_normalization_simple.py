#!/usr/bin/env python3
"""
Simple Normalization Fix
========================
Directly find raw data for Volvo Cars West County and create normalized records.
"""

import sys
import logging
from pathlib import Path

# Setup paths
current_file = Path(__file__).resolve()
sys.path.insert(0, str(current_file.parent))

from database_connection import db_manager
from scraper_data_normalizer import ScraperDataNormalizer

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def create_normalized_records(dealership_name: str):
    """Create normalized records for raw vehicle data"""
    logger.info(f"=== CREATING NORMALIZED RECORDS FOR {dealership_name} ===")
    
    # Get raw vehicles for this dealership
    raw_query = '''
        SELECT id, vin, type, status, year, make, model, trim, price, msrp, 
               ext_color, body_style, fuel_type, location, import_id
        FROM raw_vehicle_data 
        WHERE location = %s
        ORDER BY import_timestamp DESC
    '''
    
    raw_vehicles = db_manager.execute_query(raw_query, [dealership_name])
    if not raw_vehicles:
        logger.error(f"No raw vehicle data found for {dealership_name}")
        return False
    
    logger.info(f"Found {len(raw_vehicles)} raw vehicle records")
    
    # Check how many already have normalized records
    existing_query = '''
        SELECT COUNT(*) as count
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        WHERE rvd.location = %s
    '''
    existing_result = db_manager.execute_query(existing_query, [dealership_name])
    existing_count = existing_result[0]['count'] if existing_result else 0
    
    logger.info(f"Existing normalized records: {existing_count}")
    
    if existing_count >= len(raw_vehicles):
        logger.info("All vehicles already normalized")
        return True
    
    # Create normalizer
    normalizer = ScraperDataNormalizer()
    
    # Process each raw vehicle
    created_count = 0
    for vehicle in raw_vehicles:
        try:
            # Check if this vehicle already has normalized record
            existing_norm = db_manager.execute_query(
                'SELECT id FROM normalized_vehicle_data WHERE raw_data_id = %s',
                [vehicle['id']]
            )
            
            if existing_norm:
                continue  # Skip if already normalized
            
            # Normalize the vehicle data
            raw_type = vehicle.get('type', '')
            raw_status = vehicle.get('status', '')
            
            normalized_type = normalizer.normalize_vehicle_type(raw_type)
            lot_status = normalizer.normalize_lot_status(raw_status)
            
            # Insert normalized record
            db_manager.execute_query('''
                INSERT INTO normalized_vehicle_data 
                (raw_data_id, vin, location, year, make, model, trim, price, msrp,
                 ext_color, body_style, fuel_type, vehicle_condition, on_lot_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                vehicle['id'],
                vehicle['vin'],
                vehicle['location'],
                vehicle['year'],
                vehicle['make'],
                vehicle['model'],
                vehicle['trim'],
                vehicle['price'],
                vehicle['msrp'],
                vehicle['ext_color'],
                vehicle['body_style'],
                vehicle['fuel_type'],
                normalized_type,
                lot_status
            ))
            
            created_count += 1
            
            if created_count <= 5:  # Show first 5 for verification
                logger.info(f"Created: VIN {vehicle['vin']} - status '{raw_status}' -> '{lot_status}'")
            
        except Exception as e:
            logger.error(f"Error processing vehicle {vehicle.get('vin', 'unknown')}: {e}")
            continue
    
    logger.info(f"CREATED {created_count} NEW NORMALIZED RECORDS")
    
    # Verify the results
    final_query = '''
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN on_lot_status = 'onlot' THEN 1 END) as onlot_count,
               COUNT(CASE WHEN on_lot_status = 'offlot' THEN 1 END) as offlot_count
        FROM normalized_vehicle_data 
        WHERE location = %s
    '''
    final_result = db_manager.execute_query(final_query, [dealership_name])
    
    if final_result:
        row = final_result[0]
        logger.info(f"FINAL COUNTS: Total={row['total']}, OnLot={row['onlot_count']}, OffLot={row['offlot_count']}")
        
        # Show sample of expected VINs
        expected_vins = [
            'YV4062JE8T1435316', 'YV4M12RC8T1331153', 'YV4062JE7T1434433',
            'YV4M12RC5T1329666', 'YV4M12RC3T1336034'
        ]
        
        logger.info("CHECKING EXPECTED VINS:")
        for vin in expected_vins[:3]:  # Check first 3
            check_query = 'SELECT on_lot_status FROM normalized_vehicle_data WHERE vin = %s'
            check_result = db_manager.execute_query(check_query, [vin])
            if check_result:
                logger.info(f"  {vin}: {check_result[0]['on_lot_status']}")
            else:
                logger.error(f"  {vin}: NOT FOUND")
        
        return row['onlot_count'] > 0
    
    return False

if __name__ == "__main__":
    dealership = "Volvo Cars West County"
    success = create_normalized_records(dealership)
    
    if success:
        print(f"\nSUCCESS: Normalized records created for {dealership}")
        print("You can now test CAO processing!")
    else:
        print(f"\nFAILED: Could not create normalized records for {dealership}")