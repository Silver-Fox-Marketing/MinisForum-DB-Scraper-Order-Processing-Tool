#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
from database_connection import DatabaseManager

def main():
    print("=== CHECKING RAW DATA FOR NORMALIZATION ISSUES ===")
    
    db_manager = DatabaseManager()
    
    # All 32 VINs from the CAO result
    all_vins = [
        # Expected 9
        '1C4HJXDG2JW305627',
        '3FA6P0H74FR234230',
        '4S4WMAMD0N3469009',
        '1C4HJXCG7JW174387',
        '1FMCU0F75EUD29617',
        '1GCPYBEHXMZ173012',
        '3VV3B7AX6KM196670',
        '5TDKDRAH3PS008347',
        'KNMAT2MT3LP513444',
        # Extra 23
        '1FM5K8D89FGA60210',
        '1C4PJXDN4RW112692',
        '5FNRL6H87RB022989',
        '3GNKBBRA0KS610414',
        '1C4HJXEG2JW287869',
        '3FMCR9D9XPRE32312',
        '5N1BT3BBXPC852781',
        '2C3CDXBG8NH157383',
        '1G1ZD5ST0NF101598',
        '5NTJDDAF2NH002265',
        '1FMDE5BH0MLA93699',
        '1FMCU9H96NUA00136',
        '1C4RJFBG8MC599686',
        '55SWF4KBXHU195101',
        '5YFBU4EE6DP173803',
        '1FMEE5DH8NLA81738',
        '1N4BL4BV1RN411252',
        '1HGCY1F36RA055932',
        'W1K5J4GB5PN357159',
        '3MW39FS02P8D51749',
        'KL77LJE2XRC022814',
        '1FTBR1Y80PKA55237',
        '3TYAX5GN6PT077451'
    ]
    
    # Status values that should normalize to "offlot" per normalization map
    offlot_statuses = [
        'In-transit', 'In-Transit', 'Allocated', 'In-Build-Phase', 
        'In Transit', 'In Transit to U.S.', 'Arriving Soon', 
        'In Production', 'Build Phase', 'Being Built', 
        'Courtesy Vehicle', 'In-Service Courtesy Vehicle', 
        'Dealer Ordered', 'In-Service FCTP', 'In-service',
        'off lot', 'Off Lot'
    ]
    
    print("\n1. CHECKING RAW DATA FOR ALL 32 VEHICLES:")
    print("-" * 120)
    print("VIN | Stock | Raw Status | Raw Type | Price | Year Make Model | ISSUES")
    print("-" * 120)
    
    # Get raw data for all VINs
    placeholders = ', '.join(['%s'] * len(all_vins))
    query = f'''
        SELECT 
            rvd.vin,
            rvd.stock,
            rvd.status,
            rvd.type,
            rvd.price,
            rvd.year,
            rvd.make,
            rvd.model,
            rvd.trim,
            rvd.ext_color
        FROM raw_vehicle_data rvd
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE rvd.vin IN ({placeholders})
        AND rvd.location = 'Suntrup Ford Kirkwood'
        AND si.status = 'active'
        ORDER BY rvd.vin
    '''
    
    results = db_manager.execute_query(query, tuple(all_vins))
    
    vehicles_with_issues = []
    courtesy_vehicles = []
    in_service_vehicles = []
    
    for vehicle in results:
        vin = vehicle['vin']
        stock = vehicle['stock']
        status = vehicle['status']
        v_type = vehicle['type']
        price = vehicle['price']
        vehicle_desc = f"{vehicle['year']} {vehicle['make']} {vehicle['model']}"
        
        issues = []
        
        # Check if status should normalize to offlot
        if status:
            for offlot_status in offlot_statuses:
                if offlot_status.lower() in status.lower():
                    issues.append(f'OFFLOT-STATUS: {status}')
                    vehicles_with_issues.append((vin, status))
                    
                    if 'courtesy' in status.lower():
                        courtesy_vehicles.append((vin, status))
                    elif 'in-service' in status.lower() or 'fctp' in status.lower():
                        in_service_vehicles.append((vin, status))
                    break
        
        # Check for missing stock
        if not stock or stock.strip() == '' or stock == '*':
            issues.append('NO-STOCK')
        
        # Check if it's in the expected 9
        is_expected = vin in all_vins[:9]
        
        issue_str = ' | '.join(issues) if issues else 'CLEAN'
        expected_str = '[EXPECTED]' if is_expected else '[EXTRA]'
        
        print(f"{vin} | {stock or 'NONE'} | {status or 'N/A'} | {v_type} | ${price or 0} | {vehicle_desc} | {issue_str} {expected_str}")
    
    print("-" * 120)
    
    print(f"\n2. SUMMARY OF ISSUES:")
    print(f"Total vehicles with offlot status issues: {len(vehicles_with_issues)}")
    print(f"  - Courtesy Vehicles: {len(courtesy_vehicles)}")
    print(f"  - In-Service/FCTP Vehicles: {len(in_service_vehicles)}")
    
    if vehicles_with_issues:
        print("\n3. VEHICLES THAT SHOULD BE FILTERED OUT (OFFLOT STATUS):")
        for vin, status in vehicles_with_issues:
            print(f"  {vin}: {status}")
    
    # Check how these are being normalized
    print("\n4. CHECKING NORMALIZATION FOR PROBLEMATIC VEHICLES:")
    if vehicles_with_issues:
        problem_vins = [v[0] for v in vehicles_with_issues]
        placeholders2 = ', '.join(['%s'] * len(problem_vins))
        
        normalized_query = f'''
            SELECT 
                nvd.vin,
                rvd.status as raw_status,
                nvd.status as normalized_status,
                nvd.on_lot_status,
                nvd.vehicle_condition
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE nvd.vin IN ({placeholders2})
            AND nvd.location = 'Suntrup Ford Kirkwood'
            AND si.status = 'active'
        '''
        
        norm_results = db_manager.execute_query(normalized_query, tuple(problem_vins))
        
        print("VIN | Raw Status | Normalized Status | On Lot Status | Condition")
        print("-" * 100)
        for norm in norm_results:
            print(f"{norm['vin']} | {norm['raw_status']} | {norm['normalized_status']} | {norm['on_lot_status']} | {norm['vehicle_condition']}")
            
            # Check if normalization is wrong
            if norm['on_lot_status'] != 'offlot' and any(s.lower() in norm['raw_status'].lower() for s in ['courtesy', 'in-service', 'fctp']):
                print(f"  [ERROR] Should be 'offlot' but normalized as '{norm['on_lot_status']}'")
    
    db_manager.close()

if __name__ == "__main__":
    main()