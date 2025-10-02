"""
Fix Thoroughbred Ford dealer configuration
Check table structure and create proper config
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_connection import db_manager

def fix_thoroughbred_config():
    """Fix dealer configuration for Thoroughbred Ford"""
    
    print("="*60)
    print("FIXING THOROUGHBRED FORD DEALER CONFIGURATION")
    print("="*60)
    
    # Test database connection
    if not db_manager.test_connection():
        print("[ERROR] Database connection failed")
        return False
    
    # Step 1: Check dealership_configs table structure
    print(f"\n[STEP 1] Checking dealership_configs table structure...")
    try:
        structure_query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'dealership_configs'
        ORDER BY ordinal_position
        """
        
        columns = db_manager.execute_query(structure_query)
        
        if columns:
            print(f"   [INFO] dealership_configs table structure:")
            for col in columns:
                print(f"     - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
        else:
            print(f"   [ERROR] dealership_configs table does not exist")
            return False
            
    except Exception as e:
        print(f"   [ERROR] Failed to check table structure: {str(e)}")
        return False
    
    # Step 2: Check existing configs to understand the pattern
    print(f"\n[STEP 2] Checking existing dealer configurations...")
    try:
        # Just get all configs to see structure
        all_configs_query = "SELECT * FROM dealership_configs LIMIT 3"
        configs = db_manager.execute_query(all_configs_query)
        
        if configs:
            print(f"   [INFO] Found {len(configs)} existing configurations:")
            for i, config in enumerate(configs):
                print(f"   Config {i+1}:")
                for key, value in config.items():
                    print(f"     - {key}: {value}")
                print()
        else:
            print(f"   [INFO] No existing configurations found")
            
    except Exception as e:
        print(f"   [ERROR] Failed to check existing configs: {str(e)}")
        return False
    
    # Step 3: Look for South County DCJR config to use as template
    print(f"\n[STEP 3] Finding South County DCJR config as template...")
    try:
        # Try different possible column names for dealership identification
        possible_queries = [
            "SELECT * FROM dealership_configs WHERE location = 'South County DCJR'",
            "SELECT * FROM dealership_configs WHERE dealership = 'South County DCJR'", 
            "SELECT * FROM dealership_configs WHERE name = 'South County DCJR'",
            "SELECT * FROM dealership_configs WHERE location LIKE '%South County%'",
            "SELECT * FROM dealership_configs WHERE dealership LIKE '%South County%'",
            "SELECT * FROM dealership_configs WHERE name LIKE '%South County%'"
        ]
        
        template_config = None
        for query in possible_queries:
            try:
                result = db_manager.execute_query(query)
                if result:
                    template_config = result[0]
                    print(f"   [OK] Found South County config using: {query}")
                    break
            except:
                continue
        
        if not template_config:
            print(f"   [WARNING] Could not find South County DCJR config")
            print(f"   [INFO] Will create basic config for Thoroughbred Ford")
            
    except Exception as e:
        print(f"   [ERROR] Failed to find template config: {str(e)}")
        template_config = None
    
    # Step 4: Create or update Thoroughbred Ford config
    print(f"\n[STEP 4] Creating/updating Thoroughbred Ford configuration...")
    try:
        # Determine correct column name for dealership identification
        dealership_column = None
        if columns:
            for col in columns:
                col_name = col['column_name'].lower()
                if 'location' in col_name:
                    dealership_column = col['column_name']
                    break
                elif 'dealership' in col_name:
                    dealership_column = col['column_name'] 
                    break
                elif 'name' in col_name:
                    dealership_column = col['column_name']
                    break
        
        if not dealership_column:
            print(f"   [ERROR] Could not determine dealership column name")
            return False
        
        print(f"   [INFO] Using dealership column: {dealership_column}")
        
        # Check if Thoroughbred Ford config exists
        check_query = f"SELECT * FROM dealership_configs WHERE {dealership_column} = %s"
        existing_config = db_manager.execute_query(check_query, ('Thoroughbred Ford',))
        
        if existing_config:
            print(f"   [INFO] Existing Thoroughbred Ford config found")
            config = existing_config[0]
            
            # Check if it needs updating for used-only filtering
            vehicle_types = config.get('vehicle_types', [])
            if isinstance(vehicle_types, str):
                # Handle string representation of array
                import ast
                try:
                    vehicle_types = ast.literal_eval(vehicle_types)
                except:
                    vehicle_types = [vehicle_types]
            
            print(f"   [INFO] Current vehicle_types: {vehicle_types}")
            
            if 'new' in vehicle_types:
                print(f"   [ACTION] Updating config to filter out new vehicles")
                
                # Update to used only
                update_query = f"""
                UPDATE dealership_configs 
                SET vehicle_types = %s
                WHERE {dealership_column} = %s
                """
                
                # Try both array format and string format
                try:
                    db_manager.execute_query(update_query, (['used'], 'Thoroughbred Ford'))
                    print(f"   [OK] Updated config to used vehicles only")
                except:
                    # Try string format
                    db_manager.execute_query(update_query, ('["used"]', 'Thoroughbred Ford'))
                    print(f"   [OK] Updated config to used vehicles only (string format)")
            else:
                print(f"   [OK] Config already filters to used vehicles only")
        else:
            print(f"   [INFO] No existing config found - creating new one")
            
            # Create new config based on template or defaults
            if template_config:
                # Use template but modify for used only
                insert_query = f"""
                INSERT INTO dealership_configs ({dealership_column}, vehicle_types, active)
                VALUES (%s, %s, %s)
                """
                
                try:
                    db_manager.execute_query(insert_query, ('Thoroughbred Ford', ['used'], True))
                    print(f"   [OK] Created config based on template (used only)")
                except:
                    # Try string format
                    db_manager.execute_query(insert_query, ('Thoroughbred Ford', '["used"]', True))
                    print(f"   [OK] Created config based on template (used only, string format)")
            else:
                # Create basic config
                basic_query = f"""
                INSERT INTO dealership_configs ({dealership_column}, vehicle_types, active)
                VALUES (%s, %s, %s)
                """
                
                try:
                    db_manager.execute_query(basic_query, ('Thoroughbred Ford', ['used'], True))
                    print(f"   [OK] Created basic config (used only)")
                except:
                    # Try string format  
                    db_manager.execute_query(basic_query, ('Thoroughbred Ford', '["used"]', True))
                    print(f"   [OK] Created basic config (used only, string format)")
        
    except Exception as e:
        print(f"   [ERROR] Failed to create/update config: {str(e)}")
        return False
    
    # Step 5: Verify the configuration
    print(f"\n[STEP 5] Verifying Thoroughbred Ford configuration...")
    try:
        verify_query = f"SELECT * FROM dealership_configs WHERE {dealership_column} = %s"
        final_config = db_manager.execute_query(verify_query, ('Thoroughbred Ford',))
        
        if final_config:
            config = final_config[0]
            print(f"   [OK] Thoroughbred Ford configuration verified:")
            for key, value in config.items():
                print(f"     - {key}: {value}")
        else:
            print(f"   [ERROR] Configuration not found after creation")
            return False
            
    except Exception as e:
        print(f"   [ERROR] Failed to verify config: {str(e)}")
        return False
    
    print(f"\n{'='*60}")
    print("THOROUGHBRED FORD CONFIG FIXED")
    print('='*60)
    
    return True

if __name__ == "__main__":
    success = fix_thoroughbred_config()
    
    if success:
        print(f"\n[SUCCESS] Thoroughbred Ford dealer config fixed!")
    else:
        print(f"\n[ERROR] Failed to fix Thoroughbred Ford config!")