"""
Check for dealership name mismatches in Thoroughbred Ford data
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_connection import db_manager

def check_name_matching():
    """Check for dealership name mismatches that could cause CAO issues"""
    
    print("="*60)
    print("CHECKING THOROUGHBRED FORD NAME MATCHING")
    print("="*60)
    
    # Test database connection
    if not db_manager.test_connection():
        print("[ERROR] Database connection failed")
        return False
    
    # Step 1: Check all variations of Thoroughbred Ford in different tables
    print(f"\n[STEP 1] Checking dealership name variations...")
    
    tables_to_check = [
        ('normalized_vehicle_data', 'location'),
        ('raw_vehicle_data', 'location'),
        ('dealership_configs', 'name'),
        ('thoroughbred_ford_vin_log', 'dealership')
    ]
    
    thoroughbred_variations = set()
    
    for table, column in tables_to_check:
        try:
            # Check if table exists
            exists_query = """
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = %s
            """
            exists_result = db_manager.execute_query(exists_query, (table,))
            
            if exists_result and exists_result[0]['count'] > 0:
                # Get all variations that contain "thoroughbred" or "ford"
                variations_query = f"""
                SELECT DISTINCT {column} as name, COUNT(*) as count
                FROM {table}
                WHERE LOWER({column}) LIKE '%thoroughbred%' 
                   OR LOWER({column}) LIKE '%ford%'
                GROUP BY {column}
                ORDER BY count DESC
                """
                
                variations = db_manager.execute_query(variations_query)
                
                if variations:
                    print(f"   [INFO] {table}.{column} variations:")
                    for variation in variations:
                        name = variation['name']
                        count = variation['count']
                        print(f"     - '{name}': {count} records")
                        
                        # Add to our set of variations
                        if name and ('thoroughbred' in name.lower() or 'ford' in name.lower()):
                            thoroughbred_variations.add(name)
                else:
                    print(f"   [INFO] No Thoroughbred/Ford entries in {table}.{column}")
            else:
                print(f"   [INFO] Table {table} does not exist")
                
        except Exception as e:
            print(f"   [ERROR] Failed to check {table}: {str(e)}")
    
    # Step 2: Show all unique variations found
    print(f"\n[STEP 2] All Thoroughbred Ford name variations found:")
    if thoroughbred_variations:
        for i, name in enumerate(sorted(thoroughbred_variations), 1):
            print(f"   {i}. '{name}'")
    else:
        print("   [WARNING] No Thoroughbred Ford variations found!")
    
    # Step 3: Test CAO query with each variation
    print(f"\n[STEP 3] Testing CAO processing for each name variation...")
    
    for name in thoroughbred_variations:
        try:
            # Test the CAO query
            cao_query = """
            SELECT COUNT(*) as count
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE nvd.location = %s
            AND si.status = 'active'
            AND nvd.vehicle_condition IN ('po', 'cpo')
            AND nvd.on_lot_status = 'onlot'
            """
            
            cao_result = db_manager.execute_query(cao_query, (name,))
            count = cao_result[0]['count'] if cao_result else 0
            
            # Check VIN log for this name variation
            vin_log_query = """
            SELECT COUNT(*) as count
            FROM thoroughbred_ford_vin_log
            WHERE dealership = %s
            """
            
            vin_log_result = db_manager.execute_query(vin_log_query, (name,))
            vin_log_count = vin_log_result[0]['count'] if vin_log_result else 0
            
            status = ""
            if count >= 7:
                status = " <- GOOD FOR CAO"
            elif count == 0:
                status = " <- NO DATA"
            
            print(f"   '{name}': {count} CAO eligible vehicles, {vin_log_count} in VIN log{status}")
            
        except Exception as e:
            print(f"   [ERROR] Failed to test '{name}': {str(e)}")
    
    # Step 4: Check if dealership config name matches data
    print(f"\n[STEP 4] Checking dealership config name matching...")
    
    try:
        # Get the config name
        config_query = "SELECT name FROM dealership_configs WHERE name LIKE '%Thoroughbred%' OR name LIKE '%Ford%'"
        config_result = db_manager.execute_query(config_query)
        
        if config_result:
            config_name = config_result[0]['name']
            print(f"   [INFO] Dealer config name: '{config_name}'")
            
            # Check if this exact name exists in normalized data
            data_query = """
            SELECT COUNT(*) as count
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE nvd.location = %s
            AND si.status = 'active'
            """
            
            data_result = db_manager.execute_query(data_query, (config_name,))
            data_count = data_result[0]['count'] if data_result else 0
            
            print(f"   [INFO] Vehicles found for config name '{config_name}': {data_count}")
            
            if data_count == 0:
                print(f"   [WARNING] Config name doesn't match any vehicle data!")
                print(f"   [ACTION] Need to update config name or fix data name")
        else:
            print(f"   [ERROR] No Thoroughbred Ford config found")
            
    except Exception as e:
        print(f"   [ERROR] Failed to check config name matching: {str(e)}")
    
    # Step 5: Recommend the canonical name
    print(f"\n[STEP 5] Recommendation...")
    
    # Find the name with the most vehicle data
    best_name = None
    best_count = 0
    
    for name in thoroughbred_variations:
        try:
            count_query = """
            SELECT COUNT(*) as count
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE nvd.location = %s
            AND si.status = 'active'
            """
            
            count_result = db_manager.execute_query(count_query, (name,))
            count = count_result[0]['count'] if count_result else 0
            
            if count > best_count:
                best_count = count
                best_name = name
                
        except:
            continue
    
    if best_name:
        print(f"   [RECOMMEND] Use '{best_name}' as canonical name ({best_count} vehicles)")
        print(f"   [ACTION] Update dealer config to use: '{best_name}'")
        print(f"   [ACTION] Ensure VIN log uses: '{best_name}'")
    else:
        print(f"   [ERROR] Could not determine best name")
    
    print(f"\n{'='*60}")
    print("NAME MATCHING CHECK COMPLETE")
    print('='*60)
    
    return True

if __name__ == "__main__":
    check_name_matching()