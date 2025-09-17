#!/usr/bin/env python3
"""
Import missing duplicate VIN entries from CSV to database - FIXED VERSION
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database_connection import db_manager
import csv
from datetime import datetime

def main():
    print('=== CORRECTLY IMPORTING MISSING VIN ENTRIES ===')

    # Read ALL entries from CSV exactly as they appear
    csv_path = 'C:/Users/Workstation_1/Downloads/AUFFENBERG_HYUNDAI_VINLOG - LOG (1).csv'
    csv_entries = []

    print('Reading CSV file...')
    with open(csv_path, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        line_num = 1
        for row in reader:
            line_num += 1
            vin = row.get('VIN', '').strip()
            order = row.get('ORDER', '').strip()

            # Only process rows with valid VINs
            if vin and len(vin) > 5:
                # Normalize order number
                order_normalized = order if order else 'HISTORICAL'

                csv_entries.append({
                    'vin': vin,
                    'order_number': order_normalized,
                    'line_number': line_num
                })

    print(f'CSV entries parsed: {len(csv_entries)}')

    # Get ALL existing entries from database with exact matching
    print('Querying existing database entries...')
    existing_entries = db_manager.execute_query('''
        SELECT vin, COALESCE(order_number, 'HISTORICAL') as order_number
        FROM auffenberg_hyundai_vin_log
    ''')

    # Create exact matching set
    existing_set = set()
    for entry in existing_entries:
        # Normalize the order number for comparison
        order_norm = entry['order_number'] if entry['order_number'] else 'HISTORICAL'
        key = f"{entry['vin']}@@{order_norm}"
        existing_set.add(key)

    print(f'Existing database entries: {len(existing_entries)}')

    # Find entries that are in CSV but NOT in database
    missing_entries = []
    for csv_entry in csv_entries:
        key = f"{csv_entry['vin']}@@{csv_entry['order_number']}"
        if key not in existing_set:
            missing_entries.append(csv_entry)

    print(f'Missing entries to import: {len(missing_entries)}')

    if missing_entries:
        print('\nFirst 10 missing entries:')
        for i, entry in enumerate(missing_entries[:10]):
            print(f'  {i+1}. {entry["vin"]} | Order: {entry["order_number"]} (CSV line {entry["line_number"]})')

        # Import the missing entries
        print(f'\nImporting {len(missing_entries)} missing entries...')

        insert_data = []
        for entry in missing_entries:
            insert_data.append((
                entry['vin'],
                entry['order_number'],
                datetime.now().date(),  # processed_date
                'historical',  # order_type
                'shortcut_pack',  # template_type
                datetime.now(),  # created_at
                datetime.now(),  # imported_at
                datetime.now().date(),  # order_date
                'Auffenberg Hyundai'  # dealership
            ))

        try:
            inserted = db_manager.execute_batch_insert(
                table='auffenberg_hyundai_vin_log',
                columns=['vin', 'order_number', 'processed_date', 'order_type',
                        'template_type', 'created_at', 'imported_at', 'order_date', 'dealership'],
                data=insert_data
            )
            print(f'Successfully imported {inserted} missing entries')

        except Exception as e:
            print(f'Import error: {e}')
            return False

    else:
        print('No missing entries found - all CSV data is already in database')

    # Final verification
    final_count = db_manager.execute_query(
        'SELECT COUNT(*) as count FROM auffenberg_hyundai_vin_log',
        fetch='one'
    )['count']

    print(f'\n=== FINAL VERIFICATION ===')
    print(f'Database entries: {final_count}')
    print(f'CSV entries: {len(csv_entries)}')

    if final_count == len(csv_entries):
        print('✓ SUCCESS: All CSV entries (including duplicates) are now in database!')
        return True
    else:
        difference = len(csv_entries) - final_count
        print(f'✗ WARNING: {difference} entries still missing')
        return False

if __name__ == '__main__':
    main()