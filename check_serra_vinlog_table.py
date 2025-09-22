#!/usr/bin/env python3
"""
Check Serra Honda VIN log table name
"""

import sys

# Add the scripts directory to Python path
scripts_path = r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts'
sys.path.append(scripts_path)

from database_connection import DatabaseManager

def check_serra_vinlog_table():
    """Check Serra Honda VIN log table name"""
    print("=== Checking Serra Honda VIN Log Table ===")

    # Initialize database
    try:
        db = DatabaseManager()
        print("OK Database connection established")
    except Exception as e:
        print(f"ERROR Database connection failed: {e}")
        return False

    # Check for all VIN log tables
    print("\n--- All VIN Log Tables ---")
    try:
        tables_result = db.execute_query("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name LIKE '%vin_log%'
            ORDER BY table_name
        """)

        if tables_result:
            for table in tables_result:
                print(f"  {table['table_name']}")
        else:
            print("No VIN log tables found")

    except Exception as e:
        print(f"ERROR Failed to get tables: {e}")

    # Check specifically for Serra Honda variations
    print("\n--- Serra Honda Table Variations ---")
    serra_variations = [
        "serra_honda_o_fallon_vin_log",
        "serra_honda_ofallon_vin_log",
        "serra_honda_vin_log",
        "serrahondaofallon_vin_log"
    ]

    for table_name in serra_variations:
        try:
            result = db.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
            if result:
                print(f"  {table_name}: {result[0]['count']} records")
        except Exception as e:
            print(f"  {table_name}: Does not exist")

    return True

def main():
    """Main function"""
    check_serra_vinlog_table()
    return 0

if __name__ == "__main__":
    sys.exit(main())