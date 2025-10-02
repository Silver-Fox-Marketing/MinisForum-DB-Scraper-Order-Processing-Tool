"""
Test Thoroughbred Ford CAO processing - Windows compatible
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_connection import db_manager

def test_thoroughbred_cao():
    """Test CAO processing for Thoroughbred Ford"""
    
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
    print(f"Expected VINs: {len(expected_vins)} VINs")
    
    # Test the CAO query
    print(f"\n[STEP 1] Testing CAO query...")
    try:
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
        AND nvd.vehicle_condition IN ('po', 'cpo')
        AND nvd.on_lot_status = 'onlot'
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
            expected_found = 0
            for i, vehicle in enumerate(cao_result):
                is_expected = vehicle['vin'] in expected_vins
                if is_expected:
                    expected_found += 1
                status = "[EXPECTED]" if is_expected else ""
                print(f"     {i+1}. {vehicle['vin']}: {vehicle['year']} {vehicle['make']} {vehicle['model']} | {vehicle['vehicle_condition']} {status}")
            
            print(f"   [RESULT] Expected VINs found: {expected_found} / {len(expected_vins)}")
            
            if expected_found == len(expected_vins):
                print(f"   [SUCCESS] All expected VINs found!")
                return True
            else:
                missing = [vin for vin in expected_vins if not any(r['vin'] == vin for r in cao_result)]
                print(f"   [WARNING] Missing expected VINs: {len(missing)}")
                for vin in missing:
                    print(f"     - {vin}")
        else:
            print(f"   [ERROR] CAO query returned 0 results")
    
    except Exception as e:
        print(f"   [ERROR] Failed to test CAO query: {str(e)}")
        return False
    
    # Test each expected VIN individually
    print(f"\n[STEP 2] Testing each expected VIN...")
    try:
        eligible_count = 0
        for vin in expected_vins:
            vin_query = """
            SELECT 
                nvd.vin,
                nvd.vehicle_condition,
                nvd.on_lot_status,
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
                
                if cao_eligible:
                    eligible_count += 1
                    status = "[OK]"
                else:
                    status = "[NOT ELIGIBLE]"
                
                print(f"   {vin}: {v['vehicle_condition']} | {v['on_lot_status']} | VIN log: {v['in_vin_log']} | {status}")
            else:
                print(f"   {vin}: [NOT FOUND]")
        
        print(f"\n   [SUMMARY] CAO eligible VINs: {eligible_count} / {len(expected_vins)}")
    
    except Exception as e:
        print(f"   [ERROR] Failed to test specific VINs: {str(e)}")
        return False
    
    print(f"\n{'='*60}")
    print("THOROUGHBRED FORD CAO TEST COMPLETE")
    print(f"Expected 7 VINs, found {eligible_count} eligible for CAO")
    print('='*60)
    
    return eligible_count >= 7

if __name__ == "__main__":
    success = test_thoroughbred_cao()
    if success:
        print(f"\n[SUCCESS] CAO processing should work for Thoroughbred Ford!")
    else:
        print(f"\n[ISSUE] CAO processing may have issues")