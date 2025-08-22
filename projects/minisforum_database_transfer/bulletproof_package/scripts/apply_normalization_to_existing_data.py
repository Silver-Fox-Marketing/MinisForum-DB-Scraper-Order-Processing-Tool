#!/usr/bin/env python3
"""
Apply Normalization to Existing Scraper Data
===========================================
Updates all existing raw_vehicle_data records with normalized values.
"""

import sys
import logging
from pathlib import Path

# Add scripts directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from database_connection import db_manager
from scraper_data_normalizer import normalizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_existing_data():
    """Apply normalization to all existing vehicle records"""
    
    try:
        # Get all records that need normalization
        query = """
        SELECT id, type, status 
        FROM raw_vehicle_data 
        WHERE normalized_type IS NULL OR on_lot_status IS NULL
        ORDER BY id
        """
        
        records = db_manager.execute_query(query)
        logger.info(f"Found {len(records)} records to normalize")
        
        if not records:
            logger.info("No records need normalization")
            return
        
        # Process records in batches
        batch_size = 1000
        processed = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: records {i+1} to {min(i+batch_size, len(records))}")
            
            # Prepare batch updates
            updates = []
            for record in batch:
                record_id = record['id']
                raw_type = record['type'] or ''
                raw_status = record['status'] or ''
                
                # Normalize the data
                normalized_type = normalizer.normalize_vehicle_type(raw_type)
                lot_status = normalizer.normalize_lot_status(raw_status)
                
                updates.append((normalized_type, lot_status, record_id))
            
            # Execute batch update
            update_query = """
            UPDATE raw_vehicle_data 
            SET normalized_type = %s, on_lot_status = %s
            WHERE id = %s
            """
            
            for update in updates:
                db_manager.execute_query(update_query, update)
                processed += 1
            
            logger.info(f"Processed {len(batch)} records in this batch")
        
        logger.info(f"Successfully normalized {processed} records")
        
        # Verify the results
        verification_query = """
        SELECT 
            on_lot_status,
            normalized_type,
            COUNT(*) as count
        FROM raw_vehicle_data 
        WHERE normalized_type IS NOT NULL AND on_lot_status IS NOT NULL
        GROUP BY on_lot_status, normalized_type
        ORDER BY on_lot_status, normalized_type
        """
        
        results = db_manager.execute_query(verification_query)
        
        print("\n" + "="*50)
        print("NORMALIZATION RESULTS:")
        print("="*50)
        print(f"{'Lot Status':<12} | {'Type':<8} | {'Count':<10}")
        print("-" * 35)
        
        for result in results:
            lot_status = result['on_lot_status']
            norm_type = result['normalized_type']
            count = result['count']
            print(f"{lot_status:<12} | {norm_type:<8} | {count:<10}")
        
        # Summary stats
        onlot_count = sum(r['count'] for r in results if r['on_lot_status'] == 'onlot')
        offlot_count = sum(r['count'] for r in results if r['on_lot_status'] == 'offlot')
        
        print("-" * 35)
        print(f"ON LOT:      {onlot_count:,} vehicles")
        print(f"OFF LOT:     {offlot_count:,} vehicles")
        print(f"TOTAL:       {onlot_count + offlot_count:,} vehicles")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Error normalizing data: {e}")
        raise

if __name__ == "__main__":
    normalize_existing_data()