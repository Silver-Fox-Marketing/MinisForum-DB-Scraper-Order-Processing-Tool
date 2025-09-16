#!/usr/bin/env python3
"""
Check the structure of Auffenberg Hyundai VIN log table
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'projects/minisforum_database_transfer/bulletproof_package/scripts'))

from database_connection import db_manager

def check_table_structure():
    """Check the current structure of the Auffenberg Hyundai VIN log table"""

    table_name = "auffenberg_hyundai_vin_log"

    print(f"=== CHECKING VIN LOG TABLE STRUCTURE: {table_name} ===")

    # Get table structure
    print(f"\n[1] TABLE COLUMNS:")
    columns = db_manager.execute_query("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))

    for col in columns:
        print(f"    {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']}, default: {col['column_default']})")

    # Get sample data to understand current format
    print(f"\n[2] SAMPLE CURRENT DATA (first 5 rows):")
    sample_data = db_manager.execute_query(f"""
        SELECT * FROM {table_name}
        ORDER BY created_at DESC
        LIMIT 5
    """)

    for row in sample_data:
        print(f"    {dict(row)}")

    # Get total count
    count_data = db_manager.execute_query(f"""
        SELECT COUNT(*) as total_count
        FROM {table_name}
    """)

    print(f"\n[3] CURRENT RECORD COUNT: {count_data[0]['total_count']}")

if __name__ == "__main__":
    check_table_structure()