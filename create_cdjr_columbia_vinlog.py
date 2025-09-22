#!/usr/bin/env python3
"""
Create missing VIN log table for CDJR of Columbia
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'projects/minisforum_database_transfer/bulletproof_package/scripts'))

from database_connection import db_manager

def create_cdjr_columbia_vinlog():
    """Create VIN log table for CDJR of Columbia"""

    dealership_name = "CDJR of Columbia"
    table_name = "cdjr_of_columbia_vin_log"

    print(f"=== CREATING VIN LOG TABLE FOR {dealership_name} ===\n")

    # Check if table already exists
    table_exists = db_manager.execute_query("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = %s
    """, (table_name,))

    if table_exists:
        print(f"[WARNING] Table {table_name} already exists!")
        return True
    else:
        # Create VIN log table with same structure as others
        create_table_query = f"""
            CREATE TABLE {table_name} (
                vin VARCHAR(17) PRIMARY KEY,
                order_number VARCHAR(50),
                processed_date DATE DEFAULT CURRENT_DATE,
                order_type VARCHAR(20) DEFAULT 'HISTORICAL',
                template_type VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                order_date DATE,
                dealership VARCHAR(100)
            )
        """

        db_manager.execute_query(create_table_query)
        print(f"[OK] Created VIN log table: {table_name}")

        # Create indexes for performance
        db_manager.execute_query(f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_order_number
            ON {table_name}(order_number)
        """)

        db_manager.execute_query(f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_processed_date
            ON {table_name}(processed_date)
        """)

        db_manager.execute_query(f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_order_type
            ON {table_name}(order_type)
        """)

        print(f"[OK] Created indexes for {table_name}")

    print(f"\n=== COMPLETE ===")
    print(f"VIN log table ready for {dealership_name}")
    print(f"Name mapping: 'CDJR of Columbia' -> 'Joe Machens Chrysler Dodge Jeep Ram'")

    return True

if __name__ == "__main__":
    create_cdjr_columbia_vinlog()