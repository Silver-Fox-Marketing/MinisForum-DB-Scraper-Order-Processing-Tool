#!/usr/bin/env python3
"""
Test Order Queue with Real Data
===============================

Test the order queue system with dealerships that have real scraped data.

Author: Silver Fox Assistant
Created: 2025-07-29
"""

import os
import sys
import logging
from datetime import date
from pathlib import Path

# Add project paths
current_file = Path(__file__).resolve()
scripts_dir = current_file.parent
sys.path.insert(0, str(scripts_dir))

from database_connection import db_manager
from order_queue_manager import OrderQueueManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_templates():
    """Test template loading"""
    logger.info("=" * 60)
    logger.info("TESTING TEMPLATE LOADING")
    logger.info("=" * 60)
    
    queue_manager = OrderQueueManager()
    
    logger.info(f"Templates loaded: {len(queue_manager.templates)}")
    for template_name, template_data in queue_manager.templates.items():
        logger.info(f"\nTemplate: {template_name}")
        logger.info(f"  Type: {template_data['type']}")
        logger.info(f"  Headers: {template_data['headers']}")
        logger.info(f"  QR Column: {template_data['qr_column']}")
        logger.info(f"  Formatting Rules: {template_data['formatting_rules']}")

def test_with_columbia_honda():
    """Test queue processing with Columbia Honda (has real data)"""
    logger.info("=" * 60)
    logger.info("TESTING WITH COLUMBIA HONDA")
    logger.info("=" * 60)
    
    queue_manager = OrderQueueManager()
    
    # Manually add Columbia Honda to queue with different templates
    today = date.today()
    
    # Clear existing queue
    db_manager.execute_query("DELETE FROM order_queue WHERE scheduled_date = %s", (today,))
    
    # Add test orders
    test_orders = [
        ('Columbia Honda', 'CAO', 'Flyout', ['used']),
        ('Columbia Honda', 'CAO', 'Shortcut', ['new']),  
        ('Columbia Honda', 'CAO', 'Shortcut Pack', ['new'])
    ]
    
    for dealership, order_type, template_type, vehicle_types in test_orders:
        db_manager.execute_query("""
            INSERT INTO order_queue 
            (dealership_name, order_type, template_type, vehicle_types, scheduled_date, day_of_week)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (dealership, order_type, template_type, vehicle_types, today, today.strftime('%A')))
        logger.info(f"Added: {dealership} - {template_type}")
    
    # Get and show queue
    daily_queue = queue_manager.get_daily_queue(today)
    logger.info(f"\nQueue has {len(daily_queue)} orders")
    
    for order in daily_queue:
        logger.info(f"Order {order['queue_id']}: {order['dealership_name']} - {order['template_type']} - {order['vehicle_types']}")
    
    # Process each order
    for order in daily_queue:
        logger.info(f"\n🚀 Processing Order {order['queue_id']}: {order['dealership_name']} ({order['template_type']})")
        result = queue_manager.process_queue_order(order['queue_id'])
        
        if result['success']:
            logger.info(f"✅ SUCCESS: {result['vehicles_processed']} vehicles, {result['qr_codes_generated']} QR codes")
            logger.info(f"   CSV: {result['csv_file']}")
            
            # Show first few lines of CSV
            if os.path.exists(result['csv_file']):
                logger.info("   CSV Preview:")
                with open(result['csv_file'], 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:3]  # First 3 lines
                    for i, line in enumerate(lines):
                        logger.info(f"     {i+1}: {line.strip()}")
        else:
            logger.error(f"❌ FAILED: {result.get('error', 'Unknown error')}")
    
    # Final queue summary
    summary = queue_manager.get_queue_summary(today)
    logger.info(f"\n📊 Final Queue Summary: {summary}")

def test_shortcut_pack_new_prefix():
    """Specifically test the NEW prefix in shortcut pack template"""
    logger.info("=" * 60)
    logger.info("TESTING NEW PREFIX IN SHORTCUT PACK")
    logger.info("=" * 60)
    
    # Check what vehicle types we have in Columbia Honda
    vehicles = db_manager.execute_query("""
        SELECT DISTINCT type, COUNT(*) as count
        FROM raw_vehicle_data 
        WHERE location = 'Columbia Honda'
        GROUP BY type
        ORDER BY count DESC
    """)
    
    logger.info("Columbia Honda vehicle types:")
    for vehicle in vehicles:
        logger.info(f"  {vehicle['type']}: {vehicle['count']} vehicles")
    
    # Test with NEW vehicles specifically if we have any
    new_vehicles = db_manager.execute_query("""
        SELECT vin, make, model, year, type, stock
        FROM raw_vehicle_data 
        WHERE location = 'Columbia Honda' AND type = 'new'
        LIMIT 3
    """)
    
    if new_vehicles:
        logger.info(f"\nFound {len(new_vehicles)} new vehicles:")
        for vehicle in new_vehicles:
            logger.info(f"  {vehicle['year']} {vehicle['make']} {vehicle['model']} - {vehicle['type']} - Stock: {vehicle['stock']}")
        
        # Process with Shortcut Pack template
        queue_manager = OrderQueueManager()
        
        # Manually create and test the shortcut pack formatting
        qr_paths = ["C:\\test\\qr1.png", "C:\\test\\qr2.png", "C:\\test\\qr3.png"]
        qr_path_map = {vehicle['vin']: qr_paths[i] for i, vehicle in enumerate(new_vehicles)}
        
        # Test shortcut pack row generation
        logger.info("\nTesting Shortcut Pack row generation:")
        
        output_folder = Path("test_shortcut_pack")
        output_folder.mkdir(exist_ok=True)
        
        csv_path = queue_manager._generate_template_csv(
            new_vehicles, 'Columbia Honda', 'Shortcut Pack', 
            output_folder, qr_paths
        )
        
        if os.path.exists(csv_path):
            logger.info(f"Generated CSV: {csv_path}")
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                logger.info("CSV Content:")
                for i, line in enumerate(lines):
                    logger.info(f"  {i+1}: {line.strip()}")
        
    else:
        logger.warning("No new vehicles found in Columbia Honda data")

def main():
    """Run all tests"""
    test_templates()
    test_with_columbia_honda()
    test_shortcut_pack_new_prefix()

if __name__ == "__main__":
    main()