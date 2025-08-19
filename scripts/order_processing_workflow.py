#!/usr/bin/env python3
"""
Order Processing Workflow Implementation
========================================

Complete implementation of Silver Fox order processing based on reference materials.

Workflow Overview:
1. Check ORDER INPUT TIMELINE for CAO schedule and order types
2. Run automated 4AM daily scrape for all dealerships
3. Import scraper data and filter based on dealership requirements
4. Compare VIN lists to identify new vehicles on lot
5. Run order processing to generate QR codes
6. Output QR file paths and CSV file for Adobe

Author: Silver Fox Assistant
Created: 2025-07-29
"""

import os
import sys
import json
import logging
import schedule
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import qrcode
from PIL import Image
import io

# Add project paths
current_file = Path(__file__).resolve()
scripts_dir = current_file.parent
sys.path.insert(0, str(scripts_dir))

from database_connection import db_manager
from real_scraper_integration import RealScraperIntegration

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('order_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OrderProcessingWorkflow:
    """Complete order processing workflow implementation"""
    
    def __init__(self):
        self.scraper_integration = RealScraperIntegration()
        self.order_schedule = self._load_order_schedule()
        self.dealership_configs = self._load_dealership_configs()
        
    def _load_order_schedule(self) -> Dict[str, List[Dict]]:
        """Load the weekly order schedule"""
        schedule = {
            'Monday': {
                'CAO': [
                    {'name': 'Porsche STL - New & Used', 'template': 'Shortcut'},
                    {'name': 'South County DCJR - New & Used', 'template': 'Shortcut Pack'},
                    {'name': 'Frank Leta Honda', 'template': 'Flyout'}
                ],
                'As Ordered': [
                    {'name': 'Dave Sinclair Lincoln SOCO', 'template': 'Shortcut Pack'},
                    {'name': 'Dave Sinclair Manchester', 'template': 'Flyout'},
                    {'name': 'Dave Sinclair Lincoln St. Peters', 'template': 'Shortcut Pack'},
                    {'name': 'Suntrup Hyundai', 'template': 'Shortcut Pack'},
                    {'name': 'Suntrup Kia', 'template': 'Shortcut Pack'},
                    {'name': 'Pundmann Ford', 'template': 'Shortcut Pack'},
                    {'name': 'Bommarito Cadillac', 'template': 'Shortcut Pack'},
                    {'name': 'Mini STL', 'template': 'Flyout'},
                    {'name': 'BMW of West STL', 'template': 'Flyout'},
                    {'name': 'Kia Of Columbia - Used', 'template': 'Shortcut Pack'},
                    {'name': 'BMW of Columbia - New & Used', 'template': 'Shortcut Pack'},
                    {'name': 'Joe Machens Nissan - Used', 'template': 'Shortcut Pack'},
                    {'name': 'Joe Machens Toyota - New & Used', 'template': 'Shortcut Pack'},
                    {'name': 'Joe Machens CDJR - New & Used', 'template': 'Shortcut Pack USED, Shortcut NEW'},
                    {'name': 'Columbia Honda - Used', 'template': 'Flyout'},
                    {'name': 'Rusty Drewing Chevrolet - New & Used', 'template': 'Shortcut Pack'},
                    {'name': 'Rusty Drewing Cadillac - New', 'template': 'Shortcut Pack'}
                ]
            },
            'Tuesday': {
                'CAO': [
                    {'name': 'Spirit Lexus', 'template': 'Flyout'},
                    {'name': 'Suntrup Ford Kirkwood', 'template': 'Flyout'},
                    {'name': 'Suntrup Ford Westport', 'template': 'Flyout'},
                    {'name': 'Weber Chevy', 'template': 'Custom'},
                    {'name': 'HW KIA - Used', 'template': 'Flyout'},
                    {'name': 'Volvo Cars West County - New', 'template': 'Shortcut'},
                    {'name': 'Bommarito West County - Used', 'template': 'Flyout'},
                    {'name': 'Glendale CDJR - Used', 'template': 'Shortcut Pack'},
                    {'name': 'Honda of Frontenac - Used', 'template': 'Shortcut Pack'},
                    {'name': 'Volvo Cars West County - UCM', 'template': ''}
                ],
                'As Ordered': []
            },
            'Wednesday': {
                'CAO': [
                    {'name': 'Pappas Toyota - New & Loaner', 'template': 'Shortcut Pack'},
                    {'name': 'Porsche STL - New & Used', 'template': 'Shortcut'},
                    {'name': 'Serra New & Used', 'template': 'Shortcut Pack'},
                    {'name': 'Auffenberg Used', 'template': 'Shortcut Pack'},
                    {'name': 'Frank Leta Honda', 'template': 'Flyout'},
                    {'name': 'Suntrup Buick GMC', 'template': 'Shortcut, Flyout'}
                ],
                'As Ordered': []
            },
            'Thursday': {
                'CAO': [
                    {'name': 'Spirit Lexus', 'template': 'Flyout'},
                    {'name': 'Suntrup Ford Kirkwood', 'template': 'Flyout'},
                    {'name': 'Suntrup Ford Westport', 'template': 'Flyout'},
                    {'name': 'Weber Chevy', 'template': 'Custom'},
                    {'name': 'HW KIA - Used', 'template': 'Flyout'},
                    {'name': 'Volvo Cars West County - UCM', 'template': ''},
                    {'name': 'Volvo Cars West County - New', 'template': 'Shortcut'},
                    {'name': 'Bommarito West County - Used', 'template': 'Flyout'},
                    {'name': 'Glendale CDJR - Used', 'template': 'Shortcut Pack'},
                    {'name': 'Honda of Frontenac - New & Used', 'template': 'Shortcut Pack'},
                    {'name': 'South County DCJR - New & Used', 'template': 'Shortcut Pack'},
                    {'name': 'Thoroughbred - Used', 'template': 'Shortcut Pack'}
                ],
                'As Ordered': []
            },
            'Friday': {
                'CAO': [],
                'As Ordered': []
            }
        }
        return schedule
    
    def _load_dealership_configs(self) -> Dict[str, Dict]:
        """Load dealership configurations from database"""
        try:
            configs = db_manager.execute_query("""
                SELECT name, filtering_rules, output_rules, qr_output_path
                FROM dealership_configs
            """)
            
            dealership_map = {}
            for config in configs:
                dealership_map[config['name']] = {
                    'filtering_rules': config['filtering_rules'] or {},
                    'output_rules': config['output_rules'] or {},
                    'qr_output_path': config['qr_output_path'] or ''
                }
            return dealership_map
            
        except Exception as e:
            logger.error(f"Error loading dealership configs: {e}")
            return {}
    
    def run_daily_scrape(self):
        """Run 4AM daily scrape for all dealerships"""
        logger.info("="*80)
        logger.info("[DAILY SCRAPE] Starting 4AM automated scrape for all dealerships")
        logger.info("="*80)
        
        start_time = datetime.now()
        
        # Run all available scrapers
        results = self.scraper_integration.run_all_available_scrapers()
        
        # Log results
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"[DAILY SCRAPE] Completed in {duration:.1f}s")
        logger.info(f"[DAILY SCRAPE] Total vehicles: {results['total_vehicles']}")
        logger.info(f"[DAILY SCRAPE] Real data: {results['total_real_data']}")
        logger.info(f"[DAILY SCRAPE] Fallback data: {results['total_fallback_data']}")
        
        # Update last scrape timestamp for all dealerships
        self._update_scrape_timestamps()
        
        return results
    
    def _update_scrape_timestamps(self):
        """Update last scrape timestamp for all dealerships"""
        try:
            db_manager.execute_query("""
                UPDATE dealership_configs
                SET last_scrape_timestamp = CURRENT_TIMESTAMP
            """)
        except Exception as e:
            logger.error(f"Error updating scrape timestamps: {e}")
    
    def filter_vehicles_by_type(self, dealership_name: str, vehicle_types: List[str], import_id: int = None) -> List[Dict]:
        """Filter vehicles based on dealership requirements (new/cpo/used) - ONLY from latest import"""
        try:
            # CRITICAL: Only use latest active import if not specified
            if not import_id:
                from scraper_import_manager import import_manager
                active_import = import_manager.get_active_import()
                if not active_import:
                    logger.error(f"No active import found! Cannot process CAO order.")
                    return []
                import_id = active_import['import_id']
                logger.info(f"Using active import ID: {import_id} from {active_import['import_date']}")
            
            # Build condition based on vehicle types
            type_conditions = []
            if 'new' in vehicle_types:
                type_conditions.append("type = 'New'")
            if 'cpo' in vehicle_types:
                type_conditions.append("type = 'Certified Pre-Owned'")
            if 'used' in vehicle_types:
                type_conditions.append("type = 'Used'")
            if 'po' in vehicle_types:  # Pre-owned
                type_conditions.append("type IN ('Used', 'Pre-Owned')")
            
            type_filter = " OR ".join(type_conditions) if type_conditions else "TRUE"
            
            # Get filtering rules for this dealership
            config = self.dealership_configs.get(dealership_name, {})
            filtering_rules = config.get('filtering_rules', {})
            
            # Apply additional filters
            additional_filters = []
            
            # Filter out missing stock numbers if configured
            if filtering_rules.get('exclude_missing_stock', True):
                additional_filters.append("stock IS NOT NULL AND stock != ''")
            
            # Apply require_status filter (highest priority)
            if filtering_rules.get('require_status'):
                require_statuses = filtering_rules['require_status']
                if isinstance(require_statuses, list):
                    status_conditions = [f"status = '{status}'" for status in require_statuses]
                    additional_filters.append(f"({' OR '.join(status_conditions)})")
                else:
                    additional_filters.append(f"status = '{require_statuses}'")
            
            # Apply exclude_status filter  
            if filtering_rules.get('exclude_status'):
                exclude_statuses = filtering_rules['exclude_status']
                if isinstance(exclude_statuses, list):
                    status_conditions = [f"status != '{status}'" for status in exclude_statuses]
                    additional_filters.append(f"({' AND '.join(status_conditions)})")
                else:
                    additional_filters.append(f"status != '{exclude_statuses}'")
            
            # Filter out in-transit if configured (legacy support)
            elif filtering_rules.get('exclude_in_transit', False):
                additional_filters.append("status != 'In-Transit'")
            
            # Filter out missing prices if configured
            if filtering_rules.get('exclude_missing_price', True):
                additional_filters.append("price IS NOT NULL AND price > 0")
            
            # Build final query - CRITICAL: Include import_id to only get latest data
            where_conditions = [
                f"location = %s", 
                f"({type_filter})",
                "import_id = %s",
                "is_archived = FALSE"  # Extra safety - only non-archived data
            ]
            if additional_filters:
                where_conditions.extend(additional_filters)
            
            where_clause = " AND ".join(where_conditions)
            
            query = f"""
                SELECT * FROM raw_vehicle_data
                WHERE {where_clause}
                ORDER BY year DESC, make, model
            """
            
            vehicles = db_manager.execute_query(query, (dealership_name, import_id))
            
            logger.info(f"[FILTER] {dealership_name}: {len(vehicles)} vehicles after filtering")
            return vehicles
            
        except Exception as e:
            logger.error(f"Error filtering vehicles for {dealership_name}: {e}")
            return []
    
    def compare_vin_lists(self, dealership_name: str, current_vins: List[str], test_mode: bool = False) -> Tuple[List[str], List[str]]:
        """Compare current VINs with dealership-specific VIN log to find new vehicles
        
        Args:
            dealership_name: Name of the dealership
            current_vins: List of current VINs from inventory
            test_mode: If True, skip updating VIN history for repeated testing
        """
        try:
            # Convert dealership name to table name format
            # Example: "Porsche St. Louis" -> "porsche_st_louis_vin_log"
            table_name = dealership_name.lower().replace(' ', '_').replace('.', '').replace("'", '') + '_vin_log'
            
            # Check if dealership-specific table exists
            table_check = db_manager.execute_query("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            """, (table_name,))
            
            if not table_check:
                logger.warning(f"VIN log table {table_name} does not exist. Creating it...")
                # Create the table if it doesn't exist
                create_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    vin VARCHAR(17) PRIMARY KEY,
                    processed_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    order_type VARCHAR(20),
                    template_type VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                db_manager.execute_query(create_sql)
                logger.info(f"Created VIN log table: {table_name}")
            
            # Get previous VINs from dealership-specific table
            query = f"""
                SELECT vin FROM {table_name}
            """
            previous_vins = db_manager.execute_query(query)
            
            previous_vin_set = {row['vin'] for row in previous_vins}
            current_vin_set = set(current_vins)
            
            # Find new VINs (in current but not in previous)
            new_vins = list(current_vin_set - previous_vin_set)
            
            # Find removed VINs (in previous but not in current)  
            removed_vins = list(previous_vin_set - current_vin_set)
            
            logger.info(f"[VIN COMPARE] {dealership_name}: {len(new_vins)} new, {len(removed_vins)} removed")
            logger.info(f"[VIN COMPARE] Using table: {table_name}")
            logger.info(f"[VIN COMPARE] Previous VINs in log: {len(previous_vin_set)}, Current inventory: {len(current_vin_set)}")
            
            # Update dealership-specific VIN history (skip in test mode)
            if test_mode:
                logger.info(f"[TEST MODE] Skipping VIN history update for {dealership_name}")
            else:
                self._update_dealership_vin_history(dealership_name, table_name, new_vins)
            
            return new_vins, removed_vins
            
        except Exception as e:
            logger.error(f"Error comparing VINs for {dealership_name}: {e}")
            return current_vins, []  # Treat all as new if comparison fails
    
    def _update_dealership_vin_history(self, dealership_name: str, table_name: str, new_vins: List[str], order_type: str = 'CAO', order_number: str = None):
        """Update dealership-specific VIN history for tracking"""
        try:
            if not new_vins:
                logger.info(f"No new VINs to add to {table_name}")
                return
                
            # Generate order number if not provided
            if not order_number:
                # Extract dealership slug from table name
                dealership_slug = table_name.replace('_vin_log', '')
                
                # Generate unique order number
                order_number_query = f"""
                    SELECT generate_order_number('{dealership_slug}', '{order_type}')
                """
                result = db_manager.execute_query(order_number_query)
                order_number = result[0]['generate_order_number'] if result else f"{dealership_slug.upper()}_{order_type}_{datetime.now().strftime('%Y%m%d')}_001"
            
            logger.info(f"[VIN HISTORY] Using order number: {order_number}")
                
            # Insert new VINs into dealership-specific table with order tracking
            for vin in new_vins:
                insert_sql = f"""
                    INSERT INTO {table_name} (vin, processed_date, order_type, order_number, order_date)
                    VALUES (%s, CURRENT_DATE, %s, %s, CURRENT_DATE)
                    ON CONFLICT (vin) DO NOTHING
                """
                db_manager.execute_query(insert_sql, (vin, order_type, order_number))
            
            logger.info(f"[VIN HISTORY] Added {len(new_vins)} new VINs to {table_name} with order {order_number}")
                
        except Exception as e:
            logger.error(f"Error updating dealership VIN history: {e}")
            
            # Fallback to basic insert without order number
            try:
                for vin in new_vins:
                    insert_sql = f"""
                        INSERT INTO {table_name} (vin, processed_date, order_type)
                        VALUES (%s, CURRENT_DATE, %s)
                        ON CONFLICT (vin) DO NOTHING
                    """
                    db_manager.execute_query(insert_sql, (vin, order_type))
                logger.info(f"[VIN HISTORY] Fallback: Added {len(new_vins)} VINs without order number")
            except Exception as fallback_error:
                logger.error(f"Fallback VIN history update also failed: {fallback_error}")
    
    def generate_qr_codes(self, vehicles: List[Dict], dealership_name: str, output_folder: Path) -> List[str]:
        """Generate QR codes for vehicle URLs"""
        qr_paths = []
        
        # Clean dealership name for file naming
        clean_name = dealership_name.replace(' ', '_').replace('/', '_')
        
        for idx, vehicle in enumerate(vehicles):
            try:
                url = vehicle.get('vehicle_url', '')
                if not url:
                    continue
                
                # Generate QR code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(url)
                qr.make(fit=True)
                
                # Create QR code image
                img = qr.make_image(fill_color="rgb(50,50,50)", back_color="white")
                
                # Resize to 388x388 as per Apps Script
                img = img.resize((388, 388), Image.Resampling.LANCZOS)
                
                # Save QR code
                filename = f"{clean_name}_QR_Code_{idx + 1}.png"
                filepath = output_folder / filename
                img.save(filepath)
                
                qr_paths.append(str(filepath))
                
            except Exception as e:
                logger.error(f"Error generating QR code for vehicle {vehicle.get('vin', 'unknown')}: {e}")
        
        logger.info(f"[QR CODES] Generated {len(qr_paths)} QR codes for {dealership_name}")
        return qr_paths
    
    def generate_adobe_csv(self, vehicles: List[Dict], dealership_name: str, output_path: Path, qr_paths: List[str] = None) -> str:
        """Generate CSV file for Adobe processing with QR code file paths"""
        try:
            import csv
            
            # Define CSV headers matching SCRAPERDATA format + QR Path
            headers = [
                'Vin', 'Stock', 'Type', 'Year', 'Make', 'Model', 'Trim',
                'Ext Color', 'Status', 'Price', 'Body Style', 'Fuel Type',
                'MSRP', 'Date In Stock', 'Street Address', 'Locality',
                'Postal Code', 'Region', 'Country', 'Location', 'Vehicle URL', 'QR_Code_Path'
            ]
            
            # Clean dealership name for file naming
            clean_name = dealership_name.replace(' ', '_').replace('/', '_')
            filename = f"{clean_name}_adobe_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = output_path / filename
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                
                # Create QR path mapping if provided
                qr_path_map = {}
                if qr_paths:
                    for idx, qr_path in enumerate(qr_paths):
                        if idx < len(vehicles):
                            vehicle_vin = vehicles[idx].get('vin', '')
                            if vehicle_vin:
                                qr_path_map[vehicle_vin] = qr_path
                
                for vehicle in vehicles:
                    vin = vehicle.get('vin', '')
                    qr_path = qr_path_map.get(vin, '') if qr_paths else ''
                    
                    row = {
                        'Vin': vin,
                        'Stock': vehicle.get('stock', ''),
                        'Type': vehicle.get('type', ''),
                        'Year': vehicle.get('year', ''),
                        'Make': vehicle.get('make', ''),
                        'Model': vehicle.get('model', ''),
                        'Trim': vehicle.get('trim', ''),
                        'Ext Color': vehicle.get('ext_color', ''),
                        'Status': vehicle.get('status', ''),
                        'Price': vehicle.get('price', ''),
                        'Body Style': vehicle.get('body_style', ''),
                        'Fuel Type': vehicle.get('fuel_type', ''),
                        'MSRP': vehicle.get('msrp', ''),
                        'Date In Stock': vehicle.get('date_in_stock', ''),
                        'Street Address': vehicle.get('street_address', ''),
                        'Locality': vehicle.get('locality', ''),
                        'Postal Code': vehicle.get('postal_code', ''),
                        'Region': vehicle.get('region', ''),
                        'Country': vehicle.get('country', ''),
                        'Location': vehicle.get('location', ''),
                        'Vehicle URL': vehicle.get('vehicle_url', ''),
                        'QR_Code_Path': qr_path
                    }
                    writer.writerow(row)
            
            logger.info(f"[ADOBE CSV] Generated {filepath} with {len(vehicles)} vehicles")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error generating Adobe CSV: {e}")
            return ""
    
    def process_cao_order(self, dealership_name: str, vehicle_types: List[str] = None, test_mode: bool = False) -> Dict[str, Any]:
        """Process a Comparative Analysis Order (CAO)
        
        Args:
            dealership_name: Name of the dealership
            vehicle_types: List of vehicle types to process (default: ['new', 'cpo', 'used'])
            test_mode: If True, skip VIN logging to allow repeated testing
        """
        logger.info(f"[CAO ORDER] Processing {dealership_name} (Test Mode: {test_mode})")
        
        if vehicle_types is None:
            vehicle_types = ['new', 'cpo', 'used']  # Default to all types
        
        try:
            # Step 1: Filter vehicles by type
            vehicles = self.filter_vehicles_by_type(dealership_name, vehicle_types)
            
            if not vehicles:
                logger.warning(f"No vehicles found for {dealership_name}")
                return {
                    'success': False,
                    'error': 'No vehicles found',
                    'dealership': dealership_name
                }
            
            # Step 2: Compare VINs to find new vehicles
            current_vins = [v['vin'] for v in vehicles]
            new_vins, removed_vins = self.compare_vin_lists(dealership_name, current_vins, test_mode)
            
            # Filter to only new vehicles
            new_vehicles = [v for v in vehicles if v['vin'] in new_vins]
            
            logger.info(f"[CAO ORDER] {dealership_name}: {len(new_vehicles)} new vehicles to process")
            
            # Step 3: Create output folders
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_base = Path(f"orders/{dealership_name.replace(' ', '_')}/{timestamp}")
            qr_folder = output_base / "qr_codes"
            csv_folder = output_base / "adobe"
            
            qr_folder.mkdir(parents=True, exist_ok=True)
            csv_folder.mkdir(parents=True, exist_ok=True)
            
            # Step 4: Generate QR codes FIRST
            qr_paths = self.generate_qr_codes(new_vehicles, dealership_name, qr_folder)
            
            # Step 5: Generate Adobe CSV with QR paths included
            csv_path = self.generate_adobe_csv(new_vehicles, dealership_name, csv_folder, qr_paths)
            
            # Step 6: Create order record
            order_id = self._create_order_record(
                dealership_name, 
                'CAO',
                len(new_vehicles),
                len(qr_paths),
                csv_path
            )
            
            return {
                'success': True,
                'dealership': dealership_name,
                'order_type': 'CAO',
                'order_id': order_id,
                'total_vehicles': len(vehicles),
                'new_vehicles': len(new_vehicles),
                'removed_vehicles': len(removed_vins),
                'processed_vins': new_vins,  # Include processed VINs for order number tracking
                'qr_codes_generated': len(qr_paths),
                'qr_folder': str(qr_folder),
                'csv_file': csv_path,
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Error processing CAO order for {dealership_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'dealership': dealership_name
            }
    
    def process_list_order(self, dealership_name: str, vin_list: List[str]) -> Dict[str, Any]:
        """Process a list-based order (transcribed VINs from installers)"""
        logger.info(f"[LIST ORDER] Processing {dealership_name} with {len(vin_list)} VINs")
        
        try:
            # Get vehicles by VIN list
            vehicles = []
            for vin in vin_list:
                vehicle_data = db_manager.execute_query("""
                    SELECT * FROM raw_vehicle_data
                    WHERE vin = %s AND location = %s
                    ORDER BY import_timestamp DESC
                    LIMIT 1
                """, (vin, dealership_name))
                
                if vehicle_data:
                    vehicles.append(vehicle_data[0])
                else:
                    logger.warning(f"VIN {vin} not found for {dealership_name}")
            
            logger.info(f"[LIST ORDER] Found {len(vehicles)} of {len(vin_list)} VINs")
            
            # Create output folders
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_base = Path(f"orders/{dealership_name.replace(' ', '_')}/{timestamp}")
            qr_folder = output_base / "qr_codes"
            csv_folder = output_base / "adobe"
            
            qr_folder.mkdir(parents=True, exist_ok=True)
            csv_folder.mkdir(parents=True, exist_ok=True)
            
            # Generate QR codes FIRST
            qr_paths = self.generate_qr_codes(vehicles, dealership_name, qr_folder)
            
            # Generate Adobe CSV with QR paths included
            csv_path = self.generate_adobe_csv(vehicles, dealership_name, csv_folder, qr_paths)
            
            # Create order record
            order_id = self._create_order_record(
                dealership_name,
                'LIST',
                len(vehicles),
                len(qr_paths),
                csv_path
            )
            
            return {
                'success': True,
                'dealership': dealership_name,
                'order_type': 'LIST',
                'order_id': order_id,
                'requested_vins': len(vin_list),
                'found_vehicles': len(vehicles),
                'missing_vins': len(vin_list) - len(vehicles),
                'processed_vins': vin_list,  # Include processed VINs for order number tracking
                'qr_codes_generated': len(qr_paths),
                'qr_folder': str(qr_folder),
                'csv_file': csv_path,
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Error processing list order for {dealership_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'dealership': dealership_name
            }
    
    def _create_order_record(self, dealership_name: str, order_type: str, 
                           vehicle_count: int, qr_count: int, csv_path: str) -> int:
        """Create order processing record in database"""
        try:
            result = db_manager.execute_query("""
                INSERT INTO order_processing_jobs 
                (dealership_name, job_type, vehicle_count, qr_count, export_file, status, created_at)
                VALUES (%s, %s, %s, %s, %s, 'completed', CURRENT_TIMESTAMP)
                RETURNING job_id
            """, (dealership_name, order_type, vehicle_count, qr_count, csv_path))
            
            return result[0]['job_id'] if result else None
            
        except Exception as e:
            logger.error(f"Error creating order record: {e}")
            return None
    
    def get_todays_cao_schedule(self) -> List[Dict]:
        """Get today's CAO schedule"""
        day_name = datetime.now().strftime('%A')
        return self.order_schedule.get(day_name, {}).get('CAO', [])
    
    def process_daily_cao_orders(self):
        """Process all CAO orders for today"""
        logger.info("="*80)
        logger.info("[DAILY CAO] Processing today's CAO orders")
        logger.info("="*80)
        
        cao_orders = self.get_todays_cao_schedule()
        logger.info(f"[DAILY CAO] {len(cao_orders)} CAO orders scheduled for today")
        
        results = []
        for order in cao_orders:
            dealership_name = order['name']
            
            # Determine vehicle types from dealership name
            vehicle_types = []
            if 'New' in dealership_name:
                vehicle_types.append('new')
            if 'Used' in dealership_name or 'Pre-Owned' in dealership_name:
                vehicle_types.extend(['used', 'po'])
            if 'Certified' in dealership_name:
                vehicle_types.append('cpo')
            
            # Default to all types if not specified
            if not vehicle_types:
                vehicle_types = ['new', 'cpo', 'used']
            
            result = self.process_cao_order(dealership_name, vehicle_types)
            results.append(result)
        
        # Summary
        successful = sum(1 for r in results if r['success'])
        logger.info(f"[DAILY CAO] Completed: {successful}/{len(results)} orders processed successfully")
        
        return results
    
    def schedule_daily_tasks(self):
        """Schedule daily automated tasks"""
        # Schedule 4AM daily scrape
        schedule.every().day.at("04:00").do(self.run_daily_scrape)
        
        # Schedule CAO processing at 8AM (after scrape completes)
        schedule.every().day.at("08:00").do(self.process_daily_cao_orders)
        
        logger.info("[SCHEDULER] Daily tasks scheduled:")
        logger.info("  - 4:00 AM: Daily scrape of all dealerships")
        logger.info("  - 8:00 AM: Process daily CAO orders")
        
    def run_scheduler(self):
        """Run the scheduler loop"""
        logger.info("[SCHEDULER] Starting order processing scheduler...")
        self.schedule_daily_tasks()
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def main():
    """Main entry point"""
    workflow = OrderProcessingWorkflow()
    
    # For testing, run a sample order
    logger.info("Testing order processing workflow...")
    
    # Test CAO order
    result = workflow.process_cao_order('Columbia Honda', ['used'])
    print(json.dumps(result, indent=2))
    
    # To run the scheduler:
    # workflow.run_scheduler()

if __name__ == "__main__":
    main()