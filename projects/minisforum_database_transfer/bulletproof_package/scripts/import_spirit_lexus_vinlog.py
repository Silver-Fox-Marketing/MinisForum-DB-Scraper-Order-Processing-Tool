#!/usr/bin/env python3
"""
Import Spirit Lexus VIN Log with Order Grouping
Processes CSV in grouped format and imports to database with proper order associations
"""

import csv
import sys
from datetime import datetime
from database_connection import db_manager

def parse_grouped_vinlog(file_path):
    """
    Parse the Spirit Lexus VIN log CSV file with order grouping format
    Returns list of (order_number, vin, order_date) tuples
    """
    records = []
    current_order = None
    
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        
        # Skip header row
        next(reader, None)
        
        for row in reader:
            if not row:  # Empty row
                continue
                
            order_col = row[0].strip() if row[0] else ""
            vin_col = row[1].strip() if len(row) > 1 and row[1] else ""
            
            # Skip completely empty rows
            if not order_col and not vin_col:
                continue
            
            # Check if this is a new order (has order number)
            if order_col and order_col != "":
                # Skip baseline and date entries that aren't order numbers
                if order_col.upper().startswith("BASELINE") or "/" in order_col:
                    continue
                    
                try:
                    # Verify it's a numeric order number
                    int(order_col)
                    current_order = order_col
                    
                    # If there's also a VIN in this row, add it
                    if vin_col:
                        records.append((current_order, vin_col, '2025-08-25'))
                        
                except ValueError:
                    # Not a numeric order, skip
                    continue
            
            # If this is just a VIN (no order number) and we have a current order
            elif vin_col and current_order:
                records.append((current_order, vin_col, '2025-08-25'))
    
    return records

def import_vinlog_records(records):
    """
    Import the parsed VIN log records into the database
    """
    dealership_name = 'Spirit Lexus'
    table_name = f'{dealership_name.lower().replace(" ", "_").replace(".", "")}_vin_log'
    
    print(f"Importing {len(records)} records into {table_name}...")
    
    success_count = 0
    error_count = 0
    
    for order_number, vin, order_date in records:
        try:
            # Insert record into dealership-specific VIN log table
            insert_query = f"""
                INSERT INTO {table_name} (vin, processed_date, order_type, template_type, order_number)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            db_manager.execute_query(insert_query, [
                vin,
                order_date,
                'list',  # Spirit Lexus uses list orders
                'standard',
                order_number
            ])
            
            success_count += 1
            
            if success_count % 50 == 0:  # Progress update every 50 records
                print(f"  Imported {success_count} records...")
            
        except Exception as e:
            print(f"  Error importing VIN {vin} for order {order_number}: {e}")
            error_count += 1
    
    print(f"\nImport completed:")
    print(f"  Successfully imported: {success_count} records")
    if error_count > 0:
        print(f"  Errors: {error_count} records")
    
    return success_count, error_count

def main():
    file_path = r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\VIN LOGS\SPIRIT_LEXUS_VINLOG - LOG.csv"
    
    print("Processing Spirit Lexus VIN Log...")
    print(f"Reading from: {file_path}")
    
    try:
        # Parse the VIN log data
        records = parse_grouped_vinlog(file_path)
        
        if not records:
            print("ERROR: No valid records found in the file")
            return 1
        
        print(f"Parsed {len(records)} VIN records with order associations")
        
        # Show sample of what will be imported
        print("\nSample records to import:")
        for i, (order, vin, date) in enumerate(records[:5]):
            print(f"  Order {order}: {vin} (Date: {date})")
        if len(records) > 5:
            print(f"  ... and {len(records) - 5} more records")
        
        # Import the records
        print(f"\nImporting records into database...")
        success_count, error_count = import_vinlog_records(records)
        
        # Verify the import
        table_name = 'spirit_lexus_vin_log'
        count_query = f'SELECT COUNT(*) as count FROM {table_name}'
        result = db_manager.execute_query(count_query)
        total_in_db = result[0]["count"]
        
        print(f"\nImport verification:")
        print(f"  Records in database: {total_in_db}")
        print(f"  All VINs dated: 8/25/25")
        print(f"  Order associations: Maintained from CSV grouping")
        
        return 0
        
    except Exception as e:
        print(f"ERROR: Error processing VIN log: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())