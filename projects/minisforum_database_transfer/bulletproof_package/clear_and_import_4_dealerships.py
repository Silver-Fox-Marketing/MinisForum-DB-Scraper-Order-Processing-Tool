#!/usr/bin/env python3
"""
Clear and re-import VIN logs for the 4 specified dealerships:
- Bommarito Cadillac
- Frank Leta Honda
- Pappas Toyota
- Rusty Drewing Chevrolet Buick GMC
"""

import sys
import csv
from pathlib import Path
from datetime import datetime

current_file = Path(__file__).resolve()
sys.path.insert(0, str(current_file.parent / 'scripts'))

from database_connection import db_manager

# Mapping of dealership names to their VIN log table names and CSV files
DEALERSHIP_MAPPING = {
    'Bommarito Cadillac': {
        'table': 'bommarito_cadillac_vin_log',
        'file': 'BOMM_CADILLAC_VINLOG - LOG.csv',
        'name': 'Bommarito Cadillac'
    },
    'Frank Leta Honda': {
        'table': 'frank_leta_honda_vin_log', 
        'file': 'FRANKLETA_HONDA_VINLOG - LOG.csv',
        'name': 'Frank Leta Honda'
    },
    'Pappas Toyota': {
        'table': 'pappas_toyota_vin_log',
        'file': 'PAPPAS_TOYOTA_VINLOG - LOG.csv',
        'name': 'Pappas Toyota'
    },
    'Rusty Drewing Chevrolet Buick GMC': {
        'table': 'rusty_drewing_chevrolet_buick_gmc_vin_log',
        'file': 'RDCHEVY_VINLOG - LOG.csv',
        'name': 'Rusty Drewing Chevrolet Buick GMC'
    }
}

def clear_vinlog_table(table_name, dealership_name):
    """Clear existing VIN log table for a dealership"""
    try:
        # Get count before clearing
        count_query = f"SELECT COUNT(*) as count FROM {table_name}"
        count_result = db_manager.execute_query(count_query)
        before_count = count_result[0]['count'] if count_result else 0
        
        # Clear the table
        clear_query = f"DELETE FROM {table_name}"
        db_manager.execute_query(clear_query)
        
        print(f"[OK] Cleared {before_count} records from {table_name} ({dealership_name})")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to clear {table_name}: {e}")
        return False

def import_vinlog_file(csv_file_path, table_name, dealership_name):
    """Import VIN log from CSV file with proper order number formatting"""
    try:
        imported_count = 0
        current_order = None
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            header = next(reader)  # Skip header row
            
            for row in reader:
                if len(row) < 2:
                    continue
                    
                # First column is ORDER (may be empty if continuing from previous)
                # Second column is VIN
                order_number = row[0].strip() if row[0] else current_order
                vin = row[1].strip() if len(row) > 1 else ''
                
                # Update current order if we have a new one
                if row[0]:
                    current_order = order_number
                
                if not vin:
                    continue
                    
                # Check if VIN already exists (for tables without unique constraint)
                check_query = f"SELECT vin FROM {table_name} WHERE vin = %s"
                existing = db_manager.execute_query(check_query, [vin])
                
                if existing:
                    # Update existing record - use standard structure
                    update_query = f"""
                        UPDATE {table_name}
                        SET order_number = %s, created_at = %s
                        WHERE vin = %s
                    """
                    params = [order_number, datetime.now(), vin]
                    db_manager.execute_query(update_query, params)
                else:
                    # Insert new record with standard structure
                    insert_query = f"""
                        INSERT INTO {table_name} 
                        (vin, order_number, created_at)
                        VALUES (%s, %s, %s)
                    """
                    params = [vin, order_number, datetime.now()]
                    db_manager.execute_query(insert_query, params)
                imported_count += 1
        
        print(f"[OK] Imported {imported_count} VINs into {table_name} ({dealership_name})")
        return imported_count
        
    except Exception as e:
        print(f"[ERROR] Failed to import {csv_file_path}: {e}")
        import traceback
        traceback.print_exc()
        return 0

def main():
    """Main function to clear and import all VIN logs"""
    print("=== CLEARING AND IMPORTING VIN LOGS FOR 4 DEALERSHIPS ===")
    print(f"Starting at: {datetime.now()}")
    
    vinlog_dir = Path(r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\Vinlogs")
    
    if not vinlog_dir.exists():
        print(f"[ERROR] Vinlog directory not found: {vinlog_dir}")
        return
    
    total_cleared = 0
    total_imported = 0
    
    for dealership, config in DEALERSHIP_MAPPING.items():
        print(f"\n--- Processing {dealership} ---")
        
        # Clear existing data
        if clear_vinlog_table(config['table'], config['name']):
            total_cleared += 1
        
        # Import new data
        csv_path = vinlog_dir / config['file']
        if csv_path.exists():
            count = import_vinlog_file(csv_path, config['table'], config['name'])
            if count > 0:
                total_imported += 1
        else:
            print(f"[WARNING] CSV file not found: {csv_path}")
    
    # Verify the imports
    print("\n=== VERIFICATION ===")
    for dealership, config in DEALERSHIP_MAPPING.items():
        verify_query = f"""
            SELECT COUNT(*) as total_vins,
                   COUNT(DISTINCT order_number) as total_orders,
                   MIN(created_at) as import_time
            FROM {config['table']}
        """
        
        result = db_manager.execute_query(verify_query)
        if result and result[0]['total_vins'] > 0:
            r = result[0]
            print(f"{dealership}: {r['total_vins']} VINs, {r['total_orders']} orders")
        else:
            print(f"{dealership}: No data found")
    
    print(f"\n=== SUMMARY ===")
    print(f"Tables cleared: {total_cleared}/4")
    print(f"Tables imported: {total_imported}/4")
    print(f"Completed at: {datetime.now()}")

if __name__ == '__main__':
    main()