"""
Fix Porsche CAO order processing - Create missing VIN log table and update logic
"""
import sys
sys.path.insert(0, 'scripts')
from database_connection import db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_porsche_vin_log_table():
    """Create the missing porsche_st_louis_vin_log table"""
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS porsche_st_louis_vin_log (
        vin VARCHAR(17) PRIMARY KEY,
        processed_date DATE NOT NULL DEFAULT CURRENT_DATE,
        order_type VARCHAR(20),
        template_type VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    try:
        db_manager.execute_query(create_table_sql)
        logger.info("✅ Created porsche_st_louis_vin_log table")
        
        # Create index for faster lookups
        index_sql = """
        CREATE INDEX IF NOT EXISTS idx_porsche_vin_log_date 
        ON porsche_st_louis_vin_log(processed_date);
        """
        db_manager.execute_query(index_sql)
        logger.info("✅ Created index on processed_date")
        
        # Check if old vin_history has Porsche data to migrate
        migrate_check = """
        SELECT COUNT(*) as count 
        FROM vin_history 
        WHERE dealership_name = 'Porsche St. Louis';
        """
        
        result = db_manager.execute_query(migrate_check)
        if result and result[0]['count'] > 0:
            logger.info(f"Found {result[0]['count']} Porsche VINs in old vin_history table")
            
            # Migrate existing Porsche VINs
            migrate_sql = """
            INSERT INTO porsche_st_louis_vin_log (vin, processed_date, order_type)
            SELECT DISTINCT vin, order_date, 'MIGRATED'
            FROM vin_history
            WHERE dealership_name = 'Porsche St. Louis'
            ON CONFLICT (vin) DO NOTHING;
            """
            
            db_manager.execute_query(migrate_sql)
            logger.info("✅ Migrated existing Porsche VINs to new table")
            
            # Verify migration
            verify_sql = "SELECT COUNT(*) as count FROM porsche_st_louis_vin_log;"
            verify_result = db_manager.execute_query(verify_sql)
            logger.info(f"✅ porsche_st_louis_vin_log now contains {verify_result[0]['count']} VINs")
        else:
            logger.info("No existing Porsche VINs to migrate")
            
    except Exception as e:
        logger.error(f"Error creating Porsche VIN log table: {e}")
        raise

def fix_order_processing_workflow():
    """Update the order_processing_workflow.py to use dealership-specific VIN logs"""
    
    import os
    workflow_path = "order_processing_workflow.py"
    
    if not os.path.exists(workflow_path):
        logger.error(f"Could not find {workflow_path}")
        return
    
    # Read the current file
    with open(workflow_path, 'r') as f:
        content = f.read()
    
    # Check if already fixed
    if 'dealership_vin_table' in content:
        logger.info("✅ order_processing_workflow.py already updated for dealership-specific VIN logs")
        return
    
    logger.info("📝 Updating order_processing_workflow.py to use dealership-specific VIN logs...")
    
    # The updated compare_vin_lists method
    new_compare_method = '''    def compare_vin_lists(self, dealership_name: str, current_vins: List[str]) -> Tuple[List[str], List[str]]:
        """Compare current VINs with dealership-specific VIN log to find new vehicles"""
        try:
            # Convert dealership name to table name format
            # Example: "Porsche St. Louis" -> "porsche_st_louis_vin_log"
            table_name = dealership_name.lower().replace(' ', '_').replace('.', '').replace("'", '') + '_vin_log'
            
            # Check if dealership-specific table exists
            table_check = db_manager.execute_query("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            """, (table_name,))
            
            if not table_check:
                logger.warning(f"VIN log table {table_name} does not exist. Creating it...")
                # Create the table if it doesn't exist
                create_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    vin VARCHAR(17) PRIMARY KEY,
                    processed_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    order_type VARCHAR(20),
                    template_type VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                db_manager.execute_query(create_sql)
                logger.info(f"Created VIN log table: {table_name}")
            
            # Get previous VINs from dealership-specific table
            query = f"""
                SELECT vin FROM {table_name}
            """
            previous_vins = db_manager.execute_query(query)
            
            previous_vin_set = {row['vin'] for row in previous_vins}
            current_vin_set = set(current_vins)
            
            # Find new VINs (in current but not in previous)
            new_vins = list(current_vin_set - previous_vin_set)
            
            # Find removed VINs (in previous but not in current)
            removed_vins = list(previous_vin_set - current_vin_set)
            
            logger.info(f"[VIN COMPARE] {dealership_name}: {len(new_vins)} new, {len(removed_vins)} removed")
            logger.info(f"[VIN COMPARE] Using table: {table_name}")
            logger.info(f"[VIN COMPARE] Previous VINs in log: {len(previous_vin_set)}, Current inventory: {len(current_vin_set)}")
            
            # Update dealership-specific VIN history
            self._update_dealership_vin_history(dealership_name, table_name, new_vins)
            
            return new_vins, removed_vins
            
        except Exception as e:
            logger.error(f"Error comparing VINs for {dealership_name}: {e}")
            return current_vins, []  # Treat all as new if comparison fails
    
    def _update_dealership_vin_history(self, dealership_name: str, table_name: str, new_vins: List[str]):
        """Update dealership-specific VIN history for tracking"""
        try:
            if not new_vins:
                logger.info(f"No new VINs to add to {table_name}")
                return
                
            # Insert new VINs into dealership-specific table
            for vin in new_vins:
                insert_sql = f"""
                    INSERT INTO {table_name} (vin, processed_date, order_type)
                    VALUES (%s, CURRENT_DATE, 'CAO')
                    ON CONFLICT (vin) DO NOTHING
                """
                db_manager.execute_query(insert_sql, (vin,))
            
            logger.info(f"[VIN HISTORY] Added {len(new_vins)} new VINs to {table_name}")
                
        except Exception as e:
            logger.error(f"Error updating dealership VIN history: {e}")'''
    
    # Write the updated method to a separate file for now
    with open('updated_compare_method.py', 'w') as f:
        f.write(new_compare_method)
    
    logger.info("✅ Created updated_compare_method.py with fixed logic")
    logger.info("Note: The compare_vin_lists method needs to be manually updated in order_processing_workflow.py")

def test_porsche_cao_with_fixed_logic():
    """Test the Porsche CAO order with the fixed logic"""
    
    logger.info("\n=== TESTING PORSCHE CAO ORDER WITH FIXED LOGIC ===")
    
    # First ensure the table exists
    create_porsche_vin_log_table()
    
    # Check current Porsche inventory (using older data since no current scrape)
    inventory_query = """
    SELECT DISTINCT ON (vin) vin, make, model, year, type, price, import_date
    FROM raw_vehicle_data 
    WHERE location = 'Porsche St. Louis'
    ORDER BY vin, import_date DESC
    LIMIT 10;
    """
    
    inventory = db_manager.execute_query(inventory_query)
    logger.info(f"\n📊 Sample Porsche inventory (latest available):")
    for vehicle in inventory[:5]:
        logger.info(f"  {vehicle['year']} {vehicle['make']} {vehicle['model']} - VIN: {vehicle['vin']}")
    
    # Check what's in the VIN log
    vin_log_query = """
    SELECT COUNT(*) as total_vins,
           MIN(processed_date) as earliest,
           MAX(processed_date) as latest
    FROM porsche_st_louis_vin_log;
    """
    
    vin_log_stats = db_manager.execute_query(vin_log_query)
    if vin_log_stats:
        stats = vin_log_stats[0]
        logger.info(f"\n📋 Porsche VIN log status:")
        logger.info(f"  Total VINs processed: {stats['total_vins']}")
        logger.info(f"  Date range: {stats['earliest']} to {stats['latest']}")
    
    # Simulate CAO comparison
    all_current_vins_query = """
    SELECT DISTINCT vin 
    FROM raw_vehicle_data 
    WHERE location = 'Porsche St. Louis';
    """
    
    current_vins = db_manager.execute_query(all_current_vins_query)
    current_vin_list = [row['vin'] for row in current_vins]
    
    # Get processed VINs
    processed_vins_query = "SELECT vin FROM porsche_st_louis_vin_log;"
    processed_vins = db_manager.execute_query(processed_vins_query)
    processed_vin_set = {row['vin'] for row in processed_vins}
    
    # Calculate new VINs
    new_vins = [vin for vin in current_vin_list if vin not in processed_vin_set]
    
    logger.info(f"\n✅ CAO Analysis Results:")
    logger.info(f"  Total current inventory: {len(current_vin_list)} vehicles")
    logger.info(f"  Previously processed: {len(processed_vin_set)} vehicles")
    logger.info(f"  NEW vehicles needing graphics: {len(new_vins)} vehicles")
    
    if new_vins:
        logger.info(f"\n  Sample of new VINs (first 5):")
        for vin in new_vins[:5]:
            logger.info(f"    - {vin}")
    
    return len(new_vins)

if __name__ == "__main__":
    try:
        # Create the missing table
        create_porsche_vin_log_table()
        
        # Show how to fix the workflow
        fix_order_processing_workflow()
        
        # Test the logic
        new_vehicle_count = test_porsche_cao_with_fixed_logic()
        
        logger.info("\n" + "="*60)
        logger.info("🎯 SUMMARY:")
        logger.info(f"  ✅ porsche_st_louis_vin_log table created")
        logger.info(f"  ✅ Logic for dealership-specific VIN comparison documented")
        logger.info(f"  ✅ {new_vehicle_count} vehicles would be processed in a CAO order")
        logger.info("  ⚠️  order_processing_workflow.py needs manual update with new compare_vin_lists method")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Error in fix process: {e}")
        import traceback
        traceback.print_exc()