"""
Diagnose Suntrup Kia South Normalization Issue
Investigates why raw_status shows N/A (JOIN failure between normalized and raw data)
"""

import sys
import os

# Add the correct paths for database connection
sys.path.insert(0, r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts')

import psycopg2
import json

# Use the same database configuration as the working system
DB_CONFIG = {
    'host': 'localhost', 
    'database': 'vehicle_inventory',
    'user': 'postgres',
    'password': 'password'
}

def diagnose_normalization_issue():
    """Systematically investigate the normalization issue for Suntrup Kia South"""
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print('=' * 60)
        print('DIAGNOSING SUNTRUP KIA SOUTH NORMALIZATION ISSUE')
        print('=' * 60)
        
        # 1. Check active import status
        print('1. CHECKING ACTIVE IMPORT STATUS')
        cursor.execute("""
            SELECT import_id, dealership_name, status, import_date, vehicle_count 
            FROM scraper_imports 
            WHERE dealership_name = 'Suntrup Kia South'
            ORDER BY import_date DESC LIMIT 5
        """)
        
        imports = cursor.fetchall()
        print('Recent Suntrup Kia South imports:')
        active_import_id = None
        for imp in imports:
            status_marker = '✅ ACTIVE' if imp[2] == 'active' else '📁 archived'
            print(f'  Import ID {imp[0]}: {status_marker} - {imp[1]} - {imp[3]} ({imp[4]} vehicles)')
            if imp[2] == 'active':
                active_import_id = imp[0]
        
        if not active_import_id:
            print('❌ ERROR: No active import found for Suntrup Kia South!')
            return False
            
        print(f'✅ Active import ID: {active_import_id}')
        print()
        
        # 2. Check raw data count
        print('2. CHECKING RAW DATA COUNT')
        cursor.execute("""
            SELECT COUNT(*) as raw_count
            FROM raw_vehicle_data 
            WHERE import_id = %s
        """, (active_import_id,))
        
        raw_count = cursor.fetchone()[0]
        print(f'Raw vehicles in active import: {raw_count}')
        print()
        
        # 3. Check normalized data count
        print('3. CHECKING NORMALIZED DATA COUNT')
        cursor.execute("""
            SELECT COUNT(*) as normalized_count
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            WHERE rvd.import_id = %s
        """, (active_import_id,))
        
        normalized_count = cursor.fetchone()[0]
        print(f'Normalized vehicles linked to active import: {normalized_count}')
        
        if normalized_count == 0:
            print('❌ CRITICAL: No normalized data linked to active import!')
            print('This explains why raw_status shows N/A - no JOIN possible')
            print()
            
            # Check if normalized data exists for other imports
            print('4. CHECKING NORMALIZED DATA FOR OTHER IMPORTS')
            cursor.execute("""
                SELECT rvd.import_id, si.status, COUNT(*) as count
                FROM normalized_vehicle_data nvd
                JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                JOIN scraper_imports si ON rvd.import_id = si.import_id
                WHERE nvd.location = 'Suntrup Kia South'
                GROUP BY rvd.import_id, si.status
                ORDER BY rvd.import_id DESC
            """)
            
            other_normalized = cursor.fetchall()
            if other_normalized:
                print('Normalized data found in other imports:')
                for norm in other_normalized:
                    status_marker = '✅ ACTIVE' if norm[1] == 'active' else '📁 archived'  
                    print(f'  Import ID {norm[0]}: {status_marker} - {norm[2]} normalized vehicles')
                    
                print('❌ PROBLEM: Normalized data exists for non-active imports!')
                print('SOLUTION NEEDED: Re-normalize the active import data')
            else:
                print('❌ NO normalized data found for Suntrup Kia South at all!')
                print('SOLUTION NEEDED: Run normalization process for active import')
            
            return False
            
        elif normalized_count != raw_count:
            print(f'⚠️  WARNING: Count mismatch - {raw_count} raw vs {normalized_count} normalized')
            print('Some vehicles may not be normalized properly')
            
        print()
        
        # 4. Test sample VINs from console output
        print('4. TESTING SAMPLE VINs FROM CONSOLE OUTPUT')
        sample_vins = ['5XYK6CDF7TG369346', '5XYRH4JF4TG415508', 'KNAG64J77T5425770']
        
        for vin in sample_vins:
            # Check if VIN exists in raw data
            cursor.execute("""
                SELECT id, status, location FROM raw_vehicle_data 
                WHERE vin = %s AND import_id = %s
            """, (vin, active_import_id))
            
            raw_result = cursor.fetchone()
            
            if raw_result:
                print(f'✅ VIN {vin}: Found in raw data (ID: {raw_result[0]}, Status: {raw_result[1]})')
                
                # Check if normalized record exists and links correctly
                cursor.execute("""
                    SELECT nvd.id, nvd.raw_data_id 
                    FROM normalized_vehicle_data nvd
                    WHERE nvd.vin = %s
                """, (vin,))
                
                norm_result = cursor.fetchone()
                if norm_result:
                    print(f'   ✅ Normalized record exists (ID: {norm_result[0]}, Links to raw_data_id: {norm_result[1]})')
                    
                    # Verify the link is correct
                    if norm_result[1] == raw_result[0]:
                        print(f'   ✅ Link is CORRECT')
                    else:
                        print(f'   ❌ Link is BROKEN - points to {norm_result[1]}, should be {raw_result[0]}')
                else:
                    print(f'   ❌ NO normalized record found for this VIN')
            else:
                print(f'❌ VIN {vin}: NOT found in active raw data')
                
        print()
        
        # 5. Compare with working dealership (Porsche)
        print('5. COMPARING WITH WORKING DEALERSHIP (PORSCHE)')
        cursor.execute("""
            SELECT si.import_id, COUNT(rvd.id) as raw_count, COUNT(nvd.id) as norm_count
            FROM scraper_imports si
            LEFT JOIN raw_vehicle_data rvd ON si.import_id = rvd.import_id
            LEFT JOIN normalized_vehicle_data nvd ON nvd.raw_data_id = rvd.id
            WHERE si.dealership_name = 'Porsche St. Louis' AND si.status = 'active'
            GROUP BY si.import_id
        """)
        
        porsche_data = cursor.fetchone()
        if porsche_data:
            print(f'Porsche St. Louis (WORKING): Import {porsche_data[0]} - {porsche_data[1]} raw, {porsche_data[2]} normalized')
            if porsche_data[1] == porsche_data[2]:
                print('   ✅ Perfect 1:1 raw to normalized ratio')
            else:
                print('   ⚠️  Count mismatch in working dealership too')
        
        print()
        print('=' * 60)
        print('DIAGNOSIS SUMMARY')
        print('=' * 60)
        
        if normalized_count == 0:
            print('❌ ROOT CAUSE: NO normalized data for active import')
            print('SOLUTION: Run normalization process for active import')
        elif normalized_count != raw_count:
            print('⚠️  ROOT CAUSE: Incomplete normalization')
            print('SOLUTION: Re-run normalization to ensure all vehicles are processed')
        else:
            print('❌ UNEXPECTED: Counts match but JOIN still failing')
            print('SOLUTION: Investigate JOIN logic and data integrity')
            
        cursor.close()
        conn.close()
        
        return normalized_count > 0
        
    except Exception as e:
        print(f'Database error: {e}')
        print('Make sure the Flask server is running and database is accessible')
        return False

if __name__ == "__main__":
    success = diagnose_normalization_issue()
    if not success:
        print('\n[CRITICAL] Normalization issue confirmed!')
        print('Next step: Run normalization process for Suntrup Kia South active import.')
    else:
        print('\n[INFO] Normalization data exists - investigate JOIN logic.')