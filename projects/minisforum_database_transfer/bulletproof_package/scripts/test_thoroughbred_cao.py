"""
Test Thoroughbred Ford CAO processing with proper config
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_connection import db_manager

def test_thoroughbred_cao():
    """Test CAO processing for Thoroughbred Ford with expected VINs"""
    
    print("="*60)
    print("TESTING THOROUGHBRED FORD CAO PROCESSING")
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
    print(f"Expected VINs: {expected_vins}")
    
    # Step 1: Test the exact CAO query logic
    print(f"\n[STEP 1] Testing CAO query with proper filtering...")
    try:
        # This matches the CAO processing logic from correct_order_processing.py
        cao_query = """
        SELECT 
            nvd.vin,
            nvd.vehicle_condition, 
            nvd.on_lot_status,
            rvd.type as raw_type,
            rvd.year,
            rvd.make,
            rvd.model
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = %s
        AND si.status = 'active'
        AND nvd.vehicle_condition IN ('po', 'cpo')  -- Used vehicles only (cpo = certified pre-owned, po = pre-owned)
        AND nvd.on_lot_status = 'onlot'  -- Only on-lot vehicles
        AND nvd.vin NOT IN (
            SELECT vin FROM thoroughbred_ford_vin_log 
            WHERE vin IS NOT NULL
        )
        ORDER BY nvd.vin
        """
        
        cao_result = db_manager.execute_query(cao_query, (dealership_name,))
        
        print(f"   [INFO] CAO query returned: {len(cao_result)} vehicles")
        
        if cao_result:
            print(f"   [INFO] CAO results:")
            for i, vehicle in enumerate(cao_result):
                status = "✓ EXPECTED" if vehicle['vin'] in expected_vins else ""
                print(f"     {i+1}. {vehicle['vin']}: {vehicle['year']} {vehicle['make']} {vehicle['model']} | {vehicle['vehicle_condition']} | {vehicle['raw_type']} {status}")
            
            # Check how many expected VINs we found
            found_expected_vins = [v['vin'] for v in cao_result if v['vin'] in expected_vins]
            print(f"   [RESULT] Expected VINs found: {len(found_expected_vins)} / {len(expected_vins)}")
            
            if len(found_expected_vins) == len(expected_vins):
                print(f"   [SUCCESS] All expected VINs found in CAO results!")
            else:
                missing = [vin for vin in expected_vins if vin not in found_expected_vins]
                print(f"   [WARNING] Missing expected VINs: {missing}")
        else:
            print(f"   [ERROR] CAO query returned 0 results")
            
            # Debug step by step
            print(f"\n   [DEBUG] Step-by-step analysis:")
            
            # Check total normalized vehicles
            debug1_query = """
            SELECT COUNT(*) as count
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE nvd.location = %s
            AND si.status = 'active'
            """
            
            debug1_result = db_manager.execute_query(debug1_query, (dealership_name,))
            debug1_count = debug1_result[0]['count'] if debug1_result else 0
            print(f"     1. Total normalized vehicles: {debug1_count}")
            
            # Check used vehicles only
            debug2_query = """
            SELECT COUNT(*) as count
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE nvd.location = %s
            AND si.status = 'active'
            AND nvd.vehicle_condition IN ('po', 'cpo')
            """
            
            debug2_result = db_manager.execute_query(debug2_query, (dealership_name,))
            debug2_count = debug2_result[0]['count'] if debug2_result else 0
            print(f"     2. Used vehicles only: {debug2_count}")
            
            # Check on-lot only
            debug3_query = """
            SELECT COUNT(*) as count
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE nvd.location = %s
            AND si.status = 'active'
            AND nvd.vehicle_condition IN ('po', 'cpo')
            AND nvd.on_lot_status = 'onlot'
            """
            
            debug3_result = db_manager.execute_query(debug3_query, (dealership_name,))
            debug3_count = debug3_result[0]['count'] if debug3_result else 0
            print(f"     3. Used + on-lot vehicles: {debug3_count}")
            
            # Check VIN log exclusions
            debug4_query = """
            SELECT COUNT(*) as total_vehicles, COUNT(tfl.vin) as in_vin_log
            FROM (
                SELECT nvd.vin
                FROM normalized_vehicle_data nvd
                JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                JOIN scraper_imports si ON rvd.import_id = si.import_id
                WHERE nvd.location = %s
                AND si.status = 'active'
                AND nvd.vehicle_condition IN ('po', 'cpo')
                AND nvd.on_lot_status = 'onlot'
            ) vehicles
            LEFT JOIN thoroughbred_ford_vin_log tfl ON vehicles.vin = tfl.vin
            """
            
            debug4_result = db_manager.execute_query(debug4_query, (dealership_name,))
            if debug4_result:
                total_vehicles = debug4_result[0]['total_vehicles']
                in_vin_log = debug4_result[0]['in_vin_log']
                available_for_cao = total_vehicles - in_vin_log
                print(f"     4. Total vehicles: {total_vehicles}, In VIN log: {in_vin_log}, Available for CAO: {available_for_cao}")
            
    except Exception as e:
        print(f"   [ERROR] Failed to test CAO query: {str(e)}")
        return False
    
    # Step 2: Test specific expected VINs
    print(f"\n[STEP 2] Testing specific expected VINs...")
    try:
        for vin in expected_vins:
            vin_query = """
            SELECT 
                nvd.vin,
                nvd.vehicle_condition,
                nvd.on_lot_status,
                rvd.type,
                si.status as import_status,
                CASE WHEN tfl.vin IS NOT NULL THEN 'YES' ELSE 'NO' END as in_vin_log
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            LEFT JOIN thoroughbred_ford_vin_log tfl ON nvd.vin = tfl.vin
            WHERE nvd.location = %s
            AND nvd.vin = %s
            """
            
            vin_result = db_manager.execute_query(vin_query, (dealership_name, vin))
            
            if vin_result:
                v = vin_result[0]
                cao_eligible = (
                    v['vehicle_condition'] in ('po', 'cpo') and 
                    v['on_lot_status'] == 'onlot' and
                    v['import_status'] == 'active' and
                    v['in_vin_log'] == 'NO'
                )
                status = "✓ CAO ELIGIBLE" if cao_eligible else "❌ NOT ELIGIBLE"
                print(f"   {vin}: {v['vehicle_condition']} | {v['on_lot_status']} | {v['import_status']} | VIN log: {v['in_vin_log']} | {status}")
                
                if not cao_eligible:
                    reasons = []
                    if v['vehicle_condition'] not in ('po', 'cpo'):
                        reasons.append(f"condition={v['vehicle_condition']}")
                    if v['on_lot_status'] != 'onlot':
                        reasons.append(f"status={v['on_lot_status']}")
                    if v['import_status'] != 'active':
                        reasons.append(f"import={v['import_status']}")
                    if v['in_vin_log'] == 'YES':
                        reasons.append("in VIN log")
                    print(f"     Reasons: {', '.join(reasons)}")
            else:
                print(f"   {vin}: NOT FOUND in normalized data")
    
    except Exception as e:
        print(f"   [ERROR] Failed to test specific VINs: {str(e)}")
        return False
    
    print(f"\n{'='*60}")
    print("THOROUGHBRED FORD CAO TEST COMPLETE")
    print('='*60)
    
    return True

if __name__ == "__main__":
    test_thoroughbred_cao()