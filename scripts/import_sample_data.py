#!/usr/bin/env python3
"""
Import Sample Vehicle Data
=========================

Imports the complete_data.csv from project reference with only the essential columns
we need for testing the search functionality.

Author: Silver Fox Assistant  
Created: 2025-07-29
"""

import pandas as pd
import sys
from pathlib import Path
from database_connection import db_manager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_sample_data():
    """Import sample vehicle data for testing search functionality"""
    
    # Path to the sample CSV
    csv_path = Path(r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\Project reference for scraper\vehicle_scraper 18\output_data\2025-05-29\complete_data.csv")
    
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return False
    
    logger.info(f"Loading sample data from: {csv_path}")
    
    try:
        # Read CSV file
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} rows from CSV")
        
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
        logger.info("Cleaning up data...")
        
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
        
        logger.info(f"Prepared {len(df_filtered)} vehicles for import")
        
        # Import into database
        logger.info("Starting database import...")
        
        success_count = 0
        error_count = 0
        
        for index, row in df_filtered.iterrows():
            try:
                # Insert into raw_vehicle_data table (using actual column names)
                db_manager.execute_query("""
                    INSERT INTO raw_vehicle_data 
                    (vin, stock, type, year, make, model, trim, ext_color, 
                     price, body_style, fuel_type, location, vehicle_url, status, import_timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
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
                ))
                
                success_count += 1
                
                if success_count % 100 == 0:
                    logger.info(f"Imported {success_count} vehicles...")
                    
            except Exception as e:
                error_count += 1
                if error_count <= 5:  # Show first 5 errors
                    logger.error(f"Error importing vehicle {row.get('vin', 'unknown')}: {e}")
        
        logger.info(f"Import completed: {success_count} successful, {error_count} errors")
        
        # Also create normalized data entries
        logger.info("Creating normalized data entries...")
        
        normalized_count = 0
        for index, row in df_filtered.iterrows():
            try:
                # Get the raw_data_id
                raw_data = db_manager.execute_query(
                    "SELECT id FROM raw_vehicle_data WHERE vin = %s ORDER BY import_timestamp DESC LIMIT 1",
                    (row['vin'],)
                )
                
                if raw_data:
                    raw_data_id = raw_data[0]['id']
                    
                    # Insert into normalized_vehicle_data (using actual column names)
                    db_manager.execute_query("""
                        INSERT INTO normalized_vehicle_data 
                        (raw_data_id, vin, stock, year, make, model, trim, 
                         price, location, vehicle_url, vehicle_condition, status, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """, (
                        raw_data_id,
                        row['vin'],
                        row['stock_number'],
                        row['year'],
                        row['make'], 
                        row['model'],
                        row['trim'],
                        row['price'],
                        row['dealer_name'],  # location
                        row['vehicle_url'],
                        'available',  # vehicle_condition
                        'available'   # status
                    ))
                    
                    normalized_count += 1
                    
            except Exception as e:
                logger.error(f"Error creating normalized data for {row.get('vin', 'unknown')}: {e}")
        
        logger.info(f"Created {normalized_count} normalized data entries")
        
        # Print summary
        print("\n" + "="*60)
        print("🎉 SAMPLE DATA IMPORT COMPLETE!")
        print("="*60)
        print(f"📊 Raw vehicles imported: {success_count}")
        print(f"📊 Normalized entries created: {normalized_count}")
        print(f"❌ Import errors: {error_count}")
        print(f"🔍 Ready to test Data Search functionality!")
        print("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"Import failed: {e}")
        return False

if __name__ == "__main__":
    import_sample_data()