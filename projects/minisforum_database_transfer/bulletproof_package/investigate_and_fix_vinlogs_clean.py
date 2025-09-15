#!/usr/bin/env python3
"""
CRITICAL VIN LOG INVESTIGATION AND STANDARDIZATION SCRIPT
Silver Fox Order Processing System - VIN Log Table Audit and Repair

This script will:
1. Catalog all existing VIN log tables
2. Examine their schemas
3. Identify naming convention conflicts
4. Standardize all tables to single format
5. Migrate data from old tables to standardized tables
6. Drop duplicate tables

STANDARD FORMAT: dealership_name_vin_log
STANDARD SCHEMA:
- id (SERIAL PRIMARY KEY)
- vin (VARCHAR(17) NOT NULL)
- dealership_name (VARCHAR(255))
- order_date (DATE DEFAULT CURRENT_DATE) 
- order_type (VARCHAR(50))
- vehicle_type (VARCHAR(20))
- created_at (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
"""

import sys
import os

# Set working directory and add scripts to path
os.chdir('C:/Users/Workstation_1/Documents/Tools/ClaudeCode/projects/minisforum_database_transfer/bulletproof_package')
sys.path.insert(0, './scripts')

from database_connection import db_manager

def main():
 # db_manager is already imported and connected

 print("[CRITICAL] VIN LOG INVESTIGATION - SILVER FOX ORDER PROCESSING SYSTEM")
 print("=" * 80)
 
 # Step 1: Get all VIN log tables
 print("\nSTEP 1: CATALOGING ALL VIN LOG TABLES")
 tables = db_manager.execute_query("""
  SELECT table_name 
  FROM information_schema.tables 
  WHERE table_schema = 'public' 
  AND table_name LIKE '%vin_log%' 
  ORDER BY table_name
 """)
 
    old_convention = []  # vin_log_dealername
    new_convention = []  # dealername_vin_log
    other_patterns = []  # unexpected patterns

    for table in tables:
        table_name = table['table_name']
        if table_name.startswith('vin_log_'):
            old_convention.append(table_name)
        elif table_name.endswith('_vin_log'):
            new_convention.append(table_name)
        else:
            other_patterns.append(table_name)

 print(f"FOUND {len(tables)} VIN LOG TABLES:")
 print(f" OLD CONVENTION (vin_log_*): {len(old_convention)} tables")
 print(f" NEW CONVENTION (*_vin_log): {len(new_convention)} tables") 
 print(f" OTHER PATTERNS: {len(other_patterns)} tables")

 # Step 2: Examine table schemas and data counts
 print("\nSTEP 2: EXAMINING TABLE SCHEMAS AND DATA")
 
 all_tables = old_convention + new_convention + other_patterns
 table_info = {}
 
 for table_name in all_tables:
  print(f"\nAnalyzing: {table_name}")
  
  # Get column info
  columns = db_manager.execute_query(f"""
  SELECT column_name, data_type, is_nullable, column_default
  FROM information_schema.columns 
  WHERE table_name = '{table_name}' 
  ORDER BY ordinal_position
  """)
  
  # Get row count
  count_result = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
  row_count = count_result[0]['count'] if count_result else 0
  
  # Get sample data if exists
  sample_data = None
  if row_count > 0:
  sample_data = db_manager.execute_query(f"SELECT * FROM {table_name} LIMIT 3")
  
  table_info[table_name] = {
  'columns': columns,
  'row_count': row_count,
  'sample_data': sample_data,
  'convention': 'old' if table_name.startswith('vin_log_') else 'new' if table_name.endswith('_vin_log') else 'other'
  }
  
  print(f" Rows: {row_count}")
  print(f" Columns: {[col['column_name'] for col in columns]}")
 
 # Step 3: Identify conflicts and required actions
 print("\n STEP 3: IDENTIFYING CONFLICTS AND REQUIRED ACTIONS")
 
 # Group tables by dealership
 dealership_tables = {}
 
 for table_name in all_tables:
  # Extract dealership name from table name
  if table_name.startswith('vin_log_'):
  dealership_key = table_name[9:] # Remove 'vin_log_' prefix
  elif table_name.endswith('_vin_log'):
  dealership_key = table_name[:-8] # Remove '_vin_log' suffix
  else:
  dealership_key = table_name
  
  if dealership_key not in dealership_tables:
  dealership_tables[dealership_key] = []
  dealership_tables[dealership_key].append(table_name)
 
 conflicts = []
 for dealership_key, tables in dealership_tables.items():
  if len(tables) > 1:
  conflicts.append((dealership_key, tables))
 
 print(f"\n[ALERT] FOUND {len(conflicts)} DEALERSHIP CONFLICTS:")
 for dealership_key, table_list in conflicts:
  print(f" {dealership_key}:")
  for table in table_list:
  info = table_info[table]
  print(f" - {table} ({info['row_count']} rows, {info['convention']} convention)")
 
 # Step 4: Show column schema differences
 print("\n STEP 4: COLUMN SCHEMA ANALYSIS")
 
 all_columns = set()
 for table_name, info in table_info.items():
  for col in info['columns']:
  all_columns.add(col['column_name'])
 
 print(f" UNIQUE COLUMNS FOUND: {sorted(all_columns)}")
 
 # Check for critical columns
 critical_columns = ['vin', 'order_date', 'dealership_name', 'order_type']
 for col in critical_columns:
  tables_with_col = [name for name, info in table_info.items() 
     if col in [c['column_name'] for c in info['columns']]]
  print(f" '{col}' column: {len(tables_with_col)}/{len(all_tables)} tables")
 
 # Step 5: Generate standardization plan
 print("\n STEP 5: STANDARDIZATION PLAN")
 print(" TARGET SCHEMA:")
 print(" - Table naming: dealership_name_vin_log")
 print(" - Columns: id, vin, dealership_name, order_date, order_type, vehicle_type, created_at")
 
 # Create SQL commands to standardize
 sql_commands = []
 
 # For each dealership with conflicts, consolidate to new convention
 for dealership_key, table_list in conflicts:
  target_table = f"{dealership_key}_vin_log"
  
  print(f"\n CONSOLIDATION PLAN FOR {dealership_key}:")
  print(f" Target table: {target_table}")
  
  # Find which table has the most data
  primary_table = max(table_list, key=lambda t: table_info[t]['row_count'])
  other_tables = [t for t in table_list if t != primary_table]
  
  print(f" Primary source: {primary_table} ({table_info[primary_table]['row_count']} rows)")
  for other in other_tables:
  print(f" Merge from: {other} ({table_info[other]['row_count']} rows)")
  
  # Generate SQL for this consolidation
  if primary_table != target_table:
  sql_commands.append(f"-- Rename primary table to standard naming")
  sql_commands.append(f"ALTER TABLE {primary_table} RENAME TO {target_table};")
  
  for other_table in other_tables:
  if table_info[other_table]['row_count'] > 0:
   sql_commands.append(f"-- Merge data from {other_table}")
   # This would need specific column mapping based on actual schemas
   sql_commands.append(f"-- INSERT INTO {target_table} SELECT ... FROM {other_table};")
  sql_commands.append(f"DROP TABLE {other_table};")
 
 # Step 6: Show final recommendations
 print("\n STEP 6: FINAL RECOMMENDATIONS")
 print("[ALERT] CRITICAL ISSUES IDENTIFIED:")
 print(" 1. Multiple naming conventions causing data fragmentation")
 print(" 2. Column schema mismatches (order_date vs order_type)")
 print(" 3. Missing standard columns in some tables")
 print(" 4. Duplicate tables splitting dealership data")
 
 print(f"\n RECOMMENDED ACTIONS:")
 print(f" 1. Standardize ALL tables to: dealership_name_vin_log")
 print(f" 2. Ensure all tables have: order_date column (not just order_type)") 
 print(f" 3. Migrate all data to consolidated tables")
 print(f" 4. Drop duplicate/old convention tables")
 print(f" 5. Update application code to use single convention")
 
 # Output SQL for review
 if sql_commands:
  print(f"\n GENERATED SQL COMMANDS:")
  print("-- WARNING: Review carefully before executing!")
  for cmd in sql_commands[:10]: # Show first 10 commands
  print(cmd)
  if len(sql_commands) > 10:
  print(f"... and {len(sql_commands)-10} more commands")
 
 print(f"\n INVESTIGATION COMPLETE - {len(all_tables)} tables analyzed")
 print("[ALERT] MANUAL REVIEW REQUIRED BEFORE PROCEEDING WITH FIXES")

if __name__ == "__main__":
 main()