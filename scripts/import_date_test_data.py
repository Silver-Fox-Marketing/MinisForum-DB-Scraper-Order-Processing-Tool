#!/usr/bin/env python3
"""
Import Date Test Data
====================

Simple script to manually insert historical vehicle data with different timestamps
for testing the date search functionality. Uses a subset of existing data to avoid
database constraints.

Author: Silver Fox Assistant  
Created: 2025-07-29
"""

import sys
from pathlib import Path
from database_connection import db_manager
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_data_with_dates():
    """Create test vehicle data with different import dates"""
    
    # Define test datasets with different dates
    test_dates = [
        (datetime.now() - timedelta(days=7), "7 days ago"),
        (datetime.now() - timedelta(days=14), "14 days ago"), 
        (datetime.now() - timedelta(days=30), "30 days ago")
    ]
    
    # Sample vehicle data for each date
    sample_vehicles = [
        {
            'vin': 'TEST001DATE7DAYS00',
            'stock': 'T7-001',
            'type': 'used',
            'year': 2022,
            'make': 'Ford',
            'model': 'F-150',
            'trim': 'XLT',
            'ext_color': 'Oxford White',
            'price': 35999,
            'body_style': 'Crew Cab',
            'fuel_type': 'Regular Unleaded',
            'location': 'Test Date Dealer',
            'vehicle_url': 'https://test.com/vehicle1'
        },
        {
            'vin': 'TEST002DATE14DAYS0',
            'stock': 'T14-002',
            'type': 'new',
            'year': 2024,
            'make': 'Chevrolet',
            'model': 'Silverado',
            'trim': 'LT',
            'ext_color': 'Summit White',
            'price': 42999,
            'body_style': 'Crew Cab',
            'fuel_type': 'Regular Unleaded',
            'location': 'Test Date Dealer',
            'vehicle_url': 'https://test.com/vehicle2'
        },
        {
            'vin': 'TEST003DATE30DAYS0',
            'stock': 'T30-003',
            'type': 'cpo',
            'year': 2023,
            'make': 'Toyota',
            'model': 'Camry',
            'trim': 'LE',
            'ext_color': 'Midnight Black',
            'price': 28999,
            'body_style': 'Sedan',
            'fuel_type': 'Regular Unleaded',
            'location': 'Test Date Dealer',
            'vehicle_url': 'https://test.com/vehicle3'
        }
    ]
    
    total_added = 0
    
    print("\n" + "="*60)
    print(">> ADDING DATE TEST DATA FOR SEARCH TESTING")
    print("="*60)
    
    for i, (target_date, date_label) in enumerate(test_dates):
        vehicle_data = sample_vehicles[i]
        
        print(f"\n[DATE] Adding vehicle for {date_label}...")
        print(f"       Date: {target_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"       Vehicle: {vehicle_data['year']} {vehicle_data['make']} {vehicle_data['model']}")
        
        try:
            # Insert multiple vehicles for each date to provide more test data
            for j in range(5):  # 5 vehicles per date
                # Modify VIN and stock to be unique
                unique_vin = f"{vehicle_data['vin'][:-2]}{j:02d}"
                unique_stock = f"{vehicle_data['stock']}-{j+1}"
                
                # Insert into raw_vehicle_data
                db_manager.execute_query("""
                    INSERT INTO raw_vehicle_data 
                    (vin, stock, type, year, make, model, trim, ext_color, 
                     price, body_style, fuel_type, location, vehicle_url, status, import_timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    unique_vin,
                    unique_stock,
                    vehicle_data['type'],
                    vehicle_data['year'],
                    vehicle_data['make'],
                    vehicle_data['model'], 
                    vehicle_data['trim'],
                    vehicle_data['ext_color'],
                    vehicle_data['price'] + (j * 500),  # Vary price slightly
                    vehicle_data['body_style'],
                    vehicle_data['fuel_type'],
                    vehicle_data['location'],
                    vehicle_data['vehicle_url'],
                    'available',
                    target_date
                ))
                
                total_added += 1
                
        except Exception as e:
            logger.error(f"Error adding test data for {date_label}: {e}")
    
    # Get updated database stats
    try:
        raw_count = db_manager.execute_query("SELECT COUNT(*) as count FROM raw_vehicle_data")
        total_vehicles = raw_count[0]['count'] if raw_count else 0
        
        # Get date range
        date_range = db_manager.execute_query("""
            SELECT 
                MIN(import_timestamp) as earliest,
                MAX(import_timestamp) as latest,
                COUNT(DISTINCT DATE(import_timestamp)) as unique_dates
            FROM raw_vehicle_data
        """)
        
        if date_range:
            earliest = date_range[0]['earliest']
            latest = date_range[0]['latest'] 
            unique_dates = date_range[0]['unique_dates']
        else:
            earliest = latest = unique_dates = "Unknown"
            
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        total_vehicles = "Unknown"
        earliest = latest = unique_dates = "Unknown"
    
    print("\n" + "="*60)
    print(">> DATE TEST DATA IMPORT COMPLETE!")
    print("="*60)
    print(f"[STATS] Total vehicles in database: {total_vehicles}")
    print(f"[STATS] Test vehicles added: {total_added}")
    print(f"[DATES] Date range: {earliest} to {latest}")
    print(f"[DATES] Unique dates in database: {unique_dates}")
    print(f"[READY] Ready to test Date Search functionality!")
    print("\nTest scenarios:")
    print("   1. Search for 'Ford' and filter by date range")
    print("   2. Search for 'Test Date Dealer' vehicles")
    print("   3. Use date filters to show only recent vs older data")
    print("   4. Test sorting by date added")
    print("="*60)
    
    return True

if __name__ == "__main__":
    create_test_data_with_dates()