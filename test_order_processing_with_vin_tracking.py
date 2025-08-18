#!/usr/bin/env python3
"""
Test Order Processing Wizard with VIN Tracking
==============================================

This script tests the Order Processing Wizard with real BMW data,
ensuring that VIN history tracking prevents duplicate processing.
"""

import sys
import os

# Add project paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from database_connection import db_manager
from correct_order_processing import CorrectOrderProcessor
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_bmw_inventory():
    """Check available BMW inventory and VIN tracking status"""
    print("\n=== BMW INVENTORY STATUS ===")
    
    # Get current BMW inventory
    inventory_query = """
    WITH current_inventory AS (
        SELECT 
            vin, 
            stock, 
            make, 
            model, 
            year, 
            price,
            vehicle_url
        FROM raw_vehicle_data
        WHERE location = 'BMW of West St. Louis'
        AND import_date = '2025-08-01'
    ),
    processed_vins AS (
        SELECT DISTINCT vin
        FROM vin_history
        WHERE dealership_name = 'BMW of West St. Louis'
        AND source IN ('CAO_ORDER', 'LIST_ORDER')
    )
    SELECT 
        ci.*,
        CASE WHEN pv.vin IS NOT NULL THEN 'YES' ELSE 'NO' END as already_processed
    FROM current_inventory ci
    LEFT JOIN processed_vins pv ON ci.vin = pv.vin
    ORDER BY already_processed, ci.year DESC, ci.model
    LIMIT 10;
    """
    
    results = db_manager.execute_query(inventory_query)
    
    if results:
        print(f"Found {len(results)} BMW vehicles (showing first 10):")
        print("-" * 100)
        print(f"{'VIN':<20} {'Year':<6} {'Model':<20} {'Stock':<15} {'Price':<10} {'Processed'}")
        print("-" * 100)
        
        for vehicle in results:
            print(f"{vehicle['vin']:<20} {vehicle['year']:<6} {vehicle['model']:<20} "
                  f"{vehicle['stock']:<15} ${vehicle['price']:<9} {vehicle['already_processed']}")
    else:
        print("No BMW vehicles found!")
        return False
    
    # Get summary statistics
    stats_query = """
    WITH stats AS (
        SELECT 
            COUNT(*) as total_inventory,
            COUNT(DISTINCT CASE WHEN vh.vin IS NOT NULL THEN rd.vin END) as already_processed,
            COUNT(DISTINCT CASE WHEN vh.vin IS NULL THEN rd.vin END) as available_for_processing
        FROM raw_vehicle_data rd
        LEFT JOIN vin_history vh ON rd.vin = vh.vin 
            AND vh.dealership_name = 'BMW of West St. Louis'
            AND vh.source IN ('CAO_ORDER', 'LIST_ORDER')
        WHERE rd.location = 'BMW of West St. Louis'
        AND rd.import_date = '2025-08-01'
    )
    SELECT * FROM stats;
    """
    
    stats = db_manager.execute_query(stats_query)
    if stats:
        stat = stats[0]
        print(f"\n=== PROCESSING STATUS ===")
        print(f"Total BMW inventory: {stat['total_inventory']} vehicles")
        print(f"Already processed: {stat['already_processed']} vehicles")
        print(f"Available for new orders: {stat['available_for_processing']} vehicles")
    
    return True

def test_cao_order():
    """Test CAO (Create All Orders) processing"""
    print("\n=== TESTING CAO ORDER PROCESSING ===")
    
    processor = CorrectOrderProcessor()
    
    # Process a CAO order for BMW
    print("\nProcessing CAO order for BMW of West St. Louis...")
    result = processor.process_cao_order(
        dealership_name="BMW of West St. Louis",
        template_type="shortcut_pack"
    )
    
    print(f"\n=== CAO ORDER RESULT ===")
    print(f"Success: {result['success']}")
    print(f"Vehicles processed: {result.get('vehicles_processed', 0)}")
    print(f"QR codes generated: {result.get('qr_codes_generated', 0)}")
    print(f"VINs logged to history: {result.get('vins_logged_to_history', 0)}")
    print(f"Duplicate VINs skipped: {result.get('duplicate_vins_skipped', 0)}")
    
    if result.get('csv_output_path'):
        print(f"CSV output: {result['csv_output_path']}")
    if result.get('qr_output_path'):
        print(f"QR output: {result['qr_output_path']}")
    
    if not result['success']:
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    return result

