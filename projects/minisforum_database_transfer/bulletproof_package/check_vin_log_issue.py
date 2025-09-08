#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
from database_connection import DatabaseManager

def main():
    print("=== INVESTIGATING WHY 23 EXTRA VINS ARE INCLUDED ===")
    
    db_manager = DatabaseManager()
    
    # The 9 VINs that SHOULD be returned
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
    
    # The 23 VINs that should NOT be returned
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
    
    # Check the VIN log table for Suntrup Ford Kirkwood
    print("\n1. CHECKING VIN LOG TABLE:")
    
    # First, find the correct VIN log table name
    vin_log_tables = db_manager.execute_query("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%suntrup%kirkwood%vin%'
        OR table_name LIKE '%kirkwood%vin%'
    """)
    
    if vin_log_tables:
        for table in vin_log_tables:
            print(f"Found VIN log table: {table['table_name']}")
            
            # Check if expected VINs are in the log
            table_name = table['table_name']
            
            # First check the schema
            schema = db_manager.execute_query(f"""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = '{table_name}'
            """)
            print(f"  Columns in {table_name}: {[col['column_name'] for col in schema]}")
            
            # Check expected VINs
            print(f"\n2. CHECKING EXPECTED VINS IN {table_name}:")
            for vin in expected_vins:
                result = db_manager.execute_query(f"""
                    SELECT vin FROM {table_name}
                    WHERE vin = %s
                """, (vin,))
                
                if result:
                    print(f"  {vin} - IN LOG [Should be excluded]")
                else:
                    print(f"  {vin} - NOT IN LOG [CORRECT - needs graphics]")
            
            # Check extra VINs
            print(f"\n3. CHECKING EXTRA VINS IN {table_name}:")
            for vin in extra_vins[:10]:  # Check first 10
                result = db_manager.execute_query(f"""
                    SELECT vin FROM {table_name}
                    WHERE vin = %s
                """, (vin,))
                
                if result:
                    print(f"  {vin} - IN LOG [CORRECT - should be excluded]")
                else:
                    print(f"  {vin} - NOT IN LOG [ERROR - being included when shouldn't]")
    else:
        print("No VIN log table found for Suntrup Ford Kirkwood")
        
    # Check if there's a vin_history table
    print("\n4. CHECKING MAIN VIN_HISTORY TABLE:")
    vin_history_count = db_manager.execute_query("""
        SELECT COUNT(*) as count FROM vin_history 
        WHERE dealership = 'Suntrup Ford Kirkwood'
    """)
    
    if vin_history_count:
        print(f"Found {vin_history_count[0]['count']} entries in vin_history for Suntrup Ford Kirkwood")
        
        # Check some extra VINs in vin_history
        for vin in extra_vins[:5]:
            result = db_manager.execute_query("""
                SELECT vin, dealership FROM vin_history
                WHERE vin = %s AND dealership = 'Suntrup Ford Kirkwood'
            """, (vin,))
            
            if result:
                print(f"  {vin} - IN HISTORY")
            else:
                print(f"  {vin} - NOT IN HISTORY")
    
    # Check what the CAO query is actually doing
    print("\n5. SIMULATING CAO QUERY:")
    
    # This simulates what correct_order_processing.py does
    cao_simulation = db_manager.execute_query("""
        SELECT COUNT(*) as total_count,
               COUNT(CASE WHEN vh.vin IS NULL THEN 1 END) as new_vehicles_count
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        LEFT JOIN vin_history vh ON nvd.vin = vh.vin AND vh.dealership = 'Suntrup Ford Kirkwood'
        WHERE nvd.location = 'Suntrup Ford Kirkwood'
        AND si.status = 'active'
        AND nvd.vehicle_condition IN ('used', 'po', 'cpo', 'certified', 'pre-owned')
        AND nvd.stock IS NOT NULL 
        AND nvd.stock != ''
        AND nvd.stock != '*'
    """)
    
    if cao_simulation:
        print(f"Total vehicles matching filters: {cao_simulation[0]['total_count']}")
        print(f"Vehicles NOT in VIN history (new graphics needed): {cao_simulation[0]['new_vehicles_count']}")
    
    db_manager.close()

if __name__ == "__main__":
    main()