#!/usr/bin/env python3
"""
Update Bommarito Cadillac VIN Log from Downloaded CSV
Processes VINs from column 2 only, assigns order number 66666 where missing,
and imports all VINs (including duplicates) with date 9/14 and type Historical.
"""

import csv
import sys
import os
import psycopg2
from datetime import datetime

# Database connection parameters (update these if needed)
DB_PARAMS = {
    'host': 'localhost',
    'database': 'minisforum_vehicle_data',
    'user': 'minisforum_user',
    'password': 'secure_password_2024'
}

def connect_to_database():
    """Connect to the PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        return conn
    except psycopg2.Error as e:
        print(f"ERROR Database connection failed: {e}")
        return None

def read_downloaded_csv(file_path):
    """Read the downloaded CSV and extract VINs from column 2"""
    vins_with_orders = []

    print(f"Reading downloaded CSV: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)

            for row_num, row in enumerate(csv_reader, 1):
                if row_num == 1:  # Skip header
                    continue

                if len(row) >= 2:  # Ensure we have at least 2 columns
                    order_number = row[0].strip() if row[0].strip() else None
                    vin = row[1].strip() if row[1].strip() else None

                    # Only process if VIN exists in column 2
                    if vin:
                        # Assign order number 66666 if missing
                        if not order_number:
                            order_number = "66666"

                        vins_with_orders.append({
                            'vin': vin,
                            'order_number': order_number,
                            'row': row_num
                        })
                        print(f"Row {row_num}: VIN={vin}, Order={order_number}")

    except FileNotFoundError:
        print(f"ERROR File not found: {file_path}")
        return []
    except Exception as e:
        print(f"ERROR Reading CSV: {e}")
        return []

    print(f"OK Extracted {len(vins_with_orders)} VINs from downloaded CSV")
    return vins_with_orders

def update_vin_log(conn, vins_data):
    """Update the Bommarito Cadillac VIN log table"""
    cursor = conn.cursor()

    # Process date: 9/14 (assuming 2025)
    process_date = '2025-09-14'
    order_type = 'Historical'

    success_count = 0
    error_count = 0

    print(f"Updating bommarito_cadillac_vin_log table...")
    print(f"Using date: {process_date}, order_type: {order_type}")

    for vin_data in vins_data:
        try:
            # Insert or update VIN record (using ON CONFLICT to handle duplicates)
            insert_query = """
            INSERT INTO bommarito_cadillac_vin_log
            (vin, order_number, processed_date, order_date, order_type, template_type, created_at, imported_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (vin) DO UPDATE SET
                order_number = EXCLUDED.order_number,
                processed_date = EXCLUDED.processed_date,
                order_date = EXCLUDED.order_date,
                order_type = EXCLUDED.order_type,
                imported_at = EXCLUDED.imported_at
            """

            cursor.execute(insert_query, (
                vin_data['vin'],
                vin_data['order_number'],
                process_date,
                process_date,
                order_type,
                'Historical Import',
                datetime.now(),
                datetime.now()
            ))

            success_count += 1
            print(f"OK Processed VIN: {vin_data['vin']} (Order: {vin_data['order_number']})")

        except psycopg2.Error as e:
            error_count += 1
            print(f"ERROR Processing VIN {vin_data['vin']}: {e}")

    # Commit all changes
    try:
        conn.commit()
        print(f"OK Database commit successful")
    except psycopg2.Error as e:
        print(f"ERROR Database commit failed: {e}")
        conn.rollback()
        return False

    print(f"SUMMARY: {success_count} VINs processed successfully, {error_count} errors")
    return True

def main():
    """Main function"""
    # File path to downloaded CSV
    csv_file_path = r"C:\Users\Workstation_1\Downloads\BOMM_CADILLAC_VINLOG - LOG (1).csv"

    print("=== Bommarito Cadillac VIN Log Update ===")
    print(f"Processing file: {csv_file_path}")

    # Check if file exists
    if not os.path.exists(csv_file_path):
        print(f"ERROR File not found: {csv_file_path}")
        return 1

    # Read VINs from CSV
    vins_data = read_downloaded_csv(csv_file_path)
    if not vins_data:
        print("ERROR No VINs found to process")
        return 1

    # Connect to database
    conn = connect_to_database()
    if not conn:
        print("ERROR Could not connect to database")
        return 1

    try:
        # Update VIN log
        success = update_vin_log(conn, vins_data)
        if success:
            print("SUCCESS VIN log update completed")
            return 0
        else:
            print("ERROR VIN log update failed")
            return 1

    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())