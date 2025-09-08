#!/usr/bin/env python3
"""
EMERGENCY: Fix Import 12 Normalization Gap
==========================================
Normalize the missing 7453 records from Import 12 using working pattern
"""

import sys
import logging
from pathlib import Path

current_file = Path(__file__).resolve()
sys.path.insert(0, str(current_file.parent / 'scripts'))

from database_connection import db_manager
from scraper_data_normalizer import ScraperDataNormalizer

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def fix_import12_normalization():
    """Normalize missing records from Import 12"""
    logger.info("EMERGENCY FIX: NORMALIZING IMPORT 12 MISSING RECORDS")
    
    # Check current status
    coverage_query = """
        SELECT 
            COUNT(rvd.id) as total_raw,
            COUNT(nvd.id) as total_normalized,
            COUNT(rvd.id) - COUNT(nvd.id) as missing_normalized
        FROM raw_vehicle_data rvd
        LEFT JOIN normalized_vehicle_data nvd ON rvd.id = nvd.raw_data_id
        WHERE rvd.import_id = 12
    """
    
    coverage = db_manager.execute_query(coverage_query)
    if coverage:
        cov = coverage[0]
        logger.info(f"Import 12 status: {cov['total_raw']} raw, {cov['total_normalized']} normalized, {cov['missing_normalized']} missing")
        
        if cov['missing_normalized'] == 0:
            logger.info("SUCCESS: No missing normalized records!")
            return True
    
    # Get all raw vehicles from Import 12 that aren't normalized yet
    query = '''
        SELECT r.id, r.vin, r.type, r.status, r.year, r.make, r.model, r.trim, 
               r.price, r.msrp, r.stock, r.vehicle_url, r.location
        FROM raw_vehicle_data r
        LEFT JOIN normalized_vehicle_data n ON r.id = n.raw_data_id
        WHERE r.import_id = 12 AND n.id IS NULL
        ORDER BY r.id
    '''
    
    raw_vehicles = db_manager.execute_query(query)
    logger.info(f"Found {len(raw_vehicles)} vehicles needing normalization")
    
    if len(raw_vehicles) == 0:
        logger.info("No vehicles need normalization")
        return True
    
    # Create normalizer
    normalizer = ScraperDataNormalizer()
    
    # Process each vehicle
    created_count = 0
    onlot_count = 0
    error_count = 0
    
    for i, vehicle in enumerate(raw_vehicles):
        try:
            # Normalize the vehicle data
            raw_type = vehicle.get('type', '')
            raw_status = vehicle.get('status', '')
            
            normalized_type = normalizer.normalize_vehicle_type(raw_type)
            lot_status = normalizer.normalize_lot_status(raw_status)
            
            # Insert normalized record using the same pattern as working script
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
                vehicle.get('location', ''),
                vehicle.get('vehicle_url', ''),
                lot_status
            ))
            
            created_count += 1
            if lot_status == 'onlot':
                onlot_count += 1
            
            # Progress reporting
            if created_count % 500 == 0:
                logger.info(f"  Progress: {created_count}/{len(raw_vehicles)} normalized")
            elif created_count <= 5:  # Show first 5
                logger.info(f"  {vehicle['vin']}: '{raw_status}' -> '{lot_status}' ({normalized_type})")
            
        except Exception as e:
            error_count += 1
            if error_count <= 5:  # Only show first few errors
                logger.error(f"Error normalizing {vehicle.get('vin', 'unknown')}: {e}")
    
    logger.info(f"NORMALIZATION COMPLETE: {created_count} normalized, {error_count} errors")
    logger.info(f"ON-LOT VEHICLES: {onlot_count}")
    
    # Verify the fix
    final_coverage = db_manager.execute_query(coverage_query)
    if final_coverage:
        cov = final_coverage[0]
        logger.info(f"Final status: {cov['total_raw']} raw, {cov['total_normalized']} normalized, {cov['missing_normalized']} missing")
        
        if cov['missing_normalized'] == 0:
            logger.info("SUCCESS: All Import 12 records now normalized!")
            return True
        else:
            logger.warning(f"WARNING: Still {cov['missing_normalized']} records missing")
            return False
    
    return created_count > 0

if __name__ == "__main__":
    success = fix_import12_normalization()
    if success:
        print("\nEMERGENCY FIX COMPLETED: Import 12 normalization complete!")
        print("CAO should now return the expected VINs!")
    else:
        print("\nEMERGENCY FIX FAILED: Manual intervention required")