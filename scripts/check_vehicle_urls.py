#!/usr/bin/env python3
"""
Check vehicle URLs in the database to diagnose QR code issue
"""

import sys
from pathlib import Path
from database_connection import db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_vehicle_urls():
    """Check sample vehicle URLs from different dealerships"""
    
    dealerships = [
        'BMW of West St. Louis',
        'Columbia Honda',
        'Dave Sinclair Lincoln',
        'Test Integration Dealer'
    ]
    
    for dealership in dealerships:
        logger.info(f"\n=== Checking {dealership} ===")
        
        try:
            # Get sample vehicles with their URLs
            vehicles = db_manager.execute_query("""
                SELECT vin, stock, year, make, model, vehicle_url 
                FROM raw_vehicle_data 
                WHERE location = %s 
                LIMIT 5
            """, (dealership,))
            
            if not vehicles:
                logger.warning(f"No vehicles found for {dealership}")
                continue
                
            for vehicle in vehicles:
                vin = vehicle['vin']
                stock = vehicle['stock'] 
                year = vehicle['year']
                make = vehicle['make']
                model = vehicle['model']
                url = vehicle['vehicle_url']
                
                logger.info(f"  {year} {make} {model}")
                logger.info(f"  VIN: {vin}")
                logger.info(f"  Stock: {stock}")
                logger.info(f"  URL: {url}")
                
                # Check if URL looks like a specific vehicle page
                if url:
                    if '/inventory/' in url or '/vehicle/' in url or 'vin=' in url.lower() or 'stock=' in url.lower():
                        logger.info("  ✅ URL appears to be vehicle-specific")
                    else:
                        logger.warning("  ⚠️ URL might be generic/homepage")
                else:
                    logger.error("  ❌ No URL found")
                    
                logger.info("")
                
        except Exception as e:
            logger.error(f"Error checking {dealership}: {e}")
            
    # Also check for any patterns in URLs
    logger.info("\n=== URL Pattern Analysis ===")
    try:
        url_patterns = db_manager.execute_query("""
            SELECT 
                location as dealership,
                COUNT(*) as total_vehicles,
                COUNT(vehicle_url) as vehicles_with_urls,
                COUNT(DISTINCT vehicle_url) as unique_urls
            FROM raw_vehicle_data
            WHERE location IN %s
            GROUP BY location
        """, (tuple(dealerships),))
        
        for pattern in url_patterns:
            logger.info(f"\n{pattern['dealership']}:")
            logger.info(f"  Total vehicles: {pattern['total_vehicles']}")
            logger.info(f"  Vehicles with URLs: {pattern['vehicles_with_urls']}")
            logger.info(f"  Unique URLs: {pattern['unique_urls']}")
            
            if pattern['unique_urls'] == 1 and pattern['vehicles_with_urls'] > 1:
                logger.warning("  ⚠️ All vehicles have the same URL (likely homepage)")
            elif pattern['unique_urls'] < pattern['vehicles_with_urls'] / 2:
                logger.warning("  ⚠️ Many duplicate URLs detected")
                
    except Exception as e:
        logger.error(f"Error analyzing URL patterns: {e}")

if __name__ == "__main__":
    check_vehicle_urls()