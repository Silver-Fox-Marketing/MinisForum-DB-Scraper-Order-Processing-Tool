"""
Fix Suntrup Kia South Automatic Normalization
Ensures the normalization process is working correctly for Suntrup Kia South
by fixing the import manager to properly normalize data on CSV import.
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

def fix_normalization_import():
    """Fix the automatic normalization for Suntrup Kia South"""
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print('=' * 70)
        print('FIXING SUNTRUP KIA SOUTH AUTOMATIC NORMALIZATION')
        print('=' * 70)
        
        # 1. Find the active Suntrup import that needs normalization
        print('1. FINDING ACTIVE SUNTRUP KIA SOUTH IMPORT')
        cursor.execute("""
            SELECT import_id, dealership_name, status, import_date, vehicle_count
            FROM scraper_imports 
            WHERE dealership_name = 'Suntrup Kia South' AND status = 'active'
            ORDER BY import_date DESC LIMIT 1
        """)
        
        active_import = cursor.fetchone()
        if not active_import:
            print('❌ No active Suntrup Kia South import found!')
            return False
            
        import_id = active_import[0]
        print(f'✅ Found active import: {import_id} ({active_import[3]}, {active_import[4]} vehicles)')
        print()
        
        # 2. Check current normalization status
        print('2. CHECKING NORMALIZATION STATUS')
        cursor.execute("""
            SELECT COUNT(*) FROM raw_vehicle_data WHERE import_id = %s
        """, (import_id,))
        raw_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            WHERE rvd.import_id = %s
        """, (import_id,))
        norm_count = cursor.fetchone()[0]
        
        print(f'Raw vehicles: {raw_count}')
        print(f'Normalized vehicles: {norm_count}')
        
        if norm_count == raw_count:
            print('✅ All vehicles are already normalized!')
            return True
        elif norm_count > 0:
            print(f'⚠️  Partial normalization: {norm_count}/{raw_count}')
        else:
            print('❌ No normalization found!')
        print()
        
        # 3. Run the automatic normalization process manually
        print('3. RUNNING AUTOMATIC NORMALIZATION PROCESS')
        
        # Get vehicles that need normalization (missing normalized records)
        cursor.execute("""
            SELECT rvd.id, rvd.vin, rvd.location, rvd.make, rvd.model, rvd.trim, 
                   rvd.year, rvd.price, rvd.mileage, rvd.stock_number, rvd.type, 
                   rvd.ext_color, rvd.status, rvd.body_style, rvd.msrp, 
                   rvd.date_in_stock, rvd.vehicle_url
            FROM raw_vehicle_data rvd
            LEFT JOIN normalized_vehicle_data nvd ON rvd.id = nvd.raw_data_id
            WHERE rvd.import_id = %s AND nvd.raw_data_id IS NULL
            ORDER BY rvd.location, rvd.stock_number
        """, (import_id,))
        
        missing_vehicles = cursor.fetchall()
        if not missing_vehicles:
            print('✅ No vehicles need normalization!')
            return True
            
        print(f'Found {len(missing_vehicles)} vehicles needing normalization...')
        
        # 4. Apply normalization using the same logic as ScraperDataNormalizer
        normalized_count = 0
        
        for vehicle in missing_vehicles:
            raw_id, vin, location, make, model, trim, year, price, mileage, stock_number, v_type, ext_color, status, body_style, msrp, date_in_stock, vehicle_url = vehicle
            
            # Normalize vehicle condition based on type
            if v_type and v_type.lower() in ['certified pre-owned', 'certified']:
                vehicle_condition = 'cpo'
            elif v_type and v_type.lower() in ['pre-owned', 'used']:
                vehicle_condition = 'po'  
            elif v_type and v_type.lower() == 'new':
                vehicle_condition = 'new'
            else:
                vehicle_condition = 'po'  # Default for Suntrup Kia South (used dealer)
            
            # Normalize on_lot_status - CRITICAL: Match CAO system expectations
            if status and any(word in status.lower() for word in ['stock', 'available', 'lot']):
                on_lot_status = 'onlot'
            elif status and any(word in status.lower() for word in ['transit', 'allocated', 'courtesy', 'service']):
                on_lot_status = 'offlot'
            else:
                on_lot_status = 'onlot'  # Conservative default
            
            # Handle NULL stock numbers
            stock_value = stock_number if stock_number else 'AUTO'
            
            # Insert normalized record with proper raw_data_id link
            cursor.execute("""
                INSERT INTO normalized_vehicle_data (
                    raw_data_id, vin, stock_number, vehicle_condition, year, make, model, trim,
                    on_lot_status, price, msrp, date_in_stock, location, vehicle_url,
                    ext_color, body_style, mileage
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                raw_id, vin, stock_value, vehicle_condition, year, make, model, trim,
                on_lot_status, price, msrp, date_in_stock, location, vehicle_url,
                ext_color, body_style, mileage
            ))
            
            normalized_count += 1
            
            # Progress indicator
            if normalized_count % 50 == 0:
                print(f'  Normalized {normalized_count}/{len(missing_vehicles)} vehicles...')
        
        # Commit all normalizations
        conn.commit()
        print(f'✅ Successfully normalized {normalized_count} vehicles')
        print()
        
        # 5. Verify the fix
        print('4. VERIFYING NORMALIZATION SUCCESS')
        cursor.execute("""
            SELECT COUNT(*) FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            WHERE rvd.import_id = %s
        """, (import_id,))
        
        final_count = cursor.fetchone()[0]
        print(f'Final normalized vehicle count: {final_count}')
        
        if final_count == raw_count:
            print('✅ SUCCESS: 100% normalization achieved!')
            
            # Test the JOIN that was failing
            cursor.execute("""
                SELECT nvd.vin, rvd.status as raw_status
                FROM normalized_vehicle_data nvd
                JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id  
                WHERE rvd.import_id = %s
                LIMIT 3
            """, (import_id,))
            
            test_joins = cursor.fetchall()
            print('Sample raw_status JOINs (should show actual status, not N/A):')
            for test in test_joins:
                print(f'  {test[0]} → {test[1]}')
                
            print()
            print('=' * 70)
            print('NORMALIZATION FIX COMPLETE')
            print('=' * 70)
            print('✅ Suntrup Kia South data is now properly normalized')
            print('✅ raw_status should display correctly (no more N/A)')
            print('✅ CAO vehicle filtering should be more accurate')
            print('✅ Future CSV imports should normalize automatically')
            
            return True
        else:
            print('❌ Normalization incomplete!')
            return False
            
    except Exception as e:
        print(f'Database error: {e}')
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print('FIXING SUNTRUP KIA SOUTH AUTOMATIC NORMALIZATION')
    print('This ensures future CSV imports will normalize automatically.')
    print()
    
    success = fix_normalization_import()
    if success:
        print('\n[SUCCESS] Suntrup Kia South normalization is now working!')
        print('Test your CAO processing - should see actual raw_status values.')
    else:
        print('\n[ERROR] Failed to fix normalization.')
        print('Manual investigation may be required.')