#!/usr/bin/env python3
"""
Import Multiple Vehicle Datasets for Date Testing
=================================================

Imports the complete_data.csv file three additional times with different 
import timestamps to test the date search functionality.

Author: Silver Fox Assistant  
Created: 2025-07-29
"""

import pandas as pd
import sys
from pathlib import Path
from database_connection import db_manager
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_dataset_with_date(date_offset_days: int, dataset_label: str):
    """Import sample vehicle data with a specific date offset"""
    
    # Path to the sample CSV
    csv_path = Path(r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\Project reference for scraper\vehicle_scraper 18\output_data\2025-05-29\complete_data.csv")
    
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return False
    
    # Calculate the target date
    target_date = datetime.now() - timedelta(days=date_offset_days)
    
    logger.info(f"Loading {dataset_label} from: {csv_path}")
    logger.info(f"Target import date: {target_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Read CSV file
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} rows from CSV for {dataset_label}")
        
        # Column mapping from CSV to our database schema
        column_mapping = {
            'Vin': 'vin',
            'Stock': 'stock_number', 
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
        
        # Select and rename only the columns we want
        essential_columns = list(column_mapping.keys())
        df_filtered = df[essential_columns].copy()
        df_filtered.rename(columns=column_mapping, inplace=True)
        
        # Clean up the data
        logger.info(f"Cleaning up {dataset_label} data...")
        
        # Convert price to numeric, handling any string formatting
        df_filtered['price'] = pd.to_numeric(df_filtered['price'], errors='coerce')
        
        # Convert year to integer
        df_filtered['year'] = pd.to_numeric(df_filtered['year'], errors='coerce').astype('Int64')
        
        # Clean up vehicle_type (map to our standard values)
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
            logger.info(f"Removed {before_count - after_count} rows with missing critical data")
        
        # Modify VINs to make them unique for this dataset
        # Add suffix based on date offset to ensure uniqueness
        vin_suffix = f"_{date_offset_days:02d}"
        df_filtered['vin'] = df_filtered['vin'].astype(str) + vin_suffix
        df_filtered['stock_number'] = df_filtered['stock_number'].astype(str) + vin_suffix
        
        logger.info(f"Prepared {len(df_filtered)} vehicles for {dataset_label} import")
        
        # Import into database with specific timestamp
        logger.info(f"Starting database import for {dataset_label}...")
        
        success_count = 0
        error_count = 0
        
        for index, row in df_filtered.iterrows():
            try:
                # Insert into raw_vehicle_data table with specific timestamp
                db_manager.execute_query("""
                    INSERT INTO raw_vehicle_data 
                    (vin, stock, type, year, make, model, trim, ext_color, 
                     price, body_style, fuel_type, location, vehicle_url, status, import_timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    row['vin'],
                    row['stock_number'], 
                    row['vehicle_type'],
                    row['year'],
                    row['make'],
                    row['model'], 
                    row['trim'],
                    row['exterior_color'],
                    row['price'],
                    row['body_style'],
                    row['fuel_type'],
                    row['dealer_name'],  # location 
                    row['vehicle_url'],
                    'available',  # status
                    target_date  # specific timestamp
                ))
                
                success_count += 1
                
                if success_count % 200 == 0:
                    logger.info(f"Imported {success_count} vehicles for {dataset_label}...")
                    
            except Exception as e:
                error_count += 1
                if error_count <= 3:  # Show first 3 errors
                    logger.error(f"Error importing vehicle {row.get('vin', 'unknown')}: {e}")
        
        logger.info(f"{dataset_label} import completed: {success_count} successful, {error_count} errors")
        return success_count, error_count
        
    except Exception as e:
        logger.error(f"{dataset_label} import failed: {e}")
        return 0, 1

def import_multiple_datasets():
    """Import three additional datasets with different dates"""
    
    datasets = [
        (7, "7 Days Ago Dataset"),    # 1 week ago
        (15, "15 Days Ago Dataset"),  # 2 weeks ago  
        (30, "30 Days Ago Dataset")   # 1 month ago
    ]
    
    total_success = 0
    total_errors = 0
    
    print("\n" + "="*80)
    print(">> STARTING MULTIPLE DATASET IMPORT FOR DATE TESTING")
    print("="*80)
    
    for days_offset, label in datasets:
        print(f"\n[DATE] Importing {label}...")
        success, errors = import_dataset_with_date(days_offset, label)
        total_success += success
        total_errors += errors
        print(f"[OK] {label}: {success} vehicles imported, {errors} errors")
    
    # Get final database counts
    try:
        raw_count = db_manager.execute_query("SELECT COUNT(*) as count FROM raw_vehicle_data")
        total_vehicles = raw_count[0]['count'] if raw_count else 0
        
        # Get date range
        date_range = db_manager.execute_query("""
            SELECT 
                MIN(import_timestamp) as earliest,
                MAX(import_timestamp) as latest
            FROM raw_vehicle_data
        """)
        
        earliest = date_range[0]['earliest'] if date_range else 'Unknown'
        latest = date_range[0]['latest'] if date_range else 'Unknown'
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        total_vehicles = "Unknown"
        earliest = "Unknown"
        latest = "Unknown"
    
    print("\n" + "="*80)
    print(">> MULTIPLE DATASET IMPORT COMPLETE!")
    print("="*80)
    print(f"[STATS] Total vehicles in database: {total_vehicles}")
    print(f"[STATS] New vehicles added: {total_success}")
    print(f"[ERROR] Total import errors: {total_errors}")
    print(f"[DATES] Date range: {earliest} to {latest}")
    print(f"[READY] Ready to test Date Search functionality!")
    print("   - Try filtering by date ranges")
    print("   - Search across different time periods")
    print("   - Test dealer-specific date filtering")
    print("="*80)
    
    return True

if __name__ == "__main__":
    import_multiple_datasets()