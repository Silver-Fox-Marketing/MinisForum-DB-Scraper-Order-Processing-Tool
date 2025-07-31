#!/usr/bin/env python3
"""
Debug Database Search
====================

Check what data exists in the database and test search queries directly.

Author: Silver Fox Assistant  
Created: 2025-07-29
"""

import sys
from pathlib import Path
from database_connection import db_manager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_database():
    """Debug database contents and search functionality"""
    
    print("\n" + "="*60)
    print(">> DATABASE DEBUGGING AND SEARCH TEST")
    print("="*60)
    
    try:
        # Check total count
        print("\n[CHECK] Getting total vehicle count...")
        total_count = db_manager.execute_query("SELECT COUNT(*) as count FROM raw_vehicle_data")
        if total_count:
            print(f"Total vehicles in raw_vehicle_data: {total_count[0]['count']}")
        
        # Check sample data
        print("\n[CHECK] Getting sample vehicle data...")
        sample_data = db_manager.execute_query("""
            SELECT vin, make, model, location, import_timestamp, year, price
            FROM raw_vehicle_data 
            ORDER BY import_timestamp DESC 
            LIMIT 10
        """)
        
        if sample_data:
            print("Sample vehicles:")
            for vehicle in sample_data:
                print(f"  - {vehicle['year']} {vehicle['make']} {vehicle['model']} | {vehicle['location']} | {vehicle['vin']}")
        else:
            print("No sample data found!")
            
        # Check unique makes
        print("\n[CHECK] Getting unique makes...")
        makes = db_manager.execute_query("""
            SELECT DISTINCT make, COUNT(*) as count 
            FROM raw_vehicle_data 
            GROUP BY make 
            ORDER BY count DESC 
            LIMIT 10
        """)
        
        if makes:
            print("Top makes:")
            for make in makes:
                print(f"  - {make['make']}: {make['count']} vehicles")
        
        # Check unique dealers
        print("\n[CHECK] Getting unique dealers...")
        dealers = db_manager.execute_query("""
            SELECT DISTINCT location, COUNT(*) as count 
            FROM raw_vehicle_data 
            GROUP BY location 
            ORDER BY count DESC 
            LIMIT 10
        """)
        
        if dealers:
            print("Top dealers:")
            for dealer in dealers:
                print(f"  - {dealer['location']}: {dealer['count']} vehicles")
        
        # Test search query like the API would use
        print("\n[TEST] Testing search query for 'Lincoln'...")
        search_result = db_manager.execute_query("""
            SELECT vin, make, model, location, year, price, import_timestamp
            FROM raw_vehicle_data 
            WHERE make ILIKE %s OR model ILIKE %s OR location ILIKE %s
            LIMIT 5
        """, ('%Lincoln%', '%Lincoln%', '%Lincoln%'))
        
        if search_result:
            print("Lincoln search results:")
            for vehicle in search_result:
                print(f"  - {vehicle['year']} {vehicle['make']} {vehicle['model']} | {vehicle['location']} | ${vehicle['price']}")
        else:
            print("No Lincoln vehicles found!")
            
        # Test search query for BMW
        print("\n[TEST] Testing search query for 'BMW'...")
        bmw_result = db_manager.execute_query("""
            SELECT vin, make, model, location, year, price, import_timestamp
            FROM raw_vehicle_data 
            WHERE make ILIKE %s OR model ILIKE %s OR location ILIKE %s
            LIMIT 5
        """, ('%BMW%', '%BMW%', '%BMW%'))
        
        if bmw_result:
            print("BMW search results:")
            for vehicle in bmw_result:
                print(f"  - {vehicle['year']} {vehicle['make']} {vehicle['model']} | {vehicle['location']} | ${vehicle['price']}")
        else:
            print("No BMW vehicles found!")
            
        # Check date range
        print("\n[CHECK] Getting date range...")
        date_info = db_manager.execute_query("""
            SELECT 
                MIN(import_timestamp) as earliest,
                MAX(import_timestamp) as latest,
                COUNT(DISTINCT DATE(import_timestamp)) as unique_dates
            FROM raw_vehicle_data
        """)
        
        if date_info:
            print(f"Date range: {date_info[0]['earliest']} to {date_info[0]['latest']}")
            print(f"Unique dates: {date_info[0]['unique_dates']}")
            
    except Exception as e:
        logger.error(f"Error during database debug: {e}")
        print(f"[ERROR] Database debug failed: {e}")
    
    print("\n" + "="*60)
    print(">> DATABASE DEBUG COMPLETE")
    print("="*60)

if __name__ == "__main__":
    debug_database()