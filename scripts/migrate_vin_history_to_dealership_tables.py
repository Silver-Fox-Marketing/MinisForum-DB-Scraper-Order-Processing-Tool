"""
Migrate VIN History to Dealership-Specific Tables
Silver Fox Order Processing System v2.1
Created: 2025-08-08

This script migrates existing VIN history data from the unified 'vin_history' 
table to individual dealership-specific VIN log tables.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database_connection import db_manager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VINHistoryMigrator:
    """Handles migration from unified vin_history to dealership-specific tables"""
    
    def __init__(self):
        self.migrated_count = 0
        self.error_count = 0
        self.dealership_table_map = {}
    
    def _get_dealership_vin_log_table(self, dealership_name: str) -> str:
        """
        Generate the correct dealership-specific VIN log table name.
        Same logic as in correct_order_processing.py
        """
        if dealership_name in self.dealership_table_map:
            return self.dealership_table_map[dealership_name]
            
        # Create slug from dealership name
        slug = dealership_name.lower()
        slug = slug.replace(' ', '_')
        slug = slug.replace('&', 'and')
        slug = slug.replace('.', '')
        slug = slug.replace(',', '')
        slug = slug.replace('-', '_')
        slug = slug.replace('/', '_')
        slug = slug.replace('__', '_')
        
        # Handle special cases that might not match exactly
        special_mappings = {
            'serra_honda_of_o_fallon': 'vin_log_serra_honda_ofallon',
            'rusty_drew_chevrolet': 'vin_log_rusty_drewing_chevrolet_buick_gmc',
            'h_w_kia': 'vin_log_handw_kia'
        }
        
        if slug in special_mappings:
            table_name = special_mappings[slug]
        else:
            table_name = f'vin_log_{slug}'
        
        self.dealership_table_map[dealership_name] = table_name
        logger.debug(f"Dealership '{dealership_name}' -> table '{table_name}'")
        return table_name
    
    def check_migration_readiness(self):
        """Check if migration can proceed"""
        logger.info("=== CHECKING MIGRATION READINESS ===")
        
        # Check source data
        try:
            source_count = db_manager.execute_query("SELECT COUNT(*) FROM vin_history")[0]['count']
            logger.info(f"Source records in vin_history: {source_count}")
            
            if source_count == 0:
                logger.warning("No data to migrate from vin_history table")
                return False
                
        except Exception as e:
            logger.error(f"Cannot access vin_history table: {e}")
            return False
        
        # Check target tables exist
        vin_log_tables = db_manager.execute_query("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'vin_log_%'
        """)
        
        logger.info(f"Available VIN log tables: {len(vin_log_tables)}")
        if len(vin_log_tables) == 0:
            logger.error("No dealership VIN log tables found! Run create_dealership_vin_logs.sql first")
            return False
        
        return True
    
    def get_dealership_mapping_issues(self):
        """Identify dealerships in vin_history that don't have corresponding tables"""
        logger.info("=== CHECKING DEALERSHIP NAME MAPPING ===")
        
        # Get all dealerships from vin_history that are still active
        dealerships = db_manager.execute_query("""
            SELECT vh.dealership_name, COUNT(*) as record_count
            FROM vin_history vh
            INNER JOIN dealership_configs dc ON vh.dealership_name = dc.name
            WHERE dc.is_active = true
            GROUP BY vh.dealership_name 
            ORDER BY record_count DESC
        """)
        
        # Get all available VIN log tables
        available_tables = set()
        tables = db_manager.execute_query("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'vin_log_%'
        """)
        for table in tables:
            available_tables.add(table['table_name'])
        
        mapping_issues = []
        mapping_ok = []
        
        for dealer in dealerships:
            dealership_name = dealer['dealership_name']
            record_count = dealer['record_count']
            
            expected_table = self._get_dealership_vin_log_table(dealership_name)
            
            if expected_table in available_tables:
                mapping_ok.append((dealership_name, expected_table, record_count))
                logger.info(f"✓ {dealership_name} -> {expected_table} ({record_count} records)")
            else:
                mapping_issues.append((dealership_name, expected_table, record_count))
                logger.warning(f"✗ {dealership_name} -> {expected_table} (TABLE NOT FOUND) ({record_count} records)")
        
        logger.info(f"\nMapping Summary:")
        logger.info(f"  ✓ {len(mapping_ok)} dealerships have matching tables")
        logger.info(f"  ✗ {len(mapping_issues)} dealerships have missing tables")
        
        if mapping_issues:
            logger.error("\nMissing tables for these dealerships:")
            for name, table, count in mapping_issues:
                logger.error(f"  {name} ({count} records) -> {table}")
        
        return len(mapping_issues) == 0
    
    def migrate_dealership_data(self, dealership_name: str) -> dict:
        """Migrate data for a specific dealership"""
        target_table = self._get_dealership_vin_log_table(dealership_name)
        
        try:
            # Get all records for this dealership
            source_records = db_manager.execute_query("""
                SELECT vin, vehicle_type, order_date, created_at
                FROM vin_history 
                WHERE dealership_name = %s
                ORDER BY created_at
            """, (dealership_name,))
            
            if not source_records:
                return {'success': True, 'migrated': 0, 'skipped': 0, 'errors': 0}
            
            migrated = 0
            skipped = 0
            errors = 0
            
            logger.info(f"Migrating {len(source_records)} records from {dealership_name} to {target_table}")
            
            for record in source_records:
                try:
                    # Insert into dealership-specific table
                    insert_query = f"""
                        INSERT INTO {target_table} (vin, vehicle_type, order_date, created_at)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (vin, order_date) DO UPDATE SET
                        vehicle_type = EXCLUDED.vehicle_type,
                        created_at = EXCLUDED.created_at
                    """
                    
                    db_manager.execute_query(insert_query, (
                        record['vin'],
                        record['vehicle_type'], 
                        record['order_date'],
                        record['created_at']
                    ))
                    
                    migrated += 1
                    
                except Exception as e:
                    logger.error(f"Error migrating record {record['vin']} for {dealership_name}: {e}")
                    errors += 1
            
            logger.info(f"Completed {dealership_name}: {migrated} migrated, {errors} errors")
            
            return {
                'success': errors == 0,
                'migrated': migrated,
                'skipped': skipped,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Failed to migrate {dealership_name}: {e}")
            return {'success': False, 'migrated': 0, 'skipped': 0, 'errors': 1}
    
    def run_full_migration(self):
        """Run complete migration from vin_history to dealership-specific tables"""
        logger.info("=== STARTING FULL VIN HISTORY MIGRATION ===")
        
        # Check readiness
        if not self.check_migration_readiness():
            logger.error("Migration readiness check failed")
            return False
        
        # Check mapping
        if not self.get_dealership_mapping_issues():
            logger.error("Dealership mapping issues found - cannot proceed")
            return False
        
        # Get list of dealerships to migrate - ONLY active dealerships we still do business with
        dealerships = db_manager.execute_query("""
            SELECT vh.dealership_name, COUNT(*) as record_count
            FROM vin_history vh
            INNER JOIN dealership_configs dc ON vh.dealership_name = dc.name
            WHERE dc.is_active = true
            GROUP BY vh.dealership_name 
            ORDER BY vh.dealership_name
        """)
        
        logger.info(f"\n=== MIGRATING {len(dealerships)} DEALERSHIPS ===")
        
        total_migrated = 0
        total_errors = 0
        successful_dealerships = 0
        
        for dealer in dealerships:
            dealership_name = dealer['dealership_name']
            record_count = dealer['record_count']
            
            logger.info(f"\n--- Migrating {dealership_name} ({record_count} records) ---")
            
            result = self.migrate_dealership_data(dealership_name)
            
            if result['success']:
                successful_dealerships += 1
                total_migrated += result['migrated']
            else:
                total_errors += result['errors']
        
        logger.info(f"\n=== MIGRATION COMPLETE ===")
        logger.info(f"Successful dealerships: {successful_dealerships}/{len(dealerships)}")
        logger.info(f"Total records migrated: {total_migrated}")
        logger.info(f"Total errors: {total_errors}")
        
        if total_errors == 0:
            logger.info("✓ Migration completed successfully with no errors!")
            return True
        else:
            logger.warning(f"✗ Migration completed with {total_errors} errors")
            return False
    
    def verify_migration(self):
        """Verify migration was successful by comparing record counts"""
        logger.info("=== VERIFYING MIGRATION RESULTS ===")
        
        try:
            # Get source count
            source_total = db_manager.execute_query("SELECT COUNT(*) FROM vin_history")[0]['count']
            
            # Get target counts
            target_total = 0
            dealership_counts = {}
            
            # Get all VIN log tables
            vin_log_tables = db_manager.execute_query("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'vin_log_%'
                ORDER BY table_name
            """)
            
            for table in vin_log_tables:
                table_name = table['table_name']
                count_query = f"SELECT COUNT(*) FROM {table_name}"
                count = db_manager.execute_query(count_query)[0]['count']
                target_total += count
                if count > 0:
                    dealership_counts[table_name] = count
            
            logger.info(f"Source total (vin_history): {source_total}")
            logger.info(f"Target total (all VIN logs): {target_total}")
            
            if len(dealership_counts) > 0:
                logger.info(f"\nPer-dealership counts ({len(dealership_counts)} active):")
                for table, count in sorted(dealership_counts.items()):
                    logger.info(f"  {table}: {count}")
            
            if source_total == target_total:
                logger.info("✓ Migration verification successful - record counts match!")
                return True
            else:
                logger.warning(f"✗ Migration verification failed - count mismatch")
                logger.warning(f"  Difference: {target_total - source_total}")
                return False
                
        except Exception as e:
            logger.error(f"Error during verification: {e}")
            return False

def main():
    """Main migration function"""
    migrator = VINHistoryMigrator()
    
    print("Silver Fox VIN History Migration Tool")
    print("=" * 50)
    
    # Run migration
    success = migrator.run_full_migration()
    
    if success:
        print("\n" + "=" * 50)
        print("Migration completed successfully!")
        
        # Verify results
        migrator.verify_migration()
        
        print("\nNext steps:")
        print("1. Test the new dealership-specific VIN logic")
        print("2. Backup the old vin_history table")
        print("3. Consider dropping vin_history after verification")
        
    else:
        print("\n" + "=" * 50)
        print("Migration failed - check logs for details")
        print("Do not drop the vin_history table until migration succeeds")

if __name__ == "__main__":
    main()