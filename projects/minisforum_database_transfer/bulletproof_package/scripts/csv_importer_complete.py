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
from scraper_data_normalizer import normalizer
from scraper_import_manager import ScraperImportManager

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
    
    def standardize_dealership_name(self, raw_name: str) -> str:
        """Standardize dealership names during CSV import to ensure consistency
        
        This function handles known dealership name variations to prevent
        data fragmentation and ensure CAO processing works correctly.
        """
        if not raw_name:
            return raw_name
            
        # Define dealership name standardization mappings
        # Maps CSV names to standard database names for consistency
        name_mappings = {
            'South County Dodge Chrysler Jeep RAM': 'South County DCJR',
            'South County Dodge Chrysler Jeep Ram': 'South County DCJR', 
            'South County Autos': 'South County DCJR',
            'Dave Sinclair Lincoln of St Louis': 'Dave Sinclair Lincoln',
            'Dave Sinclair Lincoln of South County': 'Dave Sinclair Lincoln South',
            'Dave Sinclair Lincoln of St Peters': 'Dave Sinclair Lincoln St. Peters',
            # 'HW Kia of West County': 'HW Kia',  # Let this import as-is, mapping handled in CAO processor
            'BMW of West St Louis': 'BMW of West St. Louis',  # Handle period difference
            'Glendale Chrysler Jeep Dodge Ram': 'Glendale CDJR',  # Map to shorter config name
            # Most other names should match exactly between CSV and configs
        }
        
        # Check for exact match first
        if raw_name in name_mappings:
            logger.info(f"DEALERSHIP NAME STANDARDIZATION: '{raw_name}' -> '{name_mappings[raw_name]}'")
            return name_mappings[raw_name]
        
        # Check for partial matches (case-insensitive)
        raw_name_lower = raw_name.lower()
        for pattern, standard_name in name_mappings.items():
            if pattern.lower() == raw_name_lower:
                logger.info(f"DEALERSHIP NAME STANDARDIZATION (case): '{raw_name}' -> '{standard_name}'")
                return standard_name
        
        # Return original name if no mapping found
        return raw_name

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
        """Normalize vehicle condition from scraper data to match database constraint"""
        if pd.isna(condition_value) or condition_value == '':
            return 'po'  # Default to 'po' (pre-owned) as safest default
        
        condition_str = str(condition_value).lower().strip()
        
        # Map conditions to exact database constraint values:
        # Allowed: 'new', 'po', 'cpo', 'offlot', 'onlot'
        condition_map = {
            'new': 'new',
            'used': 'po',  # Map 'used' to 'po' (pre-owned)
            'pre-owned': 'po',
            'preowned': 'po',
            'po': 'po',
            'certified': 'cpo',  # Map 'certified' to 'cpo'
            'cpo': 'cpo',
            'certified pre-owned': 'cpo',
            'certified-pre-owned': 'cpo',
            'off-lot': 'offlot',
            'offlot': 'offlot',
            'off lot': 'offlot',
            'on-lot': 'onlot',
            'onlot': 'onlot',
            'on lot': 'onlot'
        }
        
        return condition_map.get(condition_str, 'po')  # Default to 'po' if unknown
    
    def get_column_value(self, row: Dict, field_mappings: List[str], default_value='') -> str:
        """Get column value using flexible column name matching"""
        row_columns = {k.lower(): k for k in row.keys()}
        
        for possible_name in field_mappings:
            if possible_name.lower() in row_columns:
                actual_column = row_columns[possible_name.lower()]
                value = row.get(actual_column, default_value)
                if not pd.isna(value):
                    return str(value).strip()
        
        return default_value
    
    def validate_row(self, row: Dict) -> Tuple[bool, Optional[str]]:
        """Validate a single row of data"""
        # Create case-insensitive column mapping
        row_columns = {k.lower(): k for k in row.keys()}
        
        # Check required fields with flexible column name matching
        required_mappings = {
            'vin': ['vin', 'vehicle_vin', 'vehiclevin'],
            'stock': ['stock', 'stock_number', 'stocknumber', 'stock_no'],
            'dealer_name': ['dealer_name', 'dealership_name', 'dealer', 'location']
        }
        
        for field, possible_names in required_mappings.items():
            found_column = None
            for possible_name in possible_names:
                if possible_name.lower() in row_columns:
                    found_column = row_columns[possible_name.lower()]
                    break
            
            if not found_column:
                available_columns = list(row.keys())[:10]  # Show first 10 columns for debugging
                return False, f"Missing required field: {field}. Available columns: {available_columns}"
            
            # Check if the found column has a value
            if pd.isna(row[found_column]) or str(row[found_column]).strip() == '':
                return False, f"Empty required field: {field} (column: {found_column})"
        
        # Validate VIN (find the VIN column again)
        vin_column = None
        for possible_name in required_mappings['vin']:
            if possible_name.lower() in row_columns:
                vin_column = row_columns[possible_name.lower()]
                break
        
        if vin_column:
            vin = str(row[vin_column]).strip().upper()
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
        date_formats = ['%Y/%m/%d', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']
        
        for fmt in date_formats:
            try:
                return datetime.strptime(str(value), fmt)
            except ValueError:
                continue
        
        return None
    
    def import_complete_csv(self, file_path: str) -> Dict:
        """Import the complete_data.csv file using proper ScraperImportManager"""
        logger.info(f"Importing complete CSV file: {file_path}")
        
        try:
            # Initialize ScraperImportManager first to get active import ID
            import_manager = ScraperImportManager()
            
            # Get or create active import
            active_import = self.db.execute_query(
                "SELECT import_id FROM scraper_imports WHERE status = 'active' LIMIT 1"
            )
            
            if not active_import:
                # Create new import
                import_id = import_manager.create_new_import()
            else:
                import_id = active_import[0]['import_id']
            
            logger.info(f"Using import ID: {import_id}")
            
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
            dealership_groups = df.groupby('Location')
            
            for raw_dealership_name, group_df in dealership_groups:
                # CRITICAL FIX: Standardize dealership names during import
                dealership_name = self.standardize_dealership_name(raw_dealership_name)
                logger.info(f"ROBUST DEBUG: Starting import for {dealership_name} with {len(group_df)} vehicles")
                self.import_stats['dealerships'][dealership_name] = {
                    'total': 0,
                    'imported': 0,
                    'skipped': 0
                }
                
                raw_data = []
                normalized_data = []
                vin_history_data = []
                today = date.today()  # Define today for VIN history
                
                # Track validation and filtering results
                validation_passed = 0
                validation_failed = 0
                filter_passed = 0
                filter_failed = 0
                
                for idx, row in group_df.iterrows():
                    self.import_stats['total_rows'] += 1
                    self.import_stats['dealerships'][dealership_name]['total'] += 1
                    
                    # DEBUG: Show first 5 vehicles for each dealership
                    if idx < 5:
                        logger.info(f"ROBUST DEBUG: {dealership_name} Row {idx}: VIN={row.get('Vin', 'MISSING')}, Stock={row.get('Stock', 'MISSING')}, Type={row.get('Type', 'MISSING')}")
                    
                    # Validate row
                    is_valid, error_msg = self.validate_row(row)
                    if not is_valid:
                        validation_failed += 1
                        self.import_stats['skipped_rows'] += 1
                        self.import_stats['dealerships'][dealership_name]['skipped'] += 1
                        self.import_stats['errors'].append(
                            f"{dealership_name} Row {idx + 1}: {error_msg}"
                        )
                        # DEBUG: Log first 3 validation failures per dealership
                        if validation_failed <= 3:
                            logger.warning(f"ROBUST DEBUG: {dealership_name} Row {idx} VALIDATION FAILED: {error_msg}")
                        continue
                    else:
                        validation_passed += 1
                    
                    # Check dealership-specific filtering rules
                    should_include, filter_msg = self.should_include_vehicle(row, dealership_name)
                    if not should_include:
                        filter_failed += 1
                        self.import_stats['skipped_rows'] += 1
                        self.import_stats['dealerships'][dealership_name]['skipped'] += 1
                        self.import_stats['errors'].append(
                            f"{dealership_name} Row {idx + 1}: Filtered - {filter_msg}"
                        )
                        # DEBUG: Log first 3 filter failures per dealership
                        if filter_failed <= 3:
                            logger.warning(f"ROBUST DEBUG: {dealership_name} Row {idx} FILTER FAILED: {filter_msg}")
                        continue
                    else:
                        filter_passed += 1
                    
                    # Prepare raw data tuple using flexible column mapping
                    vin = self.get_column_value(row, ['Vin', 'vin', 'vehicle_vin', 'vehiclevin']).upper()
                    stock = self.get_column_value(row, ['Stock', 'stock', 'stock_number', 'stocknumber', 'stock_no'])
                    year_str = self.get_column_value(row, ['Year', 'year'])
                    
                    # BREAKTHROUGH FIX: Get proper data for normalization
                    condition_data = self.get_column_value(row, ['Type', 'type', 'condition', 'vehicle_condition'])  # Vehicle type
                    status_data = self.get_column_value(row, ['Status', 'status'])  # Vehicle status for lot determination
                    
                    # Apply normalization using the correct fields
                    normalized_type = normalizer.normalize_vehicle_type(condition_data or '')
                    lot_status = normalizer.normalize_lot_status(status_data or '')
                    
                    # CRITICAL: Override lot status if no stock number
                    if not stock:
                        lot_status = 'offlot'  # Force offlot for missing stock
                    
                    # Store normalized values for use in normalized_vehicle_data table
                    self.current_normalized_type = normalized_type
                    self.current_lot_status = lot_status
                    
                    raw_tuple = (
                        vin,
                        stock,
                        condition_data or 'Vehicle',  # type (use condition data that actually exists)
                        int(year_str) if year_str and year_str.isdigit() else None,
                        self.get_column_value(row, ['Make', 'make']),
                        self.get_column_value(row, ['Model', 'model']),
                        self.get_column_value(row, ['Trim', 'trim']),
                        self.get_column_value(row, ['Ext Color', 'exterior_color', 'ext_color', 'color']),
                        self.normalize_condition(self.get_column_value(row, ['Status', 'condition', 'vehicle_condition', 'status'])),
                        self.clean_numeric(self.get_column_value(row, ['Price', 'price'])),
                        self.get_column_value(row, ['Body Style', 'body_style']),  # Available in CSV
                        self.get_column_value(row, ['Fuel Type', 'fuel_type', 'fuel']),
                        self.clean_numeric(self.get_column_value(row, ['MSRP', 'msrp'])),
                        self.clean_date(self.get_column_value(row, ['Date In Stock', 'date_in_stock'])),  # Convert empty dates to None
                        self.get_column_value(row, ['Street Address', 'street_address']),  # Available in CSV
                        self.get_column_value(row, ['Locality', 'locality']),  # Available in CSV
                        self.get_column_value(row, ['Postal Code', 'postal_code']),  # Available in CSV
                        self.get_column_value(row, ['Region', 'region']),  # Available in CSV
                        self.get_column_value(row, ['Country', 'country']),  # Available in CSV
                        dealership_name,  # location
                        row.get('Vechile URL', row.get('url', '')),  # Note: CSV has typo "Vechile URL"
                        import_id,  # import_id - CRITICAL for active dataset filtering
                        datetime.now(),  # import_timestamp
                        date.today()  # import_date
                    )
                    raw_data.append(raw_tuple)
                
                # ROBUST DEBUG: Log final processing results for this dealership
                logger.info(f"ROBUST DEBUG: {dealership_name} FINAL RESULTS:")
                logger.info(f"  - Total vehicles in CSV: {len(group_df)}")
                logger.info(f"  - Validation passed: {validation_passed}")
                logger.info(f"  - Validation failed: {validation_failed}")
                logger.info(f"  - Filter passed: {filter_passed}")
                logger.info(f"  - Filter failed: {filter_failed}")
                logger.info(f"  - Raw data ready for import: {len(raw_data)}")
                
                # Bulk insert raw data for this dealership
                if raw_data:
                    raw_columns = [
                        'vin', 'stock', 'type', 'year', 'make', 'model', 'trim',
                        'ext_color', 'status', 'price', 'body_style', 'fuel_type',
                        'msrp', 'date_in_stock', 'street_address', 'locality',
                        'postal_code', 'region', 'country', 'location', 'vehicle_url',
                        'import_id', 'import_timestamp', 'import_date'
                    ]
                    
                    logger.info(f"ROBUST DEBUG: About to batch insert {len(raw_data)} rows for {dealership_name}")
                    logger.info(f"ROBUST DEBUG: First few raw_data tuples: {raw_data[:2] if raw_data else 'NO DATA'}")
                    
                    rows_inserted = self.db.execute_batch_insert(
                        'raw_vehicle_data', 
                        raw_columns, 
                        raw_data
                    )
                    
                    logger.info(f"ROBUST DEBUG: Batch insert returned {rows_inserted} rows for {dealership_name}")
                    
                    self.import_stats['imported_rows'] += rows_inserted
                    self.import_stats['dealerships'][dealership_name]['imported'] = rows_inserted
                    
                    # Get inserted records for normalization using import_id
                    raw_records = self.db.execute_query(
                        """
                        SELECT id, vin, stock, type, year, make, model, trim, 
                               status, price, msrp, date_in_stock, location, vehicle_url
                        FROM raw_vehicle_data
                        WHERE location = %s AND import_id = %s
                        """,
                        (dealership_name, import_id)
                    )
                    
                    # Prepare normalized data
                    logger.info(f"DEBUG: Preparing to normalize {len(raw_records)} records for {dealership_name}")
                    for record in raw_records:
                        # BREAKTHROUGH FIX: Use proper fields for normalization
                        condition_data = record.get('type', '')  # For vehicle type (new/used/cpo)
                        status_data = record.get('status', '')   # For lot status (In Transit/Available/etc)
                        stock_data = record.get('stock', '')     # For stock validation
                        
                        # Normalize vehicle type using condition/type field
                        normalized_vehicle_type = normalizer.normalize_vehicle_type(condition_data)
                        
                        # Normalize lot status using STATUS field (handles "In Transit" etc)
                        normalized_lot_status = normalizer.normalize_lot_status(status_data)
                        
                        # CRITICAL BREAKTHROUGH: Override lot status if no stock number OR in-transit
                        if not stock_data or 'in-transit' in status_data.lower() or 'in transit' in status_data.lower():
                            normalized_lot_status = 'offlot'  # Force offlot for missing stock OR in-transit
                        
                        # Use normalizer output directly - CAO system expects 'onlot'/'offlot' format
                        db_lot_status = normalized_lot_status
                        
                        # CRITICAL FIX: Handle NULL stock values
                        stock_value = record['stock'] if record['stock'] else 'AUTO'
                        
                        normalized_tuple = (
                            record['id'],  # raw_data_id
                            record['vin'],
                            stock_value,  # Use 'AUTO' for NULL stock to satisfy NOT NULL constraint
                            normalized_vehicle_type,  # vehicle_condition (po, cpo, new)
                            record['year'],
                            record['make'],
                            record['model'],
                            record['trim'],
                            db_lot_status,  # status (on lot, off lot)
                            record['price'],
                            record['msrp'],
                            record['date_in_stock'],
                            record['location'],
                            record['vehicle_url'],
                            db_lot_status,  # on_lot_status column
                            datetime.now(),  # created_at
                            datetime.now(),  # updated_at
                            date.today()  # last_seen_date
                        )
                        normalized_data.append(normalized_tuple)
                        
                        # VIN history entry (no raw_data_id column in vin_history table)
                        vin_history_data.append((
                            record['location'],  # dealership_name
                            record['vin'],
                            today  # order_date
                        ))
                    
                    # Upsert normalized data
                    logger.info(f"DEBUG: About to upsert {len(normalized_data)} normalized records for {dealership_name}")
                    if normalized_data:
                        norm_columns = [
                            'raw_data_id', 'vin', 'stock', 'vehicle_condition',
                            'year', 'make', 'model', 'trim', 'status', 'price',
                            'msrp', 'date_in_stock', 'location', 'vehicle_url', 'on_lot_status',
                            'created_at', 'updated_at', 'last_seen_date'
                        ]
                        
                        try:
                            result = self.db.upsert_data(
                                'normalized_vehicle_data',
                                norm_columns,
                                normalized_data,
                                conflict_columns=['vin', 'location'],
                                update_columns=['stock', 'vehicle_condition', 'price', 
                                              'status', 'on_lot_status', 'last_seen_date', 'updated_at']
                            )
                            logger.info(f"DEBUG: Upsert result: {result} rows affected for {dealership_name}")
                        except Exception as e:
                            logger.error(f"CRITICAL: Normalization upsert failed for {dealership_name}: {e}")
                            raise
                    
                    # Insert VIN history (handle duplicates gracefully)
                    if vin_history_data:
                        self.db.upsert_data(
                            'vin_history',
                            ['dealership_name', 'vin', 'order_date'],
                            vin_history_data,
                            conflict_columns=['dealership_name', 'vin', 'order_date'],
                            update_columns=[]  # Don't update on conflict, just ignore
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
                SELECT COUNT(DISTINCT order_date)
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
    
    def import_csv(self, file_path: str) -> Dict:
        """
        Web server compatibility method - wraps the main import logic
        This method is called by the web server (app.py line 192)
        """
        logger.info(f"Web server calling import_csv with: {file_path}")
        
        try:
            # Call the import logic that includes normalization
            # The web server CSV format matches the "complete_data.csv" format
            result = self.import_complete_csv(file_path)
            
            # Return result in format expected by web server
            return {
                'success': True,
                'processed': result.get('imported_rows', 0),
                'message': f"Successfully imported {result.get('imported_rows', 0)} vehicles",
                'details': result
            }
            
        except Exception as e:
            logger.error(f"import_csv failed: {e}")
            return {
                'success': False,
                'processed': 0,
                'message': f"Import failed: {str(e)}",
                'error': str(e)
            }

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