#!/usr/bin/env python3
"""
Import Updated VIN Logs to Dealership-Specific Tables
Silver Fox Order Processing System v2.1

This script imports NEW VINs from updated VIN log Excel files into the 
corresponding dealership-specific VIN log database tables.
Only adds VINs that don't already exist in the database.
"""

import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add scripts directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from database_connection import db_manager

# VIN log file to dealership mapping - UPDATED TO USE _vin_log SUFFIX TABLES
VIN_LOG_MAPPING = {
    'AUDIRANCHOMIRAGE_VINLOG.xlsx': 'audi_ranch_mirage_vin_log',
    'AUFFENBERG_HYUNDAI_VINLOG.xlsx': 'auffenberg_hyundai_vin_log', 
    'BMW_WEST_STL_VINLOG.xlsx': 'bmw_of_west_st_louis_vin_log',
    'BOMM_CADILLAC_VINLOG.xlsx': 'bommarito_cadillac_vin_log',
    'BOMM_WCPO_VINLOG.xlsx': 'bommarito_west_county_vin_log',
    'COMOBMW_VINLOG.xlsx': 'columbia_bmw_vin_log',
    'COMO_HONDA_VINLOG.xlsx': 'columbia_honda_vin_log',
    'DAVESINCLAIRSTPETERS_VINLOG.xlsx': 'dave_sinclair_lincoln_st_peters_vin_log',
    'DSINCLAIRLINC_VINLOG.xlsx': 'dave_sinclair_lincoln_vin_log',
    'FRANKLETA_HONDA_VINLOG.xlsx': 'frank_leta_honda_vin_log',
    'GLENDALE_VINLOG.xlsx': 'glendale_chrysler_jeep_vin_log',
    'HONDAofFRONTENAC_VINLOG.xlsx': 'honda_of_frontenac_vin_log',
    'HW_KIA_VINLOG.xlsx': 'hw_kia_vin_log',
    'INDIGOAUTOGROUP_VINLOG.xlsx': 'indigo_auto_group_vin_log',
    'JAGUARRANCHOMIRAGE_VINLOG.xlsx': 'jaguar_ranch_mirage_vin_log',
    'JM NISSAN LOG.xlsx': 'joe_machens_nissan_vin_log',
    'JMCDJR_VINLOG.xlsx': 'joe_machens_cdjr_vin_log',
    'JMHYUNDAI_VINLOG.xlsx': 'joe_machens_hyundai_vin_log',
    'JM_TOYOTA_VINLOG.xlsx': 'joe_machens_toyota_vin_log',
    'KIACOMO_VINLOG.xlsx': 'kia_of_columbia_vin_log',
    'LANDROVERRANCHOMIRAGE_VINLOG.xlsx': 'land_rover_ranch_mirage_vin_log',
    'Mini_of_St_Louis_VINLOG.xlsx': 'mini_of_st_louis_vin_log',
    'PAPPAS_TOYOTA_VINLOG.xlsx': 'pappas_toyota_vin_log',
    'PORSCHESTL_VINLOG.xlsx': 'porsche_st_louis_vin_log',
    'PUNDMANN_VINLOG.xlsx': 'pundmann_ford_vin_log',
    'RDCADILLAC_VINLOG.xlsx': 'rusty_drewing_cadillac_vin_log',
    'RDCHEVY_VINLOG.xlsx': 'rusty_drewing_chevrolet_buick_gmc_vin_log',
    'SERRAHONDA_VINLOG.xlsx': 'serra_honda_ofallon_vin_log',
    'SOCODCJR_VINLOG.xlsx': 'south_county_autos_vin_log',
    'SPIRIT_LEXUS_VINLOG.xlsx': 'spirit_lexus_vin_log',
    'SUNTRUP_BGMC_VINLOG.xlsx': 'suntrup_buick_gmc_vin_log',
    'SUNTRUP_FORD_KIRKWOOD_VINLOG.xlsx': 'suntrup_ford_kirkwood_vin_log',
    'SUNTRUP_FORD_WESTPORT_VINLOG.xlsx': 'suntrup_ford_west_vin_log',
    'SUNTRUP_HYUNDAI_VINLOG.xlsx': 'suntrup_hyundai_south_vin_log',
    'SUNTRUP_KIA_VINLOG.xlsx': 'suntrup_kia_south_vin_log',
    'TBRED_FORD_VINLOG.xlsx': 'thoroughbred_ford_vin_log',
    'TOMSTEHOUWER_VINLOG.xlsx': 'stehouwer_auto_vin_log',
    'TWINCITYTOYO_VINLOG.xlsx': 'twin_city_toyota_vin_log',
    'VOLVO_WC_VINLOG.xlsx': 'west_county_volvo_cars_vin_log',
    'WEBER_VINLOG.xlsx': 'weber_chevrolet_vin_log'
}

def create_table_if_not_exists(table_name):
    """Create VIN log table if it doesn't exist"""
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        vin VARCHAR(17) PRIMARY KEY,
        processed_date DATE NOT NULL DEFAULT CURRENT_DATE,
        order_type VARCHAR(20) DEFAULT 'BASELINE',
        template_type VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        db_manager.execute_query(create_sql)
        print(f"Table {table_name} created/verified")
        return True
    except Exception as e:
        print(f"Error creating table {table_name}: {e}")
        return False

