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
        self.dealership_name_mapping = {
            'Dave Sinclair Lincoln South': 'Dave Sinclair Lincoln',
            'BMW of West St. Louis': 'BMW of West St. Louis', 
            'Columbia Honda': 'Columbia Honda',
            'South County Dodge Chrysler Jeep RAM': 'South County Dodge Chrysler Jeep RAM'
        }
        
        # Reverse mapping for VIN history lookups
        self.vin_history_name_variations = {
            'Dave Sinclair Lincoln South': ['Dave Sinclair Lincoln South', 'Dave Sinclair Lincoln'],
            'Dave Sinclair Lincoln': ['Dave Sinclair Lincoln South', 'Dave Sinclair Lincoln'],
            'BMW of West St. Louis': ['BMW of West St. Louis'],
            'Columbia Honda': ['Columbia Honda'],
            'Bommarito West County': ['Bommarito West County'],
            'Bommarito Cadillac': ['Bommarito Cadillac']
        }
    
    def _get_dealership_vin_log_table(self, dealership_name: str) -> str:
        """
        Generate the correct dealership-specific VIN log table name.
        
        Args:
            dealership_name: The dealership name from dealership_configs
            
        Returns:
            The PostgreSQL table name for this dealership's VIN log
        """
        # Create slug from dealership name
        slug = dealership_name.lower()
        slug = slug.replace(' ', '_')
        slug = slug.replace('&', 'and')
        slug = slug.replace('.', '')
        slug = slug.replace(',', '')
        slug = slug.replace('-', '_')
        slug = slug.replace('/', '_')
        slug = slug.replace('__', '_')
        
        table_name = f'{slug}_vin_log'
        logger.debug(f"Dealership '{dealership_name}' -> table '{table_name}'")
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
            
            logger.info(f"Found {len(current_vehicles)} total vehicles")
            
            # Step 2: Compare VIN lists to find NEW vehicles (Enhanced Logic)
            current_vins = [v['vin'] for v in current_vehicles]
            new_vins = self._find_new_vehicles_enhanced(dealership_name, current_vins, current_vehicles)
            
            # Filter to only NEW vehicles
            new_vehicles = [v for v in current_vehicles if v['vin'] in new_vins]
            logger.info(f"Found {len(new_vehicles)} NEW vehicles needing graphics")
            
            if not new_vehicles:
                return {'success': True, 'new_vehicles': 0, 'message': 'No new vehicles to process'}
            
            # Step 3: Create output folders
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            order_folder = self.output_base / dealership_name.replace(' ', '_') / timestamp
            qr_folder = order_folder / "qr_codes"
            
            order_folder.mkdir(parents=True, exist_ok=True)
            qr_folder.mkdir(exist_ok=True)
            
            # Step 4: Generate QR codes for vehicle URLs
            qr_paths = self._generate_qr_codes(new_vehicles, dealership_name, qr_folder)
            
            # Step 5: Generate Adobe CSV in EXACT format we need
            csv_path = self._generate_adobe_csv(new_vehicles, dealership_name, template_type, order_folder, qr_paths)
            
            # Step 5.5: Generate billing sheet CSV automatically after QR codes
            billing_csv_path = self._generate_billing_sheet_csv(new_vehicles, dealership_name, order_folder, timestamp)
            
            # Step 6: CRITICAL - Log processed vehicle VINs to history database (unless testing)
            if skip_vin_logging:
                logger.info("Skipping VIN logging - test data processing")
                vin_logging_result = {'success': True, 'vins_logged': 0, 'duplicates_skipped': 0, 'errors': []}
            else:
                vin_logging_result = self._log_processed_vins_to_history(new_vehicles, dealership_name, 'CAO_ORDER')
            
            return {
                'success': True,
                'dealership': dealership_name,
                'template_type': template_type,
                'total_vehicles': len(current_vehicles),
                'new_vehicles': len(new_vehicles),
                'qr_codes_generated': len(qr_paths),
                'qr_folder': str(qr_folder),
                'csv_file': str(csv_path),
                'download_csv': f"/download_csv/{csv_path.name}",
                'billing_csv_file': str(billing_csv_path),
                'download_billing_csv': f"/download_csv/{billing_csv_path.name}",
                'timestamp': timestamp,
                'vins_logged_to_history': vin_logging_result['vins_logged'],
                'duplicate_vins_skipped': vin_logging_result['duplicates_skipped'],
                'vin_logging_success': vin_logging_result['success']
            }
            
        except Exception as e:
            logger.error(f"Error processing CAO order: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_list_order(self, dealership_name: str, vin_list: List[str], template_type: str = "shortcut_pack", skip_vin_logging: bool = False) -> Dict[str, Any]:
        """
        Process List Order (transcribed VINs from installers)
        """
        
        logger.info(f"[LIST] Processing {dealership_name} with {len(vin_list)} VINs")
        
        try:
            # Get vehicles by specific VIN list
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
            
            logger.info(f"Found {len(vehicles)} vehicles from VIN list")
            
            # Apply dealership filtering to LIST orders as well
            filtered_vehicles = self._apply_dealership_filters(vehicles, dealership_name)
            logger.info(f"After filtering: {len(filtered_vehicles)} vehicles match dealership criteria")
            
            if not filtered_vehicles:
                return {
                    'success': False, 
                    'error': f'No vehicles match dealership filtering criteria. Found {len(vehicles)} vehicles but none match the configured filters (new/used/certified).'
                }
            
            # Create output folders
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            order_folder = self.output_base / dealership_name.replace(' ', '_') / timestamp
            qr_folder = order_folder / "qr_codes"
            
            order_folder.mkdir(parents=True, exist_ok=True)
            qr_folder.mkdir(exist_ok=True)
            
            # Generate QR codes - use filtered vehicles
            qr_paths = self._generate_qr_codes(filtered_vehicles, dealership_name, qr_folder)
            
            # Generate Adobe CSV - use filtered vehicles
            csv_path = self._generate_adobe_csv(filtered_vehicles, dealership_name, template_type, order_folder, qr_paths)
            
            # Generate billing sheet CSV automatically after QR codes
            billing_csv_path = self._generate_billing_sheet_csv(filtered_vehicles, dealership_name, order_folder, timestamp)
            
            # CRITICAL: Log processed vehicle VINs to history database for future order accuracy - use filtered vehicles (unless testing)
            if skip_vin_logging:
                logger.info("Skipping VIN logging - test data processing")
                vin_logging_result = {'success': True, 'vins_logged': 0, 'duplicates_skipped': 0, 'errors': []}
            else:
                vin_logging_result = self._log_processed_vins_to_history(filtered_vehicles, dealership_name, 'LIST_ORDER')
            
            return {
                'success': True,
                'dealership': dealership_name,
                'template_type': template_type,
                'vehicles_requested': len(vehicles),
                'vehicles_processed': len(filtered_vehicles),
                'vehicles_filtered_out': len(vehicles) - len(filtered_vehicles),
                'qr_codes_generated': len(qr_paths),
                'qr_folder': str(qr_folder),
                'csv_file': str(csv_path),
                'download_csv': f"/download_csv/{csv_path.name}",
                'billing_csv_file': str(billing_csv_path),
                'download_billing_csv': f"/download_csv/{billing_csv_path.name}",
                'timestamp': timestamp,
                'vins_logged_to_history': vin_logging_result['vins_logged'],
                'duplicate_vins_skipped': vin_logging_result['duplicates_skipped'],
                'vin_logging_success': vin_logging_result['success']
            }
            
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
        logger.info(f"Mapping {dealership_name} -> {actual_location_name}")
        
        # Get dealership config
        config = db_manager.execute_query("""
            SELECT filtering_rules FROM dealership_configs WHERE name = %s
        """, (dealership_name,))
        
        filtering_rules = {}
        if config:
            filtering_rules = config[0]['filtering_rules']
            if isinstance(filtering_rules, str):
                filtering_rules = json.loads(filtering_rules)
        
        # Build query with filters - use actual location name for data lookup
        # CRITICAL: Only process vehicles from the ACTIVE scraper import that are physically on the lot
        query = """
            SELECT rvd.* FROM raw_vehicle_data rvd
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE rvd.location = %s 
            AND rvd.on_lot_status = 'onlot'
            AND si.status = 'active'
        """
        params = [actual_location_name]
        
        # Apply vehicle type filter using normalized_type field (much cleaner!)
        vehicle_types = filtering_rules.get('allowed_vehicle_types', filtering_rules.get('vehicle_types', ['new', 'used', 'cpo']))
        if vehicle_types and 'all' not in vehicle_types:
            # Convert dealership filter terms to normalized terms
            normalized_types = []
            for vtype in vehicle_types:
                if vtype in ['cpo', 'certified']:
                    normalized_types.append('cpo')
                elif vtype in ['new']:
                    normalized_types.append('new') 
                elif vtype in ['used']:
                    normalized_types.append('po')  # pre-owned
            
            if normalized_types:
                # Use simple normalized_type field instead of complex raw type matching
                placeholders = ','.join(['%s'] * len(normalized_types))
                query += f" AND normalized_type IN ({placeholders})"
                params.extend(normalized_types)
        
        # Apply year filter
        min_year = filtering_rules.get('min_year')
        if min_year:
            query += " AND year >= %s"
            params.append(min_year)
        
        # Apply require_status filter (highest priority - checks the 'type' column)
        require_statuses = filtering_rules.get('require_status')
        if require_statuses:
            if isinstance(require_statuses, list):
                status_conditions = []
                for status in require_statuses:
                    status_conditions.append("rvd.type ILIKE %s")
                    params.append(f"%{status}%")
                query += f" AND ({' OR '.join(status_conditions)})"
            else:
                query += " AND rvd.type ILIKE %s"
                params.append(f"%{require_statuses}%")
        
        # Apply exclude_status filter (checks the 'type' column for raw status values)
        exclude_statuses = filtering_rules.get('exclude_status')
        if exclude_statuses:
            if isinstance(exclude_statuses, list):
                for status in exclude_statuses:
                    # Use ILIKE for case-insensitive matching against the 'type' column
                    query += " AND rvd.type NOT ILIKE %s"
                    params.append(f"%{status}%")
            else:
                query += " AND rvd.type NOT ILIKE %s"
                params.append(f"%{exclude_statuses}%")
        
        # Apply stock number filter (exclude missing and asterisk placeholders)
        if filtering_rules.get('exclude_missing_stock', True):
            query += " AND stock IS NOT NULL AND stock != %s AND stock != %s"
            params.extend(['', '*'])
            
        # Apply price filter  
        if filtering_rules.get('exclude_missing_price', True):
            query += " AND price IS NOT NULL AND price > 0"
        
        query += " ORDER BY import_timestamp DESC"
        
        logger.info(f"Query: {query}")
        logger.info(f"Params: {params}")
        
        try:
            # Ensure params is properly formatted as tuple for database query
            query_params = tuple(params) if params else None
            logger.info(f"Final query params as tuple: {query_params}")
            result = db_manager.execute_query(query, query_params)
            logger.info(f"Query returned {len(result)} vehicles")
            return result
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            logger.error("Attempting simplified query without problematic constraints...")
            # Try a simplified query without filtering if the main query fails
            # CRITICAL: Still only process vehicles from ACTIVE import that are on the lot
            simplified_query = """
                SELECT rvd.* FROM raw_vehicle_data rvd
                JOIN scraper_imports si ON rvd.import_id = si.import_id
                WHERE rvd.location = %s 
                AND rvd.on_lot_status = 'onlot'
                AND si.status = 'active'
                ORDER BY rvd.import_timestamp DESC
            """
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
        # Get dealership config
        config = db_manager.execute_query("""
            SELECT filtering_rules FROM dealership_configs WHERE name = %s
        """, (dealership_name,))
        
        filtering_rules = {}
        if config:
            filtering_rules = config[0]['filtering_rules']
            if isinstance(filtering_rules, str):
                filtering_rules = json.loads(filtering_rules)
        
        # Get allowed vehicle types using the new 'allowed_vehicle_types' field
        vehicle_types = filtering_rules.get('allowed_vehicle_types', filtering_rules.get('vehicle_types', ['new', 'used', 'certified']))
        
        # Filter vehicles based on type
        filtered_vehicles = []
        for vehicle in vehicles:
            vehicle_type = vehicle.get('type', '').lower()
            
            # Check if vehicle type matches allowed types
            type_matches = False
            if 'all' in vehicle_types:
                type_matches = True
            else:
                for allowed_type in vehicle_types:
                    if allowed_type == 'certified':
                        if 'certified' in vehicle_type or 'cpo' in vehicle_type:
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
                
                # Generate QR code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_content)
                qr.make(fit=True)
                
                # Create QR image - 388x388 as per reference
                img = qr.make_image(fill_color="rgb(50,50,50)", back_color="white")
                img = img.resize((388, 388), Image.Resampling.LANCZOS)
                
                # Save with exact naming convention from reference
                filename = f"{clean_name}_QR_Code_{idx}.PNG"
                filepath = output_folder / filename
                img.save(filepath)
                
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
        filename = f"{clean_name}_{template_type}_{timestamp}.csv"
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
                    type_prefix = self._get_type_prefix(vehicle.get('type', ''))
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
                    type_prefix = self._get_type_prefix(vehicle.get('type', ''))
                    
                    qr_path = qr_paths[idx] if idx < len(qr_paths) else ''
                    
                    # Handle NEW prefix for new vehicles
                    if type_prefix == "NEW":
                        yearmake = f"{year} {make}"
                        stock_field = f"{year} {model} - {stock}"
                        vin_field = f"{type_prefix} - {vin}"
                        qryearmodel = f"{year} {model} - {stock}"
                        qrstock = f"{type_prefix} - {vin}"
                        misc = f"{year} {model} - {stock} - {type_prefix} - {vin}"
                    else:
                        yearmake = f"{year} {make}"
                        stock_field = f"{year} {model} - {stock}"
                        vin_field = f"{type_prefix} - {vin}"
                        qryearmodel = f"{year} {model} - {stock}"
                        qrstock = f"{type_prefix} - {vin}"
                        misc = f"{year} {model} - {stock} - {type_prefix} - {vin}"
                    
                    writer.writerow([
                        yearmake, model, trim, stock_field, vin_field, qr_path,
                        qryearmodel, qrstock, qr_path, misc
                    ])
        
        logger.info(f"Generated Adobe CSV: {csv_path}")
        return csv_path
    
    def _get_type_prefix(self, vehicle_type: str) -> str:
        """Convert vehicle type to prefix used in Adobe CSVs"""
        vtype = vehicle_type.lower()
        if 'new' in vtype:
            return 'NEW'
        elif 'certified' in vtype or 'cpo' in vtype:
            return 'CERTIFIED'
        else:
            return 'USED'
    
    def _generate_billing_sheet_csv(self, vehicles: List[Dict], dealership_name: str, output_folder: Path, timestamp: str) -> Path:
        """Generate billing sheet CSV automatically after QR codes - matches exact format from examples"""
        
        # File naming pattern: [DEALERSHIP NAME] [DATE] - BILLING.csv
        clean_name = dealership_name.upper().replace(' ', '')
        date_str = datetime.now().strftime('%m-%d')  # Format: 8-19
        filename = f"{clean_name}_{date_str} - BILLING.csv"
        billing_path = output_folder / filename
        
        logger.info(f"Generating billing sheet CSV: {billing_path}")
        
        # Count vehicle types
        new_count = 0
        used_count = 0
        cpo_count = 0
        
        vehicle_lines = []
        vin_list = []
        
        for vehicle in vehicles:
            year = vehicle.get('year', '')
            make = vehicle.get('make', '')
            model = vehicle.get('model', '')
            stock = vehicle.get('stock', '')
            vin = vehicle.get('vin', '')
            vtype = vehicle.get('type', '').lower()
            
            # Determine vehicle type for billing
            if 'new' in vtype:
                billing_type = 'New'
                new_count += 1
            elif 'certified' in vtype or 'cpo' in vtype or 'pre-owned' in vtype:
                billing_type = 'Pre-Owned'
                cpo_count += 1
            else:
                billing_type = 'Used'
                used_count += 1
            
            # Format vehicle line: "Year Make Model - Stock - VIN"
            vehicle_line = f"{year} {make} {model} - {stock} - {vin}"
            vehicle_lines.append([vehicle_line, billing_type])
            vin_list.append(vin)
        
        total_vehicles = len(vehicles)
        
        # Write billing CSV in exact format from examples
        with open(billing_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header row - matches format from examples
            writer.writerow(['Printed Vehicles:', '', 'TOTALS:', '', 'VINLOG:', '', 'Duplicates:'])
            
            # Vehicle lines with summary statistics in right columns
            for i, (vehicle_line, vehicle_type) in enumerate(vehicle_lines):
                if i == 0:
                    # First row includes New count
                    writer.writerow([vehicle_line, vehicle_type, 'New:', new_count, vin_list[i] if i < len(vin_list) else '', '', 'No Dupes'])
                elif i == 1:
                    # Second row includes Used count
                    writer.writerow([vehicle_line, vehicle_type, 'Used:', used_count, vin_list[i] if i < len(vin_list) else '', '', ''])
                elif i == 2:
                    # Third row includes Pre-Owned count
                    writer.writerow([vehicle_line, vehicle_type, 'Pre-Owned:', cpo_count, vin_list[i] if i < len(vin_list) else '', '', ''])
                elif i == 3:
                    # Fourth row includes Total
                    writer.writerow([vehicle_line, vehicle_type, 'Total:', total_vehicles, vin_list[i] if i < len(vin_list) else '', '', ''])
                elif i == 4:
                    # Fifth row includes Duplicates count (always 0 for new orders)
                    writer.writerow([vehicle_line, vehicle_type, 'Duplicates:', 0, vin_list[i] if i < len(vin_list) else '', '', ''])
                else:
                    # Remaining rows just have vehicle info and VIN
                    writer.writerow([vehicle_line, vehicle_type, '', '', vin_list[i] if i < len(vin_list) else '', '', ''])
            
            # Add empty rows if needed (billing sheets typically have some padding)
            for _ in range(3):
                writer.writerow(['', '', '', '', '', '', ''])
        
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
        logger.info(f"Using dealership-specific VIN log table: {vin_log_table}")
        
        new_vins = []
        
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
                logger.info(f"Skipping {vin}: Previously processed as {prev_order_type} on {processed_date}")
                should_process = False
            else:
                # No history in this dealership's log = definitely new
                logger.info(f"Processing {vin}: No previous history in {dealership_name}")
                should_process = True
            
            if should_process:
                new_vins.append(vin)
        
        logger.info(f"Simplified v2.1 logic: {len(current_vins)} current, {len(new_vins)} need processing")
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
    
    # Test CAO order with Dave Sinclair Lincoln
    result = processor.process_cao_order("Dave Sinclair Lincoln", "shortcut_pack")
    print(json.dumps(result, indent=2))