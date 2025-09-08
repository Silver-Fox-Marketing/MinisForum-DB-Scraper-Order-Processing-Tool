#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
from database_connection import DatabaseManager

def main():
    print("=== INVESTIGATING STATUS N/A ISSUE ===")
    
    db_manager = DatabaseManager()
    
    # The 9 expected VINs
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
    
    # The 23 extra VINs (first 10)
    extra_vins = [
        '1FM5K8D89FGA60210',
        '1C4PJXDN4RW112692',
        '5FNRL6H87RB022989',
        '3GNKBBRA0KS610414',
        '1C4HJXEG2JW287869',
        '3FMCR9D9XPRE32312',
        '5N1BT3BBXPC852781',
        '2C3CDXBG8NH157383',
        '1G1ZD5ST0NF101598',
        '5NTJDDAF2NH002265'
    ]
    
    print("\n1. CHECKING RAW DATA STATUS VALUES:")
    print("-" * 100)
    
    # Check expected VINs
    print("\nEXPECTED 9 VINS (should be in CAO):")
    for vin in expected_vins:
        result = db_manager.execute_query("""
            SELECT rvd.vin, rvd.status, rvd.type, rvd.stock, rvd.import_id, rvd.year, rvd.make, rvd.model
            FROM raw_vehicle_data rvd
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE rvd.vin = %s
            AND rvd.location = 'Suntrup Ford Kirkwood'
            AND si.status = 'active'
        """, (vin,))
        
        if result:
            r = result[0]
            status_display = f"'{r['status']}'" if r['status'] else "NULL"
            print(f"  {r['vin']}: Status={status_display}, Type={r['type']}, Stock={r['stock']}, Import={r['import_id']}")
        else:
            print(f"  {vin}: NOT FOUND in active import")
    
    print("\nEXTRA VINS (should NOT be in CAO):")
    for vin in extra_vins:
        result = db_manager.execute_query("""
            SELECT rvd.vin, rvd.status, rvd.type, rvd.stock, rvd.import_id, rvd.year, rvd.make, rvd.model
            FROM raw_vehicle_data rvd
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE rvd.vin = %s
            AND rvd.location = 'Suntrup Ford Kirkwood'
            AND si.status = 'active'
        """, (vin,))
        
        if result:
            r = result[0]
            status_display = f"'{r['status']}'" if r['status'] else "NULL"
            print(f"  {r['vin']}: Status={status_display}, Type={r['type']}, Stock={r['stock']}, Import={r['import_id']}")
    
    # Check normalized data
    print("\n2. CHECKING NORMALIZED DATA:")
    print("-" * 100)
    
    print("\nEXPECTED 9 VINS NORMALIZED DATA:")
    for vin in expected_vins:
        result = db_manager.execute_query("""
            SELECT nvd.vin, nvd.status as norm_status, nvd.on_lot_status, 
                   nvd.vehicle_condition, rvd.status as raw_status
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
            norm_display = f"'{r['norm_status']}'" if r['norm_status'] else "NULL"
            print(f"  {r['vin']}: Raw={raw_display} -> Normalized={norm_display}, OnLot={r['on_lot_status']}, Condition={r['vehicle_condition']}")
        else:
            print(f"  {vin}: NOT FOUND in normalized data")
    
    print("\nEXTRA VINS NORMALIZED DATA:")
    for vin in extra_vins:
        result = db_manager.execute_query("""
            SELECT nvd.vin, nvd.status as norm_status, nvd.on_lot_status, 
                   nvd.vehicle_condition, rvd.status as raw_status
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
            norm_display = f"'{r['norm_status']}'" if r['norm_status'] else "NULL"
            print(f"  {r['vin']}: Raw={raw_display} -> Normalized={norm_display}, OnLot={r['on_lot_status']}, Condition={r['vehicle_condition']}")
    
    # Check if NULL status is the issue
    print("\n3. CHECKING FOR NULL STATUS FILTERING:")
    print("-" * 100)
    
    null_status_count = db_manager.execute_query("""
        SELECT COUNT(*) as count
        FROM raw_vehicle_data rvd
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE rvd.location = 'Suntrup Ford Kirkwood'
        AND si.status = 'active'
        AND rvd.status IS NULL
    """)
    
    available_status_count = db_manager.execute_query("""
        SELECT COUNT(*) as count
        FROM raw_vehicle_data rvd
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE rvd.location = 'Suntrup Ford Kirkwood'
        AND si.status = 'active'
        AND rvd.status = 'available'
    """)
    
    print(f"Vehicles with NULL status: {null_status_count[0]['count']}")
    print(f"Vehicles with 'available' status: {available_status_count[0]['count']}")
    
    # Check what the CAO filter sees
    print("\n4. WHAT THE CAO FILTER SEES:")
    print("-" * 100)
    
    cao_vehicles = db_manager.execute_query("""
        SELECT nvd.vin, nvd.status, nvd.on_lot_status
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
        AND vlog.vin IS NULL
        LIMIT 10
    """)
    
    print("First 10 vehicles CAO would process:")
    for v in cao_vehicles:
        status_display = f"'{v['status']}'" if v['status'] else "NULL"
        print(f"  {v['vin']}: Status={status_display}, OnLot={v['on_lot_status']}")
    
    db_manager.close()

if __name__ == "__main__":
    main()