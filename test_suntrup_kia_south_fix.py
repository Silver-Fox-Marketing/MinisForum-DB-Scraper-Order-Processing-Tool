"""
Test Suntrup Kia South Configuration Fix
Verifies that the dealership now returns ~37 vehicles instead of 377
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

def test_suntrup_kia_south_fix():
    """Test CAO filtering for Suntrup Kia South after configuration fix"""
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print('=' * 60)
        print('TESTING SUNTRUP KIA SOUTH CONFIGURATION FIX')
        print('=' * 60)
        
        # 1. Verify current configuration
        print('1. VERIFYING CURRENT CONFIGURATION')
        cursor.execute("""
            SELECT name, filtering_rules, is_active 
            FROM dealership_configs 
            WHERE name = 'Suntrup Kia South'
        """)
        
        config_result = cursor.fetchone()
        if config_result:
            print(f'Dealership: {config_result[0]}')
            print(f'Active: {config_result[2]}')
            filtering_rules = config_result[1]
            if filtering_rules:
                print('Filtering Rules:')
                print(json.dumps(filtering_rules, indent=2))
                allowed_types = filtering_rules.get('allowed_vehicle_types', [])
                print(f'Allowed Vehicle Types: {allowed_types}')
            else:
                print('ERROR: No filtering rules found!')
                return False
        else:
            print('ERROR: Suntrup Kia South configuration not found!')
            return False
        
        print()
        
        # 2. Test raw inventory count
        print('2. CHECKING RAW INVENTORY DATA')
        cursor.execute("""
            SELECT COUNT(*) as total_count
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE nvd.location = 'Suntrup Kia South'
            AND nvd.on_lot_status IN ('onlot', 'on lot')
            AND si.status = 'active'
        """)
        
        raw_count = cursor.fetchone()[0]
        print(f'Total active inventory: {raw_count} vehicles')
        
        # 3. Test filtering by vehicle condition
        print('3. TESTING VEHICLE CONDITION FILTERING')
        
        # Count by vehicle condition
        cursor.execute("""
            SELECT nvd.vehicle_condition, COUNT(*) as count
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE nvd.location = 'Suntrup Kia South'
            AND nvd.on_lot_status IN ('onlot', 'on lot')
            AND si.status = 'active'
            GROUP BY nvd.vehicle_condition
            ORDER BY count DESC
        """)
        
        condition_counts = cursor.fetchall()
        total_by_condition = 0
        print('Vehicle condition breakdown:')
        for condition, count in condition_counts:
            print(f'  {condition}: {count} vehicles')
            total_by_condition += count
        
        print()
        
        # 4. Apply the actual CAO filtering logic
        print('4. TESTING CAO FILTERING LOGIC')
        
        # Simulate the filtering that CAO would apply based on allowed_vehicle_types: ["used"]
        # "used" should include both 'po' and 'cpo' conditions
        allowed_conditions = []
        for vtype in allowed_types:
            if vtype == 'new':
                allowed_conditions.append('new')
            elif vtype == 'used':
                # UMBRELLA TERM: "used" includes both po (Pre-Owned) AND cpo (Certified Pre-Owned)
                allowed_conditions.extend(['po', 'cpo'])
            elif vtype in ['certified', 'cpo']:
                allowed_conditions.append('cpo')
            elif vtype in ['po', 'pre-owned']:
                allowed_conditions.append('po')
        
        # Remove duplicates
        allowed_conditions = list(set(allowed_conditions))
        print(f'Allowed conditions for CAO: {allowed_conditions}')
        
        if allowed_conditions:
            placeholders = ', '.join(['%s'] * len(allowed_conditions))
            
            cursor.execute(f"""
                SELECT COUNT(*) as filtered_count
                FROM normalized_vehicle_data nvd
                JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                JOIN scraper_imports si ON rvd.import_id = si.import_id
                WHERE nvd.location = 'Suntrup Kia South'
                AND nvd.on_lot_status IN ('onlot', 'on lot')
                AND si.status = 'active'
                AND nvd.vehicle_condition IN ({placeholders})
            """, allowed_conditions)
            
            filtered_count = cursor.fetchone()[0]
            print(f'CAO would process: {filtered_count} vehicles')
            
            # 5. Compare with VIN log to simulate actual CAO result
            print('5. SIMULATING FULL CAO COMPARISON')
            cursor.execute(f"""
                SELECT COUNT(*) as cao_result_count
                FROM normalized_vehicle_data nvd
                JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                JOIN scraper_imports si ON rvd.import_id = si.import_id
                WHERE nvd.location = 'Suntrup Kia South'
                AND nvd.on_lot_status IN ('onlot', 'on lot')
                AND si.status = 'active'
                AND nvd.vehicle_condition IN ({placeholders})
                AND nvd.vin NOT IN (SELECT vin FROM suntrup_kia_south_vin_log)
            """, allowed_conditions)
            
            cao_result_count = cursor.fetchone()[0]
            print(f'CAO result (after VIN log comparison): {cao_result_count} vehicles')
            
            # 6. Evaluation
            print()
            print('=' * 60)
            print('EVALUATION RESULTS')
            print('=' * 60)
            
            if cao_result_count <= 50:  # Reasonable range for expected ~37
                print('[SUCCESS] CAO result is in expected range!')
                print(f'Expected: ~37 vehicles')
                print(f'Actual: {cao_result_count} vehicles')
                print('Configuration fix appears to be working correctly.')
            else:
                print('[WARNING] CAO result still too high')
                print(f'Expected: ~37 vehicles')
                print(f'Actual: {cao_result_count} vehicles')
                print('May need additional filtering adjustments.')
            
            return cao_result_count <= 50
            
        else:
            print('ERROR: No allowed conditions determined!')
            return False
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'Database error: {e}')
        print('Make sure the Flask server is running and database is accessible')
        return False

if __name__ == "__main__":
    success = test_suntrup_kia_south_fix()
    if success:
        print('\n[SUCCESS] Suntrup Kia South configuration fix verified!')
        print('Ready for production CAO processing.')
    else:
        print('\n[NEEDS ATTENTION] Configuration may need further adjustments.')
        print('Review the results above and consider additional filtering.')