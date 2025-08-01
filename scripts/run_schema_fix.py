#!/usr/bin/env python3
"""
Run the VIN History schema fix to resolve database constraint issues.
This fixes the Order Processing Wizard generating exactly 100 vehicles issue.
"""

import sys
import logging
from pathlib import Path
from database_connection import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_schema_fix():
    """Execute the VIN history schema fix SQL script."""
    try:
        # Read the schema fix SQL
        schema_fix_path = Path(__file__).parent / "fix_vin_history_schema.sql"
        
        if not schema_fix_path.exists():
            logger.error(f"Schema fix file not found: {schema_fix_path}")
            return False
            
        with open(schema_fix_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        logger.info("Executing VIN history schema fix...")
        
        # Execute the schema fix using execute_query (it can handle complex SQL)
        db_manager.execute_query(sql_content)
        
        logger.info("✅ VIN history schema fix completed successfully!")
        
        # Test the fix by checking the table structure
        columns = db_manager.execute_query("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'vin_history' 
            ORDER BY ordinal_position
        """)
        
        logger.info("Current VIN history table structure:")
        for col in columns:
            logger.info(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        
        # Check if unique constraint exists
        constraints = db_manager.execute_query("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints 
            WHERE table_name = 'vin_history' 
            AND constraint_type = 'UNIQUE'
        """)
        
        if constraints:
            logger.info("✅ Unique constraint found:")
            for constraint in constraints:
                logger.info(f"  - {constraint['constraint_name']}: {constraint['constraint_type']}")
        else:
            logger.warning("⚠️ No unique constraint found - this may cause duplicate issues")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema fix failed: {e}")
        return False

if __name__ == "__main__":
    success = run_schema_fix()
    if success:
        print("\n🎉 Database schema fix completed! The Order Processing Wizard should now work correctly.")
    else:
        print("\n❌ Schema fix failed. Check the logs above for details.")
        sys.exit(1)