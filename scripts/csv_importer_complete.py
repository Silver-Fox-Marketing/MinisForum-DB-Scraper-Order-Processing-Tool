"""
CSV import script for complete_data.csv from Silver Fox scrapers
Handles the unified CSV containing all dealership data
"""
import csv
import os
import logging
import json
from datetime import datetime, date
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import pandas as pd
from database_connection import db_manager
from database_config import (
    config, CONDITION_MAPPING, CSV_COLUMNS, 
    REQUIRED_COLUMNS, NUMERIC_COLUMNS, DATE_COLUMNS
)

logger = logging.getLogger(__name__)

class CompleteCSVImporter:
    """Handles complete_data.csv import with validation and normalization"""
    
    def __init__(self, db_manager_instance=None):
        self.db = db_manager_instance or db_manager
        self.import_stats = {
            'total_rows': 0,
            'imported_rows': 0,
            'skipped_rows': 0,
            'dealerships': {},
            'errors': []
        }
        self.dealership_configs = {}
        self.load_dealership_configs()
    
    def load_dealership_configs(self):
        """Load dealership configurations from database"""
        try:
            configs = self.db.execute_query(
                "SELECT name, filtering_rules, output_rules, qr_output_path, is_active FROM dealership_configs WHERE is_active = true"
            )
            
            for config in configs:
                # Handle both string and dict JSON data from PostgreSQL
                filtering_rules = config['filtering_rules']
                if isinstance(filtering_rules, str):
                    filtering_rules = json.loads(filtering_rules) if filtering_rules else {}
                elif not isinstance(filtering_rules, dict):
                    filtering_rules = {}
                
                output_rules = config['output_rules']
                if isinstance(output_rules, str):
                    output_rules = json.loads(output_rules) if output_rules else {}
                elif not isinstance(output_rules, dict):
                    output_rules = {}
                
                self.dealership_configs[config['name']] = {
                    'filtering_rules': filtering_rules,
                    'output_rules': output_rules,
                    'qr_output_path': config['qr_output_path'],
                    'is_active': config['is_active']
                }
            
            logger.info(f"Loaded configurations for {len(self.dealership_configs)} dealerships")
            
        except Exception as e:
            logger.warning(f"Could not load dealership configs: {e}")
            self.dealership_configs = {}
    
    def should_include_vehicle(self, row: Dict, dealership_name: str) -> Tuple[bool, Optional[str]]:
        """Check if vehicle should be included based on dealership config"""
        config = self.dealership_configs.get(dealership_name, {})
        filtering_rules = config.get('filtering_rules', {})
        
        # Check excluded conditions
        exclude_conditions = filtering_rules.get('exclude_conditions', [])
        vehicle_condition = self.normalize_condition(row.get('condition', ''))
        if vehicle_condition in exclude_conditions:
            return False, f"Excluded condition: {vehicle_condition}"
        
        # Check stock requirement
        if filtering_rules.get('require_stock', False):
            stock = str(row.get('stock_number', '')).strip()
            if not stock:
                return False, "Missing required stock number"
        
        # Check price range
        try:
            price = self.clean_numeric(row.get('price'))
            if price is not None:
                min_price = filtering_rules.get('min_price', 0)
                max_price = filtering_rules.get('max_price', float('inf'))
                if price < min_price or price > max_price:
                    return False, f"Price ${price} outside range ${min_price}-${max_price}"
        except:
            pass
        
        # Check year range
        try:
            year = int(row.get('year', 0))
            if year > 0:
                year_min = filtering_rules.get('year_min', 1980)
                year_max = filtering_rules.get('year_max', datetime.now().year + 2)
                if year < year_min or year > year_max:
                    return False, f"Year {year} outside range {year_min}-{year_max}"
        except:
            pass
        
        # Check excluded makes
        exclude_makes = filtering_rules.get('exclude_makes', [])
        if exclude_makes:
            make = str(row.get('make', '')).lower()
            if any(excluded.lower() in make for excluded in exclude_makes):
                return False, f"Excluded make: {make}"
        
        # Check include only makes (if specified)
        include_only_makes = filtering_rules.get('include_only_makes', [])
        if include_only_makes:
            make = str(row.get('make', '')).lower()
            if not any(included.lower() in make for included in include_only_makes):
                return False, f"Make not in allowed list: {make}"
        
        return True, None
    
    def normalize_condition(self, condition_value: str) -> str:
        """Normalize vehicle condition from scraper data"""
        if pd.isna(condition_value) or condition_value == '':
            return 'used'  # Default
        
        condition_str = str(condition_value).lower().strip()
        
        # Map conditions from complete_data.csv
        condition_map = {
            'new': 'new',
            'used': 'used',
            'certified': 'certified',
            'cpo': 'certified',
            'off-lot': 'offlot',
            'offlot': 'offlot'
        }
        
        return condition_map.get(condition_str, 'used')
    
    def validate_row(self, row: Dict) -> Tuple[bool, Optional[str]]:
        """Validate a single row of data"""
        # Check required fields for complete_data.csv format
        required_fields = ['vin', 'stock_number', 'dealer_name']
        
        for field in required_fields:
            if field not in row or pd.isna(row[field]) or str(row[field]).strip() == '':
                return False, f"Missing required field: {field}"
        
        # Validate VIN
        vin = str(row['vin']).strip().upper()
        if len(vin) != 17:
            return False, f"Invalid VIN length: {len(vin)} (should be 17)"
        
        # Skip mock data if needed (optional)
        if vin.startswith('MOCK'):
            # You can choose to skip mock data or import it
            pass  # Currently allowing mock data for testing
        
        # Validate year
        if 'year' in row and not pd.isna(row['year']):
            try:
                year = int(row['year'])
                current_year = datetime.now().year
                if year < 1980 or year > current_year + 2:
                    return False, f"Invalid year: {year}"
            except (ValueError, TypeError):
                return False, "Invalid year format"
        
        # Validate price
        if 'price' in row and not pd.isna(row['price']):
            try:
                price = self.clean_numeric(row['price'])
                if price is not None and (price < 0 or price > 500000):
                    return False, f"Invalid price: ${price}"
            except:
                pass
        
        return True, None
    
    def clean_numeric(self, value) -> Optional[float]:
        """Clean and convert numeric values"""
        if pd.isna(value) or value == '':
            return None
        
        # Remove common currency symbols and commas
        cleaned = str(value).replace('$', '').replace(',', '').strip()
        
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    def clean_date(self, value) -> Optional[datetime]:
        """Clean and convert date values"""
        if pd.isna(value) or value == '':
            return None
        
        # Handle ISO format from scrapers (YYYY-MM-DDTHH:MM:SS.ffffff)
        if 'T' in str(value):
            try:
                return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
            except:
                pass
        
        # Try other common formats
        date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']
        
        for fmt in date_formats:
            try:
                return datetime.strptime(str(value), fmt)
            except ValueError:
                continue
        
        return None
    
    def import_complete_csv(self, file_path: str) -> Dict:
        """Import the complete_data.csv file"""
        logger.info(f"Importing complete CSV file: {file_path}")
        
        try:
            # Read CSV with pandas
            df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
            
            # Verify we have the expected columns
            expected_columns = [
                'vin', 'stock_number', 'year', 'make', 'model', 'trim',
                'price', 'msrp', 'mileage', 'exterior_color', 'interior_color',
                'fuel_type', 'transmission', 'condition', 'url', 'dealer_name',
                'scraped_at'
            ]
            
            missing_columns = set(expected_columns) - set(df.columns)
            if missing_columns:
                logger.warning(f"Missing columns in CSV: {missing_columns}")
            
            # Process data by dealership for better tracking
            dealership_groups = df.groupby('dealer_name')
            
            for dealership_name, group_df in dealership_groups:
                self.import_stats['dealerships'][dealership_name] = {
                    'total': 0,
                    'imported': 0,
                    'skipped': 0
                }
                
                raw_data = []
                normalized_data = []
                vin_history_data = []
                
                for idx, row in group_df.iterrows():
                    self.import_stats['total_rows'] += 1
                    self.import_stats['dealerships'][dealership_name]['total'] += 1
                    
                    # Validate row
                    is_valid, error_msg = self.validate_row(row)
                    if not is_valid:
                        self.import_stats['skipped_rows'] += 1
                        self.import_stats['dealerships'][dealership_name]['skipped'] += 1
                        self.import_stats['errors'].append(
                            f"{dealership_name} Row {idx + 1}: {error_msg}"
                        )
                        continue
                    
                    # Check dealership-specific filtering rules
                    should_include, filter_msg = self.should_include_vehicle(row, dealership_name)
                    if not should_include:
                        self.import_stats['skipped_rows'] += 1
                        self.import_stats['dealerships'][dealership_name]['skipped'] += 1
                        self.import_stats['errors'].append(
                            f"{dealership_name} Row {idx + 1}: Filtered - {filter_msg}"
                        )
                        continue
                    
                    # Prepare raw data tuple (mapping complete_data.csv to database schema)
                    raw_tuple = (
                        str(row['vin']).strip().upper(),
                        str(row['stock_number']).strip(),
                        'Vehicle',  # type (generic)
                        int(row['year']) if row.get('year') and str(row['year']).isdigit() else None,
                        row.get('make', ''),
                        row.get('model', ''),
                        row.get('trim', ''),
                        row.get('exterior_color', ''),
                        row.get('condition', ''),
                        self.clean_numeric(row.get('price')),
                        '',  # body_style (not in complete_data.csv)
                        row.get('fuel_type', ''),
                        self.clean_numeric(row.get('msrp')),
                        None,  # date_in_stock (not in complete_data.csv)
                        '',  # street_address
                        '',  # locality
                        '',  # postal_code
                        '',  # region
                        '',  # country
                        dealership_name,  # location
                        row.get('url', '')
                    )
                    raw_data.append(raw_tuple)
                
                # Bulk insert raw data for this dealership
                if raw_data:
                    raw_columns = [
                        'vin', 'stock', 'type', 'year', 'make', 'model', 'trim',
                        'ext_color', 'status', 'price', 'body_style', 'fuel_type',
                        'msrp', 'date_in_stock', 'street_address', 'locality',
                        'postal_code', 'region', 'country', 'location', 'vehicle_url'
                    ]
                    
                    rows_inserted = self.db.execute_batch_insert(
                        'raw_vehicle_data', 
                        raw_columns, 
                        raw_data
                    )
                    
                    self.import_stats['imported_rows'] += rows_inserted
                    self.import_stats['dealerships'][dealership_name]['imported'] = rows_inserted
                    
                    # Get inserted records for normalization
                    today = date.today()
                    raw_records = self.db.execute_query(
                        """
                        SELECT id, vin, stock, type, year, make, model, trim, 
                               status, price, msrp, date_in_stock, location, vehicle_url
                        FROM raw_vehicle_data
                        WHERE location = %s AND import_date = %s
                        """,
                        (dealership_name, today)
                    )
                    
                    # Prepare normalized data
                    for record in raw_records:
                        condition = self.normalize_condition(record['status'])
                        
                        normalized_tuple = (
                            record['id'],  # raw_data_id
                            record['vin'],
                            record['stock'],
                            condition,
                            record['year'],
                            record['make'],
                            record['model'],
                            record['trim'],
                            record['status'],
                            record['price'],
                            record['msrp'],
                            record['date_in_stock'],
                            record['location'],
                            record['vehicle_url']
                        )
                        normalized_data.append(normalized_tuple)
                        
                        # VIN history entry
                        vin_history_data.append((
                            record['vin'],
                            record['location'],
                            today,
                            record['id']
                        ))
                    
                    # Upsert normalized data
                    if normalized_data:
                        norm_columns = [
                            'raw_data_id', 'vin', 'stock', 'vehicle_condition',
                            'year', 'make', 'model', 'trim', 'status', 'price',
                            'msrp', 'date_in_stock', 'location', 'vehicle_url'
                        ]
                        
                        self.db.upsert_data(
                            'normalized_vehicle_data',
                            norm_columns,
                            normalized_data,
                            conflict_columns=['vin', 'location'],
                            update_columns=['stock', 'vehicle_condition', 'price', 
                                          'status', 'last_seen_date', 'updated_at']
                        )
                    
                    # Insert VIN history
                    if vin_history_data:
                        self.db.execute_batch_insert(
                            'vin_history',
                            ['vin', 'dealership_name', 'scan_date', 'raw_data_id'],
                            vin_history_data
                        )
                
                logger.info(f"Imported {dealership_name}: "
                           f"{self.import_stats['dealerships'][dealership_name]['imported']} vehicles")
            
            # Update VIN scan counts
            self.update_vin_scan_counts()
            
            # Run maintenance
            logger.info("Running VACUUM ANALYZE on tables...")
            self.db.vacuum_analyze('raw_vehicle_data')
            self.db.vacuum_analyze('normalized_vehicle_data')
            
            return self.import_stats
            
        except Exception as e:
            logger.error(f"Error importing {file_path}: {e}")
            self.import_stats['errors'].append(f"File error: {str(e)}")
            raise
    
    def update_vin_scan_counts(self):
        """Update VIN scan counts in normalized data"""
        query = """
            UPDATE normalized_vehicle_data n
            SET vin_scan_count = (
                SELECT COUNT(DISTINCT scan_date)
                FROM vin_history v
                WHERE v.vin = n.vin AND v.dealership_name = n.location
            )
            WHERE last_seen_date = CURRENT_DATE
        """
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query)
            updated = cursor.rowcount
            logger.info(f"Updated scan counts for {updated} vehicles")
    
    def print_import_summary(self):
        """Print a detailed summary of the import"""
        print("\n" + "="*60)
        print("IMPORT SUMMARY")
        print("="*60)
        print(f"Total Rows Processed: {self.import_stats['total_rows']:,}")
        print(f"Successfully Imported: {self.import_stats['imported_rows']:,}")
        print(f"Skipped Rows: {self.import_stats['skipped_rows']:,}")
        
        if self.import_stats['dealerships']:
            print(f"\nDealerships Processed: {len(self.import_stats['dealerships'])}")
            print("-"*40)
            for dealer, stats in self.import_stats['dealerships'].items():
                print(f"{dealer:30} | Imported: {stats['imported']:5} | Skipped: {stats['skipped']:3}")
        
        if self.import_stats['errors']:
            print(f"\nErrors: {len(self.import_stats['errors'])}")
            for i, error in enumerate(self.import_stats['errors'][:10]):  # Show first 10
                print(f"  {i+1}. {error}")
            if len(self.import_stats['errors']) > 10:
                print(f"  ... and {len(self.import_stats['errors']) - 10} more errors")
        
        print("="*60)

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Import complete_data.csv to dealership database')
    parser.add_argument('csv_path', help='Path to complete_data.csv file')
    parser.add_argument('--skip-mock', action='store_true', 
                       help='Skip mock data (VINs starting with MOCK)')
    
    args = parser.parse_args()
    
    if not os.path.isfile(args.csv_path):
        print(f"Error: {args.csv_path} is not a valid file")
        return
    
    importer = CompleteCSVImporter()
    
    try:
        print(f"Importing {args.csv_path}...")
        stats = importer.import_complete_csv(args.csv_path)
        importer.print_import_summary()
        
    except Exception as e:
        print(f"Import failed: {e}")
        raise

if __name__ == "__main__":
    main()