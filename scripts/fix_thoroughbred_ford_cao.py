"""
Fix Thoroughbred Ford CAO processing
1. Check normalized data exists
2. Verify dealer config (filter out new cars, keep used only)
3. Test expected VINs are available
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_connection import db_manager

def fix_thoroughbred_ford_cao():
    """Fix CAO processing for Thoroughbred Ford"""
    
    print("="*60)
    print("FIXING THOROUGHBRED FORD CAO PROCESSING")
    print("="*60)
    
    # Test database connection
    if not db_manager.test_connection():
        print("[ERROR] Database connection failed")
        return False
    
    dealership_name = 'Thoroughbred Ford'
    expected_vins = [
        'MAJ6S3GL3KC284530',
        '1FTEW1EP9NKD39089', 
        '5NTJCDDE3RH110230',
        '5TDFZRBH7MS089740',
        '1FMCU9JZ9RUB01395',
        '1FA6P8CF3R5408633',
        '1FMSK8DH6PGB07634'
    ]
    
    print(f"Dealership: {dealership_name}")
    print(f"Expected VINs: {len(expected_vins)}")
    print(f"Expected VINs: {expected_vins}")
    
    # Step 1: Check if normalized data exists for Thoroughbred Ford
    print(f"\n[STEP 1] Checking normalized data...")
    try:
        # Check total normalized vehicles
        total_query = """
        SELECT COUNT(*) as total_count
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = %s
        AND si.status = 'active'
        """
        
        total_result = db_manager.execute_query(total_query, (dealership_name,))
        total_count = total_result[0]['total_count'] if total_result else 0
        
        print(f"   [INFO] Total normalized vehicles for {dealership_name}: {total_count}")
        
        if total_count == 0:
            print(f"   [ERROR] No normalized data found for {dealership_name}")
            print(f"   [INFO] Checking raw data...")
            
            # Check raw data
            raw_query = """
            SELECT COUNT(*) as raw_count
            FROM raw_vehicle_data rvd
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE rvd.location = %s
            AND si.status = 'active'
            """
            
            raw_result = db_manager.execute_query(raw_query, (dealership_name,))
            raw_count = raw_result[0]['raw_count'] if raw_result else 0
            print(f"   [INFO] Raw vehicles available: {raw_count}")
            
            if raw_count > 0:
                print(f"   [ACTION] Raw data exists but normalized data missing - need normalization")
                return False
            else:
                print(f"   [ERROR] No raw data found either - no scraper data available")
                return False
        
        # Check expected VINs in normalized data
        expected_vins_query = """
        SELECT nvd.vin, nvd.vehicle_condition, nvd.on_lot_status
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = %s
        AND si.status = 'active'
        AND nvd.vin = ANY(%s)
        """
        
        found_vins = db_manager.execute_query(expected_vins_query, (dealership_name, expected_vins))
        
        print(f"   [INFO] Expected VINs found in normalized data: {len(found_vins)}")
        for vin_record in found_vins:
            print(f"     - {vin_record['vin']}: {vin_record['vehicle_condition']} | {vin_record['on_lot_status']}")
        
        missing_vins = [vin for vin in expected_vins if not any(f['vin'] == vin for f in found_vins)]
        if missing_vins:
            print(f"   [WARNING] Missing VINs: {missing_vins}")
        
    except Exception as e:
        print(f"   [ERROR] Failed to check normalized data: {str(e)}")
        return False
    
    # Step 2: Check dealer configuration
    print(f"\n[STEP 2] Checking dealer configuration...")
    try:
        # Check if dealer config exists
        config_query = "SELECT * FROM dealership_configs WHERE dealership_name = %s"
        config_result = db_manager.execute_query(config_query, (dealership_name,))
        
        if not config_result:
            print(f"   [INFO] No dealer config found for {dealership_name}")
            print(f"   [ACTION] Creating dealer config based on South County DCJR...")
            
            # Get South County DCJR config as template
            template_query = "SELECT * FROM dealership_configs WHERE dealership_name = 'South County DCJR'"
            template_result = db_manager.execute_query(template_query)
            
            if template_result:
                template_config = template_result[0]
                print(f"   [INFO] Using South County DCJR config as template")
                
                # Create Thoroughbred Ford config (used cars only, filter out new)
                insert_config_query = """
                INSERT INTO dealership_configs (
                    dealership_name, vehicle_types, price_min, price_max, 
                    days_on_lot_min, exclude_patterns, include_patterns, active
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                db_manager.execute_query(insert_config_query, (
                    dealership_name,
                    ['used'],  # Only used cars - filter out new
                    template_config.get('price_min', 0),
                    template_config.get('price_max', 999999),
                    template_config.get('days_on_lot_min', 0),
                    template_config.get('exclude_patterns'),
                    template_config.get('include_patterns'),
                    True
                ))
                
                print(f"   [OK] Created dealer config for {dealership_name}")
                print(f"   [INFO] Vehicle types: ['used'] - filters out new cars")
            else:
                print(f"   [ERROR] Could not find South County DCJR template config")
                return False
        else:
            config = config_result[0]
            print(f"   [INFO] Existing dealer config found:")
            print(f"     - Vehicle types: {config.get('vehicle_types', 'N/A')}")
            print(f"     - Price range: {config.get('price_min', 0)} - {config.get('price_max', 999999)}")
            print(f"     - Active: {config.get('active', False)}")
            
            # Check if vehicle_types includes 'new' - if so, remove it
            vehicle_types = config.get('vehicle_types', [])
            if 'new' in vehicle_types:
                print(f"   [WARNING] Config includes 'new' vehicles - updating to used only")
                
                update_query = """
                UPDATE dealership_configs 
                SET vehicle_types = %s
                WHERE dealership_name = %s
                """
                
                db_manager.execute_query(update_query, (['used'], dealership_name))
                print(f"   [OK] Updated config to filter out new vehicles")
    
    except Exception as e:
        print(f"   [ERROR] Failed to check/create dealer config: {str(e)}")
        return False
    
    # Step 3: Test CAO query logic
    print(f"\n[STEP 3] Testing CAO query logic...")
    try:
        # Simulate the CAO query that should return the expected VINs
        cao_query = """
        SELECT nvd.vin, nvd.vehicle_condition, nvd.on_lot_status, rvd.type
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = %s
        AND si.status = 'active'
        AND nvd.vehicle_condition IN ('po', 'cpo', 'certified')  -- Used cars only
        AND nvd.vin NOT IN (
            SELECT vin FROM thoroughbred_ford_vin_log 
            WHERE vin IS NOT NULL
        )
        """
        
        cao_result = db_manager.execute_query(cao_query, (dealership_name,))
        
        print(f"   [INFO] CAO query returned: {len(cao_result)} vehicles")
        
        if cao_result:
            print(f"   [INFO] Sample CAO results:")
            for i, vehicle in enumerate(cao_result[:10]):  # Show first 10
                print(f"     {i+1}. {vehicle['vin']}: {vehicle['vehicle_condition']} | {vehicle['type']} | {vehicle['on_lot_status']}")
            
            # Check if expected VINs are in CAO results
            cao_vins = [v['vin'] for v in cao_result]
            found_expected = [vin for vin in expected_vins if vin in cao_vins]
            
            print(f"   [INFO] Expected VINs in CAO results: {len(found_expected)}")
            for vin in found_expected:
                print(f"     - {vin} ✓")
            
            missing_expected = [vin for vin in expected_vins if vin not in cao_vins]
            if missing_expected:
                print(f"   [WARNING] Expected VINs missing from CAO: {missing_expected}")
                
                # Check why they're missing (in VIN log? wrong condition? not active?)
                for vin in missing_expected:
                    debug_query = """
                    SELECT 
                        nvd.vin,
                        nvd.vehicle_condition,
                        nvd.on_lot_status,
                        rvd.type as raw_type,
                        si.status as import_status,
                        CASE WHEN tfl.vin IS NOT NULL THEN 'In VIN Log' ELSE 'Not in VIN Log' END as vin_log_status
                    FROM normalized_vehicle_data nvd
                    JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                    JOIN scraper_imports si ON rvd.import_id = si.import_id
                    LEFT JOIN thoroughbred_ford_vin_log tfl ON nvd.vin = tfl.vin
                    WHERE nvd.location = %s
                    AND nvd.vin = %s
                    """
                    
                    debug_result = db_manager.execute_query(debug_query, (dealership_name, vin))
                    if debug_result:
                        debug = debug_result[0]
                        print(f"     - {vin}: {debug['vehicle_condition']} | {debug['raw_type']} | {debug['import_status']} | {debug['vin_log_status']}")
                    else:
                        print(f"     - {vin}: NOT FOUND in normalized data")
        else:
            print(f"   [ERROR] CAO query returned 0 results - this explains the issue")
            
            # Debug: Check total vehicles without VIN log filter
            debug_query = """
            SELECT COUNT(*) as count
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE nvd.location = %s
            AND si.status = 'active'
            AND nvd.vehicle_condition IN ('po', 'cpo', 'certified')
            """
            
            debug_result = db_manager.execute_query(debug_query, (dealership_name,))
            debug_count = debug_result[0]['count'] if debug_result else 0
            print(f"   [DEBUG] Total used vehicles before VIN log filter: {debug_count}")
            
    except Exception as e:
        print(f"   [ERROR] Failed to test CAO query: {str(e)}")
        return False
    
    # Step 4: Check VIN log contents
    print(f"\n[STEP 4] Checking VIN log...")
    try:
        vin_log_query = "SELECT COUNT(*) as count FROM thoroughbred_ford_vin_log"
        vin_log_result = db_manager.execute_query(vin_log_query)
        vin_log_count = vin_log_result[0]['count'] if vin_log_result else 0
        
        print(f"   [INFO] VINs in thoroughbred_ford_vin_log: {vin_log_count}")
        
        # Check if any expected VINs are in the VIN log (they shouldn't be)
        expected_in_log_query = """
        SELECT vin, order_number, order_date 
        FROM thoroughbred_ford_vin_log 
        WHERE vin = ANY(%s)
        """
        
        vins_in_log = db_manager.execute_query(expected_in_log_query, (expected_vins,))
        
        if vins_in_log:
            print(f"   [WARNING] Expected VINs found in VIN log (should not be there):")
            for vin_record in vins_in_log:
                print(f"     - {vin_record['vin']}: Order {vin_record['order_number']} | {vin_record['order_date']}")
        else:
            print(f"   [OK] Expected VINs not in VIN log - good for CAO processing")
            
    except Exception as e:
        print(f"   [ERROR] Failed to check VIN log: {str(e)}")
        return False
    
    print(f"\n{'='*60}")
    print("THOROUGHBRED FORD CAO DIAGNOSIS COMPLETE")
    print('='*60)
    
    return True

if __name__ == "__main__":
    success = fix_thoroughbred_ford_cao()
    
    if success:
        print(f"\n[SUCCESS] Thoroughbred Ford CAO diagnosis completed!")
    else:
        print(f"\n[ERROR] Thoroughbred Ford CAO diagnosis failed!")