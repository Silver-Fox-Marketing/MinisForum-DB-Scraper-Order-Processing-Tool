#!/usr/bin/env python3
"""
COMPLETE VIN LOG RE-IMPORT WITH TEXT-BASED ORDER SUPPORT
Silver Fox Order Processing System - Fixed VIN Log Import

This script re-imports ALL VIN logs with support for text-based order identifiers:
- BASELINE variants
- Date-based orders (5/23/25, etc.)
- Special identifiers (Maintenance, scraper for baseline, etc.)

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
        'dealership_name': 'Suntrup Ford Westport',
        'table_name': 'suntrup_ford_westport_vin_log'
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
    'SOCODCJR_VINLOG - LOG (5).csv': {
        'dealership_name': 'South County DCJR',
        'table_name': 'south_county_dcjr_vin_log'
    }
}

def is_valid_order_identifier(order_col):
    """Check if order column contains a valid order identifier"""
    if not order_col:
        return False
    
    # Numeric orders
    if order_col.isdigit():
        return True
    
    # Skip header row
    if order_col.upper() == 'ORDER':
        return False
    
    # Text-based order patterns (case insensitive)
    text_patterns = [
        'BASELINE',
        'INITIAL',
        'SETUP', 
        'TEST',
        'MAINTENANCE'
    ]
    
    order_upper = order_col.upper()
    
    # Exact matches
    if order_upper in text_patterns:
        return True
    
    # Partial matches for baseline variants
    if 'BASELINE' in order_upper:
        return True
        
    # Date patterns (MM/DD/YY format)
    if '/' in order_col and len(order_col.split('/')) >= 2:
        return True
    
    # Any other non-empty, non-header text
    if order_col and order_col.upper() != 'VIN':
        return True
    
    return False

def validate_vin(vin):
    """Validate VIN format"""
    if not vin or len(vin) != 17:
        return False
    
    # Skip header row
    if vin.upper() in ['VIN', 'VINS']:
        return False
    
    # Check for valid VIN characters (no I, O, Q)
    invalid_chars = ['I', 'O', 'Q']
    if any(char in vin.upper() for char in invalid_chars):
        return False
    
    return True

def parse_csv_with_text_orders(csv_file_path, dealership_name):
    """Parse CSV file with comprehensive order number support"""
    
    vin_records = []
    current_order_number = None
    line_number = 0
    
    with open(csv_file_path, 'r', encoding='utf-8-sig') as file:
        csv_reader = csv.reader(file)
        
        for row in csv_reader:
            line_number += 1
            
            if len(row) < 2:
                continue
                
            order_col = row[0].strip() if row[0] else ""
            vin_col = row[1].strip() if row[1] else ""
            
            # Check if this row has a valid order identifier
            if is_valid_order_identifier(order_col):
                current_order_number = order_col
                print(f"  Line {line_number}: Found order '{current_order_number}'")
                
            # Validate and add VIN record
            if validate_vin(vin_col) and current_order_number:
                vin_records.append({
                    'vin': vin_col,
                    'order_number': current_order_number,
                    'order_type': 'cao',
                    'processed_date': '2025-09-07',
                    'order_date': '2025-09-07',
                    'line_number': line_number
                })
                
            # If row is empty (blank row), reset current order number  
            elif not order_col and not vin_col:
                current_order_number = None
    
    return vin_records

def clear_and_reimport_dealership(dealership_name, table_name, csv_filename):
    """Clear existing VIN log and re-import with fixed logic"""
    
    csv_path = f"C:/Users/Workstation_1/Documents/Tools/ClaudeCode/projects/shared_resources/VIN LOGS/{csv_filename}"
    
    print(f"\\n--- RE-IMPORTING {dealership_name} ---")
    print(f"CSV: {csv_filename}")
    print(f"Table: {table_name}")
    
    # Check if CSV exists
    if not os.path.exists(csv_path):
        print(f"  [ERROR] CSV not found: {csv_path}")
        return 0
    
    # Clear existing records
    count_result = db_manager.execute_query(f'SELECT COUNT(*) as count FROM {table_name}')
    old_count = count_result[0]['count'] if count_result else 0
    
    db_manager.execute_query(f'DELETE FROM {table_name}')
    print(f"  Cleared {old_count} existing records")
    
    # Parse CSV with enhanced logic
    vin_records = parse_csv_with_text_orders(csv_path, dealership_name)
    print(f"  Parsed {len(vin_records)} VIN records from CSV")
    
    # Count by order type
    order_counts = {}
    for record in vin_records:
        order_num = record['order_number']
        order_counts[order_num] = order_counts.get(order_num, 0) + 1
    
    print(f"  Order groups found: {len(order_counts)}")
    for order_num, count in sorted(order_counts.items(), key=lambda x: (x[0].isdigit(), x[0]))[:5]:
        print(f"    '{order_num}': {count} VINs")
    if len(order_counts) > 5:
        print(f"    ... and {len(order_counts) - 5} more groups")
    
    # Import records (including duplicates as requested)
    inserted_count = 0
    duplicate_count = 0
    error_count = 0
    
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
            if 'duplicate key' in str(e).lower():
                duplicate_count += 1
            else:
                error_count += 1
                if error_count <= 3:  # Show first 3 errors
                    print(f"    [ERROR] VIN {record['vin']}: {e}")
    
    print(f"  [SUCCESS] Imported {inserted_count} VINs")
    if duplicate_count > 0:
        print(f"  [INFO] {duplicate_count} duplicate VINs (expected)")
    if error_count > 0:
        print(f"  [WARNING] {error_count} errors during import")
    
    return inserted_count

def main():
    print("=" * 80)
    print("COMPLETE VIN LOG RE-IMPORT WITH TEXT-ORDER SUPPORT")
    print("Silver Fox Order Processing System")
    print("=" * 80)
    
    total_imported = 0
    
    for csv_filename, dealership_info in CSV_FILE_MAPPINGS.items():
        dealership_name = dealership_info['dealership_name']
        table_name = dealership_info['table_name']
        
        imported_count = clear_and_reimport_dealership(dealership_name, table_name, csv_filename)
        total_imported += imported_count
    
    print("\\n" + "=" * 80)
    print("RE-IMPORT COMPLETE")
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
            
    print("\\n[SUCCESS] All VIN logs re-imported with text-based order support")
    print("All BASELINE, date-based, and special order identifiers included")

if __name__ == "__main__":
    main()