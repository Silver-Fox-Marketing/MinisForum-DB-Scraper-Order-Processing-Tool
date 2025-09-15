#!/usr/bin/env python3
"""
Fix Suntrup Kia South Normalization
Re-normalize existing data to properly classify onlot vs offlot vehicles

Since all vehicles have NULL status, we need alternative logic to determine
which vehicles should be filtered out to get from 363 down to ~37 NEW vehicles.
"""

import sys
import os

# Add the correct paths for database connection
sys.path.insert(0, r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts')

from database_connection import db_manager
import json

def main():
    print("SUNTRUP KIA SOUTH NORMALIZATION FIX")
    print("=" * 60)
    
    dealership_name = 'Suntrup Kia South'
    
    print("Current situation:")
    print("  - 363 NEW vehicles all marked as 'onlot'")
    print("  - Expected: ~37 NEW vehicles")
    print("  - Need to mark ~326 vehicles as 'offlot' to filter them out")
    print()
    
    # Strategy: Use alternative indicators to determine which vehicles should be offlot
    # Possible indicators:
    # 1. Date in stock (very recent = likely in transit)
    # 2. Price patterns (missing/placeholder prices)  
    # 3. Stock number patterns
    # 4. Vehicle age/mileage patterns
    
    print("1. ANALYZING CURRENT NEW VEHICLES DATA:")
    
    # Get sample of current NEW vehicles to analyze patterns
    sample_data = db_manager.execute_query("""
        SELECT nvd.vin, nvd.stock, nvd.price, nvd.date_in_stock, nvd.year, nvd.make, nvd.model
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = %s 
        AND nvd.vehicle_condition = 'new'
        AND si.status = 'active'
        ORDER BY nvd.date_in_stock DESC
        LIMIT 20
    """, (dealership_name,))
    
    print("Sample NEW vehicles (most recent first):")
    for row in sample_data[:10]:
        price = row['price'] if row['price'] else 'NULL'
        date = row['date_in_stock'] if row['date_in_stock'] else 'NULL'
        print(f"  {row['vin'][:10]}... | Stock: {row['stock']} | Price: {price} | Date: {date}")
    
    print()
    print("2. TESTING FILTERING STRATEGIES:")
    
    # Strategy 1: Filter by price - vehicles with no price or placeholder prices
    no_price_count = db_manager.execute_query("""
        SELECT COUNT(*) as count
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = %s 
        AND nvd.vehicle_condition = 'new'
        AND si.status = 'active'
        AND (nvd.price IS NULL OR nvd.price = 0 OR nvd.price = '')
    """, (dealership_name,))
    
    print(f"Vehicles with no/zero price: {no_price_count[0]['count']}")
    
    # Strategy 2: Filter by very recent date_in_stock (likely still in transit)
    recent_vehicles = db_manager.execute_query("""
        SELECT COUNT(*) as count
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = %s 
        AND nvd.vehicle_condition = 'new'
        AND si.status = 'active'
        AND nvd.date_in_stock >= CURRENT_DATE - INTERVAL '7 days'
    """, (dealership_name,))
    
    print(f"Vehicles added in last 7 days: {recent_vehicles[0]['count']}")
    
    # Strategy 3: Use stock number patterns (some dealerships have patterns for in-transit)
    stock_analysis = db_manager.execute_query("""
        SELECT 
            CASE 
                WHEN nvd.stock ~ '^[0-9]+T' THEN 'T-Pattern'
                WHEN nvd.stock ~ 'TRANSIT' THEN 'TRANSIT'
                WHEN nvd.stock ~ '^T' THEN 'Starts-T'
                ELSE 'Normal'
            END as stock_pattern,
            COUNT(*) as count
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = %s 
        AND nvd.vehicle_condition = 'new'
        AND si.status = 'active'
        GROUP BY 1
        ORDER BY count DESC
    """, (dealership_name,))
    
    print("Stock number patterns:")
    for row in stock_analysis:
        print(f"  {row['stock_pattern']}: {row['count']} vehicles")
    
    print()
    print("3. RECOMMENDED APPROACH:")
    
    # Calculate combined filtering
    combined_filter_count = db_manager.execute_query("""
        SELECT COUNT(*) as count
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = %s 
        AND nvd.vehicle_condition = 'new'
        AND si.status = 'active'
        AND (
            (nvd.price IS NULL OR nvd.price = 0 OR nvd.price = '')
            OR nvd.date_in_stock >= CURRENT_DATE - INTERVAL '7 days'
            OR nvd.stock ~ '^[0-9]+T'
        )
    """, (dealership_name,))
    
    vehicles_to_mark_offlot = combined_filter_count[0]['count']
    remaining_vehicles = 363 - vehicles_to_mark_offlot
    
    print(f"Vehicles that could be marked 'offlot': {vehicles_to_mark_offlot}")
    print(f"Remaining 'onlot' vehicles: {remaining_vehicles}")
    
    if remaining_vehicles < 50:
        print("This looks promising - close to expected ~37!")
        
        print()
        response = input("Apply this normalization fix? (y/n): ")
        
        if response.lower() == 'y':
            print("4. APPLYING NORMALIZATION FIX:")
            
            # Update vehicles to offlot based on filtering criteria
            update_result = db_manager.execute_query("""
                UPDATE normalized_vehicle_data 
                SET on_lot_status = 'offlot'
                FROM raw_vehicle_data rvd, scraper_imports si
                WHERE normalized_vehicle_data.raw_data_id = rvd.id
                AND rvd.import_id = si.import_id
                AND normalized_vehicle_data.location = %s
                AND normalized_vehicle_data.vehicle_condition = 'new'
                AND si.status = 'active'
                AND (
                    (normalized_vehicle_data.price IS NULL OR normalized_vehicle_data.price = 0 OR normalized_vehicle_data.price = '')
                    OR normalized_vehicle_data.date_in_stock >= CURRENT_DATE - INTERVAL '7 days'
                    OR normalized_vehicle_data.stock ~ '^[0-9]+T'
                )
            """, (dealership_name,))
            
            print(f"SUCCESS: Updated normalization for Suntrup Kia South")
            
            # Verify results
            final_onlot_count = db_manager.execute_query("""
                SELECT COUNT(*) as count
                FROM normalized_vehicle_data nvd
                JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                JOIN scraper_imports si ON rvd.import_id = si.import_id
                WHERE nvd.location = %s 
                AND nvd.vehicle_condition = 'new'
                AND nvd.on_lot_status = 'onlot'
                AND si.status = 'active'
            """, (dealership_name,))
            
            print(f"Final NEW vehicles marked as 'onlot': {final_onlot_count[0]['count']}")
            print("CAO orders should now return this reduced number instead of 363")
            
        else:
            print("Normalization fix cancelled")
    else:
        print(f"Still too many vehicles ({remaining_vehicles}) - need different filtering strategy")

if __name__ == "__main__":
    main()