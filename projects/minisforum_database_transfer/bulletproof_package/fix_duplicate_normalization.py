#!/usr/bin/env python3
"""
FIX DUPLICATE NORMALIZATION ISSUE
=================================
Update existing normalized records to point to active Import 12 raw_data_ids
This resolves the unique constraint violation and ensures CAO works properly.
"""

import sys
from pathlib import Path

current_file = Path(__file__).resolve()
sys.path.insert(0, str(current_file.parent / 'scripts'))

from database_connection import db_manager

def fix_duplicate_normalization():
    """Update normalized records to point to active Import 12 raw data"""
    print('=== FIXING DUPLICATE NORMALIZATION ISSUE ===')
    
    try:
        # Step 1: Check current status
        print('1. Check current normalization status...')
        status_query = """
            SELECT 
                si.import_id,
                si.status,
                COUNT(rvd.id) as raw_count,
                COUNT(nvd.id) as normalized_count
            FROM scraper_imports si
            JOIN raw_vehicle_data rvd ON si.import_id = rvd.import_id
            LEFT JOIN normalized_vehicle_data nvd ON rvd.id = nvd.raw_data_id
            WHERE rvd.location = 'Volvo Cars West County'
            GROUP BY si.import_id, si.status
            ORDER BY si.import_id DESC
        """
        
        status_results = db_manager.execute_query(status_query)
        print('Import status for Volvo:')
        for result in status_results:
            print(f"  Import {result['import_id']} ({result['status']}): {result['raw_count']} raw, {result['normalized_count']} normalized")
        
        # Step 2: Find VINs that exist in multiple imports
        print('\n2. Find VINs in multiple imports...')
        duplicate_vins_query = """
            SELECT vin, COUNT(DISTINCT import_id) as import_count
            FROM raw_vehicle_data
            WHERE location = 'Volvo Cars West County'
            GROUP BY vin
            HAVING COUNT(DISTINCT import_id) > 1
            ORDER BY import_count DESC
            LIMIT 10
        """
        
        duplicate_vins = db_manager.execute_query(duplicate_vins_query)
        print(f'Sample VINs in multiple imports: {len(duplicate_vins)}')
        for dup in duplicate_vins[:5]:
            print(f"  {dup['vin']}: appears in {dup['import_count']} imports")
        
        # Step 3: Update normalized records to point to Import 12 (active)
        print('\n3. Update normalized records to use active Import 12 raw_data_ids...')
        
        # For each VIN that has both normalized data AND Import 12 raw data,
        # update the normalized record to point to the Import 12 raw_data_id
        update_query = """
            UPDATE normalized_vehicle_data 
            SET raw_data_id = import12_raw.id
            FROM (
                SELECT DISTINCT ON (vin) vin, id 
                FROM raw_vehicle_data 
                WHERE import_id = 12 
                AND location = 'Volvo Cars West County'
            ) AS import12_raw
            WHERE normalized_vehicle_data.vin = import12_raw.vin
            AND normalized_vehicle_data.location = 'Volvo Cars West County'
            RETURNING normalized_vehicle_data.vin
        """
        
        updated_vins = db_manager.execute_query(update_query)
        print(f'Updated {len(updated_vins)} normalized records to point to Import 12')
        
        # Step 4: Now normalize any remaining VINs from Import 12 that don't have normalized records
        print('\n4. Normalize remaining Import 12 VINs without normalized records...')
        
        from scraper_data_normalizer import ScraperDataNormalizer
        normalizer = ScraperDataNormalizer()
        
        # Get VINs in Import 12 that still don't have normalized records
        missing_normalized_query = """
            SELECT r.id, r.vin, r.type, r.status, r.year, r.make, r.model, r.trim,
                   r.price, r.msrp, r.stock, r.vehicle_url, r.location
            FROM raw_vehicle_data r
            LEFT JOIN normalized_vehicle_data n ON r.id = n.raw_data_id
            WHERE r.import_id = 12 
            AND r.location = 'Volvo Cars West County'
            AND n.id IS NULL
            ORDER BY r.id
        """
        
        missing_records = db_manager.execute_query(missing_normalized_query)
        print(f'Found {len(missing_records)} Import 12 VINs still needing normalization')
        
        created_count = 0
        for vehicle in missing_records:
            try:
                # Normalize the vehicle data
                raw_type = vehicle.get('type', '')
                raw_status = vehicle.get('status', '')
                
                normalized_type = normalizer.normalize_vehicle_type(raw_type)
                lot_status = normalizer.normalize_lot_status(raw_status)
                
                # Insert normalized record
                db_manager.execute_query('''
                    INSERT INTO normalized_vehicle_data 
                    (raw_data_id, vin, stock, vehicle_condition, year, make, model, trim,
                     status, price, msrp, location, vehicle_url, on_lot_status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ''', (
                    vehicle['id'],
                    vehicle['vin'],
                    vehicle.get('stock', ''),
                    normalized_type,
                    vehicle.get('year', 0),
                    vehicle.get('make', ''),
                    vehicle.get('model', ''),
                    vehicle.get('trim', ''),
                    raw_status,
                    vehicle.get('price'),
                    vehicle.get('msrp'),
                    vehicle.get('location', ''),
                    vehicle.get('vehicle_url', ''),
                    lot_status
                ))
                
                created_count += 1
                
                if created_count <= 5:
                    print(f"  Created normalized record for {vehicle['vin']}: '{raw_status}' -> '{lot_status}'")
                
            except Exception as e:
                print(f"  ERROR normalizing {vehicle.get('vin', 'unknown')}: {e}")
        
        print(f'Created {created_count} new normalized records')
        
        # Step 5: Verify the fix
        print('\n5. Verify the fix...')
        final_coverage = db_manager.execute_query("""
            SELECT 
                COUNT(rvd.id) as total_raw,
                COUNT(nvd.id) as total_normalized,
                COUNT(rvd.id) - COUNT(nvd.id) as missing_normalized,
                COUNT(CASE WHEN nvd.on_lot_status = 'onlot' THEN 1 END) as onlot_count
            FROM raw_vehicle_data rvd
            LEFT JOIN normalized_vehicle_data nvd ON rvd.id = nvd.raw_data_id
            WHERE rvd.import_id = 12 
            AND rvd.location = 'Volvo Cars West County'
        """)
        
        if final_coverage:
            cov = final_coverage[0]
            print(f'Final Import 12 status:')
            print(f'  Total RAW records: {cov["total_raw"]}')
            print(f'  Total NORMALIZED records: {cov["total_normalized"]}')
            print(f'  Missing NORMALIZED records: {cov["missing_normalized"]}')
            print(f'  On-lot vehicles: {cov["onlot_count"]}')
            
            if cov["missing_normalized"] == 0:
                print('SUCCESS: All Import 12 records now have normalized data!')
                return True
            else:
                print(f'WARNING: Still {cov["missing_normalized"]} missing normalized records')
                return False
        
        return False
        
    except Exception as e:
        print(f'ERROR during fix: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = fix_duplicate_normalization()
    if success:
        print('\nDUPLICATE NORMALIZATION ISSUE FIXED!')
        print('CAO should now return expected VINs for Volvo Cars West County.')
    else:
        print('\nFIX FAILED - Manual intervention required')