def test_list_order():
    """Test LIST order processing with specific VINs"""
    print("\n=== TESTING LIST ORDER PROCESSING ===")
    
    # Get some unprocessed VINs for testing
    unprocessed_query = """
    SELECT vin
    FROM raw_vehicle_data rd
    LEFT JOIN vin_history vh ON rd.vin = vh.vin 
        AND vh.dealership_name = 'BMW of West St. Louis'
        AND vh.source IN ('CAO_ORDER', 'LIST_ORDER')
    WHERE rd.location = 'BMW of West St. Louis'
    AND rd.import_date = '2025-08-01'
    AND vh.vin IS NULL
    LIMIT 5;
    """
    
    unprocessed = db_manager.execute_query(unprocessed_query)
    
    if not unprocessed:
        print("No unprocessed VINs available for LIST order test!")
        return None
    
    test_vins = [v['vin'] for v in unprocessed]
    print(f"Testing with {len(test_vins)} unprocessed VINs:")
    for vin in test_vins:
        print(f"  - {vin}")
    
    processor = CorrectOrderProcessor()
    
    # Process a LIST order
    print("\nProcessing LIST order...")
    result = processor.process_list_order(
        dealership_name="BMW of West St. Louis",
        vin_list=test_vins,
        template_type="shortcut_pack"
    )
    
    print(f"\n=== LIST ORDER RESULT ===")
    print(f"Success: {result['success']}")
    print(f"Vehicles processed: {result.get('vehicles_processed', 0)}")
    print(f"QR codes generated: {result.get('qr_codes_generated', 0)}")
    print(f"VINs logged to history: {result.get('vins_logged_to_history', 0)}")
    
    if not result['success']:
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    return result

def verify_vin_tracking():
    """Verify that VIN tracking is working correctly"""
    print("\n=== VERIFYING VIN TRACKING ===")
    
    # Check recent VIN history entries
    history_query = """
    SELECT 
        vh.vin,
        vh.order_date,
        vh.source,
        vh.vehicle_type,
        rd.make,
        rd.model,
        rd.year
    FROM vin_history vh
    JOIN raw_vehicle_data rd ON vh.vin = rd.vin
    WHERE vh.dealership_name = 'BMW of West St. Louis'
    AND vh.order_date >= CURRENT_DATE - INTERVAL '7 days'
    AND rd.location = 'BMW of West St. Louis'
    ORDER BY vh.created_at DESC
    LIMIT 10;
    """
    
    history = db_manager.execute_query(history_query)
    
    if history:
        print(f"\nRecent VIN history entries (last 10):")
        print("-" * 80)
        print(f"{'VIN':<20} {'Order Date':<12} {'Source':<15} {'Vehicle'}")
        print("-" * 80)
        
        for entry in history:
            vehicle_desc = f"{entry['year']} {entry['make']} {entry['model']}"
            print(f"{entry['vin']:<20} {str(entry['order_date']):<12} "
                  f"{entry['source']:<15} {vehicle_desc}")
    else:
        print("No VIN history entries found!")

def main():
    """Run all tests"""
    print("=" * 100)
    print("ORDER PROCESSING WIZARD TEST WITH VIN TRACKING")
    print("=" * 100)
    print(f"Test started at: {datetime.now()}")
    
    try:
        # Check inventory status
        if not check_bmw_inventory():
            print("\nNo BMW inventory available for testing!")
            return
        
        # Test CAO order
        cao_result = test_cao_order()
        
        # Test LIST order
        list_result = test_list_order()
        
        # Verify VIN tracking
        verify_vin_tracking()
        
        # Final inventory check
        print("\n" + "=" * 50)
        print("FINAL INVENTORY STATUS AFTER PROCESSING")
        print("=" * 50)
        check_bmw_inventory()
        
        print(f"\nTest completed at: {datetime.now()}")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        print(f"\nTest failed: {e}")

if __name__ == "__main__":
    main()