#!/usr/bin/env python3
"""
Complete reimport of Thoroughbred Ford VIN log with ALL VINs including duplicates
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from projects.minisforum_database_transfer.bulletproof_package.scripts.database_connection import db_manager
import csv
from datetime import datetime, date

def main():
    print('=== THOROUGHBRED FORD VIN LOG COMPLETE REIMPORT ===')

    # CSV path
    csv_path = 'C:/Users/Workstation_1/Downloads/TBRED_FORD_VINLOG - LOG (2).csv'

    # Parse CSV with order number tracking
    vin_entries = []
    current_order = None

    print('Reading CSV file...')
    with open(csv_path, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        line_num = 1

        for row in reader:
            line_num += 1
            order = row.get('ORDER', '').strip()
            vin = row.get('VINS', '').strip()

            # Update current order if specified
            if order:
                current_order = order

            # Process VIN if valid
            if vin and len(vin) > 5:
                # Use current order or 'BASELINE' if no order set
                order_number = current_order if current_order else 'BASELINE'

                vin_entries.append({
                    'vin': vin,
                    'order_number': order_number,
                    'line_number': line_num
                })

    print(f'Parsed {len(vin_entries)} VIN entries from CSV')

    # Show order distribution
    order_counts = {}
    for entry in vin_entries:
        order = entry['order_number']
        order_counts[order] = order_counts.get(order, 0) + 1

    print('\\nOrder distribution:')
    for order, count in sorted(order_counts.items()):
        print(f'  Order {order}: {count} VINs')

    # Clear existing data
    print('\\nClearing existing Thoroughbred Ford VIN log...')
    deleted = db_manager.execute_query(
        'DELETE FROM thoroughbred_ford_vin_log',
        fetch='none'
    )
    print(f'Cleared existing entries')

    # Import all VINs
    print(f'\\nImporting {len(vin_entries)} VIN entries...')

    insert_data = []
    for entry in vin_entries:
        insert_data.append((
            entry['vin'],
            entry['order_number'],
            date(2025, 9, 15),  # processed_date
            'HISTORICAL',  # order_type
            'shortcut_pack',  # template_type
            datetime.now(),  # created_at
            datetime.now(),  # imported_at
            date(2025, 9, 15),  # order_date
            'Thoroughbred Ford'  # dealership
        ))

    try:
        inserted = db_manager.execute_batch_insert(
            table='thoroughbred_ford_vin_log',
            columns=['vin', 'order_number', 'processed_date', 'order_type',
                    'template_type', 'created_at', 'imported_at', 'order_date', 'dealership'],
            data=insert_data
        )
        print(f'Successfully imported {inserted} VIN entries')

    except Exception as e:
        print(f'Import error: {e}')
        return False

    # Verification
    final_count = db_manager.execute_query(
        'SELECT COUNT(*) as count FROM thoroughbred_ford_vin_log',
        fetch='one'
    )['count']

    unique_vins = db_manager.execute_query(
        'SELECT COUNT(DISTINCT vin) as count FROM thoroughbred_ford_vin_log',
        fetch='one'
    )['count']

    order_verification = db_manager.execute_query('''
        SELECT order_number, COUNT(*) as count
        FROM thoroughbred_ford_vin_log
        GROUP BY order_number
        ORDER BY order_number
    ''')

    print(f'\\n=== FINAL VERIFICATION ===')
    print(f'Total entries imported: {final_count}')
    print(f'CSV entries: {len(vin_entries)}')
    print(f'Unique VINs: {unique_vins}')

    print('\\nOrder verification:')
    for row in order_verification:
        print(f'  Order {row["order_number"]}: {row["count"]} VINs')

    if final_count == len(vin_entries):
        print('\\nSUCCESS: All CSV entries imported correctly!')
        return True
    else:
        print(f'\\nERROR: Expected {len(vin_entries)}, got {final_count}')
        return False

if __name__ == '__main__':
    main()