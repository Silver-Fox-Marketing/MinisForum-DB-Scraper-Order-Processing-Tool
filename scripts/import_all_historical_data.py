#!/usr/bin/env python3
"""
Import All Historical Vehicle Data
==================================

Imports all complete_data.csv files from the historical scraper sessions
to create a large realistic dataset for testing.

Author: Silver Fox Assistant  
Created: 2025-07-29
"""

import pandas as pd
import sys
from pathlib import Path
from database_connection import db_manager
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_historical_datasets():
    """Import all historical complete_data.csv files"""
    
    # Base path to all the historical data
    base_path = Path(r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\Project reference for scraper\vehicle_scraper 18\output_data")
    
    # Find all complete_data.csv files
    csv_files = []
    for date_folder in base_path.iterdir():
        if date_folder.is_dir():
            csv_path = date_folder / "complete_data.csv"
            if csv_path.exists():
                csv_files.append((date_folder.name, csv_path))
    
    # Sort by date
    csv_files.sort(key=lambda x: x[0])
    
    print("\n" + "="*80)
    print(">> IMPORTING ALL HISTORICAL VEHICLE DATA")
    print("="*80)
    print(f"Found {len(csv_files)} CSV files to import:")
    for date_str, path in csv_files:
        print(f"  - {date_str}")
    
    total_success = 0
    total_errors = 0
    total_files_processed = 0
    
    # Column mapping from CSV to our database schema
    column_mapping = {
        'Vin': 'vin',
        'Stock': 'stock', 
        'Type': 'vehicle_type',
        'Year': 'year',
        'Make': 'make',
        'Model': 'model',
        'Trim': 'trim',
        'Ext Color': 'exterior_color',
        'Price': 'price',
        'Body Style': 'body_style',
        'Fuel Type': 'fuel_type',
        'Location': 'dealer_name',
        'Vechile URL': 'vehicle_url'  # Note: typo in original CSV
    }
    
    for date_str, csv_path in csv_files:
        try:
            print(f"\n[IMPORT] Processing {date_str}...")
            
            # Parse the date from folder name
            import_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Read CSV file
            df = pd.read_csv(csv_path)
            print(f"  Loaded {len(df)} rows from {date_str}")
            
            # Select and rename only the columns we want
            essential_columns = list(column_mapping.keys())
            
            # Check if all required columns exist
            missing_columns = set(essential_columns) - set(df.columns)
            if missing_columns:
                print(f"  [SKIP] Missing columns in {date_str}: {missing_columns}")
                continue
                
            df_filtered = df[essential_columns].copy()
            df_filtered.rename(columns=column_mapping, inplace=True)
            
            # Clean up the data
            df_filtered['price'] = pd.to_numeric(df_filtered['price'], errors='coerce')
            df_filtered['year'] = pd.to_numeric(df_filtered['year'], errors='coerce').astype('Int64')
            
            # Clean up vehicle_type
            vehicle_type_mapping = {
                'Used': 'used',
                'New': 'new', 
                'Certified Pre-Owned': 'cpo',
                'Pre-Owned': 'used'
            }
            df_filtered['vehicle_type'] = df_filtered['vehicle_type'].map(vehicle_type_mapping).fillna('used')
            
            # Handle missing values
            df_filtered['trim'] = df_filtered['trim'].fillna('')
            df_filtered['exterior_color'] = df_filtered['exterior_color'].fillna('')
            df_filtered['body_style'] = df_filtered['body_style'].fillna('')
            df_filtered['fuel_type'] = df_filtered['fuel_type'].fillna('')
            
            # Remove rows with missing critical data
            before_count = len(df_filtered)
            df_filtered = df_filtered.dropna(subset=['vin', 'dealer_name', 'make', 'model'])
            after_count = len(df_filtered)
            
            if before_count != after_count:
                print(f"  Removed {before_count - after_count} rows with missing critical data")
            
            # Import into database
            success_count = 0
            error_count = 0
            
            for index, row in df_filtered.iterrows():
                try:
                    # Insert into raw_vehicle_data table
                    db_manager.execute_query("""
                        INSERT INTO raw_vehicle_data 
                        (vin, stock, type, year, make, model, trim, ext_color, 
                         price, body_style, fuel_type, location, vehicle_url, status, import_timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        row['vin'],
                        row['stock'], 
                        row['vehicle_type'],
                        row['year'],
                        row['make'],
                        row['model'], 
                        row['trim'],
                        row['exterior_color'],
                        row['price'],
                        row['body_style'],
                        row['fuel_type'],
                        row['dealer_name'],
                        row['vehicle_url'],
                        'available',
                        import_date  # Use the actual scrape date
                    ))
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    if error_count <= 3:  # Show first 3 errors per file
                        logger.error(f"Error importing vehicle from {date_str}: {e}")
            
            print(f"  [RESULT] {date_str}: {success_count} imported, {error_count} errors")
            total_success += success_count
            total_errors += error_count
            total_files_processed += 1
            
        except Exception as e:
            logger.error(f"Failed to process {date_str}: {e}")
            total_errors += 1
    
    # Get final database stats
    try:
        raw_count = db_manager.execute_query("SELECT COUNT(*) as count FROM raw_vehicle_data")
        total_vehicles = raw_count[0]['count'] if raw_count else 0
        
        # Get date range
        date_range = db_manager.execute_query("""
            SELECT 
                MIN(import_timestamp) as earliest,
                MAX(import_timestamp) as latest,
                COUNT(DISTINCT DATE(import_timestamp)) as unique_dates
            FROM raw_vehicle_data
        """)
        
        if date_range:
            earliest = date_range[0]['earliest']
            latest = date_range[0]['latest'] 
            unique_dates = date_range[0]['unique_dates']
        else:
            earliest = latest = unique_dates = "Unknown"
            
        # Get dealer distribution
        dealer_stats = db_manager.execute_query("""
            SELECT location, COUNT(*) as vehicle_count
            FROM raw_vehicle_data 
            GROUP BY location 
            ORDER BY vehicle_count DESC 
            LIMIT 10
        """)
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        total_vehicles = "Unknown"
        earliest = latest = unique_dates = "Unknown"
        dealer_stats = []
    
    print("\n" + "="*80)
    print(">> HISTORICAL DATA IMPORT COMPLETE!")
    print("="*80)
    print(f"[STATS] Files processed: {total_files_processed}")
    print(f"[STATS] Total vehicles in database: {total_vehicles}")
    print(f"[STATS] New vehicles added: {total_success}")
    print(f"[ERROR] Total import errors: {total_errors}")
    print(f"[DATES] Date range: {earliest} to {latest}")
    print(f"[DATES] Unique dates in database: {unique_dates}")
    
    if dealer_stats:
        print(f"\n[TOP DEALERS] Vehicle distribution:")
        for dealer in dealer_stats:
            print(f"  - {dealer['location']}: {dealer['vehicle_count']} vehicles")
    
    print(f"\n[READY] Enhanced dataset ready for comprehensive testing!")
    print("  - Much larger volume for pagination testing")
    print("  - Real historical date distribution")
    print("  - Multiple dealership data across months")
    print("  - Perfect for testing all search features")
    print("="*80)
    
    return True

if __name__ == "__main__":
    import_historical_datasets()