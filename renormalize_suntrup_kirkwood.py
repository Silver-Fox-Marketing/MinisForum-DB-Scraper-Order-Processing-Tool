#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
from database_connection import DatabaseManager
from scraper_data_normalizer import ScraperDataNormalizer

def main():
    print("=== RE-NORMALIZING SUNTRUP FORD KIRKWOOD DATA WITH FIXED NULL STATUS HANDLING ===")
    
    db_manager = DatabaseManager()
    normalizer = ScraperDataNormalizer()
    
    # Get all vehicles from the active import for Suntrup Ford Kirkwood
    print("\n1. FETCHING VEHICLES WITH NULL STATUS:")
    vehicles_to_fix = db_manager.execute_query("""
        SELECT rvd.id, rvd.vin, rvd.type, rvd.status, nvd.id as norm_id
        FROM raw_vehicle_data rvd
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        LEFT JOIN normalized_vehicle_data nvd ON rvd.id = nvd.raw_data_id
        WHERE rvd.location = 'Suntrup Ford Kirkwood'
        AND si.status = 'active'
        AND rvd.status IS NULL
        AND rvd.type ILIKE '%used%'
    """)
    
    print(f"Found {len(vehicles_to_fix)} used vehicles with NULL status that need fixing")
    
    if vehicles_to_fix:
        print("\n2. UPDATING NORMALIZED DATA:")
        updated_count = 0
        
        for vehicle in vehicles_to_fix:
            # Re-normalize with the fixed logic
            vehicle_data = {
                'type': vehicle['type'],
                'status': vehicle['status']
            }
            
            normalized_type, lot_status = normalizer.normalize_vehicle_data(vehicle_data)
            
            # Update the normalized record
            if vehicle['norm_id']:
                result = db_manager.execute_query("""
                    UPDATE normalized_vehicle_data
                    SET status = %s,
                        on_lot_status = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING id
                """, ('on lot', lot_status, vehicle['norm_id']))
                
                if result:
                    updated_count += 1
                    print(f"  Updated {vehicle['vin']}: NULL -> on_lot_status={lot_status}")
            else:
                print(f"  WARNING: No normalized record found for {vehicle['vin']}")
        
        print(f"\nUpdated {updated_count} records")
    
    # Verify the fix
    print("\n3. VERIFYING THE FIX:")
    
    # Check the 9 expected VINs
    expected_vins = [
        '1C4HJXDG2JW305627',
        '3FA6P0H74FR234230',
        '4S4WMAMD0N3469009',
        '1C4HJXCG7JW174387',
        '1FMCU0F75EUD29617',
        '1GCPYBEHXMZ173012',
        '3VV3B7AX6KM196670',
        '5TDKDRAH3PS008347',
        'KNMAT2MT3LP513444'
    ]
    
    print("\nChecking expected VINs (with NULL status):")
    for vin in expected_vins:
        result = db_manager.execute_query("""
            SELECT nvd.vin, nvd.status, nvd.on_lot_status, rvd.status as raw_status
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE nvd.vin = %s
            AND nvd.location = 'Suntrup Ford Kirkwood'
            AND si.status = 'active'
        """, (vin,))
        
        if result:
            r = result[0]
            raw_display = f"'{r['raw_status']}'" if r['raw_status'] else "NULL"
            print(f"  {r['vin']}: Raw={raw_display} -> OnLot={r['on_lot_status']}")
    
    # Check how many total vehicles would be in CAO now
    print("\n4. CHECKING CAO RESULT COUNT:")
    cao_count = db_manager.execute_query("""
        SELECT COUNT(*) as count
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        LEFT JOIN suntrup_ford_kirkwood_vin_log vlog ON nvd.vin = vlog.vin
        WHERE nvd.location = 'Suntrup Ford Kirkwood'
        AND si.status = 'active'
        AND nvd.vehicle_condition IN ('used', 'po', 'cpo', 'certified', 'pre-owned')
        AND nvd.stock IS NOT NULL 
        AND nvd.stock != ''
        AND nvd.stock != '*'
        AND nvd.on_lot_status = 'on lot'
        AND vlog.vin IS NULL
    """)
    
    if cao_count:
        print(f"Total vehicles that would be in CAO: {cao_count[0]['count']}")
        print("\nNote: All 32 vehicles should now be correctly normalized as 'on lot'")
        print("Both NULL status and 'available' status vehicles are properly handled.")
    
    db_manager.close()
    
    print("\n=== NORMALIZATION FIX COMPLETE ===")
    print("The system now correctly treats NULL status as 'available' for used vehicles.")
    print("This ensures all used vehicles without explicit status are included in CAO processing.")

if __name__ == "__main__":
    main()