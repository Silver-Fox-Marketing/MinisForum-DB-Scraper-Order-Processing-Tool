#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
from database_connection import DatabaseManager

def main():
    print("=== ANALYZING EXTRA VINS FOR SUNTRUP FORD KIRKWOOD ===")
    
    db_manager = DatabaseManager()
    
    # Expected VINs (should be in results)
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
    
    # Extra VINs (should NOT be in results)
    extra_vins = [
        '1FM5K8D89FGA60210',  # Line 2
        '1C4PJXDN4RW112692',  # Line 3
        '5FNRL6H87RB022989',  # Line 4
        '3GNKBBRA0KS610414',  # Line 5
        '1C4HJXEG2JW287869',  # Line 8
        '3FMCR9D9XPRE32312',  # Line 12
        '5N1BT3BBXPC852781',  # Line 15
        '2C3CDXBG8NH157383',  # Line 16
        '1G1ZD5ST0NF101598',  # Line 17
        '5NTJDDAF2NH002265',  # Line 18
        '1FMDE5BH0MLA93699',  # Line 19
        '1FMCU9H96NUA00136',  # Line 20
        '1C4RJFBG8MC599686',  # Line 21
        '55SWF4KBXHU195101',  # Line 22
        '5YFBU4EE6DP173803',  # Line 25
        '1FMEE5DH8NLA81738',  # Line 26
        '1N4BL4BV1RN411252',  # Line 27
        '1HGCY1F36RA055932',  # Line 28
        'W1K5J4GB5PN357159',  # Line 29
        '3MW39FS02P8D51749',  # Line 30
        'KL77LJE2XRC022814',  # Line 31
        '1FTBR1Y80PKA55237',  # Line 32
        '3TYAX5GN6PT077451'   # Line 33
    ]
    
    print(f"\nExpected VINs: {len(expected_vins)}")
    print(f"Extra VINs to analyze: {len(extra_vins)}")
    
    # Check the status and stock information for extra VINs
    print("\n=== ANALYZING EXTRA VINS FROM DATABASE ===")
    
    # Query both raw and normalized data for these VINs
    placeholders = ', '.join(['%s'] * len(extra_vins))
    query = f'''
        SELECT 
            rvd.vin,
            rvd.stock,
            rvd.status as raw_status,
            nvd.status as normalized_status,
            nvd.on_lot_status,
            rvd.type,
            nvd.vehicle_condition,
            rvd.year,
            rvd.make,
            rvd.model
        FROM raw_vehicle_data rvd
        LEFT JOIN normalized_vehicle_data nvd ON rvd.id = nvd.raw_data_id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE rvd.vin IN ({placeholders})
        AND rvd.location = 'Suntrup Ford Kirkwood'
        AND si.status = 'active'
        ORDER BY rvd.vin
    '''
    
    results = db_manager.execute_query(query, tuple(extra_vins))
    
    print(f"\nFound {len(results)} extra vehicles in database:")
    print("-" * 120)
    print("VIN | Stock | Raw Status | Normalized Status | On Lot Status | Type | Condition | Vehicle")
    print("-" * 120)
    
    in_transit_count = 0
    missing_stock_count = 0
    both_issues_count = 0
    no_issues_count = 0
    
    for vehicle in results:
        vin = vehicle['vin']
        stock = vehicle['stock']
        raw_status = vehicle['raw_status']
        norm_status = vehicle['normalized_status']
        on_lot = vehicle['on_lot_status']
        v_type = vehicle['type']
        condition = vehicle['vehicle_condition']
        vehicle_desc = f"{vehicle['year']} {vehicle['make']} {vehicle['model']}"
        
        issues = []
        
        # Check for In-Transit status
        if raw_status and 'transit' in raw_status.lower():
            issues.append('IN-TRANSIT')
            in_transit_count += 1
        
        # Check for missing stock number
        if not stock or stock.strip() == '' or stock == '*':
            issues.append('NO-STOCK')
            missing_stock_count += 1
            
        if len(issues) == 2:
            both_issues_count += 1
            in_transit_count -= 1  # Adjust to avoid double counting
            missing_stock_count -= 1
        elif len(issues) == 0:
            no_issues_count += 1
            
        issue_str = ' [' + ', '.join(issues) + ']' if issues else ''
        
        print(f"{vin} | {stock or 'NONE'} | {raw_status or 'N/A'} | {norm_status or 'N/A'} | {on_lot or 'N/A'} | {v_type} | {condition} | {vehicle_desc}{issue_str}")
    
    print("-" * 120)
    print("\n=== SUMMARY OF ISSUES ===")
    print(f"Vehicles with In-Transit status: {in_transit_count}")
    print(f"Vehicles with missing stock numbers: {missing_stock_count}")
    print(f"Vehicles with BOTH issues: {both_issues_count}")
    print(f"Vehicles with NO apparent issues: {no_issues_count}")
    print(f"Total extra vehicles: {len(results)}")
    
    # Check current dealership config
    print("\n=== CURRENT DEALERSHIP CONFIG ===")
    config = db_manager.execute_query('''
        SELECT name, filtering_rules
        FROM dealership_configs
        WHERE name = 'Suntrup Ford Kirkwood'
    ''')
    
    if config:
        rules = config[0]['filtering_rules']
        print(f"Current filtering rules for Suntrup Ford Kirkwood:")
        print(f"  - exclude_status: {rules.get('exclude_status', 'NOT SET')}")
        print(f"  - require_status: {rules.get('require_status', 'NOT SET')}")
        print(f"  - exclude_missing_stock: {rules.get('exclude_missing_stock', 'NOT SET')}")
        
        if not rules.get('exclude_status'):
            print("\n[WARNING] No exclude_status filter set - In-Transit vehicles NOT being filtered!")
        if not rules.get('exclude_missing_stock'):
            print("[WARNING] exclude_missing_stock not set to True - vehicles without stock numbers NOT being filtered!")
    
    db_manager.close()

if __name__ == "__main__":
    main()