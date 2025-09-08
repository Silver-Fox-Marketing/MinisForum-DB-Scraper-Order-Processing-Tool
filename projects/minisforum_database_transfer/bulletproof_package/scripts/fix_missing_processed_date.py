"""
Fix missing processed_date column issue in CAO processing
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_connection import db_manager

def fix_processed_date_column():
    """Fix the missing processed_date column issue"""
    
    print("="*60)
    print("FIXING MISSING processed_date COLUMN")
    print("="*60)
    
    # Test database connection
    if not db_manager.test_connection():
        print("[ERROR] Database connection failed")
        return False
    
    # Step 1: Check which table needs the processed_date column
    print(f"\n[STEP 1] Checking for tables that might need processed_date column...")
    
    # Common tables that might need this column
    potential_tables = [
        'thoroughbred_ford_vin_log',
        'glendale_cdjr_vin_log',
        'processed_orders',
        'order_processing_log',
        'dealership_processing_history'
    ]
    
    for table in potential_tables:
        try:
            # Check if table exists
            exists_query = """
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = %s
            """
            exists_result = db_manager.execute_query(exists_query, (table,))
            
            if exists_result and exists_result[0]['count'] > 0:
                print(f"   [INFO] Table {table} exists")
                
                # Check if it has processed_date column
                column_query = """
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = %s AND column_name = 'processed_date'
                """
                column_result = db_manager.execute_query(column_query, (table,))
                
                if column_result:
                    print(f"     - Has processed_date column: YES")
                else:
                    print(f"     - Has processed_date column: NO")
                    
                    # Show current columns
                    all_columns_query = """
                    SELECT column_name, data_type FROM information_schema.columns 
                    WHERE table_name = %s ORDER BY ordinal_position
                    """
                    all_columns = db_manager.execute_query(all_columns_query, (table,))
                    print(f"     - Current columns:")
                    for col in all_columns:
                        print(f"       - {col['column_name']}: {col['data_type']}")
            else:
                print(f"   [INFO] Table {table} does not exist")
                
        except Exception as e:
            print(f"   [ERROR] Failed to check {table}: {str(e)}")
    
    # Step 2: Add processed_date column to VIN log tables if missing
    print(f"\n[STEP 2] Adding processed_date column to VIN log tables...")
    
    vin_log_tables = ['thoroughbred_ford_vin_log', 'glendale_cdjr_vin_log']
    
    for table in vin_log_tables:
        try:
            # Check if table exists first
            exists_query = """
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = %s
            """
            exists_result = db_manager.execute_query(exists_query, (table,))
            
            if exists_result and exists_result[0]['count'] > 0:
                # Check if processed_date column exists
                column_query = """
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = %s AND column_name = 'processed_date'
                """
                column_result = db_manager.execute_query(column_query, (table,))
                
                if not column_result:
                    print(f"   [ACTION] Adding processed_date column to {table}")
                    
                    alter_query = f"""
                    ALTER TABLE {table} 
                    ADD COLUMN processed_date TIMESTAMP DEFAULT NULL
                    """
                    
                    db_manager.execute_query(alter_query)
                    print(f"   [OK] Added processed_date column to {table}")
                else:
                    print(f"   [INFO] {table} already has processed_date column")
            else:
                print(f"   [INFO] Table {table} does not exist")
                
        except Exception as e:
            print(f"   [ERROR] Failed to add processed_date to {table}: {str(e)}")
    
    # Step 3: Check for any other database schema issues
    print(f"\n[STEP 3] Checking for other potential schema issues...")
    
    try:
        # Test a basic CAO-style query to see what fails
        test_query = """
        SELECT COUNT(*) as count
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = 'Thoroughbred Ford'
        AND si.status = 'active'
        """
        
        test_result = db_manager.execute_query(test_query)
        test_count = test_result[0]['count'] if test_result else 0
        print(f"   [OK] Basic CAO query test successful: {test_count} vehicles")
        
    except Exception as e:
        print(f"   [ERROR] Basic CAO query test failed: {str(e)}")
        return False
    
    # Step 4: Check order processing related tables
    print(f"\n[STEP 4] Checking order processing tables...")
    
    # Look for any tables that might be used in order processing
    order_tables_query = """
    SELECT table_name FROM information_schema.tables 
    WHERE table_name LIKE '%order%' OR table_name LIKE '%process%'
    """
    
    try:
        order_tables = db_manager.execute_query(order_tables_query)
        
        if order_tables:
            print(f"   [INFO] Found order/processing related tables:")
            for table in order_tables:
                table_name = table['table_name']
                print(f"     - {table_name}")
                
                # Check if this table needs processed_date
                columns_query = """
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = %s AND column_name = 'processed_date'
                """
                has_processed_date = db_manager.execute_query(columns_query, (table_name,))
                
                if not has_processed_date and 'log' in table_name.lower():
                    print(f"       [ACTION] Consider adding processed_date to {table_name}")
        else:
            print(f"   [INFO] No order/processing related tables found")
            
    except Exception as e:
        print(f"   [ERROR] Failed to check order processing tables: {str(e)}")
    
    print(f"\n{'='*60}")
    print("PROCESSED_DATE COLUMN FIX COMPLETE")
    print('='*60)
    
    return True

if __name__ == "__main__":
    success = fix_processed_date_column()
    
    if success:
        print(f"\n[SUCCESS] processed_date column issue fixed!")
    else:
        print(f"\n[ERROR] Failed to fix processed_date column issue!")