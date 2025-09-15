#!/usr/bin/env python3
"""
IMPORT OLD SYSTEM VIN LOGS
Silver Fox Order Processing System - VIN Log Import from Legacy System

This script imports VIN logs from the old system format where:
1. Order numbers are only on the first VIN of each group
2. Groups are separated by blank rows  
3. Each VIN needs the order number applied to it

CRITICAL: NO UNICODE CHARACTERS - Windows compatible output only
"""

import sys
import os
import csv
from datetime import date

# Set working directory and add scripts to path
os.chdir('C:/Users/Workstation_1/Documents/Tools/ClaudeCode/projects/minisforum_database_transfer/bulletproof_package')
sys.path.insert(0, './scripts')

from database_connection import db_manager

# Mapping of CSV files to dealership info
CSV_FILE_MAPPINGS = {
    'SUNTRUP_FORD_WESTPORT_VINLOG - LOG (4).csv': {
        'dealership_name': 'Suntrup Ford West',
        'table_name': 'suntrup_ford_west_vin_log'
    },
    'WEBER_VINLOG - LOG.csv': {
        'dealership_name': 'Weber Chevrolet', 
        'table_name': 'weber_chevrolet_vin_log'
    },
    'HW_KIA_VINLOG - LOG (1).csv': {
        'dealership_name': 'HW Kia',
        'table_name': 'hw_kia_vin_log'  
    },
    'GLENDALE_VINLOG - LOG (3).csv': {
        'dealership_name': 'Glendale CDJR',
        'table_name': 'glendale_cdjr_vin_log'
    },
    'HONDAofFRONTENAC_VINLOG - LOG.csv': {
        'dealership_name': 'Honda of Frontenac',
        'table_name': 'honda_of_frontenac_vin_log'
    },
    'PORSCHESTL_VINLOG - LOG (3).csv': {
        'dealership_name': 'Porsche St. Louis', 
        'table_name': 'porsche_st_louis_vin_log'
    },
    'SOCODCJR_VINLOG - LOG (5).csv': {
        'dealership_name': 'South County DCJR',
        'table_name': 'south_county_dcjr_vin_log'
    }
}

def parse_old_format_csv(csv_file_path):
    """Parse CSV file with order number grouping format"""
    
    vin_records = []
    current_order_number = None
    
    with open(csv_file_path, 'r', encoding='utf-8-sig') as file:
        csv_reader = csv.reader(file)
        
        # Skip header
        next(csv_reader, None)
        
        for row in csv_reader:
            if len(row) < 2:
                continue
                
            order_col = row[0].strip() if row[0] else ""
            vin_col = row[1].strip() if row[1] else ""
            
            # Check if this row has an order number (including BASELINE)
            if order_col and (order_col.isdigit() or order_col.upper() == 'BASELINE'):
                current_order_number = order_col
                
            # If we have a VIN and a current order number, add record
            if vin_col and len(vin_col) == 17 and current_order_number:
                vin_records.append({
                    'vin': vin_col,
                    'order_number': current_order_number,
                    'order_type': 'cao',
                    'processed_date': '2025-09-07',  # Set as 9/7 as requested
                    'order_date': '2025-09-07'
                })
                
            # If row is empty (blank row), reset current order number  
            elif not order_col and not vin_col:
                current_order_number = None
    
    return vin_records

def import_vin_records(dealership_name, table_name, vin_records):
    """Import VIN records into dealership table"""
    
    if not vin_records:
        print(f"  [WARNING] No VIN records found for {dealership_name}")
        return 0
    
    # Insert all records
    inserted_count = 0
    for record in vin_records:
        try:
            db_manager.execute_query(f"""
                INSERT INTO {table_name} 
                (vin, dealership, order_date, processed_date, order_type, order_number, template_type, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """, (
                record['vin'],
                dealership_name, 
                record['order_date'],
                record['processed_date'],
                record['order_type'],
                record['order_number'],
                'Standard'
            ))
            inserted_count += 1
            
        except Exception as e:
            print(f"    [ERROR] Failed to insert VIN {record['vin']}: {e}")
    
    return inserted_count

def main():
    print("=" * 80)
    print("IMPORTING OLD SYSTEM VIN LOGS")
    print("Silver Fox Order Processing System")  
    print("=" * 80)
    
    base_path = "C:/Users/Workstation_1/Documents/Tools/ClaudeCode/projects/shared_resources/VIN LOGS"
    
    total_imported = 0
    
    for csv_filename, dealership_info in CSV_FILE_MAPPINGS.items():
        dealership_name = dealership_info['dealership_name']
        table_name = dealership_info['table_name']
        csv_path = f"{base_path}/{csv_filename}"
        
        print(f"\\n--- IMPORTING {dealership_name} ---")
        print(f"CSV File: {csv_filename}")
        print(f"Target Table: {table_name}")
        
        # Check if CSV file exists
        if not os.path.exists(csv_path):
            print(f"  [ERROR] CSV file not found: {csv_path}")
            continue
            
        try:
            # Parse the CSV file
            vin_records = parse_old_format_csv(csv_path)
            print(f"  Parsed {len(vin_records)} VIN records from CSV")
            
            # Import into database
            imported_count = import_vin_records(dealership_name, table_name, vin_records)
            print(f"  [SUCCESS] Imported {imported_count} VIN records")
            
            total_imported += imported_count
            
            # Show sample of imported data
            if imported_count > 0:
                sample = vin_records[:3] 
                print(f"  Sample records:")
                for record in sample:
                    print(f"    Order {record['order_number']}: {record['vin']}")
                    
        except Exception as e:
            print(f"  [ERROR] Failed to import {dealership_name}: {e}")
    
    print("\\n" + "=" * 80)
    print("VIN LOG IMPORT COMPLETE")
    print("=" * 80)
    print(f"Total VIN records imported: {total_imported}")
    
    # Final verification
    print("\\nFINAL VERIFICATION:")
    for csv_filename, dealership_info in CSV_FILE_MAPPINGS.items():
        dealership_name = dealership_info['dealership_name']
        table_name = dealership_info['table_name']
        
        try:
            count_result = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
            count = count_result[0]['count'] if count_result else 0
            print(f"  {dealership_name}: {count} total records")
            
        except Exception as e:
            print(f"  {dealership_name}: ERROR - {e}")

if __name__ == "__main__":
    main()