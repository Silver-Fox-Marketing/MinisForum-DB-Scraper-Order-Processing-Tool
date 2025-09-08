"""
Check if the extra VIN should have been normalized to offlot (in-transit)
Reference normalization mapping to verify correct lot status
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_connection import db_manager

def check_extra_vin_normalization():
    """Check normalization of extra VIN against mapping rules"""
    
    print("="*60)
    print("CHECKING EXTRA VIN NORMALIZATION STATUS")
    print("="*60)
    
    # Test database connection
    if not db_manager.test_connection():
        print("[ERROR] Database connection failed")
        return False
    
    extra_vin = '1FTFW1ED9PFD07359'  # 2023 Ford F-150
    
    print(f"Checking VIN: {extra_vin}")
    
    # Step 1: Get raw vehicle data to see original status
    print(f"\n[STEP 1] Checking raw vehicle data...")
    try:
        raw_query = """
        SELECT 
            rvd.*,
            si.status as import_status,
            si.import_date,
            si.import_id
        FROM raw_vehicle_data rvd
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE rvd.vin = %s
        AND si.status = 'active'
        """
        
        raw_result = db_manager.execute_query(raw_query, (extra_vin,))
        
        if raw_result:
            raw_data = raw_result[0]
            print(f"   [INFO] Raw vehicle data found:")
            print(f"     - VIN: {raw_data['vin']}")
            print(f"     - Location: {raw_data['location']}")
            print(f"     - Type: {raw_data['type']}")
            print(f"     - Status: {raw_data.get('status', 'N/A')}")
            print(f"     - Stock: {raw_data['stock']}")
            print(f"     - Year: {raw_data['year']} {raw_data['make']} {raw_data['model']}")
            print(f"     - Import ID: {raw_data['import_id']}")
            print(f"     - Import Date: {raw_data['import_date']}")
            
            # Check for any status field that might indicate in-transit
            raw_status = raw_data.get('status', '').lower() if raw_data.get('status') else ''
            potential_intransit_indicators = [
                'in-transit', 'intransit', 'in transit', 'arriving', 'arriving soon', 
                'ordered', 'incoming', 'expected', 'pending'
            ]
            
            might_be_intransit = any(indicator in raw_status for indicator in potential_intransit_indicators)
            
            if might_be_intransit:
                print(f"   [WARNING] Raw status '{raw_data.get('status')}' might indicate in-transit!")
            else:
                print(f"   [OK] Raw status '{raw_data.get('status', 'N/A')}' doesn't indicate in-transit")
        else:
            print(f"   [ERROR] No raw vehicle data found for VIN")
            return False
            
    except Exception as e:
        print(f"   [ERROR] Failed to get raw data: {str(e)}")
        return False
    
    # Step 2: Check normalized vehicle data
    print(f"\n[STEP 2] Checking normalized vehicle data...")
    try:
        normalized_query = """
        SELECT 
            nvd.*,
            rvd.status as raw_status,
            rvd.type as raw_type
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.vin = %s
        AND si.status = 'active'
        """
        
        normalized_result = db_manager.execute_query(normalized_query, (extra_vin,))
        
        if normalized_result:
            norm_data = normalized_result[0]
            print(f"   [INFO] Normalized data:")
            print(f"     - VIN: {norm_data['vin']}")
            print(f"     - Vehicle Condition: {norm_data['vehicle_condition']}")
            print(f"     - On Lot Status: {norm_data['on_lot_status']}")
            print(f"     - Raw Status: {norm_data.get('raw_status', 'N/A')}")
            print(f"     - Raw Type: {norm_data.get('raw_type', 'N/A')}")
            
            # This is the key check - should it be offlot?
            if norm_data['on_lot_status'] == 'onlot':
                print(f"   [INFO] Normalized as 'onlot' - eligible for CAO processing")
            elif norm_data['on_lot_status'] == 'offlot':
                print(f"   [WARNING] Normalized as 'offlot' - should NOT be in CAO results!")
            else:
                print(f"   [UNKNOWN] Normalized as '{norm_data['on_lot_status']}' - unusual status")
        else:
            print(f"   [ERROR] No normalized data found for VIN")
            return False
            
    except Exception as e:
        print(f"   [ERROR] Failed to get normalized data: {str(e)}")
        return False
    
    # Step 3: Check normalization mapping file
    print(f"\n[STEP 3] Checking normalization mapping...")
    
    # Look for the normalization mapping CSV file
    mapping_paths = [
        r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\Scraper Data Normalization Map - Sheet1 (3).csv",
        r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\docs\Scraper Data Normalization Map - Sheet1 (2).csv"
    ]
    
    mapping_found = False
    raw_status_to_check = raw_data.get('status', '') if 'raw_data' in locals() else ''
    
    for mapping_path in mapping_paths:
        if os.path.exists(mapping_path):
            try:
                print(f"   [INFO] Found mapping file: {mapping_path}")
                
                import pandas as pd
                mapping_df = pd.read_csv(mapping_path)
                print(f"   [INFO] Mapping file columns: {list(mapping_df.columns)}")
                
                # Show first few rows to understand structure
                print(f"   [INFO] First 3 mapping rows:")
                for i, row in mapping_df.head(3).iterrows():
                    print(f"     Row {i}: {dict(row)}")
                
                # Look for the raw status in the mapping
                if raw_status_to_check:
                    # Try to find matching status in various possible columns
                    possible_status_columns = [col for col in mapping_df.columns if 'status' in col.lower()]
                    possible_raw_columns = [col for col in mapping_df.columns if 'raw' in col.lower() or 'original' in col.lower()]
                    
                    print(f"   [INFO] Possible status columns: {possible_status_columns}")
                    print(f"   [INFO] Possible raw columns: {possible_raw_columns}")
                    
                    # Search for our status value
                    found_mappings = []
                    for col in mapping_df.columns:
                        matches = mapping_df[mapping_df[col].astype(str).str.lower() == raw_status_to_check.lower()]
                        if not matches.empty:
                            for _, match in matches.iterrows():
                                found_mappings.append((col, dict(match)))
                    
                    if found_mappings:
                        print(f"   [INFO] Found {len(found_mappings)} mappings for status '{raw_status_to_check}':")
                        for col, mapping in found_mappings:
                            print(f"     Column '{col}': {mapping}")
                    else:
                        print(f"   [INFO] No specific mapping found for status '{raw_status_to_check}'")
                        print(f"   [INFO] This might use default mapping rules")
                
                mapping_found = True
                break
                
            except Exception as e:
                print(f"   [ERROR] Failed to read mapping file {mapping_path}: {str(e)}")
                continue
    
    if not mapping_found:
        print(f"   [WARNING] No normalization mapping file found")
        print(f"   [INFO] Checking hardcoded mapping rules in database_config.py...")
        
        # Check the hardcoded CONDITION_MAPPING from database_config.py
        from scripts.database_config import CONDITION_MAPPING
        
        print(f"   [INFO] Hardcoded condition mappings:")
        for key, value in CONDITION_MAPPING.items():
            print(f"     '{key}' -> '{value}'")
            
        # Check if our raw status maps to anything specific
        if raw_status_to_check.lower() in CONDITION_MAPPING:
            mapped_value = CONDITION_MAPPING[raw_status_to_check.lower()]
            print(f"   [FOUND] '{raw_status_to_check}' maps to '{mapped_value}'")
            
            if mapped_value in ['offlot', 'intransit']:
                print(f"   [WARNING] This should have been normalized to offlot!")
                print(f"   [ISSUE] Vehicle should NOT be in CAO results")
            else:
                print(f"   [OK] Mapped value '{mapped_value}' doesn't indicate offlot")
        else:
            print(f"   [INFO] Status '{raw_status_to_check}' not in hardcoded mappings")
            print(f"   [INFO] Likely uses default onlot mapping")
    
    # Step 4: Final assessment
    print(f"\n[STEP 4] Final assessment...")
    
    if 'norm_data' in locals():
        if norm_data['on_lot_status'] == 'onlot':
            print(f"   [CONCLUSION] VIN {extra_vin} is correctly normalized as 'onlot'")
            print(f"   [RESULT] Vehicle legitimately qualifies for CAO processing")
            print(f"   [STATUS] No filtering error - this is a valid bonus vehicle")
            return True
        else:
            print(f"   [CONCLUSION] VIN {extra_vin} is normalized as '{norm_data['on_lot_status']}'")
            print(f"   [RESULT] If this is 'offlot', vehicle should NOT be in CAO results")
            print(f"   [STATUS] Potential normalization or filtering error")
            return False
    else:
        print(f"   [ERROR] Could not determine final normalization status")
        return False

if __name__ == "__main__":
    print("Checking extra VIN normalization against mapping rules...")
    success = check_extra_vin_normalization()
    
    if success:
        print(f"\n[SUCCESS] Extra VIN is correctly included in CAO results")
    else:
        print(f"\n[ISSUE] Extra VIN may have normalization problems")