def import_vin_log_file(file_path, table_name, replace_existing=True):
    """Import VINs from Excel file, optionally replacing existing data"""
    try:
        # Read Excel file
        print(f"\n=== Processing {file_path.name} ===")
        df = pd.read_excel(file_path)
        
        # Display basic info about the file
        print(f"Rows in Excel file: {len(df)}")
        print(f"Columns: {list(df.columns)}")
        
        if len(df) == 0:
            print("Warning: Empty Excel file, skipping...")
            return {'success': False, 'error': 'Empty file', 'imported': 0}
        
        # Create table if it doesn't exist
        if not create_table_if_not_exists(table_name):
            return {'success': False, 'error': 'Table creation failed', 'imported': 0}
        
        if replace_existing:
            # Clear existing data
            db_manager.execute_query(f"TRUNCATE TABLE {table_name}")
            print(f"Cleared existing data from {table_name}")
            existing_vins = set()
        else:
            # Get existing VINs from database
            existing_vins_result = db_manager.execute_query(f"SELECT DISTINCT vin FROM {table_name}")
            existing_vins = {row['vin'] for row in existing_vins_result} if existing_vins_result else set()
            print(f"Existing VINs in database: {len(existing_vins)}")
        
        # Try to identify VIN column (common variations)
        vin_column = None
        for col in df.columns:
            col_lower = str(col).lower()
            if 'vin' in col_lower or 'chassis' in col_lower:
                vin_column = col
                break
        
        if vin_column is None:
            # If no VIN column found, assume first column is VIN
            vin_column = df.columns[0]
            print(f"Warning: No VIN column found, using first column: {vin_column}")
        
        print(f"Using VIN column: {vin_column}")
        
        # Prepare data for insertion
        imported_count = 0
        skipped_count = 0
        failed_count = 0
        
        for index, row in df.iterrows():
            vin = str(row[vin_column]).strip().upper()
            
            # Validate VIN (should be 17 characters)
            if len(vin) != 17 or vin == 'NAN' or vin == '':
                failed_count += 1
                continue
            
            # Skip if VIN already exists
            if vin in existing_vins:
                skipped_count += 1
                continue
            
            try:
                # Insert VIN into dealership-specific table
                db_manager.execute_query(f"""
                    INSERT INTO {table_name} (vin, processed_date, order_type)
                    VALUES (%s, CURRENT_DATE, 'BASELINE')
                    ON CONFLICT (vin) DO NOTHING
                """, (vin,))
                
                imported_count += 1
                existing_vins.add(vin)  # Add to set to prevent duplicates in same run
                
            except Exception as e:
                print(f"Error inserting VIN {vin}: {e}")
                failed_count += 1
        
        print(f"Import complete - New VINs: {imported_count}, Already Existed: {skipped_count}, Failed: {failed_count}")
        
        # Verify the import
        count_result = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
        final_count = count_result[0]['count'] if count_result else 0
        print(f"Final record count in {table_name}: {final_count}")
        
        return {
            'success': True,
            'imported': imported_count,
            'skipped': skipped_count,
            'failed': failed_count,
            'final_count': final_count
        }
        
    except Exception as e:
        print(f"Error processing {file_path.name}: {e}")
        return {'success': False, 'error': str(e), 'imported': 0}

def main(replace_existing=True):
    if replace_existing:
        print("=== VIN LOG REPLACEMENT - REPLACING ALL EXISTING DATA ===")
    else:
        print("=== VIN LOG UPDATE - ADDING NEW VINS ONLY ===")
    print(f"Started: {datetime.now()}")
    
    # Path to VIN logs directory
    vin_logs_dir = Path(r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\VIN LOGS")
    
    if not vin_logs_dir.exists():
        print(f"Error: VIN logs directory not found: {vin_logs_dir}")
        return
    
    print(f"VIN logs directory: {vin_logs_dir}")
    
    # Process each VIN log file
    total_imported = 0
    total_skipped = 0
    total_failed = 0
    processed_files = 0
    
    for filename, table_name in VIN_LOG_MAPPING.items():
        file_path = vin_logs_dir / filename
        
        if not file_path.exists():
            print(f"Warning: File not found: {filename}")
            continue
        
        # Import the file (will create table if needed)
        result = import_vin_log_file(file_path, table_name, replace_existing=replace_existing)
        
        if result['success']:
            total_imported += result['imported']
            total_skipped += result.get('skipped', 0)
            total_failed += result['failed']
            processed_files += 1
        
    print("\n" + "="*60)
    print("=== IMPORT SUMMARY ===")
    print(f"Files processed: {processed_files}")
    print(f"NEW VINs imported: {total_imported}")
    print(f"Existing VINs skipped: {total_skipped}")
    print(f"Failed VINs: {total_failed}")
    print(f"Completed: {datetime.now()}")
    
    # Display final table counts
    print("\n=== FINAL TABLE COUNTS ===")
    for filename, table_name in VIN_LOG_MAPPING.items():
        try:
            count_result = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
            count = count_result[0]['count'] if count_result else 0
            
            # Get count of recently added VINs (today)
            recent_result = db_manager.execute_query(f"""
                SELECT COUNT(*) as count 
                FROM {table_name} 
                WHERE created_at::date = CURRENT_DATE
            """)
            recent_count = recent_result[0]['count'] if recent_result else 0
            
            print(f"{table_name}: {count} total VINs ({recent_count} added today)")
        except Exception as e:
            print(f"{table_name}: Error - {e}")

if __name__ == "__main__":
    # Set to True to replace all existing data, False to only add new VINs
    REPLACE_EXISTING = True
    main(replace_existing=REPLACE_EXISTING)