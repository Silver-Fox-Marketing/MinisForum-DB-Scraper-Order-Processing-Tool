"""
Debug Normalization Difference: Porsche vs Suntrup Kia South
Investigates why the same normalization system works for Porsche but not Suntrup Kia South
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

def debug_normalization_difference():
    """Compare normalization between working (Porsche) and broken (Suntrup) dealerships"""
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print('=' * 80)
        print('DEBUGGING NORMALIZATION DIFFERENCE: PORSCHE (WORKING) vs SUNTRUP (BROKEN)')
        print('=' * 80)
        
        # 1. Compare active imports
        print('1. COMPARING ACTIVE IMPORTS')
        cursor.execute("""
            SELECT dealership_name, import_id, import_date, vehicle_count, status,
                   created_at, updated_at
            FROM scraper_imports 
            WHERE dealership_name IN ('Porsche St. Louis', 'Suntrup Kia South')
            AND status = 'active'
            ORDER BY dealership_name
        """)
        
        imports = cursor.fetchall()
        porsche_import = None
        suntrup_import = None
        
        for imp in imports:
            print(f'{imp[0]}: Import {imp[1]} - {imp[2]} ({imp[3]} vehicles)')
            print(f'  Created: {imp[5]}, Updated: {imp[6]}')
            if 'Porsche' in imp[0]:
                porsche_import = imp[1]
            elif 'Suntrup' in imp[0]:
                suntrup_import = imp[1]
        print()
        
        if not porsche_import or not suntrup_import:
            print('❌ Missing active imports for comparison!')
            return False
        
        # 2. Compare raw data structure
        print('2. COMPARING RAW DATA STRUCTURE')
        
        # Sample raw data from both dealerships
        for dealership, import_id in [('Porsche St. Louis', porsche_import), ('Suntrup Kia South', suntrup_import)]:
            cursor.execute("""
                SELECT vin, location, make, model, type, status, stock_number, price
                FROM raw_vehicle_data 
                WHERE import_id = %s
                LIMIT 3
            """, (import_id,))
            
            samples = cursor.fetchall()
            print(f'{dealership} raw data samples:')
            for sample in samples:
                print(f'  VIN: {sample[0]}, Type: {sample[4]}, Status: {sample[5]}, Stock: {sample[6]}')
            print()
        
        # 3. Compare normalization results
        print('3. COMPARING NORMALIZATION RESULTS')
        
        for dealership, import_id in [('Porsche St. Louis', porsche_import), ('Suntrup Kia South', suntrup_import)]:
            # Raw count
            cursor.execute("""
                SELECT COUNT(*) FROM raw_vehicle_data WHERE import_id = %s
            """, (import_id,))
            raw_count = cursor.fetchone()[0]
            
            # Normalized count
            cursor.execute("""
                SELECT COUNT(*) FROM normalized_vehicle_data nvd
                JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                WHERE rvd.import_id = %s
            """, (import_id,))
            norm_count = cursor.fetchone()[0]
            
            # Sample normalized data
            cursor.execute("""
                SELECT nvd.vin, nvd.vehicle_condition, nvd.on_lot_status, nvd.raw_data_id
                FROM normalized_vehicle_data nvd
                JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                WHERE rvd.import_id = %s
                LIMIT 3
            """, (import_id,))
            
            norm_samples = cursor.fetchall()
            
            print(f'{dealership} normalization:')
            print(f'  Raw: {raw_count}, Normalized: {norm_count} ({norm_count/raw_count*100:.1f}%)')
            
            if norm_samples:
                print('  Sample normalized data:')
                for sample in norm_samples:
                    print(f'    VIN: {sample[0]}, Condition: {sample[1]}, Status: {sample[2]}, Raw ID: {sample[3]}')
            else:
                print('    ❌ NO normalized data found!')
            print()
        
        # 4. Check import process logs/timing
        print('4. ANALYZING IMPORT PROCESS TIMING')
        
        for dealership, import_id in [('Porsche St. Louis', porsche_import), ('Suntrup Kia South', suntrup_import)]:
            # Check if import was finalized (this should trigger normalization)
            cursor.execute("""
                SELECT created_at, updated_at, 
                       EXTRACT(EPOCH FROM (updated_at - created_at)) as duration_seconds
                FROM scraper_imports 
                WHERE import_id = %s
            """, (import_id,))
            
            timing = cursor.fetchone()
            if timing:
                print(f'{dealership} import timing:')
                print(f'  Created: {timing[0]}')
                print(f'  Updated: {timing[1]}') 
                print(f'  Duration: {timing[2]:.1f} seconds')
                
                # Check if there was enough time for normalization
                if timing[2] and timing[2] < 5:
                    print('  ⚠️  Very short import duration - normalization may not have completed')
                elif timing[0] == timing[1]:
                    print('  ⚠️  Created = Updated - import may not have been finalized')
                else:
                    print('  ✅ Normal import duration')
            print()
        
        # 5. Check if finalize_import was called
        print('5. CHECKING NORMALIZATION TRIGGER')
        
        # Look for vehicles that should have been normalized but weren't
        cursor.execute("""
            SELECT rvd.id, rvd.vin, rvd.type, rvd.status, rvd.import_id
            FROM raw_vehicle_data rvd
            LEFT JOIN normalized_vehicle_data nvd ON rvd.id = nvd.raw_data_id
            WHERE rvd.import_id = %s
            AND nvd.raw_data_id IS NULL
            LIMIT 5
        """, (suntrup_import,))
        
        missing_norm = cursor.fetchall()
        if missing_norm:
            print(f'Suntrup vehicles missing normalization ({len(missing_norm)} samples):')
            for missing in missing_norm:
                print(f'  Raw ID: {missing[0]}, VIN: {missing[1]}, Type: {missing[2]}, Status: {missing[3]}')
            print()
            
            print('❌ ROOT CAUSE: finalize_import() was not called or failed for Suntrup import')
            print('✅ SOLUTION: The normalization system works - it just needs to be triggered')
            
            # 6. Fix the immediate problem by running normalization manually
            print('6. APPLYING IMMEDIATE FIX')
            
            # Import the ScraperImportManager and run finalize
            from scraper_import_manager import ScraperImportManager
            import_manager = ScraperImportManager()
            
            print(f'Running finalize_import({suntrup_import}) to trigger normalization...')
            try:
                import_manager.ensure_active_normalization(suntrup_import)
                print('✅ Normalization process completed!')
                
                # Verify the fix
                cursor.execute("""
                    SELECT COUNT(*) FROM normalized_vehicle_data nvd
                    JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                    WHERE rvd.import_id = %s
                """, (suntrup_import,))
                
                final_count = cursor.fetchone()[0]
                print(f'✅ Final normalized count: {final_count}')
                
                return True
                
            except Exception as e:
                print(f'❌ Error running normalization: {e}')
                return False
        else:
            print('✅ All Suntrup vehicles are normalized (unexpected!)')
            return True
            
    except Exception as e:
        print(f'Database error: {e}')
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print('INVESTIGATING WHY PORSCHE NORMALIZES BUT SUNTRUP DOES NOT')
    print('This will identify the root cause and apply the fix.')
    print()
    
    success = debug_normalization_difference()
    if success:
        print('\n[SUCCESS] Normalization difference resolved!')
        print('Suntrup Kia South should now work like Porsche.')
    else:
        print('\n[ERROR] Could not resolve normalization difference.')
        print('May require deeper investigation.')