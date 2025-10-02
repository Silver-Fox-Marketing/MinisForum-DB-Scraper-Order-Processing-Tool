#!/usr/bin/env python3
"""
Emergency Normalization Fix
===========================
Manually run normalization on existing raw data to fix the CAO zero vehicles issue.
This creates the missing normalized_vehicle_data records that should have been created during import.
"""

import sys
import logging
from pathlib import Path

# Setup paths
current_file = Path(__file__).resolve()
sys.path.insert(0, str(current_file.parent))

from database_connection import db_manager
from scraper_import_manager import ScraperImportManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_normalization_for_dealership(dealership_name: str):
    """Fix normalization for a specific dealership"""
    logger.info(f"=== FIXING NORMALIZATION FOR {dealership_name} ===")
    
    # Get active import for this dealership
    active_query = '''
        SELECT import_id
        FROM scraper_imports 
        WHERE location = %s AND status = 'active'
        ORDER BY created_at DESC
        LIMIT 1
    '''
    
    active_result = db_manager.execute_query(active_query, [dealership_name])
    if not active_result:
        logger.error(f"No active import found for {dealership_name}")
        return False
    
    import_id = active_result[0]['import_id']
    logger.info(f"Found active import {import_id}")
    
    # Check current normalized count
    norm_count_query = '''
        SELECT COUNT(*) as count
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        WHERE rvd.import_id = %s
    '''
    norm_result = db_manager.execute_query(norm_count_query, [import_id])
    current_normalized = norm_result[0]['count'] if norm_result else 0
    
    logger.info(f"Current normalized records: {current_normalized}")
    
    # Get raw count for comparison
    raw_count_query = 'SELECT COUNT(*) as count FROM raw_vehicle_data WHERE import_id = %s'
    raw_result = db_manager.execute_query(raw_count_query, [import_id])
    raw_count = raw_result[0]['count'] if raw_result else 0
    
    logger.info(f"Raw vehicle records: {raw_count}")
    
    if current_normalized >= raw_count and raw_count > 0:
        logger.info("Normalization already complete")
        return True
    
    # Run normalization using ScraperImportManager
    import_manager = ScraperImportManager()
    
    try:
        # This will create missing normalized records
        import_manager.ensure_active_normalization(import_id)
        
        # Verify it worked
        norm_result_after = db_manager.execute_query(norm_count_query, [import_id])
        final_normalized = norm_result_after[0]['count'] if norm_result_after else 0
        
        logger.info(f"Final normalized records: {final_normalized}")
        
        if final_normalized > current_normalized:
            logger.info(f"SUCCESS: Created {final_normalized - current_normalized} new normalized records")
            return True
        else:
            logger.error("FAILED: No new normalized records created")
            return False
            
    except Exception as e:
        logger.error(f"Error during normalization: {e}")
        return False

if __name__ == "__main__":
    # Fix normalization for Volvo Cars West County
    dealership = "Volvo Cars West County"
    success = fix_normalization_for_dealership(dealership)
    
    if success:
        print(f"\n=== NORMALIZATION FIX COMPLETE FOR {dealership} ===")
        print("You can now test CAO processing - it should return the expected vehicles!")
    else:
        print(f"\n=== NORMALIZATION FIX FAILED FOR {dealership} ===")
        print("Check the logs above for error details")