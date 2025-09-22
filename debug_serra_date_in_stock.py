#!/usr/bin/env python3
"""
Debug Serra Honda date_in_stock field to see why seasoning filter isn't working
"""

import sys
import json
from datetime import datetime

# Add the scripts directory to Python path
scripts_path = r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts'
sys.path.append(scripts_path)

from database_connection import DatabaseManager

def debug_serra_date_fields():
    """Debug Serra Honda's date_in_stock and related fields"""
    print("=== Debugging Serra Honda Date Fields ===")

    # Initialize database
    try:
        db = DatabaseManager()
        print("OK Database connection established")
    except Exception as e:
        print(f"ERROR Database connection failed: {e}")
        return False

    # Check Serra Honda normalized data for date fields
    print("\n--- Serra Honda Normalized Data Sample ---")
    sample_query = """
        SELECT vin, make, model, vehicle_condition, date_in_stock, created_at, updated_at, price, stock
        FROM normalized_vehicle_data nvd
        WHERE nvd.location = 'Serra Honda O''Fallon'
        ORDER BY nvd.updated_at DESC
        LIMIT 10
    """

    sample_result = db.execute_query(sample_query)
    if sample_result:
        print(f"Found {len(sample_result)} sample records:")
        for i, record in enumerate(sample_result):
            print(f"  [{i+1}] VIN: {record['vin']}")
            print(f"      Condition: {record['vehicle_condition']}")
            print(f"      date_in_stock: {record['date_in_stock']} (type: {type(record['date_in_stock'])})")
            print(f"      created_at: {record['created_at']}")
            print(f"      updated_at: {record['updated_at']}")
            print(f"      price: {record['price']}")
            print(f"      stock: {record['stock']}")

            # Calculate days on lot if date_in_stock exists
            if record['date_in_stock']:
                if isinstance(record['date_in_stock'], str):
                    try:
                        stock_date = datetime.strptime(record['date_in_stock'], '%Y-%m-%d')
                        days_on_lot = (datetime.now() - stock_date).days
                        print(f"      Days on lot: {days_on_lot}")
                    except ValueError as e:
                        print(f"      ERROR parsing date: {e}")
                elif hasattr(record['date_in_stock'], 'days'):
                    days_on_lot = (datetime.now() - record['date_in_stock']).days
                    print(f"      Days on lot: {days_on_lot}")
            else:
                print(f"      Days on lot: NULL/MISSING")
            print()
    else:
        print("ERROR No Serra Honda records found")

    # Check how many records have date_in_stock populated
    print("\n--- Date Field Statistics ---")
    stats_query = """
        SELECT
            COUNT(*) as total_records,
            COUNT(date_in_stock) as records_with_date_in_stock,
            COUNT(*) - COUNT(date_in_stock) as records_missing_date_in_stock
        FROM normalized_vehicle_data nvd
        WHERE nvd.location = 'Serra Honda O''Fallon'
    """

    stats_result = db.execute_query(stats_query)
    if stats_result:
        stats = stats_result[0]
        print(f"Total Serra Honda records: {stats['total_records']}")
        print(f"Records WITH date_in_stock: {stats['records_with_date_in_stock']}")
        print(f"Records MISSING date_in_stock: {stats['records_missing_date_in_stock']}")

        percentage_with_date = (stats['records_with_date_in_stock'] / stats['total_records']) * 100 if stats['total_records'] > 0 else 0
        print(f"Percentage with date_in_stock: {percentage_with_date:.1f}%")

    # Check alternative date fields in case date_in_stock isn't populated
    print("\n--- Alternative Date Fields Check ---")
    alt_fields_query = """
        SELECT vin, date_in_stock, created_at, updated_at,
               EXTRACT(EPOCH FROM (NOW() - created_at))/86400 as days_since_created,
               EXTRACT(EPOCH FROM (NOW() - updated_at))/86400 as days_since_updated
        FROM normalized_vehicle_data nvd
        WHERE nvd.location = 'Serra Honda O''Fallon'
        ORDER BY nvd.updated_at DESC
        LIMIT 5
    """

    alt_result = db.execute_query(alt_fields_query)
    if alt_result:
        print("Alternative date calculations:")
        for record in alt_result:
            print(f"  VIN: {record['vin']}")
            print(f"    date_in_stock: {record['date_in_stock']}")
            print(f"    Days since created: {record['days_since_created']:.1f}")
            print(f"    Days since updated: {record['days_since_updated']:.1f}")
            print()

    # Check raw data to see if the issue is in normalization
    print("\n--- Raw Data Check ---")
    raw_query = """
        SELECT vin, make, model, date_added, date_in_stock, created_at
        FROM raw_vehicle_data rvd
        WHERE rvd.location = 'Serra Honda O''Fallon'
        ORDER BY rvd.created_at DESC
        LIMIT 5
    """

    raw_result = db.execute_query(raw_query)
    if raw_result:
        print("Raw data date fields:")
        for record in raw_result:
            print(f"  VIN: {record['vin']}")
            print(f"    Raw date_in_stock: {record.get('date_in_stock')}")
            print(f"    Raw date_added: {record.get('date_added')}")
            print(f"    Raw created_at: {record['created_at']}")
            print()
    else:
        print("No raw data found")

    return True

def main():
    """Main function"""
    success = debug_serra_date_fields()
    if success:
        print("\nDebug completed")
        return 0
    else:
        print("\nDebug failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())