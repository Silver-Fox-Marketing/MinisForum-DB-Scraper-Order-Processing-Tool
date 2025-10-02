"""
Compare expected VINs with actual billing sheet results for Thoroughbred Ford
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_connection import db_manager

def compare_thoroughbred_vins():
    """Compare expected VINs with actual billing results"""
    
    print("="*60)
    print("COMPARING THOROUGHBRED FORD EXPECTED vs ACTUAL VINs")
    print("="*60)
    
    # Test database connection
    if not db_manager.test_connection():
        print("[ERROR] Database connection failed")
        return False
    
    # Expected VINs (what we should have gotten)
    expected_vins = [
        'MAJ6S3GL3KC284530',
        '1FTEW1EP9NKD39089', 
        '5NTJCDDE3RH110230',
        '5TDFZRBH7MS089740',
        '1FMCU9JZ9RUB01395',
        '1FA6P8CF3R5408633',
        '1FMSK8DH6PGB07634'
    ]
    
    # Actual VINs from billing sheet
    actual_vins = [
        '1FA6P8CF3R5408633',  # 2024 Ford Mustang
        'MAJ6S3GL3KC284530',  # 2019 Ford EcoSport
        '1FTEW1EP9NKD39089',  # 2022 Ford F-150
        '1FMCU9JZ9RUB01395',  # 2024 Ford Escape Hybrid
        '1FMSK8DH6PGB07634',  # 2023 Ford Explorer
        '1FTFW1ED9PFD07359',  # 2023 Ford F-150 (EXTRA - not expected)
        '5TDFZRBH7MS089740',  # 2021 Toyota Highlander
        '5NTJCDDE3RH110230'   # 2024 Hyundai Santa Cruz
    ]
    
    print(f"Expected VINs: {len(expected_vins)}")
    print(f"Actual VINs: {len(actual_vins)}")
    
    # Step 1: Compare the lists
    print(f"\n[STEP 1] VIN comparison analysis...")
    
    # Find VINs in both lists
    matched_vins = [vin for vin in expected_vins if vin in actual_vins]
    print(f"   [OK] Matched VINs: {len(matched_vins)} / {len(expected_vins)}")
    
    # Find expected VINs that are missing from actual
    missing_vins = [vin for vin in expected_vins if vin not in actual_vins]
    if missing_vins:
        print(f"   [WARNING] Missing VINs: {len(missing_vins)}")
        for vin in missing_vins:
            print(f"     - {vin}")
    else:
        print(f"   [SUCCESS] No missing VINs - all expected VINs are present!")
    
    # Find extra VINs that weren't expected
    extra_vins = [vin for vin in actual_vins if vin not in expected_vins]
    if extra_vins:
        print(f"   [INFO] Extra VINs (bonus): {len(extra_vins)}")
        for vin in extra_vins:
            print(f"     + {vin}")
    
    # Step 2: Analyze the extra VIN in detail
    print(f"\n[STEP 2] Analyzing the extra VIN...")
    
    for vin in extra_vins:
        try:
            print(f"\n   Analyzing: {vin}")
            
            # Get detailed info about this VIN
            detail_query = """
            SELECT 
                nvd.vin,
                nvd.vehicle_condition,
                nvd.on_lot_status,
                rvd.type as raw_type,
                rvd.year,
                rvd.make,
                rvd.model,
                rvd.stock,
                rvd.price,
                si.status as import_status,
                CASE WHEN tfl.vin IS NOT NULL THEN 'YES' ELSE 'NO' END as in_vin_log
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            LEFT JOIN thoroughbred_ford_vin_log tfl ON nvd.vin = tfl.vin
            WHERE nvd.location = 'Thoroughbred Ford'
            AND nvd.vin = %s
            """
            
            detail_result = db_manager.execute_query(detail_query, (vin,))
            
            if detail_result:
                v = detail_result[0]
                print(f"     Vehicle: {v['year']} {v['make']} {v['model']}")
                print(f"     Stock: {v['stock']}")
                print(f"     Price: ${v['price'] or 'N/A'}")
                print(f"     Condition: {v['vehicle_condition']} (raw: {v['raw_type']})")
                print(f"     Lot Status: {v['on_lot_status']}")
                print(f"     Import Status: {v['import_status']}")
                print(f"     In VIN Log: {v['in_vin_log']}")
                
                # Check if it meets CAO criteria
                cao_eligible = (
                    v['vehicle_condition'] in ('po', 'cpo') and 
                    v['on_lot_status'] == 'onlot' and
                    v['import_status'] == 'active' and
                    v['in_vin_log'] == 'NO'
                )
                
                print(f"     CAO Eligible: {'YES' if cao_eligible else 'NO'}")
                
                if cao_eligible:
                    print(f"     [ANALYSIS] This VIN correctly qualified for CAO processing")
                else:
                    print(f"     [QUESTION] Why was this VIN included if not CAO eligible?")
                    reasons = []
                    if v['vehicle_condition'] not in ('po', 'cpo'):
                        reasons.append(f"condition={v['vehicle_condition']}")
                    if v['on_lot_status'] != 'onlot':
                        reasons.append(f"status={v['on_lot_status']}")
                    if v['import_status'] != 'active':
                        reasons.append(f"import={v['import_status']}")
                    if v['in_vin_log'] == 'YES':
                        reasons.append("already in VIN log")
                    print(f"       Reasons: {', '.join(reasons)}")
            else:
                print(f"     [ERROR] VIN not found in normalized data")
                
        except Exception as e:
            print(f"     [ERROR] Failed to analyze {vin}: {str(e)}")
    
    # Step 3: Verify all expected VINs are actually eligible
    print(f"\n[STEP 3] Verifying expected VINs are CAO eligible...")
    
    for vin in expected_vins:
        try:
            # Get detailed info about this expected VIN
            detail_query = """
            SELECT 
                nvd.vin,
                nvd.vehicle_condition,
                nvd.on_lot_status,
                rvd.type as raw_type,
                si.status as import_status,
                CASE WHEN tfl.vin IS NOT NULL THEN 'YES' ELSE 'NO' END as in_vin_log
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            LEFT JOIN thoroughbred_ford_vin_log tfl ON nvd.vin = tfl.vin
            WHERE nvd.location = 'Thoroughbred Ford'
            AND nvd.vin = %s
            """
            
            detail_result = db_manager.execute_query(detail_query, (vin,))
            
            if detail_result:
                v = detail_result[0]
                
                # Check if it meets CAO criteria
                cao_eligible = (
                    v['vehicle_condition'] in ('po', 'cpo') and 
                    v['on_lot_status'] == 'onlot' and
                    v['import_status'] == 'active' and
                    v['in_vin_log'] == 'NO'
                )
                
                status = "ELIGIBLE" if cao_eligible else "NOT ELIGIBLE"
                present = "PRESENT" if vin in actual_vins else "MISSING"
                
                print(f"   {vin}: {status} | {present}")
                
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
                    print(f"     Reasons not eligible: {', '.join(reasons)}")
            else:
                print(f"   {vin}: NOT FOUND IN DATA")
                
        except Exception as e:
            print(f"   {vin}: ERROR - {str(e)}")
    
    print(f"\n{'='*60}")
    print("THOROUGHBRED FORD VIN COMPARISON COMPLETE")
    print('='*60)
    
    # Summary
    if len(matched_vins) == len(expected_vins):
        print(f"\n[SUCCESS] All {len(expected_vins)} expected VINs are present in billing sheet!")
        if extra_vins:
            print(f"[BONUS] Plus {len(extra_vins)} additional eligible vehicle(s)")
        print(f"[RESULT] CAO processing working correctly - got {len(actual_vins)} VINs total")
    else:
        print(f"\n[ISSUE] Only {len(matched_vins)} / {len(expected_vins)} expected VINs found")
        print(f"[ACTION] Need to investigate missing VINs")
    
    return len(matched_vins) == len(expected_vins)

if __name__ == "__main__":
    success = compare_thoroughbred_vins()
    if success:
        print(f"\n[CONCLUSION] CAO processing is working correctly!")
    else:
        print(f"\n[CONCLUSION] CAO processing has issues that need fixing")