#!/usr/bin/env python3
"""
Remove UNIQUE constraint from Suntrup Ford Westport VIN log table
This allows duplicate VINs to be imported on the same date for order history tracking
"""

import sys
from pathlib import Path
from psycopg2.extras import RealDictCursor

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from database_connection import DatabaseManager

def remove_unique_constraint():
    """Remove UNIQUE(vin, order_date) constraint from Suntrup Ford VIN log table"""

    db = DatabaseManager()

    try:
        with db.get_connection(cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                # First, find the actual table name
                print("Searching for Suntrup Ford VIN log table...")
                cur.execute("""
                    SELECT tablename
                    FROM pg_tables
                    WHERE tablename LIKE '%suntrup%ford%'
                    ORDER BY tablename
                """)

                tables = cur.fetchall()

                if tables:
                    print("\nFound Suntrup Ford tables:")
                    for table in tables:
                        print(f"  - {table['tablename']}")

                    # Try both possible table names
                    table_names = [
                        'suntrup_ford_westport_vin_log',
                        'suntrup_ford_west_vin_log',
                        'vin_log_suntrup_ford_west',
                        'vin_log_suntrup_ford_westport'
                    ]

                    for table_name in table_names:
                        try:
                            # Check if table exists
                            cur.execute("""
                                SELECT tablename
                                FROM pg_tables
                                WHERE tablename = %s
                            """, (table_name,))

                            table_check = cur.fetchall()
                            if not table_check:
                                continue

                            print(f"\nProcessing table: {table_name}")

                            # Find the constraint name
                            cur.execute("""
                                SELECT constraint_name, constraint_type
                                FROM information_schema.table_constraints
                                WHERE table_name = %s AND constraint_type = 'UNIQUE'
                            """, (table_name,))

                            constraints = cur.fetchall()

                            if constraints:
                                print(f"Found {len(constraints)} UNIQUE constraint(s):")
                                for constraint in constraints:
                                    constraint_name = constraint['constraint_name']
                                    print(f"  - {constraint_name}")

                                    # Drop the constraint
                                    drop_sql = f"ALTER TABLE {table_name} DROP CONSTRAINT {constraint_name}"
                                    print(f"\nExecuting: {drop_sql}")
                                    cur.execute(drop_sql)
                                    conn.commit()
                                    print(f"[OK] Removed constraint: {constraint_name}")
                            else:
                                print(f"  No UNIQUE constraints found on {table_name}")

                        except Exception as e:
                            print(f"  Error processing {table_name}: {e}")
                            conn.rollback()
                            continue

                else:
                    print("No Suntrup Ford tables found!")

        print("\n[COMPLETE] Constraint removal process finished")

    except Exception as e:
        print(f"[ERROR] Failed to remove constraints: {e}")
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("Suntrup Ford VIN Log - Remove UNIQUE Constraint")
    print("=" * 60)
    print("\nThis will allow duplicate VINs on the same date for order history")
    print("tracking purposes.\n")

    remove_unique_constraint()
