#!/usr/bin/env python3
"""
Update Glendale CDJR Specific Filters
=====================================
Adds missing price filter specifically for Glendale Chrysler Jeep dealership.
This filter will exclude any vehicles that have missing prices, missing stock numbers,
or are new vehicles (as requested).
"""

import sys
import json
import logging
from pathlib import Path

# Add project paths
current_file = Path(__file__).resolve()
scripts_dir = current_file.parent
sys.path.insert(0, str(scripts_dir))

from database_connection import db_manager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_glendale_cdjr_filters():
    """Update Glendale CDJR with specific filtering requirements"""
    
    dealership_name = "Glendale Chrysler Jeep"
    
    logger.info(f"Updating filtering rules for {dealership_name}...")
    
    try:
        # Check current configuration
        existing = db_manager.execute_query("""
            SELECT name, filtering_rules, is_active FROM dealership_configs WHERE name = %s
        """, (dealership_name,))
        
        if not existing:
            logger.error(f"❌ {dealership_name} not found in database")
            return False
        
        current_rules = existing[0]['filtering_rules']
        logger.info(f"Current rules: {current_rules}")
        
        # Define new filtering rules specifically for Glendale CDJR
        new_filtering_rules = {
            'rationale': 'Glendale CDJR - Filter out vehicles with missing prices, missing stock numbers, and new vehicles',
            'vehicle_types': ['used'],  # Only process used vehicles (filter out new)
            'exclude_missing_stock': True,  # Filter out missing stock numbers
            'exclude_missing_price': True,  # NEW: Filter out missing prices
            'notes': 'Special configuration per user request: exclude missing prices + existing stock/new filters'
        }
        
        # Convert to JSON for database storage
        filtering_rules_json = json.dumps(new_filtering_rules)
        
        # Update the database
        db_manager.execute_query("""
            UPDATE dealership_configs 
            SET filtering_rules = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE name = %s
        """, (filtering_rules_json, dealership_name))
        
        logger.info(f"✅ Updated {dealership_name} filtering rules:")
        logger.info(f"   - Exclude missing prices: {new_filtering_rules['exclude_missing_price']}")
        logger.info(f"   - Exclude missing stock: {new_filtering_rules['exclude_missing_stock']}")
        logger.info(f"   - Vehicle types: {new_filtering_rules['vehicle_types']}")
        
        # Verify the update
        updated_config = db_manager.execute_query("""
            SELECT filtering_rules FROM dealership_configs WHERE name = %s
        """, (dealership_name,))
        
        if updated_config:
            verified_rules = updated_config[0]['filtering_rules']
            logger.info(f"✅ Verification - Updated rules: {verified_rules}")
            
            # Parse and validate the rules
            parsed_rules = json.loads(verified_rules) if isinstance(verified_rules, str) else verified_rules
            
            if parsed_rules.get('exclude_missing_price') == True:
                logger.info("✅ Missing price filter successfully enabled!")
            else:
                logger.error("❌ Missing price filter not properly set")
                return False
                
            if parsed_rules.get('exclude_missing_stock') == True:
                logger.info("✅ Missing stock filter confirmed!")
            else:
                logger.warning("⚠️ Missing stock filter not set")
                
            if 'new' not in parsed_rules.get('vehicle_types', []):
                logger.info("✅ New vehicles filter confirmed (only processing used)!")
            else:
                logger.warning("⚠️ New vehicles may still be processed")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating {dealership_name}: {e}")
        return False

def verify_filtering_application():
    """Verify that the filtering rules are being applied correctly"""
    
    logger.info("\n=== VERIFYING FILTERING LOGIC ===")
    
    dealership_name = "Glendale Chrysler Jeep"
    
    try:
        # Test query to see what would be filtered
        test_query = """
        SELECT 
            COUNT(*) as total_vehicles,
            COUNT(CASE WHEN price IS NULL OR price <= 0 THEN 1 END) as missing_price_count,
            COUNT(CASE WHEN stock IS NULL OR stock = '' OR stock = '*' THEN 1 END) as missing_stock_count,
            COUNT(CASE WHEN LOWER(type) LIKE '%new%' THEN 1 END) as new_vehicle_count,
            COUNT(CASE WHEN LOWER(type) LIKE '%used%' THEN 1 END) as used_vehicle_count
        FROM raw_vehicle_data 
        WHERE location = %s
        """
        
        stats = db_manager.execute_query(test_query, (dealership_name,))
        
        if stats:
            result = stats[0]
            logger.info(f"📊 {dealership_name} inventory analysis:")
            logger.info(f"   Total vehicles: {result['total_vehicles']}")
            logger.info(f"   Missing prices: {result['missing_price_count']}")
            logger.info(f"   Missing stock: {result['missing_stock_count']}")
            logger.info(f"   New vehicles: {result['new_vehicle_count']}")
            logger.info(f"   Used vehicles: {result['used_vehicle_count']}")
            
            # Calculate what would remain after filtering
            remaining_after_filters = result['total_vehicles'] - result['missing_price_count'] - result['missing_stock_count'] - result['new_vehicle_count']
            logger.info(f"   🎯 Vehicles remaining after all filters: ~{max(0, remaining_after_filters)}")
        
    except Exception as e:
        logger.error(f"Error during verification: {e}")

if __name__ == "__main__":
    logger.info("🏁 Starting Glendale CDJR filter update...")
    
    success = update_glendale_cdjr_filters()
    
    if success:
        logger.info("✅ Filter update completed successfully!")
        verify_filtering_application()
    else:
        logger.error("❌ Filter update failed!")
    
    logger.info("🏁 Process complete!")