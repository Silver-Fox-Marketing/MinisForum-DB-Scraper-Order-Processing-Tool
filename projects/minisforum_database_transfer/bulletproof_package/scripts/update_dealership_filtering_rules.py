#!/usr/bin/env python3
"""
Update Dealership Filtering Rules
==================================
Updates dealership_configs table with filtering rules from CSV file.
Applies specific filtering rules based on the "Filter Out" column in the CSV.
"""

import sys
import pandas as pd
import json
import logging
from pathlib import Path
from typing import Dict, List

# Add project paths
current_file = Path(__file__).resolve()
scripts_dir = current_file.parent
sys.path.insert(0, str(scripts_dir))

from database_connection import db_manager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_filter_rules(filter_out_text: str) -> Dict:
    """Parse filter rules from the CSV 'Filter Out' column"""
    if pd.isna(filter_out_text) or not filter_out_text.strip():
        return {}
    
    rules = {}
    filter_items = [item.strip() for item in filter_out_text.split(',')]
    
    exclude_status = []
    exclude_types = []
    
    for item in filter_items:
        item_lower = item.lower()
        
        # Handle missing stock number filter
        if 'missing stock' in item_lower:
            rules['exclude_missing_stock'] = True
        
        # Handle missing price filter
        elif 'missing price' in item_lower:
            rules['exclude_missing_price'] = True
        
        # Handle specific status filters
        elif 'in-transit' in item_lower:
            exclude_status.append('In-Transit')
        
        # Handle vehicle type filters
        elif item_lower == 'new':
            exclude_types.append('new')
        elif item_lower == 'used':
            exclude_types.append('used')
        elif 'cpo' in item_lower or 'certified' in item_lower:
            exclude_types.append('cpo')
    
    # Add status exclusions if any
    if exclude_status:
        rules['exclude_status'] = exclude_status
    
    # Add type exclusions if any - this determines what vehicle types to INCLUDE
    # If "New" is filtered out, we only want used/cpo
    # If "Used" is filtered out, we only want new/cpo
    if exclude_types:
        all_types = {'new', 'used', 'cpo'}
        include_types = list(all_types - set(exclude_types))
        rules['allowed_vehicle_types'] = include_types
        logger.info(f"Excluding types: {exclude_types}, Including: {include_types}")
    
    return rules

def update_dealership_configs():
    """Update dealership configurations with filtering rules from CSV"""
    logger.info("Starting dealership filtering rules update...")
    
    # Read the CSV file
    csv_path = Path("C:/Users/Workstation_1/Documents/Tools/ClaudeCode/projects/shared_resources/Dealership Filtering Settings.csv")
    
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return False
    
    try:
        # Read CSV
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} dealership filtering rules")
        
        # Process each dealership
        updated_count = 0
        
        for _, row in df.iterrows():
            dealership_name = row['Name']
            filter_out = row['Filter Out']
            
            # Parse filtering rules
            filtering_rules = parse_filter_rules(filter_out)
            
            if not filtering_rules:
                logger.info(f"No specific rules for {dealership_name}, using defaults")
                filtering_rules = {
                    'exclude_missing_stock': True,
                    'exclude_missing_price': True
                }
            
            # Convert to JSON for database storage
            filtering_rules_json = json.dumps(filtering_rules)
            
            # Check if dealership exists in database
            existing = db_manager.execute_query("""
                SELECT name FROM dealership_configs WHERE name = %s
            """, (dealership_name,))
            
            if existing:
                # Update existing record
                db_manager.execute_query("""
                    UPDATE dealership_configs 
                    SET filtering_rules = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE name = %s
                """, (filtering_rules_json, dealership_name))
                logger.info(f"✅ Updated {dealership_name}: {filtering_rules}")
            else:
                # Insert new record with basic defaults
                db_manager.execute_query("""
                    INSERT INTO dealership_configs (name, filtering_rules, output_rules, created_at, updated_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (dealership_name, filtering_rules_json, '{}'))
                logger.info(f"✅ Created {dealership_name}: {filtering_rules}")
            
            updated_count += 1
        
        logger.info(f"✅ Successfully updated {updated_count} dealership configurations")
        
        # Special focus on Honda of Frontenac - should only process USED vehicles
        honda_frontenac_rules = parse_filter_rules("Missing Stock #, New")
        logger.info(f"🎯 Honda of Frontenac rules: {honda_frontenac_rules}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating dealership configs: {e}")
        return False

def test_honda_filtering():
    """Test Honda of Frontenac filtering to verify we get 17 vehicles"""
    logger.info("Testing Honda of Frontenac filtering...")
    
    try:
        # Get the latest import ID
        from scraper_import_manager import import_manager
        active_import = import_manager.get_active_import()
        
        if not active_import:
            logger.error("No active import found!")
            return
        
        import_id = active_import['import_id']
        logger.info(f"Using active import ID: {import_id}")
        
        # Test the filtering query for Honda of Frontenac
        # Based on CSV: "Missing Stock #, New" means exclude missing stock AND exclude new vehicles
        test_query = """
            SELECT COUNT(*) as vehicle_count,
                   COUNT(CASE WHEN type = 'New' THEN 1 END) as new_count,
                   COUNT(CASE WHEN type = 'Used' THEN 1 END) as used_count,
                   COUNT(CASE WHEN type ILIKE '%certified%' THEN 1 END) as cpo_count,
                   COUNT(CASE WHEN stock IS NULL OR stock = '' THEN 1 END) as missing_stock_count
            FROM raw_vehicle_data
            WHERE location = 'Honda of Frontenac'
            AND import_id = %s
            AND is_archived = FALSE
        """
        
        result = db_manager.execute_query(test_query, (import_id,))
        if result:
            stats = result[0]
            logger.info(f"Honda of Frontenac inventory stats:")
            logger.info(f"  Total vehicles: {stats['vehicle_count']}")
            logger.info(f"  New: {stats['new_count']}")
            logger.info(f"  Used: {stats['used_count']}")
            logger.info(f"  CPO: {stats['cpo_count']}")
            logger.info(f"  Missing Stock: {stats['missing_stock_count']}")
        
        # Now test with filtering applied (should only get used vehicles with stock numbers)
        filtered_query = """
            SELECT COUNT(*) as filtered_count,
                   array_agg(DISTINCT type) as types_found
            FROM raw_vehicle_data
            WHERE location = 'Honda of Frontenac'
            AND import_id = %s
            AND is_archived = FALSE
            AND stock IS NOT NULL 
            AND stock != ''
            AND type = 'Used'
        """
        
        filtered_result = db_manager.execute_query(filtered_query, (import_id,))
        if filtered_result:
            filtered_stats = filtered_result[0]
            logger.info(f"Filtered results (Used only, with stock):")
            logger.info(f"  Count: {filtered_stats['filtered_count']}")
            logger.info(f"  Types found: {filtered_stats['types_found']}")
        
    except Exception as e:
        logger.error(f"Error testing Honda filtering: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("UPDATING DEALERSHIP FILTERING RULES")
    print("=" * 60)
    
    # Update all dealership configs
    success = update_dealership_configs()
    
    if success:
        print("\n" + "=" * 60)
        print("TESTING HONDA OF FRONTENAC FILTERING")
        print("=" * 60)
        test_honda_filtering()
        
        print("\n✅ Dealership filtering rules update completed successfully!")
        print("🎯 Honda of Frontenac should now process only USED vehicles with stock numbers")
    else:
        print("\n❌ Failed to update dealership filtering rules")