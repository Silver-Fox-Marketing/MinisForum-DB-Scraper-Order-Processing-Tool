"""
Correct Order Processing Logic
Based on reference materials - focus on WHAT we're doing, not HOW
"""

import os
import sys
import json
import logging
import csv
import qrcode
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from PIL import Image

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
from database_connection import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CorrectOrderProcessor:
    """Order processing that matches our exact reference logic"""
    
    def __init__(self):
        # Use absolute path to main project orders folder
        project_root = Path(__file__).parent.parent
        self.output_base = project_root / "orders"
        self.output_base.mkdir(exist_ok=True)
        
        # Map dealership config names to actual data location names
        # Map dealership config names to actual data location names (for CAO processing)
        self.dealership_name_mapping = {
            'BMW West St. Louis': 'BMW of West St Louis',
            'BMW of West St. Louis': 'BMW of West St Louis',  # Config has period, CSV doesn't
            'CDJR of Columbia': 'Joe Machens Chrysler Dodge Jeep Ram',  # CDJR of Columbia is the new name
            'Columbia Honda': 'Columbia Honda',
            'Dave Sinclair Lincoln South': 'Dave Sinclair Lincoln',
            'Glendale CDJR': 'Glendale Chrysler Jeep Dodge Ram',  # Map config name to CSV name
            'HW Kia': 'HW Kia of West County',  # Map config name to CSV name
            'KIA of Columbia': 'Kia of Columbia',
            'Mini of St. Louis': 'MINI OF ST. LOUIS',
            'Rusty Drewing Chevy BGMC': 'Rusty Drewing Chevrolet Buick GMC',
            'South County DCJR': 'South County Dodge Chrysler Jeep RAM',  # Map config name TO CSV name
            'Weber Chevrolet': 'Weber Creve Coeur',
        }
        
        # Reverse mapping for VIN history lookups
        self.vin_history_name_variations = {
            'Dave Sinclair Lincoln South': ['Dave Sinclair Lincoln South', 'Dave Sinclair Lincoln'],
            'Dave Sinclair Lincoln': ['Dave Sinclair Lincoln South', 'Dave Sinclair Lincoln'],
            'BMW of West St. Louis': ['BMW of West St. Louis'],
            'Columbia Honda': ['Columbia Honda'],
            'Bommarito West County PO': ['Bommarito West County PO'],
            'Bommarito Cadillac': ['Bommarito Cadillac'],
            'South County DCJR': ['South County DCJR', 'South County Dodge Chrysler Jeep RAM'],
            'South County Dodge Chrysler Jeep RAM': ['South County DCJR', 'South County Dodge Chrysler Jeep RAM'],
            'Glendale CDJR': ['Glendale CDJR', 'Glendale Chrysler Jeep Dodge Ram'],
            'Glendale Chrysler Jeep Dodge Ram': ['Glendale CDJR', 'Glendale Chrysler Jeep Dodge Ram']
        }
    
    def _get_dealership_vin_log_table(self, dealership_name: str) -> str:
        """
        Generate the correct dealership-specific VIN log table name.
        
        Args:
            dealership_name: The dealership name from dealership_configs
            
        Returns:
            The PostgreSQL table name for this dealership's VIN log
        """
        # CRITICAL FIX: Handle special cases where table names don't follow the standard pattern
        # After standardization, we should use the standard pattern for all dealerships
        vin_log_table_overrides = {
            # Removed HW Kia override - now uses standard hw_kia_vin_log
            # All dealerships now follow standard pattern: dealership_name_vin_log
        }
        
        # Check for override first
        if dealership_name in vin_log_table_overrides:
            table_name = vin_log_table_overrides[dealership_name]
            logger.info(f"[VIN LOG] Using override mapping: '{dealership_name}' -> '{table_name}'")
            return table_name
        
        # Create slug from dealership name using standard pattern
        slug = dealership_name.lower()
        slug = slug.replace(' ', '_')
        slug = slug.replace('&', 'and')
        slug = slug.replace('.', '')
        slug = slug.replace(',', '')
        slug = slug.replace("'", '')  # Remove apostrophes (O'Fallon -> OFallon)
        slug = slug.replace('-', '_')
        slug = slug.replace('/', '_')
        slug = slug.replace('__', '_')
        
        table_name = f'{slug}_vin_log'
        logger.info(f"[VIN LOG] Standard mapping: '{dealership_name}' -> '{table_name}'")
        return table_name
    
    def process_cao_order(self, dealership_name: str, template_type: str = "shortcut_pack", skip_vin_logging: bool = False) -> Dict[str, Any]:
        """
        Process CAO (Comparative Analysis Order)
        
        Steps from reference:
        1. Get filtered vehicles based on dealership requirements
        2. Compare VIN lists to find NEW vehicles on lot
        3. Generate QR codes for new vehicles
        4. Output QR file paths + Adobe CSV
        """
        
        logger.info(f"[CAO] Processing {dealership_name} - {template_type}")
        
        try:
            # Step 1: Get all current vehicles for dealership
            current_vehicles = self._get_dealership_vehicles(dealership_name)
            if not current_vehicles:
                return {'success': False, 'error': 'No vehicles found'}
            
            logger.info(f"[CAO DEBUG] Found {len(current_vehicles)} total vehicles for {dealership_name}")
            
            # Step 2: Compare VIN lists to find NEW vehicles (Enhanced Logic)
            current_vins = [v['vin'] for v in current_vehicles]
            logger.info(f"[CAO DEBUG] Current VINs: {current_vins[:5]}..." if len(current_vins) > 5 else f"[CAO DEBUG] Current VINs: {current_vins}")
            
            new_vins = self._find_new_vehicles_enhanced(dealership_name, current_vins, current_vehicles)
            logger.info(f"[CAO DEBUG] NEW VINs after comparison: {new_vins[:5]}..." if len(new_vins) > 5 else f"[CAO DEBUG] NEW VINs after comparison: {new_vins}")
            
            # Filter to only NEW vehicles
            new_vehicles = [v for v in current_vehicles if v['vin'] in new_vins]
            logger.info(f"[CAO DEBUG] Found {len(new_vehicles)} NEW vehicles needing graphics for {dealership_name}")
            
            # CRITICAL FIX: Apply dealership filtering to CAO orders (same as LIST orders)
            filtered_vehicles = self._apply_dealership_filters(new_vehicles, dealership_name)
            logger.info(f"[CAO DEBUG] After dealership filtering: {len(filtered_vehicles)} vehicles match dealership criteria")
            
            if not filtered_vehicles:
                return {
                    'success': False, 
                    'error': f'No vehicles match dealership filtering criteria. Found {len(new_vehicles)} new vehicles but none match the configured filters (new/used/certified).',
                    'new_vehicles': 0,
                    'vehicles_filtered_out': len(new_vehicles)
                }
                
            # Use filtered vehicles for the rest of the process
            new_vehicles = filtered_vehicles
            
            # Step 3: Create output folders
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            order_folder = self.output_base / dealership_name.replace(' ', '_') / timestamp
            qr_folder = order_folder / "qr_codes"
            
            order_folder.mkdir(parents=True, exist_ok=True)
            qr_folder.mkdir(exist_ok=True)
            
            # Step 4: Generate QR codes for vehicle URLs
            qr_paths = self._generate_qr_codes(new_vehicles, dealership_name, qr_folder)
            
            # Step 5: Special handling for CDJR of Columbia - dual CSV output
            csv_files = {}
            if dealership_name.upper() in ['CDJR OF COLUMBIA', 'CDJR COLUMBIA']:
                csv_files = self._process_cdjr_columbia_dual_output(new_vehicles, dealership_name, template_type, order_folder, qr_paths)
                csv_path = csv_files.get('used_csv') or csv_files.get('new_csv')  # Primary file for legacy compatibility
            else:
                # Step 5: Generate Adobe CSV in EXACT format we need (normal processing)
                csv_path = self._generate_adobe_csv(new_vehicles, dealership_name, template_type, order_folder, qr_paths)
            
            # Step 5.5: Generate billing sheet CSV automatically after QR codes
            billing_csv_path = self._generate_billing_sheet_csv(new_vehicles, dealership_name, order_folder, timestamp)
            
            # Step 6: CRITICAL - Log processed vehicle VINs to history database (unless testing)
            if skip_vin_logging:
                logger.info("Skipping VIN logging - test data processing")
                vin_logging_result = {'success': True, 'vins_logged': 0, 'duplicates_skipped': 0, 'errors': []}
            else:
                vin_logging_result = self._log_processed_vins_to_history(new_vehicles, dealership_name, 'CAO_ORDER')
            
            # Build return result
            result = {
                'success': True,
                'dealership': dealership_name,
                'template_type': template_type,
                'total_vehicles': len(current_vehicles),
                'new_vehicles': len(new_vehicles),
                'vehicle_count': len(new_vehicles),
                'qr_codes_generated': len(qr_paths),
                'qr_folder': str(qr_folder),
                'csv_file': str(csv_path),
                'export_file': str(csv_path),
                'download_csv': f"/download_csv/{csv_path.name}",
                'billing_csv_file': str(billing_csv_path),
                'download_billing_csv': f"/download_csv/{billing_csv_path.name}",
                'timestamp': timestamp,
                'vins_logged_to_history': vin_logging_result['vins_logged'],
                'duplicate_vins_skipped': vin_logging_result['duplicates_skipped'],
                'vin_logging_success': vin_logging_result['success']
            }
            
            # Add CDJR Columbia dual CSV information
            if csv_files:
                result['cdjr_dual_output'] = True
                result['csv_files'] = csv_files
                if 'used_csv' in csv_files:
                    result['used_csv_file'] = csv_files['used_csv']
                    result['download_used_csv'] = f"/download_csv/{Path(csv_files['used_csv']).name}"
                if 'new_csv' in csv_files:
                    result['new_csv_file'] = csv_files['new_csv']
                    result['download_new_csv'] = f"/download_csv/{Path(csv_files['new_csv']).name}"
                    
            return result
            
        except Exception as e:
            logger.error(f"Error processing CAO order: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_list_order(self, dealership_name: str, vin_list: List[str], template_type: str = "shortcut_pack", skip_vin_logging: bool = False) -> Dict[str, Any]:
        """
        Process List Order (transcribed VINs from installers)
        """
        
        logger.info(f"[LIST] Processing {dealership_name} with {len(vin_list)} VINs")
        
        try:
            # LIST orders: Create vehicle records from user-provided VINs
            # No inventory lookup or filtering needed - process whatever VINs user provides
            vehicles = []
            for vin in vin_list:
                # Try to get vehicle data from inventory first
                vehicle_data = db_manager.execute_query("""
                    SELECT * FROM raw_vehicle_data
                    WHERE vin = %s AND location = %s
                    ORDER BY import_timestamp DESC
                    LIMIT 1
                """, (vin, dealership_name))
                
                if vehicle_data:
                    # Use existing vehicle data if found
                    vehicles.append(vehicle_data[0])
                else:
                    # Create placeholder vehicle record for user-provided VIN
                    placeholder_vehicle = {
                        'vin': vin,
                        'year': 'Unknown',
                        'make': 'Unknown', 
                        'model': 'Unknown',
                        'trim': 'Unknown',
                        'stock_number': f'LIST_{vin[-6:]}',  # Use last 6 chars of VIN
                        'type': 'Used',  # Default to Used for LIST orders
                        'mileage': 0,
                        'price': 0,
                        'dealership': dealership_name,
                        'location': dealership_name
                    }
                    vehicles.append(placeholder_vehicle)
                    logger.info(f"Created placeholder record for LIST VIN: {vin}")
            
            logger.info(f"Created {len(vehicles)} vehicle records for LIST processing")
            
            # LIST orders: Skip dealership filtering - process all provided VINs
            filtered_vehicles = vehicles  # No filtering for LIST orders
            logger.info(f"LIST processing: Using all {len(filtered_vehicles)} provided VINs")
            
            if not filtered_vehicles:
                return {
                    'success': False, 
                    'error': f'No VINs provided for LIST processing.'
                }
            
            # Create output folders
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            order_folder = self.output_base / dealership_name.replace(' ', '_') / timestamp
            qr_folder = order_folder / "qr_codes"
            
            order_folder.mkdir(parents=True, exist_ok=True)
            qr_folder.mkdir(exist_ok=True)
            
            # Generate QR codes - use filtered vehicles
            qr_paths = self._generate_qr_codes(filtered_vehicles, dealership_name, qr_folder)
            
            # Special handling for CDJR of Columbia - dual CSV output
            csv_files = {}
            if dealership_name.upper() in ['CDJR OF COLUMBIA', 'CDJR COLUMBIA']:
                csv_files = self._process_cdjr_columbia_dual_output(filtered_vehicles, dealership_name, template_type, order_folder, qr_paths)
                csv_path = csv_files.get('used_csv') or csv_files.get('new_csv')  # Primary file for legacy compatibility
            else:
                # Generate Adobe CSV - use filtered vehicles (normal processing)
                csv_path = self._generate_adobe_csv(filtered_vehicles, dealership_name, template_type, order_folder, qr_paths)
            
            # Generate billing sheet CSV automatically after QR codes
            billing_csv_path = self._generate_billing_sheet_csv(filtered_vehicles, dealership_name, order_folder, timestamp)
            
            # CRITICAL: Log processed vehicle VINs to history database for future order accuracy - use filtered vehicles (unless testing)
            if skip_vin_logging:
                logger.info("Skipping VIN logging - test data processing")
                vin_logging_result = {'success': True, 'vins_logged': 0, 'duplicates_skipped': 0, 'errors': []}
            else:
                vin_logging_result = self._log_processed_vins_to_history(filtered_vehicles, dealership_name, 'LIST_ORDER')
            
            # Build return result
            result = {
                'success': True,
                'dealership': dealership_name,
                'template_type': template_type,
                'vehicles_requested': len(vehicles),
                'vehicles_processed': len(filtered_vehicles),
                'vehicle_count': len(filtered_vehicles),
                'vehicles_filtered_out': len(vehicles) - len(filtered_vehicles),
                'qr_codes_generated': len(qr_paths),
                'qr_folder': str(qr_folder),
                'csv_file': str(csv_path),
                'export_file': str(csv_path),
                'download_csv': f"/download_csv/{csv_path.name}",
                'billing_csv_file': str(billing_csv_path),
                'download_billing_csv': f"/download_csv/{billing_csv_path.name}",
                'timestamp': timestamp,
                'vins_logged_to_history': vin_logging_result['vins_logged'],
                'duplicate_vins_skipped': vin_logging_result['duplicates_skipped'],
                'vin_logging_success': vin_logging_result['success']
            }
            
            # Add CDJR Columbia dual CSV information
            if csv_files:
                result['cdjr_dual_output'] = True
                result['csv_files'] = csv_files
                if 'used_csv' in csv_files:
                    result['used_csv_file'] = csv_files['used_csv']
                    result['download_used_csv'] = f"/download_csv/{Path(csv_files['used_csv']).name}"
                if 'new_csv' in csv_files:
                    result['new_csv_file'] = csv_files['new_csv']
                    result['download_new_csv'] = f"/download_csv/{Path(csv_files['new_csv']).name}"
                    
            return result
            
        except Exception as e:
            logger.error(f"Error processing list order: {e}")
            return {'success': False, 'error': str(e)}
    
    def _log_processed_vins_to_history(self, vehicles: List[Dict], dealership_name: str, order_type: str) -> Dict[str, Any]:
        """
        Log VINs of vehicles that were actually processed in the order output.
        This is CRITICAL for preventing duplicate processing in future orders.
        
        Args:
            vehicles: List of vehicle dictionaries that were processed
            dealership_name: Name of the dealership
            order_type: 'CAO_ORDER' or 'LIST_ORDER'
        """
        try:
            vins_logged = 0
            duplicates_skipped = 0
            errors = []
            
            logger.info(f"Logging {len(vehicles)} processed vehicle VINs to history for {dealership_name} ({order_type})")
            
            for vehicle in vehicles:
                vin = vehicle.get('vin')
                if not vin:
                    continue
                    
                vin = vin.strip().upper()
                
                try:
                    # Get dealership-specific VIN log table name
                    vin_log_table = self._get_dealership_vin_log_table(dealership_name)
                    
                    # Check if VIN already exists for this dealership (prevent duplicates)
                    check_query = f"""
                        SELECT id FROM {vin_log_table} 
                        WHERE vin = %s AND order_date = CURRENT_DATE
                    """
                    existing = db_manager.execute_query(check_query, (vin,))
                    
                    if existing:
                        duplicates_skipped += 1
                        logger.debug(f"VIN {vin} already logged for {dealership_name} today, skipping")
                        continue
                    
                    # Get vehicle type for enhanced tracking
                    vehicle_type = self._normalize_vehicle_type(vehicle.get('type', 'unknown'))
                    
                    # Insert processed VIN into dealership-specific VIN log table
                    insert_query = f"""
                        INSERT INTO {vin_log_table} (vin, vehicle_type, order_date)
                        VALUES (%s, %s, CURRENT_DATE)
                        ON CONFLICT (vin, order_date) DO UPDATE SET
                        vehicle_type = EXCLUDED.vehicle_type,
                        created_at = CURRENT_TIMESTAMP
                    """
                    db_manager.execute_query(insert_query, (vin, vehicle_type))
                    
                    vins_logged += 1
                    logger.info(f"Successfully logged processed VIN {vin} ({vehicle_type}) from {order_type} for {dealership_name}")
                    
                except Exception as vin_error:
                    error_msg = f"Failed to log VIN {vin}: {str(vin_error)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            result = {
                'success': len(errors) == 0,
                'vins_logged': vins_logged,
                'duplicates_skipped': duplicates_skipped,
                'errors': errors,
                'total_vehicles': len(vehicles)
            }
            
            if errors:
                result['error'] = f"Failed to log {len(errors)} VINs"
            
            logger.info(f"VIN logging complete: {vins_logged} logged, {duplicates_skipped} duplicates skipped, {len(errors)} errors")
            
            return result
            
        except Exception as e:
            logger.error(f"Critical error logging processed VINs: {e}")
            return {
                'success': False,
                'error': f"Critical VIN logging failure: {str(e)}",
                'vins_logged': 0,
                'duplicates_skipped': 0,
                'errors': [str(e)]
            }
    
    def _get_dealership_vehicles(self, dealership_name: str) -> List[Dict]:
        """Get all vehicles for dealership with filtering"""
        
        # Map dealership config name to actual data location name
        actual_location_name = self.dealership_name_mapping.get(dealership_name, dealership_name)
        logger.info(f"[CAO DEBUG] Mapping {dealership_name} -> {actual_location_name}")
        
        # Get dealership config - CACHE BUSTING: Force fresh query with timestamp
        config = db_manager.execute_query("""
            SELECT filtering_rules FROM dealership_configs 
            WHERE name = %s AND is_active = true
            ORDER BY updated_at DESC NULLS LAST
        """, (dealership_name,))
        
        filtering_rules = {}
        if config:
            filtering_rules = config[0]['filtering_rules']
            if isinstance(filtering_rules, str):
                filtering_rules = json.loads(filtering_rules)
            logger.info(f"[CACHE DEBUG] Loaded fresh config for {dealership_name}: {json.dumps(filtering_rules, indent=2)}")
        
        # Log the filtering rules being applied
        logger.info(f"[CAO DEBUG] Applying filtering rules for {dealership_name}: {filtering_rules}")
        
        # Build query with filters - use actual location name for data lookup
        # CRITICAL: Only process vehicles from the ACTIVE scraper import that are physically on the lot
        # Use normalized_vehicle_data for proper vehicle type filtering (po, cpo, new instead of raw values)
        # ENHANCEMENT: Include raw_status for UI review stage
        query = """
            SELECT nvd.*, rvd.status as raw_status FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE nvd.location = %s 
            AND nvd.on_lot_status IN ('onlot', 'on lot')
            AND si.status = 'active'
        """
        params = [actual_location_name]
        
        # Apply vehicle type filter - NORMALIZED DATA APPROACH
        vehicle_types = filtering_rules.get('allowed_vehicle_types', filtering_rules.get('vehicle_types', ['new', 'used']))
        if vehicle_types and 'all' not in vehicle_types:
            # Build conditions for normalized vehicle_condition values
            allowed_conditions = []
            for vtype in vehicle_types:
                if vtype == 'new':
                    allowed_conditions.append('new')
                elif vtype == 'used':
                    # UMBRELLA TERM: "used" includes both po (Pre-Owned) AND cpo (Certified Pre-Owned)
                    allowed_conditions.extend(['po', 'cpo'])
                elif vtype in ['certified', 'cpo']:
                    allowed_conditions.append('cpo')
                elif vtype in ['po', 'pre-owned']:
                    allowed_conditions.append('po')
            
            if allowed_conditions:
                # Remove duplicates
                allowed_conditions = list(set(allowed_conditions))
                # Create IN clause for exact matches on normalized values
                placeholders = ', '.join(['%s'] * len(allowed_conditions))
                query += f" AND nvd.vehicle_condition IN ({placeholders})"
                params.extend(allowed_conditions)
        
        # Apply year filter
        min_year = filtering_rules.get('min_year')
        if min_year:
            query += " AND year >= %s"
            params.append(min_year)
        
        # Apply require_status filter (highest priority - checks the 'status' column)
        require_statuses = filtering_rules.get('require_status')
        if require_statuses:
            if isinstance(require_statuses, list):
                status_conditions = []
                for status in require_statuses:
                    status_conditions.append("nvd.status ILIKE %s")
                    params.append(f"%{status}%")
                query += f" AND ({' OR '.join(status_conditions)})"
            else:
                query += " AND nvd.status ILIKE %s"
                params.append(f"%{require_statuses}%")
        
        # Apply exclude_status filter (checks the 'status' column for raw status values)
        exclude_statuses = filtering_rules.get('exclude_status')
        if exclude_statuses:
            if isinstance(exclude_statuses, list):
                for status in exclude_statuses:
                    # Use ILIKE for case-insensitive matching against the 'status' column
                    query += " AND nvd.status NOT ILIKE %s"
                    params.append(f"%{status}%")
            else:
                query += " AND nvd.status NOT ILIKE %s"
                params.append(f"%{exclude_statuses}%")
        
        # Apply stock number filter (exclude missing and asterisk placeholders)
        if filtering_rules.get('exclude_missing_stock', True):
            query += " AND nvd.stock IS NOT NULL AND nvd.stock != %s AND nvd.stock != %s"
            params.extend(['', '*'])
            
        # Apply price filter - Fixed to work with numeric price fields
        if filtering_rules.get('exclude_missing_price', False):
            # Enhanced price filtering: exclude NULL, 0, negative values
            query += " AND nvd.price IS NOT NULL AND nvd.price > 0"
            # Also check raw price data for valid numeric values only
            query += " AND rvd.price IS NOT NULL AND rvd.price > 0"
        
        query += " ORDER BY created_at DESC"
        
        logger.info(f"[CAO DEBUG] Final Query: {query}")
        logger.info(f"[CAO DEBUG] Query Params: {params}")
        
        try:
            # Ensure params is properly formatted as tuple for database query
            query_params = tuple(params) if params else None
            logger.info(f"[CAO DEBUG] Final query params as tuple: {query_params}")
            result = db_manager.execute_query(query, query_params)
            logger.info(f"[CAO DEBUG] Query returned {len(result)} vehicles for {dealership_name}")
            
            if result:
                logger.info(f"[CAO DEBUG] Sample VINs from query: {[v['vin'] for v in result[:5]]}")
            
            return result
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            logger.error("Attempting simplified query without problematic constraints...")
            # Try a simplified query without filtering if the main query fails
            # CRITICAL: Still only process vehicles from ACTIVE import that are on the lot
            # Use normalized_vehicle_data for consistent data structure
            # IMPORTANT: Include VIN log comparison even in simplified query
            vin_log_table = self._get_dealership_vin_log_table(dealership_name)

            # Apply dealership-specific filtering to simplified query
            simplified_query = f"""
                SELECT nvd.*, rvd.status as raw_status FROM normalized_vehicle_data nvd
                JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                JOIN scraper_imports si ON rvd.import_id = si.import_id
                WHERE nvd.location = %s
                AND nvd.on_lot_status IN ('onlot', 'on lot')
                AND si.status = 'active'
                AND nvd.vin NOT IN (SELECT vin FROM {vin_log_table} WHERE vin IS NOT NULL)
            """

            # Add critical filters based on dealership configuration
            if filtering_rules.get('exclude_missing_price', False):
                simplified_query += " AND nvd.price > 0"

            if filtering_rules.get('exclude_missing_stock_number', True):
                simplified_query += " AND nvd.stock IS NOT NULL AND nvd.stock != '' AND nvd.stock != '*'"

            # Add vehicle type filtering for simplified query
            vehicle_types = filtering_rules.get('allowed_vehicle_types', filtering_rules.get('vehicle_types', ['new', 'used']))
            if vehicle_types and 'all' not in vehicle_types:
                allowed_conditions = []
                for vtype in vehicle_types:
                    if vtype == 'new':
                        allowed_conditions.append('new')
                    elif vtype == 'used':
                        allowed_conditions.extend(['po', 'cpo'])
                    elif vtype in ['certified', 'cpo']:
                        allowed_conditions.append('cpo')
                    elif vtype in ['po', 'pre-owned']:
                        allowed_conditions.append('po')

                if allowed_conditions:
                    allowed_conditions = list(set(allowed_conditions))
                    placeholders = ', '.join([f"'{cond}'" for cond in allowed_conditions])
                    simplified_query += f" AND nvd.vehicle_condition IN ({placeholders})"

            # Add status exclusions for simplified query
            exclude_statuses = filtering_rules.get('exclude_status')
            if exclude_statuses:
                for status in exclude_statuses:
                    simplified_query += f" AND nvd.status NOT ILIKE '%{status}%'"

            simplified_query += " ORDER BY nvd.updated_at DESC"
            try:
                result = db_manager.execute_query(simplified_query, (actual_location_name,))
                logger.info(f"Simplified query returned {len(result)} vehicles")
                return result
            except Exception as e2:
                logger.error(f"Simplified query also failed: {e2}")
                # Only as a last resort, return empty list rather than arbitrary 100 vehicles
                logger.error("Unable to retrieve vehicle data - returning empty list")
                return []
    
    def _apply_dealership_filters(self, vehicles: List[Dict], dealership_name: str) -> List[Dict]:
        """
        Apply dealership-specific filters to a list of vehicles.
        Used for LIST orders to ensure they follow same filtering rules as CAO orders.
        """
        # Get dealership config - CACHE BUSTING: Force fresh query with timestamp
        config = db_manager.execute_query("""
            SELECT filtering_rules FROM dealership_configs 
            WHERE name = %s AND is_active = true
            ORDER BY updated_at DESC NULLS LAST
        """, (dealership_name,))
        
        filtering_rules = {}
        if config:
            filtering_rules = config[0]['filtering_rules']
            if isinstance(filtering_rules, str):
                filtering_rules = json.loads(filtering_rules)
            logger.info(f"[CACHE DEBUG] Loaded fresh config for {dealership_name}: {json.dumps(filtering_rules, indent=2)}")
        
        # Log the filtering rules being applied
        logger.info(f"Applying filtering rules for {dealership_name}: {filtering_rules}")
        
        # Get allowed vehicle types using the new 'allowed_vehicle_types' field
        vehicle_types = filtering_rules.get('allowed_vehicle_types', filtering_rules.get('vehicle_types', ['new', 'used']))
        
        # Filter vehicles based on type
        filtered_vehicles = []
        for vehicle in vehicles:
            # CRITICAL FIX: Use 'vehicle_condition' field from normalized data, not 'type'
            vehicle_type = vehicle.get('vehicle_condition', '').lower()
            
            # Check if vehicle type matches allowed types
            type_matches = False
            if 'all' in vehicle_types:
                type_matches = True
            else:
                for allowed_type in vehicle_types:
                    if allowed_type == 'used':
                        # CRITICAL: "used" is UMBRELLA term for Pre-Owned AND Certified Pre-Owned
                        # Match normalized database values: "po" and "cpo"
                        if vehicle_type in ['po', 'cpo'] or any(keyword in vehicle_type for keyword in ['used', 'pre-owned', 'pre owned', 'certified', 'cpo']):
                            type_matches = True
                            break
                    elif allowed_type in ['certified', 'cpo']:
                        # Handle both 'certified' and 'cpo' config values  
                        # Match normalized database value: "cpo"
                        if vehicle_type == 'cpo' or any(keyword in vehicle_type for keyword in ['certified', 'cpo']):
                            type_matches = True
                            break
                    elif allowed_type in ['po', 'pre-owned']:
                        # Handle pre-owned variants
                        # Match normalized database value: "po"
                        if vehicle_type == 'po' or any(keyword in vehicle_type for keyword in ['pre-owned', 'pre owned']):
                            type_matches = True
                            break
                    elif allowed_type == 'new':
                        # Match normalized database value: "new"
                        if vehicle_type == 'new':
                            type_matches = True
                            break
                    elif allowed_type in vehicle_type:
                        type_matches = True
                        break
            
            if type_matches:
                # Apply additional filters
                # Year filter
                min_year = filtering_rules.get('min_year')
                if min_year and vehicle.get('year', 0) < min_year:
                    continue
                    
                # Price filter
                min_price = filtering_rules.get('min_price')
                max_price = filtering_rules.get('max_price')
                vehicle_price = vehicle.get('price', 0)
                
                if min_price and vehicle_price < min_price:
                    continue
                if max_price and vehicle_price > max_price:
                    continue
                
                # Days on lot filter (seasoning) - Updated to use standardized template structure
                days_on_lot_config = filtering_rules.get('days_on_lot', {})
                if days_on_lot_config:
                    min_days = days_on_lot_config.get('min', 0)
                    max_days = days_on_lot_config.get('max', 999)

                    date_in_stock = vehicle.get('date_in_stock')
                    created_at = vehicle.get('created_at')

                    logger.info(f"[DAYS_ON_LOT DEBUG] VIN {vehicle.get('vin')} - date_in_stock: {date_in_stock} (type: {type(date_in_stock)}), created_at: {created_at}")

                    # Determine which date to use for seasoning calculation
                    reference_date = None
                    date_source = None

                    if date_in_stock:
                        # Check if date_in_stock looks like a scrape date (today or yesterday)
                        if isinstance(date_in_stock, str):
                            try:
                                stock_date = datetime.strptime(date_in_stock, '%Y-%m-%d')
                                days_since_stock_date = (datetime.now() - stock_date).days

                                # If date_in_stock is very recent (0-2 days), it's likely a scrape date, use created_at instead
                                if days_since_stock_date <= 2 and created_at:
                                    reference_date = created_at
                                    date_source = "created_at (date_in_stock too recent)"
                                else:
                                    reference_date = stock_date
                                    date_source = "date_in_stock"
                            except ValueError:
                                # If date parsing fails, fall back to created_at
                                reference_date = created_at
                                date_source = "created_at (date_in_stock parse failed)"
                        elif hasattr(date_in_stock, 'days'):  # datetime.date object
                            days_since_stock_date = (datetime.now().date() - date_in_stock).days

                            # If date_in_stock is very recent (0-2 days), it's likely a scrape date, use created_at instead
                            if days_since_stock_date <= 2 and created_at:
                                reference_date = created_at
                                date_source = "created_at (date_in_stock too recent)"
                            else:
                                reference_date = date_in_stock
                                date_source = "date_in_stock"
                    else:
                        # No date_in_stock, use created_at
                        reference_date = created_at
                        date_source = "created_at (no date_in_stock)"

                    if reference_date:
                        # Calculate actual days on lot
                        if isinstance(reference_date, str):
                            try:
                                ref_date = datetime.strptime(reference_date, '%Y-%m-%d %H:%M:%S.%f')
                                actual_days_on_lot = (datetime.now() - ref_date).days
                            except ValueError:
                                try:
                                    ref_date = datetime.strptime(reference_date, '%Y-%m-%d')
                                    actual_days_on_lot = (datetime.now() - ref_date).days
                                except ValueError:
                                    logger.warning(f"[DAYS_ON_LOT] Could not parse reference date for VIN {vehicle.get('vin')}: {reference_date}")
                                    continue
                        elif hasattr(reference_date, 'days'):  # date object
                            actual_days_on_lot = (datetime.now().date() - reference_date).days
                        else:  # datetime object
                            actual_days_on_lot = (datetime.now() - reference_date).days

                        logger.info(f"[DAYS_ON_LOT] VIN {vehicle.get('vin')} - Using {date_source}, calculated {actual_days_on_lot} days on lot")

                        # Apply min/max days filter
                        if actual_days_on_lot < min_days:
                            logger.info(f"[DAYS_ON_LOT] Skipping VIN {vehicle.get('vin')} - only {actual_days_on_lot} days on lot (requires min {min_days})")
                            continue
                        if actual_days_on_lot > max_days:
                            logger.info(f"[DAYS_ON_LOT] Skipping VIN {vehicle.get('vin')} - {actual_days_on_lot} days on lot (exceeds max {max_days})")
                            continue

                        logger.info(f"[DAYS_ON_LOT] VIN {vehicle.get('vin')} passed filter - {actual_days_on_lot} days (min: {min_days}, max: {max_days})")
                    else:
                        logger.warning(f"[DAYS_ON_LOT] No usable date found for VIN {vehicle.get('vin')}, allowing through filter")

                # LEGACY SUPPORT: Fall back to old seasoning_days format for backwards compatibility
                elif 'seasoning_days' in filtering_rules:
                    seasoning_days = filtering_rules.get('seasoning_days', 0)
                    if seasoning_days > 0:
                        date_in_stock = vehicle.get('date_in_stock')
                        logger.info(f"[LEGACY SEASONING] VIN {vehicle.get('vin')} - using legacy seasoning_days: {seasoning_days}")
                        if date_in_stock:
                            if isinstance(date_in_stock, str):
                                try:
                                    stock_date = datetime.strptime(date_in_stock, '%Y-%m-%d')
                                    actual_days_on_lot = (datetime.now() - stock_date).days

                                    if actual_days_on_lot < seasoning_days:
                                        logger.info(f"[LEGACY SEASONING] Skipping VIN {vehicle.get('vin')} - only {actual_days_on_lot} days on lot (requires {seasoning_days})")
                                        continue
                                except ValueError:
                                    logger.warning(f"[LEGACY SEASONING] Could not parse date_in_stock for VIN {vehicle.get('vin')}: {date_in_stock}")
                            elif hasattr(date_in_stock, 'days'):
                                actual_days_on_lot = (datetime.now() - date_in_stock).days
                                if actual_days_on_lot < seasoning_days:
                                    logger.info(f"[LEGACY SEASONING] Skipping VIN {vehicle.get('vin')} - only {actual_days_on_lot} days on lot (requires {seasoning_days})")
                                    continue
                
                # Brand filter (e.g., Pappas Toyota only wants Toyota vehicles)
                required_brands = filtering_rules.get('required_brands', [])
                if required_brands:
                    vehicle_make = vehicle.get('make', '').lower()
                    # Check if vehicle make matches any required brands
                    brand_matches = any(brand.lower() in vehicle_make or vehicle_make in brand.lower()
                                      for brand in required_brands)
                    if not brand_matches:
                        logger.info(f"[BRAND FILTER] Skipping VIN {vehicle.get('vin')} - make '{vehicle.get('make')}' not in required brands {required_brands}")
                        continue

                # If all filters pass, include the vehicle
                filtered_vehicles.append(vehicle)
        
        return filtered_vehicles
    
    def _find_new_vehicles(self, dealership_name: str, current_vins: List[str]) -> List[str]:
        """Compare with last order to find NEW vehicles"""
        
        # Map dealership config name to actual data location name
        actual_location_name = self.dealership_name_mapping.get(dealership_name, dealership_name)
        
        # Get previous VINs from dealership-specific VIN log table
        # Format: dealership_name_vin_log (matching our working solution)
        table_name = dealership_name.lower().replace(' ', '_').replace('.', '').replace("'", '') + '_vin_log'
        
        try:
            previous_vins = db_manager.execute_query(f"""
                SELECT DISTINCT vin FROM {table_name}
            """)
        except Exception as e:
            logger.warning(f"Could not access {table_name}, falling back to general vin_history: {e}")
            # Fallback to old system for compatibility
            previous_vins = db_manager.execute_query("""
                SELECT DISTINCT vin FROM vin_history
                WHERE dealership_name IN (%s, %s)
                AND order_date > CURRENT_DATE - INTERVAL '7 days'
            """, (dealership_name, actual_location_name))
        
        previous_vin_set = {row['vin'] for row in previous_vins}
        current_vin_set = set(current_vins)
        
        # NEW vehicles = in current but not in previous
        new_vins = list(current_vin_set - previous_vin_set)
        
        logger.info(f"Previous order had {len(previous_vin_set)} VINs, current has {len(current_vin_set)}, {len(new_vins)} are NEW")
        
        return new_vins
    
    def _generate_qr_codes(self, vehicles: List[Dict], dealership_name: str, output_folder: Path) -> List[str]:
        """Generate QR codes for vehicle-specific information"""
        
        qr_paths = []
        clean_name = dealership_name.replace(' ', '_')
        
        for idx, vehicle in enumerate(vehicles, 1):
            try:
                # Get vehicle details
                vin = vehicle.get('vin', '')
                stock = vehicle.get('stock', '')
                year = vehicle.get('year', '')
                make = vehicle.get('make', '')
                model = vehicle.get('model', '')
                url = vehicle.get('vehicle_url', '')
                
                # Determine the best QR content to use
                qr_content = self._get_vehicle_qr_content(vehicle, dealership_name)
                
                if not qr_content:
                    logger.warning(f"No valid QR content for vehicle {vin} - {stock}, skipping")
                    continue
                
                # Generate QR code locally with exact API specifications
                qr = qrcode.QRCode(
                    version=1,  # Automatically determines version based on data
                    error_correction=qrcode.constants.ERROR_CORRECT_L,  # Same as API default
                    box_size=10,  # Will be resized to exact 388x388
                    border=0,  # No border to match API output
                )
                qr.add_data(qr_content)
                qr.make(fit=True)

                # Create QR image with exact API color specification: #323232 (50, 50, 50 in RGB)
                img = qr.make_image(fill_color=(50, 50, 50), back_color="white")

                # Resize to exact 388x388 pixels to match API output
                img = img.resize((388, 388), Image.Resampling.LANCZOS)

                # Save with exact naming convention from current system
                filename = f"{clean_name}_QR_Code_{idx}.png"
                filepath = output_folder / filename
                img.save(filepath, format='PNG')
                
                qr_paths.append(str(filepath))
                
                logger.debug(f"Generated QR for {year} {make} {model} ({stock}): {qr_content}")
                
            except Exception as e:
                logger.error(f"Error generating QR for {vehicle.get('vin')}: {e}")
        
        logger.info(f"Generated {len(qr_paths)} QR codes")
        return qr_paths
    
    def _get_vehicle_qr_content(self, vehicle: Dict, dealership_name: str) -> str:
        """
        Determine the best QR content for a vehicle.
        Priority: Vehicle-specific URL > Stock-based URL > VIN > Stock number
        """
        
        vin = vehicle.get('vin', '').strip()
        stock = vehicle.get('stock', '').strip()
        url = vehicle.get('vehicle_url', '').strip()
        year = vehicle.get('year', '')
        make = vehicle.get('make', '')
        model = vehicle.get('model', '')
        
        # Priority 1: Check if URL is vehicle-specific (contains VIN, stock, or inventory path)
        if url and self._is_vehicle_specific_url(url, vin, stock):
            logger.debug(f"Using vehicle-specific URL: {url}")
            return url
        
        # Priority 2: Try to construct a vehicle-specific URL based on dealership patterns
        specific_url = self._construct_vehicle_url(dealership_name, vehicle)
        if specific_url:
            logger.debug(f"Constructed vehicle URL: {specific_url}")
            return specific_url
        
        # Priority 3: Use VIN if available (most unique identifier)
        if vin:
            logger.debug(f"Using VIN as QR content: {vin}")
            return vin
            
        # Priority 4: Use stock number if available
        if stock:
            logger.debug(f"Using stock number as QR content: {stock}")
            return stock
            
        # Priority 5: Fallback to vehicle description
        if year and make and model:
            description = f"{year} {make} {model}"
            logger.debug(f"Using vehicle description as QR content: {description}")
            return description
            
        logger.warning("No suitable QR content found for vehicle")
        return ""
    
    def _is_vehicle_specific_url(self, url: str, vin: str = "", stock: str = "") -> bool:
        """Check if a URL appears to be vehicle-specific rather than a generic homepage"""
        
        url_lower = url.lower()
        
        # Check for vehicle-specific URL patterns
        specific_patterns = [
            '/inventory/',
            '/vehicle/',
            '/detail/',
            '/vdp/',  # Vehicle Detail Page
            '/listing/',
            'vin=',
            'stock=',
            'id='
        ]
        
        # Check if URL contains specific patterns
        for pattern in specific_patterns:
            if pattern in url_lower:
                return True
        
        # Check if URL contains the actual VIN or stock number
        if vin and vin.lower() in url_lower:
            return True
        if stock and stock.lower() in url_lower:
            return True
            
        # If URL is just a domain or very short, it's likely generic
        if len(url.replace('https://', '').replace('http://', '').replace('www.', '')) < 20:
            return False
            
        return False
    
    def _construct_vehicle_url(self, dealership_name: str, vehicle: Dict) -> str:
        """
        Attempt to construct a vehicle-specific URL based on dealership patterns.
        This is a fallback when database URLs are generic.
        """
        
        vin = vehicle.get('vin', '').strip()
        stock = vehicle.get('stock', '').strip()
        base_url = vehicle.get('vehicle_url', '').strip()
        
        if not base_url:
            return ""
        
        # Extract base domain from existing URL
        if '://' in base_url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(base_url)
                base_domain = f"{parsed.scheme}://{parsed.netloc}"
            except:
                return ""
        else:
            return ""
        
        # Try common vehicle URL patterns based on dealership
        dealership_lower = dealership_name.lower()
        
        # BMW dealerships often use VIN in URL
        if 'bmw' in dealership_lower and vin:
            return f"{base_domain}/inventory/used/{vin}"
        
        # Honda dealerships often use stock numbers
        if 'honda' in dealership_lower and stock:
            return f"{base_domain}/vehicle-details/{stock}"
            
        # Lincoln/Ford dealerships may use different patterns
        if any(brand in dealership_lower for brand in ['lincoln', 'ford', 'sinclair']) and stock:
            return f"{base_domain}/inventory/vehicle/{stock}"
        
        # Generic fallback - try stock-based URL
        if stock:
            return f"{base_domain}/inventory/detail/{stock}"
            
        return ""
    
    def _generate_adobe_csv(self, vehicles: List[Dict], dealership_name: str, template_type: str, 
                           output_folder: Path, qr_paths: List[str]) -> Path:
        """Generate Adobe CSV in EXACT format from reference examples"""
        
        clean_name = dealership_name.replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Updated filename pattern to match current system
        date_str = datetime.now().strftime('%m.%d')  # Format: 9.18
        if template_type == "shortcut_pack":
            abbr = "SCP"
        elif template_type == "shortcut":
            abbr = "SC"
        else:
            abbr = template_type.upper()[:3]

        clean_name_upper = clean_name.upper().replace(' ', '').replace("'", '')
        filename = f"{clean_name_upper}_{abbr}_{date_str} - CSV.csv"
        csv_path = output_folder / filename
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            
            if template_type == "shortcut":
                # Shortcut format: QRYEARMODEL,QRSTOCK,@QR2
                writer = csv.writer(csvfile)
                writer.writerow(['QRYEARMODEL', 'QRSTOCK', '@QR2'])
                
                for idx, vehicle in enumerate(vehicles):
                    year = vehicle.get('year', '')
                    make = vehicle.get('make', '')
                    model = vehicle.get('model', '')
                    stock = vehicle.get('stock', '')
                    type_prefix = self._get_type_prefix(vehicle.get('vehicle_condition', ''))
                    vin = vehicle.get('vin', '')
                    
                    qr_path = qr_paths[idx] if idx < len(qr_paths) else ''
                    
                    qryearmodel = f"{year} {make} {model} - {stock}"
                    qrstock = f"{type_prefix} - {vin}"
                    
                    writer.writerow([qryearmodel, qrstock, qr_path])
            
            elif template_type == "shortcut_pack":
                # Shortcut Pack format: YEARMAKE,MODEL,TRIM,STOCK,VIN,@QR,QRYEARMODEL,QRSTOCK,@QR2,MISC
                writer = csv.writer(csvfile)
                writer.writerow(['YEARMAKE', 'MODEL', 'TRIM', 'STOCK', 'VIN', '@QR', 'QRYEARMODEL', 'QRSTOCK', '@QR2', 'MISC'])
                
                for idx, vehicle in enumerate(vehicles):
                    year = vehicle.get('year', '')
                    make = vehicle.get('make', '')
                    model = vehicle.get('model', '')
                    trim = vehicle.get('trim', '')
                    stock = vehicle.get('stock', '')
                    vin = vehicle.get('vin', '')
                    raw_status = vehicle.get('raw_status', 'N/A')  # Get raw_status from database query
                    type_prefix = self._get_type_prefix(vehicle.get('vehicle_condition', ''))
                    
                    qr_path = qr_paths[idx] if idx < len(qr_paths) else ''
                    
                    # Format fields based on NEW/USED status
                    if type_prefix == "NEW":
                        # New vehicles get "NEW" prefix in YEARMAKE field
                        yearmake = f"NEW {year} {make}"
                    else:
                        # Used vehicles have no prefix in YEARMAKE field
                        yearmake = f"{year} {make}"

                    # Common fields for both new and used
                    stock_field = f"{year} {model} - {stock}"
                    vin_field = f"{type_prefix} - {vin}"
                    qryearmodel = f"{year} {model} - {stock}"
                    qrstock = f"{type_prefix} - {vin}"
                    misc = f"{year} {model.title()} - {vin} - {stock}"
                    
                    writer.writerow([
                        yearmake, model, trim, stock_field, vin_field, qr_path,
                        qryearmodel, qrstock, qr_path, misc
                    ])
        
        logger.info(f"Generated Adobe CSV: {csv_path}")
        return csv_path
    
    def _get_type_prefix(self, vehicle_type: str) -> str:
        """Convert vehicle type to prefix used in Adobe CSVs - ONLY NEW or USED"""
        vtype = vehicle_type.lower()
        if 'new' in vtype:
            return 'NEW'
        else:
            # All non-new vehicles (including certified, cpo, po, pre-owned) become USED
            return 'USED'
    
    def _process_cdjr_columbia_dual_output(self, vehicles: List[Dict], dealership_name: str, 
                                          template_type: str, order_folder: Path, qr_paths: List[str]) -> Dict[str, str]:
        """
        Special processing for CDJR of Columbia - generates two separate CSV files:
        1. Used vehicles -> shortcut pack format (normal behavior)
        2. New vehicles -> shortcut format with custom headers (QRYEARMODEL, QRSTOCK, @QR2)
        """
        logger.info(f"[CDJR COLUMBIA] Special dual CSV output processing for {len(vehicles)} vehicles")
        
        # Separate vehicles by condition - handle missing data by defaulting to used
        new_vehicles = []
        used_vehicles = []
        
        for vehicle in vehicles:
            condition = vehicle.get('vehicle_condition', '').lower()
            
            if condition == 'new':
                new_vehicles.append(vehicle)
            elif condition in ['po', 'cpo', 'certified', 'pre-owned', 'used']:
                used_vehicles.append(vehicle)
            else:
                # Handle vehicles with missing/unknown condition data
                # Default to used category and fill missing fields with "NO DATA FOUND"
                vehicle_copy = vehicle.copy()
                if not vehicle_copy.get('year') or vehicle_copy.get('year') == 'Unknown':
                    vehicle_copy['year'] = 'NO DATA FOUND'
                if not vehicle_copy.get('make') or vehicle_copy.get('make') == 'Unknown':
                    vehicle_copy['make'] = 'NO DATA FOUND'
                if not vehicle_copy.get('model') or vehicle_copy.get('model') == 'Unknown':
                    vehicle_copy['model'] = 'NO DATA FOUND'
                if not vehicle_copy.get('stock'):
                    vehicle_copy['stock'] = 'NO DATA FOUND'
                if not vehicle_copy.get('trim'):
                    vehicle_copy['trim'] = 'NO DATA FOUND'
                
                used_vehicles.append(vehicle_copy)
                logger.info(f"[CDJR COLUMBIA] Vehicle {vehicle.get('vin', 'unknown')} missing data, defaulted to used with NO DATA FOUND fields")
        
        logger.info(f"[CDJR COLUMBIA] Split: {len(new_vehicles)} new vehicles, {len(used_vehicles)} used vehicles")
        
        csv_files = {}
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Generate used vehicles CSV (shortcut pack format - normal behavior)
        if used_vehicles:
            used_qr_paths = qr_paths[:len(used_vehicles)]  # First N QR codes for used vehicles
            used_csv_path = self._generate_cdjr_used_csv(used_vehicles, dealership_name, order_folder, used_qr_paths, timestamp)
            csv_files['used_csv'] = str(used_csv_path)
            logger.info(f"[CDJR COLUMBIA] Generated used vehicles CSV: {used_csv_path.name}")
        
        # Generate new vehicles CSV (shortcut format with custom headers)
        if new_vehicles:
            new_qr_paths = qr_paths[len(used_vehicles):]  # Remaining QR codes for new vehicles
            new_csv_path = self._generate_cdjr_new_csv(new_vehicles, dealership_name, order_folder, new_qr_paths, timestamp)
            csv_files['new_csv'] = str(new_csv_path)
            logger.info(f"[CDJR COLUMBIA] Generated new vehicles CSV: {new_csv_path.name}")
        
        return csv_files
    
    def _generate_cdjr_used_csv(self, vehicles: List[Dict], dealership_name: str, 
                               order_folder: Path, qr_paths: List[str], timestamp: str) -> Path:
        """Generate shortcut pack CSV for CDJR Columbia used vehicles"""
        clean_name = dealership_name.replace(' ', '_')
        filename = f"{clean_name}_Used_ShortcutPack_{timestamp}.csv"
        csv_path = order_folder / filename
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['YEARMAKE', 'MODEL', 'TRIM', 'STOCK', 'VIN', '@QR', 'QRYEARMODEL', 'QRSTOCK', '@QR2', 'MISC'])
            
            for idx, vehicle in enumerate(vehicles):
                year = vehicle.get('year', '')
                make = vehicle.get('make', '')
                model = vehicle.get('model', '')
                trim = vehicle.get('trim', '')
                stock = vehicle.get('stock', '')
                vin = vehicle.get('vin', '')
                raw_status = vehicle.get('raw_status', 'N/A')
                type_prefix = self._get_type_prefix(vehicle.get('vehicle_condition', ''))
                
                qr_path = qr_paths[idx] if idx < len(qr_paths) else ''
                
                # Standard shortcut pack format for used vehicles
                yearmake = f"{year} {make}"
                qryearmodel = f"{year} {make} {model} - {stock}"
                qrstock = f"{type_prefix} - {vin}"
                
                writer.writerow([yearmake, model, trim, stock, vin, qr_path, qryearmodel, qrstock, qr_path, raw_status])
        
        return csv_path
    
    def _generate_cdjr_new_csv(self, vehicles: List[Dict], dealership_name: str, 
                              order_folder: Path, qr_paths: List[str], timestamp: str) -> Path:
        """Generate shortcut CSV for CDJR Columbia new vehicles with custom headers"""
        clean_name = dealership_name.replace(' ', '_')
        filename = f"{clean_name}_New_Shortcut_{timestamp}.csv"
        csv_path = order_folder / filename
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # Custom headers for CDJR Columbia new vehicles
            writer.writerow(['QRYEARMODEL', 'QRSTOCK', '@QR2'])
            
            for idx, vehicle in enumerate(vehicles):
                year = vehicle.get('year', '')
                make = vehicle.get('make', '')
                model = vehicle.get('model', '')
                stock = vehicle.get('stock', '')
                
                qr_path = qr_paths[idx] if idx < len(qr_paths) else ''
                
                # Custom format for CDJR Columbia new vehicles
                qryearmodel = f"{year} {make} {model}"  # Year and Model only (as requested)
                qrstock = stock  # Stock number only (as requested)
                qr2 = qr_path  # Same QR data as @QR2 in shortcut pack
                
                writer.writerow([qryearmodel, qrstock, qr2])
        
        return csv_path
    
    def _generate_billing_sheet_csv(self, vehicles: List[Dict], dealership_name: str, output_folder: Path, timestamp: str) -> Path:
        """Generate billing sheet CSV - matches EXACT format from current system"""

        # File naming pattern: SOCODCJR_SCP_9.18 - BILLING2.csv pattern
        clean_name = dealership_name.upper().replace(' ', '').replace("'", '')
        date_str = datetime.now().strftime('%m.%d')  # Format: 9.18
        template_abbr = 'SCP'  # Shortcut Pack abbreviation
        filename = f"{clean_name}_{template_abbr}_{date_str} - BILLING2.csv"
        billing_path = output_folder / filename

        logger.info(f"Generating billing sheet CSV: {billing_path}")

        # Count vehicle types (ONLY NEW or USED)
        new_count = 0
        used_count = 0
        vin_list = []

        for vehicle in vehicles:
            vin = vehicle.get('vin', '')
            vtype = vehicle.get('vehicle_condition', '').lower()

            # Simple NEW/USED determination
            if 'new' in vtype:
                new_count += 1
            else:
                # Everything else (including cpo, certified, po, pre-owned) is USED
                used_count += 1

            vin_list.append(vin)

        total_vehicles = len(vehicles)

        # Write billing CSV in EXACT format from example
        with open(billing_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header row - EXACT format
            writer.writerow(['Totals:', '', '', 'DUPLICATES', '', '', '', 'ORDERED', 'PRODUCED'])

            # Summary rows
            writer.writerow(['Total Ordered', total_vehicles, '', '', '', '', '',
                           vin_list[0] if len(vin_list) > 0 else '',
                           vin_list[0] if len(vin_list) > 0 else ''])

            writer.writerow(['Total Produced:', total_vehicles, '', '', '', '', '',
                           vin_list[1] if len(vin_list) > 1 else '',
                           vin_list[1] if len(vin_list) > 1 else ''])

            writer.writerow(['Total New:', new_count, '', '', '', '', '',
                           vin_list[2] if len(vin_list) > 2 else '',
                           vin_list[2] if len(vin_list) > 2 else ''])

            writer.writerow(['Total Used:', used_count, '', '', '', '', '',
                           vin_list[3] if len(vin_list) > 3 else '',
                           vin_list[3] if len(vin_list) > 3 else ''])

            writer.writerow(['', '', '', '', '', '', '',
                           vin_list[4] if len(vin_list) > 4 else '',
                           vin_list[4] if len(vin_list) > 4 else ''])

            writer.writerow(['Used Duplicates:', 0, '', '', '', '', '',
                           vin_list[5] if len(vin_list) > 5 else '',
                           vin_list[5] if len(vin_list) > 5 else ''])

            writer.writerow(['New Duplicates', 0, '', '', '', '', '',
                           vin_list[6] if len(vin_list) > 6 else '',
                           vin_list[6] if len(vin_list) > 6 else ''])

            writer.writerow(['Duplicates:', 0, '', '', '', '', '',
                           vin_list[7] if len(vin_list) > 7 else '',
                           vin_list[7] if len(vin_list) > 7 else ''])

            # Fill in remaining VINs if there are more than 8
            for i in range(8, len(vin_list)):
                writer.writerow(['', '', '', '', '', '', '', vin_list[i], vin_list[i]])

        logger.info(f"Generated billing sheet CSV: {billing_path}")
        return billing_path
    
    def _update_vin_history(self, dealership_name: str, vins: List[str]):
        """Update VIN history for next comparison"""
        try:
            # Clear old history (keep last 7 days)
            db_manager.execute_query("""
                DELETE FROM vin_history
                WHERE dealership_name = %s AND order_date < CURRENT_DATE - INTERVAL '7 days'
            """, (dealership_name,))
            
            # Insert current VINs
            for vin in vins:
                db_manager.execute_query("""
                    INSERT INTO vin_history (dealership_name, vin, order_date)
                    VALUES (%s, %s, CURRENT_DATE)
                    ON CONFLICT (dealership_name, vin, order_date) DO NOTHING
                """, (dealership_name, vin))
                
        except Exception as e:
            logger.error(f"Error updating VIN history: {e}")
    
    def _find_new_vehicles_enhanced(self, dealership_name: str, current_vins: List[str], current_vehicles: List[Dict]) -> List[str]:
        """
        SIMPLIFIED VIN comparison using dealership-specific VIN logs.
        
        NEW v2.1 Logic:
        - Check ONLY against this dealership's historical VIN log
        - Simple comparison: current inventory vs dealership-specific VIN history
        - Skip if VIN exists in dealership's log within time window
        - Process if VIN is new to this dealership or outside time window
        """
        
        # Get the dealership-specific VIN log table
        vin_log_table = self._get_dealership_vin_log_table(dealership_name)
        logger.info(f"[CAO DEBUG] Using dealership-specific VIN log table: {vin_log_table}")
        
        new_vins = []
        
        logger.info(f"[CAO DEBUG] Checking {len(current_vehicles)} vehicles against VIN log for {dealership_name}")
        
        for vehicle in current_vehicles:
            vin = vehicle.get('vin')
            current_type = self._normalize_vehicle_type(vehicle.get('type', 'unknown'))
            
            if not vin:
                continue
                
            # Check this dealership's VIN log ONLY
            history_query = f"""
                SELECT order_type, processed_date
                FROM {vin_log_table}
                WHERE vin = %s 
                ORDER BY created_at DESC 
                LIMIT 5
            """
            
            history = db_manager.execute_query(history_query, (vin,))
            
            should_process = True
            
            if history:
                # VIN exists in this dealership's history - skip it (already processed)
                most_recent = history[0]
                prev_order_type = most_recent['order_type'] or 'unknown'
                processed_date = most_recent['processed_date']
                
                # If VIN is in the log, it's been processed before - skip it
                logger.info(f"[CAO DEBUG] Skipping {vin}: Previously processed as {prev_order_type} on {processed_date}")
                should_process = False
            else:
                # No history in this dealership's log = definitely new
                logger.info(f"[CAO DEBUG] Processing {vin}: No previous history in {dealership_name}")
                should_process = True
            
            if should_process:
                new_vins.append(vin)
        
        logger.info(f"[CAO DEBUG] VIN Comparison Summary for {dealership_name}: {len(current_vins)} current vehicles, {len(new_vins)} need processing")
        if new_vins:
            logger.info(f"[CAO DEBUG] VINs that need processing: {new_vins}")
        return new_vins
    
    def _normalize_vehicle_type(self, vehicle_type: str) -> str:
        """Normalize vehicle type to standard categories"""
        if not vehicle_type:
            return 'unknown'
            
        vehicle_type = vehicle_type.lower().strip()
        
        if any(keyword in vehicle_type for keyword in ['new', 'brand new']):
            return 'new'
        elif any(keyword in vehicle_type for keyword in ['certified', 'cpo', 'pre-owned']):
            return 'certified'
        elif any(keyword in vehicle_type for keyword in ['used', 'pre owned']):
            return 'used'
        else:
            return 'unknown'
    
    def _update_vin_history_enhanced(self, dealership_name: str, vehicles: List[Dict]):
        """Update VIN history with vehicle type information"""
        try:
            # Clear old history (keep last 30 days instead of 7 for cross-reference)
            db_manager.execute_query("""
                DELETE FROM vin_history
                WHERE dealership_name = %s AND order_date < CURRENT_DATE - INTERVAL '30 days'
            """, (dealership_name,))
            
            # Insert current vehicles with type information
            for vehicle in vehicles:
                vin = vehicle.get('vin')
                vehicle_type = self._normalize_vehicle_type(vehicle.get('type', 'unknown'))
                
                if vin:
                    db_manager.execute_query("""
                        INSERT INTO vin_history (dealership_name, vin, vehicle_type, order_date)
                        VALUES (%s, %s, %s, CURRENT_DATE)
                        ON CONFLICT (dealership_name, vin, order_date) DO UPDATE SET
                        vehicle_type = EXCLUDED.vehicle_type,
                        created_at = CURRENT_TIMESTAMP
                    """, (dealership_name, vin, vehicle_type))
                    
        except Exception as e:
            logger.error(f"Error updating enhanced VIN history: {e}")
    
    def regenerate_qr_codes_for_csv(self, csv_filename: str) -> Dict[str, Any]:
        """Regenerate QR codes for vehicles in a CSV file"""
        try:
            logger.info(f"Regenerating QR codes for CSV: {csv_filename}")
            
            # Find the CSV file
            csv_file = None
            for order_dir in self.output_base.glob("*/"):
                potential_file = order_dir / csv_filename
                if potential_file.exists():
                    csv_file = potential_file
                    break
            
            if not csv_file:
                return {'success': False, 'error': f'CSV file not found: {csv_filename}'}
            
            # Read the CSV file
            import csv
            vehicles = []
            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    vehicles.append(row)
            
            if not vehicles:
                return {'success': False, 'error': 'No vehicles found in CSV'}
            
            # Extract dealership name from filename or path
            dealership_name = csv_filename.split('_')[0].replace('_', ' ')
            
            # Create QR codes directory
            qr_folder = csv_file.parent / "qr_codes"
            qr_folder.mkdir(exist_ok=True)
            
            # Regenerate QR codes
            qr_paths = []
            for vehicle in vehicles:
                try:
                    vin = vehicle.get('VIN', '')
                    stock = vehicle.get('STOCK', '')
                    
                    if not vin or not stock:
                        continue
                    
                    # Generate QR code content (using stock number)
                    qr_content = stock
                    
                    # Create QR code
                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,
                        border=4,
                    )
                    qr.add_data(qr_content)
                    qr.make(fit=True)
                    
                    # Generate QR code image
                    qr_image = qr.make_image(fill_color="black", back_color="white")
                    
                    # Resize to exactly 388x388 pixels
                    qr_image = qr_image.resize((388, 388), Image.LANCZOS)
                    
                    # Save QR code with stock number as filename
                    qr_filename = f"{stock}.png"
                    qr_path = qr_folder / qr_filename
                    qr_image.save(qr_path, "PNG")
                    
                    qr_paths.append(str(qr_path))
                    
                except Exception as e:
                    logger.error(f"Error generating QR for vehicle {vehicle}: {e}")
                    continue
            
            logger.info(f"Regenerated {len(qr_paths)} QR codes")
            
            return {
                'success': True,
                'qr_codes_generated': len(qr_paths),
                'qr_folder': str(qr_folder),
                'qr_paths': qr_paths
            }
            
        except Exception as e:
            logger.error(f"Error regenerating QR codes: {e}")
            return {'success': False, 'error': str(e)}
    
    def regenerate_qr_codes_with_urls(self, csv_filename: str, vehicle_urls: List[Dict]) -> Dict[str, Any]:
        """Regenerate QR codes with custom URLs for each vehicle"""
        try:
            logger.info(f"Regenerating QR codes with custom URLs for CSV: {csv_filename}")
            
            # Find the CSV file
            csv_file = None
            for order_dir in self.output_base.glob("*/"):
                potential_file = order_dir / csv_filename
                if potential_file.exists():
                    csv_file = potential_file
                    break
            
            if not csv_file:
                return {'success': False, 'error': f'CSV file not found: {csv_filename}'}
            
            # Create QR codes directory
            qr_folder = csv_file.parent / "qr_codes"
            qr_folder.mkdir(exist_ok=True)
            
            # Clear existing QR codes
            for existing_qr in qr_folder.glob("*.png"):
                existing_qr.unlink()
            
            qr_paths = []
            generated_count = 0
            
            # Generate QR codes with custom URLs
            for vehicle_data in vehicle_urls:
                try:
                    stock = vehicle_data.get('stock', '')
                    url = vehicle_data.get('url', '').strip()
                    
                    if not stock:
                        logger.warning(f"Missing stock number for vehicle: {vehicle_data}")
                        continue
                    
                    # Use stock number as QR content if no URL provided
                    qr_content = url if url else stock
                    
                    # Create QR code
                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,
                        border=4,
                    )
                    qr.add_data(qr_content)
                    qr.make(fit=True)
                    
                    # Generate QR code image
                    qr_image = qr.make_image(fill_color="black", back_color="white")
                    
                    # Resize to exactly 388x388 pixels
                    qr_image = qr_image.resize((388, 388), Image.LANCZOS)
                    
                    # Save QR code with stock number as filename
                    qr_filename = f"{stock}.png"
                    qr_path = qr_folder / qr_filename
                    qr_image.save(qr_path, "PNG")
                    
                    qr_paths.append(str(qr_path))
                    generated_count += 1
                    
                    logger.info(f"Generated QR for {stock}: {qr_content}")
                    
                except Exception as e:
                    logger.error(f"Error generating QR for vehicle {vehicle_data}: {e}")
                    continue
            
            logger.info(f"Regenerated {generated_count} QR codes with custom URLs")
            
            return {
                'success': True,
                'qr_codes_generated': generated_count,
                'qr_folder': str(qr_folder),
                'qr_paths': qr_paths,
                'urls_processed': len(vehicle_urls)
            }
            
        except Exception as e:
            logger.error(f"Error regenerating QR codes with URLs: {e}")
            return {'success': False, 'error': str(e)}

# Test the correct processor
if __name__ == "__main__":
    processor = CorrectOrderProcessor()
    
    # Test CAO order with Auffenberg Hyundai
    result = processor.process_cao_order("Auffenberg Hyundai", "shortcut_pack")
    print(json.dumps(result, indent=2))