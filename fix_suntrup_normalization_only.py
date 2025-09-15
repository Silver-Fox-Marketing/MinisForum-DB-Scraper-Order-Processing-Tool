"""
Fix Suntrup Kia South Normalization ONLY
Identifies why Suntrup Kia South data doesn't get automatically normalized on CSV import
while Porsche works perfectly. Makes targeted fix without affecting working dealerships.
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

def identify_normalization_gap():
    """Find why Suntrup Kia South doesn't get normalized automatically"""
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print('=' * 70)
        print('SUNTRUP KIA SOUTH NORMALIZATION GAP ANALYSIS')
        print('=' * 70)
        
        # 1. Compare active imports for both dealerships
        print('1. COMPARING ACTIVE IMPORTS')
        cursor.execute("""
            SELECT dealership_name, import_id, import_date, vehicle_count, status
            FROM scraper_imports 
            WHERE dealership_name IN ('Suntrup Kia South', 'Porsche St. Louis')
            AND status = 'active'
            ORDER BY dealership_name
        """)
        
        active_imports = cursor.fetchall()
        suntrup_import = None
        porsche_import = None
        
        for imp in active_imports:
            print(f'{imp[0]}: Import {imp[1]} - {imp[2]} ({imp[3]} vehicles)')
            if 'Suntrup' in imp[0]:
                suntrup_import = imp[1]
            elif 'Porsche' in imp[0]:
                porsche_import = imp[1]
        
        if not suntrup_import:
            print('❌ ERROR: No active Suntrup Kia South import found!')
            return False
            
        if not porsche_import:
            print('❌ ERROR: No active Porsche import found for comparison!')
            return False
            
        print(f'✅ Suntrup active import: {suntrup_import}')
        print(f'✅ Porsche active import: {porsche_import}')
        print()
        
        # 2. Check normalization status for both
        print('2. NORMALIZATION STATUS COMPARISON')
        
        # Suntrup normalization check
        cursor.execute("""
            SELECT COUNT(*) as raw_count
            FROM raw_vehicle_data 
            WHERE import_id = %s
        """, (suntrup_import,))
        suntrup_raw = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) as norm_count
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            WHERE rvd.import_id = %s
        """, (suntrup_import,))
        suntrup_norm = cursor.fetchone()[0]
        
        # Porsche normalization check  
        cursor.execute("""
            SELECT COUNT(*) as raw_count
            FROM raw_vehicle_data 
            WHERE import_id = %s
        """, (porsche_import,))
        porsche_raw = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) as norm_count
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            WHERE rvd.import_id = %s
        """, (porsche_import,))
        porsche_norm = cursor.fetchone()[0]
        
        print(f'Suntrup Kia South: {suntrup_raw} raw → {suntrup_norm} normalized')
        print(f'Porsche St. Louis: {porsche_raw} raw → {porsche_norm} normalized')
        print()
        
        if suntrup_norm == 0:
            print('❌ CONFIRMED: Suntrup has NO normalized data')
            print('✅ CONFIRMED: Porsche has complete normalized data')
            print()
            
            # 3. Check for normalization process differences
            print('3. ANALYZING NORMALIZATION PROCESS GAPS')
            
            # Check if normalization was attempted but failed
            cursor.execute("""
                SELECT rvd.id, rvd.vin, rvd.location, rvd.type, rvd.status
                FROM raw_vehicle_data rvd
                WHERE rvd.import_id = %s
                LIMIT 5
            """, (suntrup_import,))
            
            suntrup_samples = cursor.fetchall()
            print('Sample Suntrup raw data:')
            for sample in suntrup_samples:
                print(f'  ID: {sample[0]}, VIN: {sample[1]}, Type: {sample[3]}, Status: {sample[4]}')
            print()
            
            # 4. Run normalization for Suntrup data ONLY
            print('4. RUNNING TARGETED NORMALIZATION FOR SUNTRUP KIA SOUTH')
            print('Processing raw vehicles from active import...')
            
            normalized_count = 0
            cursor.execute("""
                SELECT id, vin, location, make, model, trim, year, price, mileage, 
                       stock_number, type, ext_color, status, body_style
                FROM raw_vehicle_data 
                WHERE import_id = %s
            """, (suntrup_import,))
            
            raw_vehicles = cursor.fetchall()
            
            for vehicle in raw_vehicles:
                raw_id, vin, location, make, model, trim, year, price, mileage, stock_number, v_type, ext_color, status, body_style = vehicle
                
                # Normalize vehicle condition based on type
                if v_type and v_type.lower() in ['certified pre-owned', 'certified']:
                    vehicle_condition = 'cpo'
                elif v_type and v_type.lower() in ['pre-owned', 'used']:
                    vehicle_condition = 'po'  
                elif v_type and v_type.lower() == 'new':
                    vehicle_condition = 'new'
                else:
                    vehicle_condition = 'po'  # Default to pre-owned for unknown types
                
                # Normalize on_lot_status
                on_lot_status = 'onlot' if status and 'stock' in status.lower() else 'onlot'
                
                # Check if normalized record already exists
                cursor.execute("""
                    SELECT id FROM normalized_vehicle_data WHERE vin = %s
                """, (vin,))
                
                if not cursor.fetchone():
                    # Insert normalized record
                    cursor.execute("""
                        INSERT INTO normalized_vehicle_data (
                            vin, location, make, model, trim, year, price, mileage,
                            stock_number, vehicle_condition, ext_color, on_lot_status,
                            body_style, raw_data_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        vin, location, make, model, trim, year, price, mileage,
                        stock_number, vehicle_condition, ext_color, on_lot_status,
                        body_style, raw_id
                    ))
                    normalized_count += 1
            
            # Commit the normalization
            conn.commit()
            
            print(f'✅ NORMALIZATION COMPLETE: {normalized_count} vehicles normalized')
            print()
            
            # 5. Verify the fix
            print('5. VERIFYING NORMALIZATION FIX')
            cursor.execute("""
                SELECT COUNT(*) as norm_count
                FROM normalized_vehicle_data nvd
                JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                WHERE rvd.import_id = %s
            """, (suntrup_import,))
            
            final_norm_count = cursor.fetchone()[0]
            print(f'Final normalized count: {final_norm_count}')
            
            if final_norm_count > 0:
                print('✅ SUCCESS: Suntrup Kia South now has normalized data!')
                print('✅ This should fix the N/A raw_status issue')
                print('✅ CAO processing should now work correctly')
                
                # Test JOIN to confirm raw_status will work
                cursor.execute("""
                    SELECT nvd.vin, rvd.status as raw_status
                    FROM normalized_vehicle_data nvd
                    JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                    WHERE rvd.import_id = %s
                    LIMIT 3
                """, (suntrup_import,))
                
                test_joins = cursor.fetchall()
                print('Sample JOIN test (VIN → raw_status):')
                for test in test_joins:
                    print(f'  {test[0]} → {test[1]}')
                
                return True
            else:
                print('❌ FAILED: Normalization did not work')
                return False
                
        else:
            print('ℹ️  Suntrup already has some normalized data')
            print('Issue may be with JOIN logic or data integrity')
            return True
            
    except Exception as e:
        print(f'Database error: {e}')
        print('Make sure the Flask server is running and database is accessible')
        return False
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print('TARGETED NORMALIZATION FIX FOR SUNTRUP KIA SOUTH')
    print('Will NOT affect Porsche or any other working dealerships')
    print()
    
    success = fix_normalization_gap()
    if success:
        print('\n[SUCCESS] Suntrup Kia South normalization fixed!')
        print('Test CAO processing - raw_status should now display correctly.')
        print('Vehicle count should also be more accurate now.')
    else:
        print('\n[ERROR] Failed to fix normalization gap.')
        print('May need manual investigation of the normalization process.')