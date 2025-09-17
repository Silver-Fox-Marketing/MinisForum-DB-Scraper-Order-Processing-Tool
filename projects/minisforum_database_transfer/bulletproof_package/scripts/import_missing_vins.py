#!/usr/bin/env python3
"""
Import missing duplicate VIN entries from CSV to database
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database_connection import db_manager
import csv
from datetime import datetime

def main():
    print('=== IMPORTING ALL MISSING DUPLICATE VIN ENTRIES ===')

    # Read all CSV entries
    csv_path = 'C:/Users/Workstation_1/Downloads/AUFFENBERG_HYUNDAI_VINLOG - LOG (1).csv'
    csv_entries = []

    with open(csv_path, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            vin = row.get('VIN', '').strip()
            order = row.get('ORDER', '').strip()
            if vin and len(vin) > 5:
                order_type = 'historical'
                if order and order != 'BASELINE':
                    order_type = 'cao'

                csv_entries.append({
                    'vin': vin,
                    'order_number': order if order else 'HISTORICAL',
                    'order_type': order_type
                })

    print(f'Total CSV entries: {len(csv_entries)}')

    # Get existing entries from database
    existing_entries = db_manager.execute_query('''
        SELECT vin, COALESCE(order_number, '') as order_number
        FROM auffenberg_hyundai_vin_log
    ''')

    # Create set of existing combinations
    existing_combinations = set()
    for entry in existing_entries:
        combo = entry['vin'] + '|' + entry['order_number']
        existing_combinations.add(combo)

    print(f'Existing combinations: {len(existing_combinations)}')

    # Find missing entries
    missing_entries = []
    for csv_entry in csv_entries:
        combo = csv_entry['vin'] + '|' + csv_entry['order_number']
        if combo not in existing_combinations:
            missing_entries.append(csv_entry)

    print(f'Missing entries to import: {len(missing_entries)}')

    if missing_entries:
        print('\nSample missing entries:')
        for i, entry in enumerate(missing_entries[:5]):
            print(f'  {entry["vin"]} | Order: {entry["order_number"]}')

        # Import missing entries
        insert_data = []
        for entry in missing_entries:
            insert_data.append((
                entry['vin'],
                entry['order_number'],
                datetime.now().date(),
                entry['order_type'],
                'shortcut_pack',
                datetime.now(),
                datetime.now(),
                datetime.now().date(),
                'Auffenberg Hyundai'
            ))

        try:
            inserted = db_manager.execute_batch_insert(
                table='auffenberg_hyundai_vin_log',
                columns=['vin', 'order_number', 'processed_date', 'order_type',
                        'template_type', 'created_at', 'imported_at', 'order_date', 'dealership'],
                data=insert_data
            )
            print(f'Successfully imported {inserted} entries')

        except Exception as e:
            print(f'Import error: {e}')
            return False

    else:
        print('No missing entries found')

    # Final count verification
    final_count = db_manager.execute_query(
        'SELECT COUNT(*) as count FROM auffenberg_hyundai_vin_log',
        fetch='one'
    )['count']

    print(f'\n=== FINAL VERIFICATION ===')
    print(f'Final database count: {final_count}')
    print(f'CSV total entries: {len(csv_entries)}')
    print(f'Match: {"YES" if final_count == len(csv_entries) else "NO"}')

    if final_count == len(csv_entries):
        print('SUCCESS: All CSV entries including duplicates are now in the database!')
    else:
        difference = len(csv_entries) - final_count
        print(f'WARNING: Still missing {difference} entries')

    return final_count == len(csv_entries)

if __name__ == '__main__':
    main()