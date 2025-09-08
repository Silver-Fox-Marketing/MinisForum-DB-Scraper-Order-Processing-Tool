#!/usr/bin/env python3
"""
Fixed CSV Importer
==================
Properly integrates with ScraperImportManager for automatic normalization and CAO compatibility.
"""

import csv
import os
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List
from database_connection import db_manager
from scraper_import_manager import ScraperImportManager

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class FixedCSVImporter:
    """CSV importer that properly uses ScraperImportManager for import tracking and normalization"""
    
    def __init__(self):
        self.import_manager = ScraperImportManager()
        self.import_stats = {
            'total_dealerships': 0,
            'total_vehicles': 0,
            'successful_imports': 0,
            'failed_imports': 0,
            'dealership_results': {}
        }
    
    def import_csv(self, file_path: str) -> Dict:
        """Import CSV file using proper ScraperImportManager workflow"""
        logger.info(f"Starting CSV import: {file_path}")
        
        try:
            # Read CSV
            df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
            logger.info(f"Loaded {len(df)} vehicles from CSV")
            
            # Group by dealership
            dealership_groups = df.groupby('dealer_name')
            self.import_stats['total_dealerships'] = len(dealership_groups)
            
            for dealership_name, group_df in dealership_groups:
                logger.info(f"Processing {len(group_df)} vehicles for {dealership_name}")
                
                try:
                    # Step 1: Create proper scraper import (archives previous, creates new active one)
                    import_id = self.import_manager.create_new_import(dealership_name, len(group_df))
                    logger.info(f"Created import_id {import_id} for {dealership_name}")
                    
                    # Step 2: Insert raw vehicle data with proper import_id
                    inserted_count = self._insert_raw_vehicles(group_df, dealership_name, import_id)
                    
                    # Step 3: Finalize import (triggers automatic normalization)
                    self.import_manager.finalize_import(import_id)
                    logger.info(f"Finalized import {import_id} - normalization complete")
                    
                    # Track success
                    self.import_stats['successful_imports'] += 1
                    self.import_stats['total_vehicles'] += inserted_count
                    self.import_stats['dealership_results'][dealership_name] = {
                        'success': True,
                        'import_id': import_id,
                        'vehicles': inserted_count
                    }
                    
                except Exception as e:
                    logger.error(f"Failed to import {dealership_name}: {e}")
                    self.import_stats['failed_imports'] += 1
                    self.import_stats['dealership_results'][dealership_name] = {
                        'success': False,
                        'error': str(e)
                    }
            
            # Return summary
            return {
                'success': True,
                'message': f"Imported {self.import_stats['total_vehicles']} vehicles from {self.import_stats['successful_imports']} dealerships",
                'stats': self.import_stats
            }
            
        except Exception as e:
            logger.error(f"CSV import failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'stats': self.import_stats
            }
    
    def _insert_raw_vehicles(self, group_df: pd.DataFrame, dealership_name: str, import_id: int) -> int:
        """Insert raw vehicle data with proper import_id"""
        
        raw_data = []
        for idx, row in group_df.iterrows():
            try:
                # Extract and clean vehicle data
                vin = row.get('vin', '').upper().strip()
                if not vin:
                    continue
                
                # Prepare raw data tuple (NO normalized columns)
                raw_tuple = (
                    vin,
                    row.get('stock_number', ''),
                    row.get('condition', 'Vehicle'),  # type
                    int(row['year']) if row.get('year') and row['year'].isdigit() else None,
                    row.get('make', ''),
                    row.get('model', ''),
                    row.get('trim', ''),
                    row.get('exterior_color', ''),
                    row.get('condition', ''),  # status
                    float(row['price']) if row.get('price') and row['price'].replace('.', '').isdigit() else None,
                    '',  # body_style
                    row.get('fuel_type', ''),
                    float(row['msrp']) if row.get('msrp') and row['msrp'].replace('.', '').isdigit() else None,
                    None,  # date_in_stock
                    '',  # street_address
                    '',  # locality  
                    '',  # postal_code
                    '',  # region
                    '',  # country
                    dealership_name,  # location
                    row.get('url', ''),
                    import_id  # CRITICAL: Link to proper import_id
                )
                raw_data.append(raw_tuple)
                
            except Exception as e:
                logger.error(f"Error processing vehicle {row.get('vin', 'unknown')}: {e}")
                continue
        
        # Batch insert raw data
        if raw_data:
            raw_columns = [
                'vin', 'stock', 'type', 'year', 'make', 'model', 'trim',
                'ext_color', 'status', 'price', 'body_style', 'fuel_type', 
                'msrp', 'date_in_stock', 'street_address', 'locality',
                'postal_code', 'region', 'country', 'location', 'vehicle_url', 'import_id'
            ]
            
            rows_inserted = db_manager.execute_batch_insert(
                'raw_vehicle_data',
                raw_columns, 
                raw_data
            )
            
            logger.info(f"Inserted {rows_inserted} raw vehicles for {dealership_name}")
            return rows_inserted
        
        return 0

def main():
    """Test the fixed CSV importer"""
    importer = FixedCSVImporter()
    
    # Test with a sample CSV file
    csv_file = input("Enter CSV file path: ")
    if os.path.exists(csv_file):
        result = importer.import_csv(csv_file)
        print("\nIMPORT RESULT:")
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Message: {result['message']}")
            print("\nDealership Results:")
            for dealer, stats in result['stats']['dealership_results'].items():
                if stats['success']:
                    print(f"  ✅ {dealer}: {stats['vehicles']} vehicles (import_id: {stats['import_id']})")
                else:
                    print(f"  ❌ {dealer}: {stats['error']}")
        else:
            print(f"Error: {result['error']}")
    else:
        print("File not found!")

if __name__ == "__main__":
    main()