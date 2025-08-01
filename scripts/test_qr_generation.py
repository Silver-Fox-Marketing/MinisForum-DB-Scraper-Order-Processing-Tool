#!/usr/bin/env python3
"""
Test QR code generation with enhanced vehicle-specific logic
"""

import sys
import logging
from pathlib import Path
from database_connection import db_manager
from correct_order_processing import CorrectOrderProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_qr_generation():
    """Test the enhanced QR code generation logic"""
    
    processor = CorrectOrderProcessor()
    
    # Test dealerships
    test_dealerships = [
        'BMW of West St. Louis',
        'Columbia Honda', 
        'Dave Sinclair Lincoln',
    ]
    
    for dealership in test_dealerships:
        logger.info(f"\n=== Testing QR Generation for {dealership} ===")
        
        try:
            # Get sample vehicles
            vehicles = db_manager.execute_query("""
                SELECT vin, stock, year, make, model, type, vehicle_url 
                FROM raw_vehicle_data 
                WHERE location = %s 
                LIMIT 3
            """, (dealership,))
            
            if not vehicles:
                logger.warning(f"No vehicles found for {dealership}")
                continue
            
            # Test QR content generation for each vehicle
            for vehicle in vehicles:
                logger.info(f"\nTesting vehicle: {vehicle['year']} {vehicle['make']} {vehicle['model']}")
                logger.info(f"  VIN: {vehicle['vin']}")
                logger.info(f"  Stock: {vehicle['stock']}")
                logger.info(f"  Original URL: {vehicle['vehicle_url']}")
                
                # Test the new QR content logic
                qr_content = processor._get_vehicle_qr_content(vehicle, dealership)
                logger.info(f"  QR Content: {qr_content}")
                
                # Test URL specificity check
                url_specific = processor._is_vehicle_specific_url(
                    vehicle['vehicle_url'], 
                    vehicle['vin'], 
                    vehicle['stock']
                )
                logger.info(f"  URL is vehicle-specific: {url_specific}")
                
                # Test URL construction
                constructed_url = processor._construct_vehicle_url(dealership, vehicle)
                if constructed_url:
                    logger.info(f"  Constructed URL: {constructed_url}")
                else:
                    logger.info(f"  No URL could be constructed")
                    
        except Exception as e:
            logger.error(f"Error testing {dealership}: {e}")
    
    # Summary of improvements
    logger.info(f"\n=== QR Code Enhancement Summary ===")
    logger.info("✅ QR codes will now use:")
    logger.info("  1. Vehicle-specific URLs (if detected)")
    logger.info("  2. Constructed URLs based on dealership patterns") 
    logger.info("  3. VIN numbers (most reliable identifier)")
    logger.info("  4. Stock numbers (dealership-specific)")
    logger.info("  5. Vehicle descriptions (fallback)")
    logger.info("")
    logger.info("❌ QR codes will avoid:")
    logger.info("  - Generic dealership homepage URLs")
    logger.info("  - Empty or invalid URLs")
    logger.info("  - Non-vehicle-specific links")

def test_specific_vehicle_order():
    """Test a complete order generation with QR improvements"""
    
    logger.info(f"\n=== Testing Complete Order Generation ===")
    
    processor = CorrectOrderProcessor()
    
    # Test with BMW (known to have URL issues)
    dealership = 'BMW of West St. Louis'
    template_type = 'shortcut_pack'
    
    logger.info(f"Processing CAO order for {dealership}...")
    
    try:
        result = processor.process_cao_order(dealership, template_type)
        
        if result['success']:
            logger.info("✅ Order processed successfully!")
            logger.info(f"  Total vehicles: {result['total_vehicles']}")
            logger.info(f"  New vehicles: {result['new_vehicles']}")
            logger.info(f"  QR codes generated: {result['qr_codes_generated']}")
            logger.info(f"  QR folder: {result['qr_folder']}")
            logger.info(f"  CSV file: {result['csv_file']}")
        else:
            logger.error(f"❌ Order processing failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"❌ Error during order generation: {e}")

if __name__ == "__main__":
    print("Testing QR code generation improvements...")
    
    # Test QR content logic
    test_qr_generation()
    
    print("\n" + "="*50)
    print("Would you like to test complete order generation? (y/n)")
    response = input().lower().strip()
    
    if response == 'y':
        test_specific_vehicle_order()
    else:
        print("QR logic testing complete!")