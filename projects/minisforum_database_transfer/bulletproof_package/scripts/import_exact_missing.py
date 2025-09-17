#!/usr/bin/env python3
"""
Import exact missing VIN+order combinations from CSV
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database_connection import db_manager
import csv
from datetime import datetime

def main():
    print('=== IMPORTING EXACT MISSING VIN+ORDER COMBINATIONS ===')

    # Read ALL CSV entries exactly as they appear
    csv_path = 'C:/Users/Workstation_1/Downloads/AUFFENBERG_HYUNDAI_VINLOG - LOG (1).csv'
    csv_entries = []

    with open(csv_path, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            vin = row.get('VIN', '').strip()
            order = row.get('ORDER', '').strip()

            if vin and len(vin) > 5:  # Valid VINs only
                # Keep order exactly as in CSV - empty becomes 'HISTORICAL'
                order_value = order if order else 'HISTORICAL'

                csv_entries.append({
                    'vin': vin,
                    'order_number': order_value
                })

    print(f'Total CSV entries: {len(csv_entries)}')

    # Get existing database entries
    db_entries = db_manager.execute_query('''
        SELECT vin, COALESCE(order_number, 'HISTORICAL') as order_number
        FROM auffenberg_hyundai_vin_log
    ''')

    # Create set of existing VIN+order combinations
    existing_combinations = set()
    for entry in db_entries:
        # Use exact matching
        combination = (entry['vin'], entry['order_number'])
        existing_combinations.add(combination)

    print(f'Existing database combinations: {len(existing_combinations)}')

    # Find missing combinations
    missing_entries = []
    for csv_entry in csv_entries:
        combination = (csv_entry['vin'], csv_entry['order_number'])
        if combination not in existing_combinations:
            missing_entries.append(csv_entry)

    print(f'Missing combinations to import: {len(missing_entries)}')

    if missing_entries:
        print('\\nSample missing combinations:')
        for i, entry in enumerate(missing_entries[:10]):
            print(f'  {entry["vin"]} + {entry["order_number"]}')

        # Import missing combinations
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
            print(f'Successfully imported {inserted} missing combinations')

        except Exception as e:
            print(f'Import error: {e}')
            return False

    # Final verification
    final_count = db_manager.execute_query(
        'SELECT COUNT(*) as count FROM auffenberg_hyundai_vin_log',
        fetch='one'
    )['count']

    print(f'\\n=== FINAL VERIFICATION ===')
    print(f'Database entries: {final_count}')
    print(f'CSV entries: {len(csv_entries)}')

    if final_count == len(csv_entries):
        print('SUCCESS: Database now matches CSV exactly!')

        # Test CAO processing impact
        print('\\n=== TESTING CAO PROCESSING IMPACT ===')
        print('Now testing Auffenberg Hyundai CAO order...')

        return True
    else:
        print(f'MISMATCH: Database has {final_count}, CSV has {len(csv_entries)}')
        return False

if __name__ == '__main__':
    main()