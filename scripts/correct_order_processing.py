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
            'Dave Sinclair Lincoln South': 'Dave Sinclair Lincoln',
            'Dave Sinclair Lincoln St. Peters': 'Dave Sinclair Lincoln St. Peters',  # Exact match, but explicit for clarity
            'BMW of West St. Louis': 'BMW of West St Louis',  # Config has period, CSV doesn't
            'Columbia Honda': 'Columbia Honda',
            'South County DCJR': 'South County Dodge Chrysler Jeep RAM',  # Map config name TO CSV name
            'Glendale CDJR': 'Glendale Chrysler Jeep Dodge Ram',  # Map config name to CSV name
            'HW Kia': 'HW Kia of West County',  # Map config name to CSV name
            'KIA of Columbia': 'Kia of Columbia',  # Config has all caps KIA, scraper has title case Kia
            'Rusty Drewing Chevy BGMC': 'Rusty Drewing Chevrolet Buick GMC',  # Map short name to full scraper name
            'CDJR of Columbia': 'Joe Machens Chrysler Dodge Jeep Ram'  # Map config name to scraper data location
        }
        
        # Reverse mapping for VIN history lookups
        self.vin_history_name_variations = {
            'Dave Sinclair Lincoln South': ['Dave Sinclair Lincoln South', 'Dave Sinclair Lincoln'],
            'Dave Sinclair Lincoln': ['Dave Sinclair Lincoln South', 'Dave Sinclair Lincoln'],
            'BMW of West St. Louis': ['BMW of West St. Louis'],
            'Columbia Honda': ['Columbia Honda'],
            'Bommarito West County': ['Bommarito West County'],
            'Bommarito Cadillac': ['Bommarito Cadillac'],
            'South County DCJR': ['South County DCJR', 'South County Dodge Chrysler Jeep RAM'],
            'South County Dodge Chrysler Jeep RAM': ['South County DCJR', 'South County Dodge Chrysler Jeep RAM'],
            'Glendale CDJR': ['Glendale CDJR', 'Glendale Chrysler Jeep Dodge Ram'],
            'Glendale Chrysler Jeep Dodge Ram': ['Glendale CDJR', 'Glendale Chrysler Jeep Dodge Ram'],
            'Rusty Drewing Chevy BGMC': ['Rusty Drewing Chevy BGMC', 'Rusty Drewing Chevrolet Buick GMC'],
            'Rusty Drewing Chevrolet Buick GMC': ['Rusty Drewing Chevy BGMC', 'Rusty Drewing Chevrolet Buick GMC']
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

    def _get_dealership_template_config(self, dealership_name: str) -> str:
        """
        Get the template type from dealership configuration.

        Args:
            dealership_name: The dealership name

        Returns:
            Template type string (e.g., 'shortcut_pack', 'shortcut', 'flyout')
        """
        try:
            config_result = db_manager.execute_query(
                "SELECT output_rules FROM dealership_configs WHERE name = %s",
                (dealership_name,)
            )
            if config_result and len(config_result) > 0:
                output_rules = config_result[0].get('output_rules', {})
                template_type = output_rules.get('template_type', 'shortcut_pack')
                return template_type
        except Exception as e:
            logger.warning(f"[CONFIG] Could not fetch template type for {dealership_name}: {e}")

        # Default to shortcut_pack if config not found
        return 'shortcut_pack'

    def _get_dual_template_config(self, dealership_name: str) -> Optional[Dict[str, str]]:
        """
        Check if dealership has custom_templates configured for new/used split output.

        Args:
            dealership_name: The dealership name

        Returns:
            Dict with 'new' and 'used' template IDs if configured, None otherwise
        """
        try:
            config_result = db_manager.execute_query(
                "SELECT output_rules FROM dealership_configs WHERE name = %s",
                (dealership_name,)
            )
            if config_result and len(config_result) > 0:
                output_rules = config_result[0].get('output_rules', {})
                custom_templates = output_rules.get('custom_templates')

                if custom_templates and isinstance(custom_templates, dict):
                    if 'new' in custom_templates and 'used' in custom_templates:
                        logger.info(f"[DUAL TEMPLATE] {dealership_name} has dual templates: new={custom_templates['new']}, used={custom_templates['used']}")
                        return {
                            'new': custom_templates['new'],
                            'used': custom_templates['used']
                        }

            return None
        except Exception as e:
            logger.warning(f"[DUAL TEMPLATE] Error checking dual template config for {dealership_name}: {e}")
            return None

    def _generate_dual_template_csvs(self, vehicles: List[Dict], dealership_name: str,
                                     dual_template_config: Dict[str, str], order_folder: Path,
                                     qr_paths: Dict) -> Dict[str, any]:
        """
        Generate separate CSV files for new and used vehicles using different templates.

        Args:
            vehicles: All vehicles to process
            dealership_name: Name of dealership
            dual_template_config: Dict with 'new' and 'used' template IDs
            order_folder: Output folder path
            qr_paths: QR code paths dict

        Returns:
            Dict with CSV file paths and vehicle counts per condition
        """
        logger.info(f"[DUAL TEMPLATE] Splitting {len(vehicles)} vehicles by condition for {dealership_name}")

        # Split vehicles by condition (new vs used/cpo/po/certified/pre-owned)
        # Also track indices to split QR paths correctly
        new_vehicles = []
        used_vehicles = []
        new_vehicle_indices = []
        used_vehicle_indices = []

        for idx, vehicle in enumerate(vehicles):
            condition = vehicle.get('vehicle_condition', '').lower()
            if condition == 'new':
                new_vehicles.append(vehicle)
                new_vehicle_indices.append(idx)
            else:
                # All non-new conditions go to used: used, po, cpo, certified, pre-owned
                used_vehicles.append(vehicle)
                used_vehicle_indices.append(idx)

        logger.info(f"[DUAL TEMPLATE] Split results: {len(new_vehicles)} NEW, {len(used_vehicles)} USED")

        # Split QR paths to match vehicle splits
        new_qr_paths = [qr_paths[i] for i in new_vehicle_indices if i < len(qr_paths)]
        used_qr_paths = [qr_paths[i] for i in used_vehicle_indices if i < len(qr_paths)]

        csv_files = {}
        primary_csv = None

        # Generate NEW vehicles CSV if any exist
        if new_vehicles:
            logger.info(f"[DUAL TEMPLATE] Generating NEW CSV with template {dual_template_config['new']}")
            new_csv_path = self._generate_adobe_csv(
                new_vehicles,
                dealership_name,
                dual_template_config['new'],
                order_folder,
                new_qr_paths,
                suffix='_NEW'
            )
            csv_files['new'] = {
                'path': str(new_csv_path),
                'download_url': f"/download_csv/{new_csv_path.name}",
                'vehicle_count': len(new_vehicles),
                'template': dual_template_config['new']
            }
            if not primary_csv:
                primary_csv = new_csv_path

        # Generate USED vehicles CSV if any exist
        if used_vehicles:
            logger.info(f"[DUAL TEMPLATE] Generating USED CSV with template {dual_template_config['used']}")
            used_csv_path = self._generate_adobe_csv(
                used_vehicles,
                dealership_name,
                dual_template_config['used'],
                order_folder,
                used_qr_paths,
                suffix='_USED'
            )
            csv_files['used'] = {
                'path': str(used_csv_path),
                'download_url': f"/download_csv/{used_csv_path.name}",
                'vehicle_count': len(used_vehicles),
                'template': dual_template_config['used']
            }
            if not primary_csv:
                primary_csv = used_csv_path

        csv_files['primary_csv'] = primary_csv
        csv_files['total_vehicles'] = len(vehicles)
        csv_files['new_count'] = len(new_vehicles)
        csv_files['used_count'] = len(used_vehicles)

        logger.info(f"[DUAL TEMPLATE] Generated {len([k for k in csv_files if k in ['new', 'used']])} CSV files")
        return csv_files

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

            # Step 5: Generate Adobe CSV for review stage
            # Check if dealership has dual templates for later use in Complete stage
            dual_template_config = self._get_dual_template_config(dealership_name)
            if dual_template_config:
                logger.info(f"[CAO] Dealership {dealership_name} has dual templates (NEW={dual_template_config['new']}, USED={dual_template_config['used']}) - will split in Complete stage")

            # Always use the regular template_type for review (standard format for frontend)
            csv_path = self._generate_adobe_csv(new_vehicles, dealership_name, template_type, order_folder, qr_paths)
            csv_files = None

            # Step 5.5: Generate billing sheet CSV automatically after QR codes
            billing_csv_path = self._generate_billing_sheet_csv(new_vehicles, dealership_name, order_folder, timestamp)
            
            # Step 6: CRITICAL - Log processed vehicle VINs to history database (unless testing)
            if skip_vin_logging:
                logger.info("Skipping VIN logging - test data processing")
                vin_logging_result = {'success': True, 'vins_logged': 0, 'duplicates_skipped': 0, 'errors': []}
            else:
                vin_logging_result = self._log_processed_vins_to_history(new_vehicles, dealership_name, 'CAO_ORDER')
            
            result = {
                'success': True,
                'dealership': dealership_name,
                'template_type': template_type,
                'total_vehicles': len(current_vehicles),
                'new_vehicles': len(new_vehicles),
                'vehicle_count': len(new_vehicles),
                'vehicles_data': new_vehicles,  # Include actual vehicle data for maintenance orders
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

            # Store dual template config for later use (after review stage)
            if dual_template_config:
                result['dual_template_config'] = dual_template_config
                logger.info(f"[CAO] Stored dual template config for {dealership_name} to use after review")

            return result
            
        except Exception as e:
            logger.error(f"Error processing CAO order: {e}")
            return {'success': False, 'error': str(e)}
    def prepare_list_data(self, dealership_name: str, vin_list: List[str]) -> Dict[str, Any]:
        """
        PHASE 1: Prepare and validate LIST order VINs against scraper data.
        Returns valid VINs (with data), invalid VINs (no data), and vehicle data for review.

        Args:
            dealership_name: Name of dealership
            vin_list: List of VINs entered by user

        Returns:
            Dict with success, valid_vins, invalid_vins, vehicles_data
        """
        try:
            logger.info(f"[PREPARE LIST] Validating {len(vin_list)} VINs for {dealership_name}")

            # Map dealership config name to actual data location name
            actual_location_name = self.dealership_name_mapping.get(dealership_name, dealership_name)

            valid_vehicles = []
            invalid_vins = []

            for vin in vin_list:
                # Check if VIN exists in active scraper data
                vehicle_data = db_manager.execute_query("""
                    SELECT nvd.*, rvd.status as raw_status, rvd.stock as raw_stock, rvd.vehicle_url as vehicle_url
                    FROM normalized_vehicle_data nvd
                    JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                    JOIN scraper_imports si ON rvd.import_id = si.import_id
                    WHERE nvd.vin = %s
                    AND nvd.location = %s
                    AND si.status = 'active'
                    ORDER BY rvd.import_timestamp DESC
                    LIMIT 1
                """, (vin, actual_location_name))

                if vehicle_data and len(vehicle_data) > 0:
                    # VIN found in scraper data
                    valid_vehicles.append(vehicle_data[0])
                    logger.info(f"[PREPARE LIST] Valid VIN: {vin}")
                else:
                    # VIN not found in scraper data
                    invalid_vins.append(vin)
                    logger.warning(f"[PREPARE LIST] Invalid VIN (no scraper data): {vin}")

            logger.info(f"[PREPARE LIST] Results: {len(valid_vehicles)} valid, {len(invalid_vins)} invalid")

            return {
                'success': True,
                'dealership_name': dealership_name,
                'valid_vins': len(valid_vehicles),
                'invalid_vins': len(invalid_vins),
                'invalid_vin_list': invalid_vins,
                'vehicles_data': valid_vehicles,
                'order_type': 'list'
            }

        except Exception as e:
            logger.error(f"[PREPARE LIST] Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'valid_vins': 0,
                'invalid_vins': 0,
                'invalid_vin_list': [],
                'vehicles_data': [],
                'order_type': 'list'
            }

    def process_list_order(self, dealership_name: str, vin_list: List[str], template_type: str = "shortcut_pack", skip_vin_logging: bool = False) -> Dict[str, Any]:
        """
        Process List Order (transcribed VINs from installers)
        """

        logger.info(f"[LIST] Processing {dealership_name} with {len(vin_list)} VINs")

        try:
            # Map dealership config name to actual data location name
            actual_location_name = self.dealership_name_mapping.get(dealership_name, dealership_name)
            logger.info(f"[LIST DEBUG] Mapping {dealership_name} -> {actual_location_name}")

            # LIST orders: Create vehicle records from user-provided VINs
            # No inventory lookup or filtering needed - process whatever VINs user provides
            vehicles = []
            for vin in vin_list:
                # Try to get vehicle data from inventory first (including vehicle_url for QR codes)
                vehicle_data = db_manager.execute_query("""
                    SELECT rvd.*, rvd.vehicle_url as vehicle_url
                    FROM raw_vehicle_data rvd
                    JOIN scraper_imports si ON rvd.import_id = si.import_id
                    WHERE rvd.vin = %s AND rvd.location = %s
                    AND si.status = 'active'
                    ORDER BY rvd.import_timestamp DESC
                    LIMIT 1
                """, (vin, actual_location_name))
                
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
            
            # Generate Adobe CSV - use filtered vehicles
            csv_path = self._generate_adobe_csv(filtered_vehicles, dealership_name, template_type, order_folder, qr_paths)

            # Generate billing sheet CSV automatically after QR codes
            # For LIST orders: Pass original VIN list (what user ordered) and filtered VIN list (what was produced)
            filtered_vin_list = [v.get('vin', '') for v in filtered_vehicles]
            billing_csv_path = self._generate_billing_sheet_csv(
                filtered_vehicles,
                dealership_name,
                order_folder,
                timestamp,
                original_vin_list=vin_list,  # What user ordered
                filtered_vin_list=filtered_vin_list,  # What we actually produced
                order_type='LIST'  # Explicitly mark as LIST order
            )
            
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
            
        except Exception as e:
            logger.error(f"Error processing list order: {e}")
            return {'success': False, 'error': str(e)}

    def process_maintenance_order(self, dealership_name: str, vin_list: List[str], skip_vin_logging: bool = False) -> Dict[str, Any]:
        """
        Process Maintenance Order - combines CAO + LIST approach
        - CAO portion: Find NEW vehicles from inventory (applies VIN log filtering)
        - LIST portion: Process provided VINs (typically USED, ignores VIN log)

        For Auffenberg:
        - NEW vehicles -> shortcut_pack template (from CAO)
        - USED vehicles -> shortcut template (from LIST)
        """

        logger.info(f"[MAINTENANCE] Processing {dealership_name} - CAO for NEW vehicles + LIST for {len(vin_list)} provided VINs")

        try:
            # Step 1: Run CAO to get NEW vehicles (applies VIN log)
            cao_result = self.process_cao_order(dealership_name, template_type="shortcut_pack", skip_vin_logging=skip_vin_logging)

            cao_vehicles = []
            cao_count = 0
            if cao_result.get('success'):
                cao_vehicles = cao_result.get('vehicles_data', [])
                cao_count = len(cao_vehicles)
                logger.info(f"[MAINTENANCE] CAO returned {cao_count} NEW vehicles")
            else:
                logger.warning(f"[MAINTENANCE] CAO failed: {cao_result.get('error', 'Unknown error')}")

            # Step 2: Run LIST to process provided VINs (ignores VIN log)
            list_vehicles = []
            list_count = 0
            if vin_list and len(vin_list) > 0:
                list_result = self.process_list_order(dealership_name, vin_list, template_type="shortcut", skip_vin_logging=skip_vin_logging)

                if list_result.get('success'):
                    list_vehicles = list_result.get('vehicles_data', [])
                    # Filter out placeholder/not found vehicles (they have 'Unknown' make or year='Unknown')
                    list_vehicles = [v for v in list_vehicles if v.get('make') != 'Unknown' and v.get('year') != 'Unknown']
                    list_count = len(list_vehicles)
                    logger.info(f"[MAINTENANCE] LIST returned {list_count} valid vehicles from {len(vin_list)} provided VINs")
                else:
                    logger.warning(f"[MAINTENANCE] LIST failed: {list_result.get('error', 'Unknown error')}")

            # Step 3: Remove duplicates - LIST VINs take priority over CAO VINs
            list_vins = set(v['vin'] for v in list_vehicles)
            cao_vehicles_deduplicated = [v for v in cao_vehicles if v['vin'] not in list_vins]

            duplicates_removed = cao_count - len(cao_vehicles_deduplicated)
            if duplicates_removed > 0:
                logger.info(f"[MAINTENANCE] Removed {duplicates_removed} duplicate VINs from CAO that were in LIST")

            # Combine results - LIST first, then unique CAO vehicles
            total_vehicles = list_vehicles + cao_vehicles_deduplicated
            total_count = len(total_vehicles)

            logger.info(f"[MAINTENANCE] Total: {total_count} unique vehicles ({len(cao_vehicles_deduplicated)} from CAO + {list_count} from LIST)")

            return {
                'success': True,
                'dealership': dealership_name,
                'cao_count': cao_count,
                'list_count': list_count,
                'total_count': total_count,
                'vehicles_data': total_vehicles,  # DEDUPLICATED combined vehicles (LIST + unique CAO)
                'vehicle_count': total_count,  # Use total count, not just CAO
                'new_vehicles': total_count,  # Use total count
                'vehicles': total_vehicles,  # Use DEDUPLICATED vehicles, not just CAO
                'order_type': 'maintenance',
                'cao_result': cao_result,
                'list_result': list_result if vin_list else None
            }

        except Exception as e:
            logger.error(f"[MAINTENANCE] Error processing maintenance order: {e}")
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
        logger.info(f"[CAO DEBUG] Looking up mapping for: '{dealership_name}' (repr: {repr(dealership_name)})")
        logger.info(f"[CAO DEBUG] Available mappings: {list(self.dealership_name_mapping.keys())}")
        actual_location_name = self.dealership_name_mapping.get(dealership_name, dealership_name)
        logger.info(f"[CAO DEBUG] Mapping {dealership_name} -> {actual_location_name}")
        
        # Get dealership config
        config = db_manager.execute_query("""
            SELECT filtering_rules FROM dealership_configs WHERE name = %s
        """, (dealership_name,))
        
        filtering_rules = {}
        if config:
            filtering_rules = config[0]['filtering_rules']
            if isinstance(filtering_rules, str):
                filtering_rules = json.loads(filtering_rules)
        
        # Log the filtering rules being applied
        logger.info(f"[CAO DEBUG] Applying filtering rules for {dealership_name}: {filtering_rules}")
        
        # Build query with filters - use actual location name for data lookup
        # CRITICAL: Only process vehicles from the ACTIVE scraper import that are physically on the lot
        # Use normalized_vehicle_data for proper vehicle type filtering (po, cpo, new instead of raw values)
        # ENHANCEMENT: Include raw_status for UI review stage and date_in_stock for seasoning
        query = """
            SELECT nvd.*, rvd.status as raw_status, rvd.stock as raw_stock, rvd.date_in_stock FROM normalized_vehicle_data nvd
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
            includes_used = False  # Track if 'used' is requested

            for vtype in vehicle_types:
                if vtype == 'new':
                    allowed_conditions.append('new')
                elif vtype == 'used':
                    # CRITICAL FIX: "used" is an UMBRELLA term that includes 'used', 'po', and 'cpo'
                    # When dealer wants "used", they want ALL used vehicle types
                    allowed_conditions.extend(['used', 'po', 'cpo'])
                    includes_used = True  # Mark that we're including all used types
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

        # Apply exclude_conditions filter (exclude specific vehicle conditions)
        # CRITICAL FIX: Don't apply exclude_conditions if they contradict vehicle_types
        # If dealer wants 'used' vehicles, don't exclude 'po' or 'cpo' (they ARE used)
        exclude_conditions = filtering_rules.get('exclude_conditions')
        if exclude_conditions:
            # Check if we're including 'used' vehicles - if so, ignore po/cpo exclusions
            if includes_used:
                # Filter out po/cpo from exclude_conditions since they're part of "used"
                if isinstance(exclude_conditions, list):
                    exclude_conditions = [c for c in exclude_conditions if c not in ['po', 'cpo']]
                elif exclude_conditions in ['po', 'cpo']:
                    exclude_conditions = None  # Don't exclude if it's just po/cpo

            if exclude_conditions:
                if isinstance(exclude_conditions, list):
                    for condition in exclude_conditions:
                        query += " AND nvd.vehicle_condition != %s"
                        params.append(condition)
                    logger.info(f"[EXCLUDE CONDITIONS FILTER] Applying exclude conditions filter for {dealership_name}: {exclude_conditions}")
                else:
                    query += " AND nvd.vehicle_condition != %s"
                    params.append(exclude_conditions)
                    logger.info(f"[EXCLUDE CONDITIONS FILTER] Applying exclude conditions filter for {dealership_name}: {exclude_conditions}")

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
            
        # Apply price filter - Exclude blank and placeholder price values
        if filtering_rules.get('exclude_missing_price', False):
            logger.info(f"[PRICE FILTER] Applying missing price filter for {dealership_name}")
            # Simple price filtering: exclude only blank fields and common placeholders
            # Use CAST to text to handle any data type issues, and check for various placeholder patterns
            query += """ AND rvd.price IS NOT NULL
                AND CAST(rvd.price AS TEXT) NOT IN ('*', '', 'Call', 'TBD', 'N/A', 'call', 'tbd', 'n/a')
                AND LENGTH(TRIM(CAST(rvd.price AS TEXT))) > 0
                AND TRIM(CAST(rvd.price AS TEXT)) != '*'"""
            logger.info(f"[PRICE FILTER] Filter conditions added to query")

        # Apply brand filter (required_brands)
        required_brands = filtering_rules.get('required_brands')
        if required_brands:
            if isinstance(required_brands, list):
                if len(required_brands) == 1:
                    query += " AND nvd.make = %s"
                    params.append(required_brands[0])
                else:
                    placeholders = ', '.join(['%s'] * len(required_brands))
                    query += f" AND nvd.make IN ({placeholders})"
                    params.extend(required_brands)
                logger.info(f"[BRAND FILTER] Applying brand filter for {dealership_name}: {required_brands}")
            else:
                query += " AND nvd.make = %s"
                params.append(required_brands)
                logger.info(f"[BRAND FILTER] Applying brand filter for {dealership_name}: {required_brands}")

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

                # Special logging for Glendale CDJR to diagnose price filter issue
                if dealership_name == "Glendale CDJR" and filtering_rules.get('exclude_missing_price', False):
                    logger.info(f"[GLENDALE DEBUG] Checking prices for returned vehicles...")
                    for v in result[:10]:  # Check first 10 vehicles
                        logger.info(f"[GLENDALE DEBUG] VIN: {v.get('vin')} | Price: {v.get('price')} | Raw Status: {v.get('raw_status', 'N/A')}")
            
            return result
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            logger.error("Attempting simplified query without problematic constraints...")
            # Try a simplified query without complex filtering if the main query fails
            # CRITICAL: Still only process vehicles from ACTIVE import that are on the lot
            # Use normalized_vehicle_data for consistent data structure
            # IMPORTANT: Include VIN log comparison and basic filtering even in simplified query
            vin_log_table = self._get_dealership_vin_log_table(dealership_name)

            # Build simplified query with basic filtering
            simplified_query = f"""
                SELECT nvd.*, rvd.status as raw_status, rvd.stock as raw_stock FROM normalized_vehicle_data nvd
                JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                JOIN scraper_imports si ON rvd.import_id = si.import_id
                WHERE nvd.location = %s
                AND nvd.on_lot_status IN ('onlot', 'on lot')
                AND si.status = 'active'
                AND nvd.vin NOT IN (SELECT vin FROM {vin_log_table} WHERE vin IS NOT NULL)
            """

            simplified_params = [actual_location_name]

            # Apply vehicle type filtering in simplified query
            vehicle_types = filtering_rules.get('vehicle_types', ['used'])
            if vehicle_types and vehicle_types != ['all']:
                type_conditions = []
                for vtype in vehicle_types:
                    if vtype == 'used':
                        type_conditions.extend(['used', 'po', 'cpo', 'certified', 'pre-owned'])
                    elif vtype == 'new':
                        type_conditions.append('new')
                    else:
                        type_conditions.append(vtype)

                if type_conditions:
                    placeholders = ', '.join(['%s'] * len(type_conditions))
                    simplified_query += f" AND nvd.vehicle_condition IN ({placeholders})"
                    simplified_params.extend(type_conditions)

            # Apply stock number filter in simplified query
            if filtering_rules.get('exclude_missing_stock', True):
                simplified_query += " AND nvd.stock IS NOT NULL AND nvd.stock != %s AND nvd.stock != %s"
                simplified_params.extend(['', '*'])

            # Apply exclude_conditions filter in simplified query
            exclude_conditions = filtering_rules.get('exclude_conditions')
            if exclude_conditions:
                if isinstance(exclude_conditions, list):
                    for condition in exclude_conditions:
                        simplified_query += " AND nvd.vehicle_condition != %s"
                        simplified_params.append(condition)
                    logger.info(f"[FALLBACK EXCLUDE CONDITIONS FILTER] Applying exclude conditions filter for {dealership_name}: {exclude_conditions}")
                else:
                    simplified_query += " AND nvd.vehicle_condition != %s"
                    simplified_params.append(exclude_conditions)
                    logger.info(f"[FALLBACK EXCLUDE CONDITIONS FILTER] Applying exclude conditions filter for {dealership_name}: {exclude_conditions}")

            # Apply price filter in simplified query - Exclude blank and placeholder price values
            if filtering_rules.get('exclude_missing_price', False):
                logger.info(f"[FALLBACK PRICE FILTER] Applying missing price filter for {dealership_name}")
                # Use CAST to text to handle any data type issues, and check for various placeholder patterns
                simplified_query += """ AND rvd.price IS NOT NULL
                    AND CAST(rvd.price AS TEXT) NOT IN ('*', '', 'Call', 'TBD', 'N/A', 'call', 'tbd', 'n/a')
                    AND LENGTH(TRIM(CAST(rvd.price AS TEXT))) > 0
                    AND TRIM(CAST(rvd.price AS TEXT)) != '*'"""
                logger.info(f"[FALLBACK PRICE FILTER] Filter conditions added to simplified query")

            # Apply brand filter in simplified query
            required_brands = filtering_rules.get('required_brands')
            if required_brands:
                if isinstance(required_brands, list):
                    if len(required_brands) == 1:
                        simplified_query += " AND nvd.make = %s"
                        simplified_params.append(required_brands[0])
                    else:
                        placeholders = ', '.join(['%s'] * len(required_brands))
                        simplified_query += f" AND nvd.make IN ({placeholders})"
                        simplified_params.extend(required_brands)
                    logger.info(f"[FALLBACK BRAND FILTER] Applying brand filter for {dealership_name}: {required_brands}")
                else:
                    simplified_query += " AND nvd.make = %s"
                    simplified_params.append(required_brands)
                    logger.info(f"[FALLBACK BRAND FILTER] Applying brand filter for {dealership_name}: {required_brands}")

            simplified_query += " ORDER BY nvd.updated_at DESC"

            logger.info(f"[FALLBACK DEBUG] Simplified query: {simplified_query}")
            logger.info(f"[FALLBACK DEBUG] Simplified params: {simplified_params}")

            try:
                result = db_manager.execute_query(simplified_query, tuple(simplified_params))
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

                # Seasoning filter - check if vehicle has been on lot long enough using date_in_stock
                seasoning_days = filtering_rules.get('seasoning_days')
                if seasoning_days:
                    date_in_stock = vehicle.get('date_in_stock')
                    if date_in_stock:
                        from datetime import datetime, date
                        # Convert to date if it's a datetime
                        if isinstance(date_in_stock, datetime):
                            date_in_stock = date_in_stock.date()
                        days_on_lot = (date.today() - date_in_stock).days
                        if days_on_lot < seasoning_days:
                            logger.info(f"[SEASONING] Filtered out VIN {vehicle.get('vin')[-8:]}: {days_on_lot} days on lot < {seasoning_days} days required (in stock since: {date_in_stock})")
                            continue
                    else:
                        # If no date_in_stock, filter it out to be safe
                        logger.info(f"[SEASONING] Filtered out VIN {vehicle.get('vin')[-8:]}: No date_in_stock available")
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

        logger.info(f"[QR GENERATION] Starting for {len(vehicles)} vehicles")
        if vehicles:
            logger.info(f"[QR GENERATION] Sample vehicle keys: {list(vehicles[0].keys())}")
            logger.info(f"[QR GENERATION] Sample vehicle_url value: {vehicles[0].get('vehicle_url', 'NOT FOUND')}")

        for idx, vehicle in enumerate(vehicles, 1):
            try:
                # Get vehicle details
                vin = vehicle.get('vin', '')
                stock = vehicle.get('stock', '')
                year = vehicle.get('year', '')
                make = vehicle.get('make', '')
                model = vehicle.get('model', '')
                url = vehicle.get('vehicle_url', '')

                logger.info(f"[QR {idx}] VIN: {vin}, vehicle_url in dict: {url}")

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
    
    def _add_utm_parameters(self, url: str) -> str:
        """Add Silver Fox Marketing UTM tracking parameters to a URL"""
        if not url or not url.startswith('http'):
            return url

        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)

        # Add Silver Fox Marketing UTM parameters - EXACT specifications
        utm_params = {
            'utm_source': 'SilverFox',
            'utm_medium': 'VDP_ShortCut'
        }

        # Add UTM parameters (don't override if they already exist)
        for key, value in utm_params.items():
            if key not in query_params:
                query_params[key] = [value]

        # Rebuild query string
        new_query = urlencode(query_params, doseq=True)

        # Rebuild URL
        new_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))

        return new_url

    def _get_vehicle_qr_content(self, vehicle: Dict, dealership_name: str) -> str:
        """
        Generate QR content for a vehicle.
        Priority: Vehicle URL from database with UTM > Raw VIN fallback
        """

        vin = vehicle.get('vin', '').strip()
        year = vehicle.get('year', '')
        make = vehicle.get('make', '')

        # Strip prefix (NEW - , USED - , CPO - , CERTIFIED PRE OWNED - , etc.) from VIN
        raw_vin = vin
        if ' - ' in vin:
            raw_vin = vin.split(' - ')[-1]

        # Additional fallback: strip common vehicle type prefixes if still present
        vehicle_type_prefixes = ['NEW', 'USED', 'CPO', 'CERTIFIED PRE OWNED', 'CERTIFIED', 'PRE-OWNED', 'PRE OWNED', 'PO']
        for prefix in vehicle_type_prefixes:
            if raw_vin.upper().startswith(prefix + ' '):
                raw_vin = raw_vin[len(prefix):].strip()
                break
            if raw_vin.upper().startswith(prefix + '-'):
                raw_vin = raw_vin[len(prefix)+1:].strip()
                break

        # Priority 1: Query database for vehicle_url
        if raw_vin:
            try:
                from database_connection import db_manager
                url_result = db_manager.execute_query(
                    "SELECT vehicle_url FROM normalized_vehicle_data WHERE vin = %s LIMIT 1",
                    (raw_vin,)
                )
                if url_result and len(url_result) > 0:
                    url = url_result[0].get('vehicle_url', '').strip()
                    if url and url.startswith('http'):
                        # Add UTM tracking parameters
                        url_with_utm = self._add_utm_parameters(url)
                        logger.info(f"QR Code URL for {year} {make} {raw_vin}: {url_with_utm}")
                        return url_with_utm
            except Exception as e:
                logger.warning(f"Could not fetch vehicle_url from database for {raw_vin}: {e}")

        # Priority 2: Fallback to raw VIN if no URL available
        if raw_vin:
            logger.warning(f"No vehicle_url found for {year} {make} {raw_vin}, using VIN as fallback")
            return raw_vin

        # Priority 3: Final fallback
        logger.warning(f"No URL or VIN for vehicle, using description")
        return f"{year} {make}"
    
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
                           output_folder: Path, qr_paths: List[str], suffix: str = '') -> Path:
        """Generate Adobe CSV in EXACT format from reference examples

        Args:
            vehicles: List of vehicle dicts
            dealership_name: Name of dealership
            template_type: Template type ID
            output_folder: Output folder path
            qr_paths: List of QR code paths
            suffix: Optional suffix for filename (e.g., '_NEW', '_USED')
        """

        clean_name = dealership_name.replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{clean_name}_{template_type}{suffix}_{timestamp}.csv"
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
                    # Use raw_stock as fallback if normalized stock is empty
                    stock = vehicle.get('stock', '') or vehicle.get('raw_stock', '')
                    vin = vehicle.get('vin', '')
                    raw_status = vehicle.get('raw_status', 'N/A')  # Get raw_status from database query
                    type_prefix = self._get_type_prefix(vehicle.get('vehicle_condition', ''))
                    
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

            else:
                # Custom template - load template configuration from database
                if template_type.startswith('custom_'):
                    template_id = template_type.replace('custom_', '')
                    logger.info(f"[CUSTOM TEMPLATE CSV] Processing custom template ID: {template_id}")

                    try:
                        from order_queue_manager import OrderQueueManager
                        queue_manager = OrderQueueManager()
                        template_config = queue_manager.get_template_by_id(template_id)

                        if not template_config:
                            logger.error(f"[CUSTOM TEMPLATE CSV] Template ID {template_id} not found - using shortcut_pack fallback")
                            # Use shortcut_pack as fallback
                            writer = csv.writer(csvfile)
                            writer.writerow(['YEARMAKE', 'MODEL', 'TRIM', 'STOCK', 'VIN', '@QR', 'QRYEARMODEL', 'QRSTOCK', '@QR2', 'MISC'])
                            for idx, vehicle in enumerate(vehicles):
                                year = vehicle.get('year', '')
                                make = vehicle.get('make', '')
                                model = vehicle.get('model', '')
                                trim = vehicle.get('trim', '')
                                stock = vehicle.get('stock', '') or vehicle.get('raw_stock', '')
                                vin = vehicle.get('vin', '')
                                type_prefix = self._get_type_prefix(vehicle.get('vehicle_condition', ''))
                                qr_path = qr_paths[idx] if idx < len(qr_paths) else ''
                                yearmake = f"{year} {make}"
                                stock_field = f"{year} {model} - {stock}"
                                vin_field = f"{type_prefix} - {vin}"
                                qryearmodel = f"{year} {model} - {stock}"
                                qrstock = f"{type_prefix} - {vin}"
                                misc = f"{year} {model} - {stock} - {type_prefix} - {vin}"
                                writer.writerow([yearmake, model, trim, stock_field, vin_field, qr_path, qryearmodel, qrstock, qr_path, misc])
                        else:
                            # Use custom template configuration
                            template_fields = template_config.get('fields', [])
                            logger.info(f"[CUSTOM TEMPLATE CSV] Found {len(template_fields)} fields in template")

                            writer = csv.writer(csvfile)

                            # Create headers
                            headers = [field.get('name', '').strip() for field in template_fields if field.get('name', '').strip()]
                            if headers:
                                writer.writerow(headers)
                                logger.info(f"[CUSTOM TEMPLATE CSV] Wrote headers: {headers}")

                            # Create QR path mapping
                            qr_path_map = {}
                            for idx, qr_path in enumerate(qr_paths):
                                if idx < len(vehicles):
                                    vehicle_vin = vehicles[idx].get('vin', '')
                                    if vehicle_vin:
                                        raw_vin = vehicle_vin.split(' - ')[-1] if ' - ' in vehicle_vin else vehicle_vin
                                        qr_path_map[vehicle_vin] = qr_path
                                        qr_path_map[raw_vin] = qr_path

                            # Write data rows
                            for idx, vehicle in enumerate(vehicles):
                                row_data = []
                                for field in template_fields:
                                    field_mapping = field.get('mapping', '').strip()
                                    if field_mapping:
                                        if field_mapping == 'teststock':
                                            value = vehicle.get('stock', '') or vehicle.get('raw_stock', '')
                                        elif field_mapping == 'year_model':
                                            yearmake = vehicle.get('yearmake', '')
                                            model = vehicle.get('model', '')
                                            value = f"{yearmake} {model}".strip()
                                        elif field_mapping == 'year_model_stock':
                                            yearmake = vehicle.get('yearmake', '')
                                            model = vehicle.get('model', '')
                                            stock = vehicle.get('stock', '') or vehicle.get('raw_stock', '')
                                            year = yearmake.split()[0] if yearmake else ''
                                            value = f"{year} {model} - {stock}".strip()
                                        elif field_mapping == 'vin_prefix':
                                            vin = vehicle.get('vin', '')
                                            type_prefix = self._get_type_prefix(vehicle.get('vehicle_condition', ''))
                                            value = f"{type_prefix} - {vin}"
                                        elif field_mapping == '@qr':
                                            vin = vehicle.get('vin', '')
                                            value = qr_path_map.get(vin, qr_paths[idx] if idx < len(qr_paths) else '')
                                        else:
                                            value = vehicle.get(field_mapping, '')
                                    else:
                                        value = ''
                                    row_data.append(value)
                                writer.writerow(row_data)

                    except Exception as e:
                        logger.error(f"[CUSTOM TEMPLATE CSV] Error loading template: {e}")
                        # Fallback to empty CSV
                        pass

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
    
    def _generate_billing_sheet_csv(self, vehicles: List[Dict], dealership_name: str, output_folder: Path, timestamp: str,
                                    original_vin_list: List[str] = None, filtered_vin_list: List[str] = None, order_type: str = 'CAO') -> Path:
        """Generate billing sheet CSV automatically after QR codes - matches exact format from examples

        Args:
            vehicles: List of vehicle dictionaries
            dealership_name: Name of dealership
            output_folder: Output folder path
            timestamp: Timestamp string
            original_vin_list: Optional list of original VINs (for LIST orders)
            filtered_vin_list: Optional list of filtered VINs (for LIST orders)
        """
        
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
            vtype = vehicle.get('vehicle_condition', '').lower()

            # Strip prefix from VIN for database lookup (e.g., "NEW - VIN" -> "VIN")
            clean_vin = vin.split(' - ')[-1] if ' - ' in vin else vin

            # If vehicle_condition is missing, try to look it up from the database using clean VIN
            if not vtype and clean_vin:
                query = "SELECT vehicle_condition FROM normalized_vehicle_data WHERE vin = %s LIMIT 1"
                result = db_manager.execute_query(query, (clean_vin,))
                if result and len(result) > 0:
                    vtype = (result[0].get('vehicle_condition') or '').lower()
                    logger.info(f"[BILLING DEBUG] Looked up vehicle_condition for VIN {clean_vin}: '{vtype}'")

            # DEBUG: Log first 5 vehicles to see what vehicle_condition values we're getting
            if len(vehicle_lines) < 5:
                logger.info(f"[BILLING DEBUG] Vehicle {len(vehicle_lines)+1}: {year} {make} {model}")
                logger.info(f"[BILLING DEBUG]   - VIN (original): '{vin}'")
                logger.info(f"[BILLING DEBUG]   - VIN (clean): '{clean_vin}'")
                logger.info(f"[BILLING DEBUG]   - vehicle_condition from dict: '{vehicle.get('vehicle_condition', 'MISSING')}'")
                logger.info(f"[BILLING DEBUG]   - vtype (processed): '{vtype}'")
                logger.info(f"[BILLING DEBUG]   - All keys in vehicle: {list(vehicle.keys())}")

            # Determine vehicle type for billing using _get_type_prefix logic
            type_prefix = self._get_type_prefix(vtype)

            if type_prefix == 'NEW':
                billing_type = 'New'
                new_count += 1
            elif type_prefix == 'CERTIFIED':
                billing_type = 'CPO'
                cpo_count += 1
            else:  # USED
                billing_type = 'PO'
                used_count += 1

            # DEBUG: Log the categorization
            if len(vehicle_lines) < 3:
                logger.info(f"[BILLING DEBUG] Type prefix: {type_prefix}, Billing type: {billing_type}")
            
            # Format vehicle line: "Year Make Model - Stock - VIN"
            vehicle_line = f"{year} {make} {model} - {stock} - {vin}"
            vehicle_lines.append([vehicle_line, billing_type])
            vin_list.append(vin)
        
        total_vehicles = len(vehicles)

        # Determine if this is a LIST order - explicitly check order_type
        # CRITICAL: Only LIST orders should show "Not on Website:" section and Ordered/Produced counts
        is_list_order = (order_type == 'LIST' and original_vin_list is not None and filtered_vin_list is not None)

        # DEBUG: Log the LIST order detection
        logger.info(f"[BILLING DEBUG] order_type={order_type}, is_list_order={is_list_order}, original_vin_list={'None' if original_vin_list is None else f'{len(original_vin_list)} VINs'}, filtered_vin_list={'None' if filtered_vin_list is None else f'{len(filtered_vin_list)} VINs'}")

        # Calculate ordered vs produced for LIST orders
        if is_list_order:
            ordered_count = len(original_vin_list)
            produced_count = len(filtered_vin_list)

            # Strip prefixes from both lists for comparison
            # filtered_vin_list may have "NEW - VIN" or "USED - VIN" format
            filtered_vins_clean = []
            for vin in filtered_vin_list:
                clean_vin = vin.split(' - ')[-1] if ' - ' in vin else vin
                filtered_vins_clean.append(clean_vin)

            # Also clean original_vin_list in case it has prefixes
            original_vins_clean = []
            for vin in original_vin_list:
                clean_vin = vin.split(' - ')[-1] if ' - ' in vin else vin
                original_vins_clean.append(clean_vin)

            # Find VINs that were NOT produced (ordered but not in output)
            # Compare cleaned VINs from both lists
            not_produced_vins = [vin for vin in original_vins_clean if vin not in filtered_vins_clean]

            logger.info(f"[BILLING DEBUG] original_vin_list: {original_vin_list}")
            logger.info(f"[BILLING DEBUG] original_vins_clean: {original_vins_clean}")
            logger.info(f"[BILLING DEBUG] filtered_vins_clean: {filtered_vins_clean}")
            logger.info(f"[BILLING DEBUG] not_produced_vins: {not_produced_vins}")

            # Check for duplicates by comparing input VINs against VIN log
            # This tracks vehicles that are "losing graphics" (getting re-done)
            duplicates_count = 0
            duplicate_vins = []

            # Get VIN log table name using centralized method (ensures consistency)
            vin_log_table = self._get_dealership_vin_log_table(dealership_name)

            logger.info(f"[BILLING DEBUG] Checking {len(original_vin_list)} input VINs for duplicates in {vin_log_table}")
            logger.info(f"[BILLING DEBUG] original_vin_list contents: {original_vin_list}")

            # Check each INPUT VIN (from original order) against the VIN log
            for vin in original_vin_list:
                # Strip prefix (NEW -, USED -, etc.) to get raw VIN
                clean_vin = vin.split(' - ')[-1] if ' - ' in vin else vin

                check_query = f"SELECT vin FROM {vin_log_table} WHERE vin = %s LIMIT 1"
                logger.info(f"[BILLING DEBUG] Executing query: {check_query} with VIN={clean_vin} (original: {vin})")
                result = db_manager.execute_query(check_query, (clean_vin,))
                logger.info(f"[BILLING DEBUG] Query result for {clean_vin}: {result}")

                if result and len(result) > 0:
                    duplicates_count += 1
                    duplicate_vins.append(vin)
                    logger.info(f"[BILLING DEBUG] Found duplicate (re-done vehicle): {vin}")

            logger.info(f"[BILLING DEBUG] Total duplicates found: {duplicates_count} (vehicles being re-done)")
        else:
            ordered_count = None
            produced_count = None
            not_produced_vins = []
            duplicates_count = 0
            duplicate_vins = []

        # Write billing CSV in NEW format matching template
        with open(billing_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Build duplicate vehicle details for right column display
            duplicate_vehicle_details = []
            if is_list_order and duplicate_vins:
                for dup_vin in duplicate_vins:
                    # Find vehicle details for this duplicate VIN
                    for vehicle in vehicles:
                        if vehicle.get('vin') == dup_vin:
                            duplicate_vehicle_details.append({
                                'vin': dup_vin,
                                'year': vehicle.get('year', ''),
                                'make': vehicle.get('make', ''),
                                'model': vehicle.get('model', ''),
                                'stock': vehicle.get('stock', '').split(' - ')[-1] if ' - ' in vehicle.get('stock', '') else vehicle.get('stock', ''),
                                'type': vehicle.get('vehicle_condition', 'used').upper()
                            })
                            break

            # Row 1: Header row with Duplicates count and VINs
            logger.info(f"[BILLING DEBUG] Writing header row with duplicates_count={duplicates_count}, duplicate_vins={duplicate_vins}")
            header_row = ['Printed Vehicles:', '', '', '', '', 'TOTALS:', '', '', 'Duplicates:', duplicates_count, '']
            # Add duplicate VINs to the right of the count
            if duplicate_vins:
                header_row.extend(duplicate_vins)
            writer.writerow(header_row)

            # Rows 2-8: Vehicle data with totals on right
            for i, (vehicle_line, vehicle_type) in enumerate(vehicle_lines):
                # Get the actual vehicle data to extract correct fields
                vehicle = vehicles[i] if i < len(vehicles) else {}

                vehicle_vin = vehicle.get('vin', '')

                # Strip type prefix from VIN if present (e.g., "USED - 1C4RJYB67PC669752" -> "1C4RJYB67PC669752")
                if ' - ' in vehicle_vin:
                    vehicle_vin = vehicle_vin.split(' - ')[-1].strip()

                year = vehicle.get('year', '')
                make = vehicle.get('make', '')
                model = vehicle.get('model', '')

                # Extract just the stock number from the formatted stock field
                # Stock format: "2021 Wrangler - 9257" -> extract "9257"
                stock_field = vehicle.get('stock', '')
                if ' - ' in stock_field:
                    stock = stock_field.split(' - ')[-1].strip()
                else:
                    stock = stock_field.strip()

                # Vehicle description: "Year Make Model"
                vehicle_desc = f"{year} {make} {model}"

                # Build left side: VIN, Vehicle Description, Stock, Type, Empty
                row = [vehicle_vin, vehicle_desc, stock, vehicle_type, '']

                # Add totals column based on row number
                if i == 0:
                    row.extend(['New:', new_count, ''])
                elif i == 1:
                    row.extend(['PO:', used_count, ''])
                elif i == 2:
                    row.extend(['CPO:', cpo_count, ''])
                elif i == 3:
                    row.extend(['Total:', total_vehicles, ''])
                elif i == 4 and is_list_order:
                    row.extend(['Ordered:', ordered_count, ''])
                elif i == 5 and is_list_order:
                    row.extend(['Produced:', produced_count, ''])
                else:
                    row.extend(['', '', ''])

                # Add duplicate details on right side (starting column J)
                # Only add if we have duplicate data and it's within range
                dup_index = i - 1  # Duplicates start on row 2 (index 1)
                if dup_index >= 0 and dup_index < len(duplicate_vehicle_details):
                    dup = duplicate_vehicle_details[dup_index]
                    row.extend([dup['vin'], dup['year'], dup['make'], dup['model'], dup['stock'], dup['type']])
                else:
                    row.extend(['', '', '', '', '', ''])

                writer.writerow(row)

            # Continue with remaining vehicles if any (after summary rows)
            remaining_start = 6 if is_list_order else 4
            for i in range(remaining_start, len(vehicle_lines)):
                vehicle_line, vehicle_type = vehicle_lines[i]

                # Get the actual vehicle data
                vehicle = vehicles[i] if i < len(vehicles) else {}

                vehicle_vin = vehicle.get('vin', '')

                # Strip type prefix from VIN if present
                if ' - ' in vehicle_vin:
                    vehicle_vin = vehicle_vin.split(' - ')[-1].strip()

                year = vehicle.get('year', '')
                make = vehicle.get('make', '')
                model = vehicle.get('model', '')

                # Extract just the stock number
                stock_field = vehicle.get('stock', '')
                if ' - ' in stock_field:
                    stock = stock_field.split(' - ')[-1].strip()
                else:
                    stock = stock_field.strip()

                vehicle_desc = f"{year} {make} {model}"

                row = [vehicle_vin, vehicle_desc, stock, vehicle_type, '', '', '', '']

                # Add duplicate details if available
                dup_index = i - 1
                if dup_index >= 0 and dup_index < len(duplicate_vehicle_details):
                    dup = duplicate_vehicle_details[dup_index]
                    row.extend([dup['vin'], dup['year'], dup['make'], dup['model'], dup['stock'], dup['type']])
                else:
                    row.extend(['', '', '', '', '', ''])

                writer.writerow(row)

            # Add "Not on Website" section at bottom (for LIST orders with VINs not in scraper)
            if is_list_order and not_produced_vins:
                # Add separator rows
                writer.writerow(['', '', '', '', '', '', '', '', '', '', '', '', '', ''])

                # Start "Not on Website" section
                for idx, not_produced_vin in enumerate(not_produced_vins):
                    if idx == 0:
                        # First row has the header
                        writer.writerow(['', '', '', '', '', 'Not on Website:', not_produced_vin, '', '', '', '', '', '', ''])
                    else:
                        # Subsequent rows just have the VIN
                        writer.writerow(['', '', '', '', '', '', not_produced_vin, '', '', '', '', '', '', ''])
        
        logger.info(f"Generated billing sheet CSV: {billing_path}")
        return billing_path

    def _process_concatenated_formula(self, formula: str, vehicle: Dict) -> str:
        """
        Dynamically process a concatenated field formula.

        Formula uses placeholders like:
        - {yearmake} - direct field access
        - {model} - direct field access
        - {stock_number} - extracts number from stock field
        - {year} - extracts year from yearmake
        - etc.

        Example: "{yearmake} - {stock_number}" becomes "2026 Porsche - TLB40309"
        """
        import re

        result = formula

        # Find all placeholders in the formula
        placeholders = re.findall(r'\{(\w+)\}', formula)

        for placeholder in placeholders:
            value = ''

            # Special handlers for computed fields
            if placeholder == 'stock_number':
                # Extract just the stock number from the full stock field
                stock = vehicle.get('stock', '') or vehicle.get('raw_stock', '')
                if ' - ' in stock:
                    value = stock.split(' - ')[-1]
                else:
                    value = stock
            elif placeholder == 'year':
                # Extract year from yearmake (e.g., "2026 Porsche" -> "2026")
                yearmake = vehicle.get('yearmake', '')
                if yearmake:
                    value = yearmake.split()[0] if yearmake.split() else ''
            elif placeholder == 'make':
                # Extract make from yearmake (e.g., "2026 Porsche" -> "Porsche")
                yearmake = vehicle.get('yearmake', '')
                parts = yearmake.split()
                value = ' '.join(parts[1:]) if len(parts) > 1 else ''
            else:
                # Direct field access
                value = vehicle.get(placeholder, '')

            # Replace placeholder with value
            result = result.replace(f'{{{placeholder}}}', str(value))

        return result.strip()

    def _generate_custom_template_csv(self, vehicles: List[Dict], template_type: str,
                                    csvfile, qr_paths: List[str], dealership_name: str):
        """Generate custom template CSV data directly to an open file handle"""
        import csv

        # Check if template_type starts with "custom_" to extract template ID
        if template_type.startswith('custom_'):
            template_id = template_type.replace('custom_', '')
            logger.info(f"[CUSTOM TEMPLATE] Processing custom template ID: {template_id} for {dealership_name}")

            # Load custom template configuration from template builder
            try:
                # Import here to avoid circular dependencies
                from order_queue_manager import OrderQueueManager
                queue_manager = OrderQueueManager()

                # Get the custom template configuration
                template_config = queue_manager.get_template_by_id(template_id)
                if not template_config:
                    logger.error(f"[CUSTOM TEMPLATE] Template ID {template_id} not found")
                    # Fallback to standard shortcut format
                    self._write_shortcut_format(csvfile, vehicles, qr_paths)
                    return

                # Extract fields from template configuration (now correctly formatted)
                template_fields = template_config.get('fields', [])
                logger.info(f"[CUSTOM TEMPLATE] Found {len(template_fields)} fields in template")
                logger.info(f"[CUSTOM TEMPLATE DEBUG] Template fields: {template_fields}")

                # Write custom template CSV based on the field configuration
                writer = csv.writer(csvfile)

                # Create header row from template fields
                headers = []
                for field in template_fields:
                    field_name = field.get('name', '').strip()
                    if field_name:
                        headers.append(field_name)

                if headers:
                    writer.writerow(headers)
                    logger.info(f"[CUSTOM TEMPLATE] Wrote headers: {headers}")

                # Create QR path mapping for quick lookup
                qr_path_map = {}
                if qr_paths:
                    for idx, qr_path in enumerate(qr_paths):
                        if idx < len(vehicles):
                            vehicle_vin = vehicles[idx].get('vin', '')
                            if vehicle_vin:
                                # Strip prefix (NEW - , USED - , etc.) from VIN for mapping
                                raw_vin = vehicle_vin
                                if ' - ' in vehicle_vin:
                                    raw_vin = vehicle_vin.split(' - ')[-1]
                                # Map both prefixed and raw VIN to the same QR path
                                qr_path_map[vehicle_vin] = qr_path  # Keep original for backward compatibility
                                qr_path_map[raw_vin] = qr_path      # Add raw VIN mapping

                # Write data rows
                for idx, vehicle in enumerate(vehicles):
                    if idx == 0:  # Debug first vehicle only
                        logger.info(f"[CUSTOM TEMPLATE DEBUG] First vehicle data: {dict(vehicle)}")

                    row_data = []
                    for field in template_fields:
                        field_name = field.get('name', '').strip()
                        field_mapping = field.get('mapping', '').strip()
                        field_type = field.get('type', '').strip()

                        if field_mapping:
                            # DYNAMIC CONCATENATED FIELD PROCESSING
                            # If field type is 'concatenated' and has a formula, use dynamic processing
                            if field_type == 'concatenated' and field.get('formula'):
                                formula = field.get('formula', '')
                                value = self._process_concatenated_formula(formula, vehicle)
                            # Handle composite and calculated fields based on actual vehicle data structure
                            elif field_mapping == 'teststock':
                                # STOCK field concatenated format: uses the pre-formatted stock field
                                # This already contains "YEAR MODEL - STOCK#" format (e.g., "2026 Camry - T41990")
                                value = vehicle.get('stock', '') or vehicle.get('raw_stock', '')
                            elif field_mapping == 'year_model':
                                # Use yearmake + model (e.g., "2021 Jeep Wrangler")
                                yearmake = vehicle.get('yearmake', '')
                                model = vehicle.get('model', '')
                                value = f"{yearmake} {model}".strip()
                            elif field_mapping == 'year_make_stock':
                                # Similar to year_model_stock but with make instead of model
                                yearmake = vehicle.get('yearmake', '')  # "2026 Porsche"
                                # Use raw_stock as fallback if normalized stock is empty
                                stock = vehicle.get('stock', '') or vehicle.get('raw_stock', '')  # "2026 Macan - TLB40309"

                                # Extract just the stock number from the stock field
                                if ' - ' in stock:
                                    stock_number = stock.split(' - ')[-1]
                                else:
                                    stock_number = stock

                                value = f"{yearmake} - {stock_number}".strip()
                            elif field_mapping == 'year_model_stock':
                                # Extract year from yearmake and combine with model and stock number
                                yearmake = vehicle.get('yearmake', '')  # "2021 Jeep"
                                model = vehicle.get('model', '')        # "Wrangler"
                                # Use raw_stock as fallback if normalized stock is empty
                                stock = vehicle.get('stock', '') or vehicle.get('raw_stock', '')  # "2021 Wrangler - 9257"

                                # Extract just the stock number from the stock field
                                # stock typically looks like "2021 Wrangler - 9257", we want just "9257"
                                if ' - ' in stock:
                                    stock_number = stock.split(' - ')[-1]
                                else:
                                    stock_number = stock

                                value = f"{yearmake} {model} - {stock_number}".strip()
                            elif field_mapping == 'type_vin':
                                # vin field already contains "USED - VIN", just use it directly
                                vin = vehicle.get('vin', '')
                                value = vin.strip()
                            elif field_mapping == 'price_with_markup':
                                # Handle price with markup calculation
                                try:
                                    # Get MSRP from database since it's not in the vehicle dict
                                    msrp = 0
                                    vin = vehicle.get('vin', '')

                                    # Extract raw VIN (remove "NEW - " or "USED - " prefix)
                                    raw_vin = vin
                                    if ' - ' in vin:
                                        raw_vin = vin.split(' - ')[-1]

                                    logger.info(f"[PRICE DEBUG] Looking up MSRP for VIN: {raw_vin}")

                                    try:
                                        from database_connection import db_manager
                                        # Query for MSRP and price from normalized_vehicle_data
                                        # Use MSRP if available, otherwise fall back to price
                                        price_result = db_manager.execute_query(
                                            "SELECT msrp, price FROM normalized_vehicle_data WHERE vin = %s LIMIT 1",
                                            (raw_vin,)
                                        )
                                        if price_result and len(price_result) > 0:
                                            msrp = price_result[0].get('msrp')
                                            price = price_result[0].get('price', 0)

                                            # Use MSRP if available, otherwise use price
                                            if msrp is not None:
                                                logger.info(f"[PRICE DEBUG] Using MSRP from database: {msrp}")
                                                base_price = msrp
                                            else:
                                                logger.info(f"[PRICE DEBUG] MSRP is null, using price instead: {price}")
                                                base_price = price

                                            if isinstance(base_price, str):
                                                # Remove currency symbols and commas
                                                base_price = base_price.replace('$', '').replace(',', '')
                                                msrp = float(base_price) if base_price else 0
                                            else:
                                                msrp = float(base_price) if base_price else 0
                                        else:
                                            logger.warning(f"[PRICE DEBUG] No price data found for VIN: {raw_vin}")
                                    except Exception as e:
                                        logger.warning(f"[CUSTOM TEMPLATE] Could not fetch price from database: {e}")
                                        msrp = 0

                                    logger.info(f"[PRICE DEBUG] Final MSRP value: {msrp}")

                                    # Get markup from dealership config in database
                                    markup = 1000  # default
                                    try:
                                        config_result = db_manager.execute_query(
                                            "SELECT output_rules FROM dealership_configs WHERE name = %s",
                                            (dealership_name,)
                                        )
                                        if config_result and len(config_result) > 0:
                                            output_rules = config_result[0].get('output_rules', {})
                                            markup = output_rules.get('price_markup', 1000)
                                            logger.info(f"[PRICE DEBUG] Markup from config: {markup}")
                                    except Exception as e:
                                        logger.warning(f"[CUSTOM TEMPLATE] Could not fetch dealership markup: {e}")
                                        markup = field.get('markup_amount', 1000)

                                    price_with_markup = msrp + markup
                                    logger.info(f"[PRICE DEBUG] Final calculation: {msrp} + {markup} = {price_with_markup}")
                                    value = f"${price_with_markup:,.0f}" if price_with_markup > 0 else '$1,000'
                                    logger.info(f"[PRICE DEBUG] Final value: {value}")
                                except (ValueError, TypeError) as e:
                                    logger.warning(f"[CUSTOM TEMPLATE] Error calculating price_with_markup: {e}")
                                    value = '$1,000'
                            elif field_mapping in ['qr_code', 'qr_path']:
                                vin = vehicle.get('vin', '')
                                logger.info(f"[QR DEBUG] Looking for QR path for VIN: {vin}")
                                logger.info(f"[QR DEBUG] Available keys in qr_path_map: {list(qr_path_map.keys())[:5]}")
                                # Try to get QR path using the VIN as-is first
                                value = qr_path_map.get(vin, '')
                                logger.info(f"[QR DEBUG] Found with full VIN: {value}")
                                # If not found, try stripping the prefix
                                if not value and ' - ' in vin:
                                    raw_vin = vin.split(' - ')[-1]
                                    value = qr_path_map.get(raw_vin, '')
                                    logger.info(f"[QR DEBUG] Found with raw VIN ({raw_vin}): {value}")
                                logger.info(f"[QR DEBUG] Final QR path: {value}")
                            # Handle direct field mappings using actual vehicle data structure
                            elif field_mapping == 'yearmake':
                                value = vehicle.get('yearmake', '')
                            elif field_mapping == 'model':
                                value = vehicle.get('model', '')
                            elif field_mapping == 'stock':
                                # Use raw_stock as fallback if normalized stock is empty
                                value = vehicle.get('stock', '') or vehicle.get('raw_stock', '')
                            elif field_mapping == 'vin':
                                value = vehicle.get('vin', '')
                            elif field_mapping == 'price':
                                value = vehicle.get('price', '')
                            elif field_mapping == 'trim':
                                value = vehicle.get('trim', '')
                            elif field_mapping == 'ext_color':
                                value = vehicle.get('ext_color', '')
                            # Legacy mappings for backwards compatibility
                            elif field_mapping == 'year':
                                # Extract year from yearmake field
                                yearmake = vehicle.get('yearmake', '')
                                value = yearmake.split()[0] if yearmake else ''
                            elif field_mapping == 'make':
                                # Extract make from yearmake field
                                yearmake = vehicle.get('yearmake', '')
                                parts = yearmake.split()
                                value = ' '.join(parts[1:]) if len(parts) > 1 else ''
                            elif field_mapping == 'year_make_model':
                                yearmake = vehicle.get('yearmake', '')
                                model = vehicle.get('model', '')
                                value = f"{yearmake} {model}".strip()
                            else:
                                # Try direct field access for any other mappings
                                value = vehicle.get(field_mapping, '')
                        else:
                            value = ''

                        # Use "*" as placeholder for empty fields to prevent Adobe import misalignment
                        row_data.append(str(value) if value else '*')

                    writer.writerow(row_data)

                logger.info(f"[CUSTOM TEMPLATE] Generated CSV with {len(vehicles)} vehicles using custom template {template_id}")

            except Exception as e:
                logger.error(f"[CUSTOM TEMPLATE] Error processing custom template: {e}")
                # Fallback to standard shortcut format
                self._write_shortcut_format(csvfile, vehicles, qr_paths)
        else:
            # Handle standard template types
            if template_type == "shortcut":
                self._write_shortcut_format(csvfile, vehicles, qr_paths)
            elif template_type == "flyout":
                self._write_flyout_format(csvfile, vehicles, qr_paths)
            else:
                logger.warning(f"[CUSTOM TEMPLATE] Unknown template type: {template_type}, using shortcut format")
                self._write_shortcut_format(csvfile, vehicles, qr_paths)

    def _write_shortcut_format(self, csvfile, vehicles: List[Dict], qr_paths: List[str]):
        """Write shortcut format CSV"""
        import csv
        writer = csv.writer(csvfile)
        writer.writerow(['QRYEARMODEL', 'QRSTOCK', '@QR2'])

        for idx, vehicle in enumerate(vehicles):
            year = vehicle.get('year', '')
            make = vehicle.get('make', '')
            model = vehicle.get('model', '')
            stock = vehicle.get('stock', '')
            qr_path = qr_paths[idx] if idx < len(qr_paths) else ''

            year_make_model = f"{year} {make} {model}".strip()
            writer.writerow([year_make_model, stock, qr_path])

    def _write_flyout_format(self, csvfile, vehicles: List[Dict], qr_paths: List[str]):
        """Write flyout format CSV"""
        import csv
        writer = csv.writer(csvfile)
        writer.writerow(['QRYEARMODEL', 'QRPRICE', '@QR2'])

        for idx, vehicle in enumerate(vehicles):
            year = vehicle.get('year', '')
            make = vehicle.get('make', '')
            model = vehicle.get('model', '')
            price = vehicle.get('price', '')
            qr_path = qr_paths[idx] if idx < len(qr_paths) else ''

            year_make_model = f"{year} {make} {model}".strip()
            writer.writerow([year_make_model, price, qr_path])

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

    def generate_final_files(self, dealership_name: str, vehicles_data: List[Dict],
                            order_number: str, template_type: str = None,
                            custom_templates: Dict = None, skip_vin_logging: bool = False) -> Dict[str, Any]:
        """
        Generate final output files (CSV, QR codes, billing sheet) from reviewed vehicle data.
        This is called after user reviews and confirms vehicles in the modal wizard.

        Args:
            dealership_name: Name of the dealership
            vehicles_data: List of vehicle dictionaries (from review stage)
            order_number: Order number entered by user
            template_type: Template type to use
            custom_templates: Custom template configuration dict
            skip_vin_logging: Whether to skip VIN log updates

        Returns:
            Dict with success status, file paths, and generation details
        """
        try:
            logger.info(f"[GENERATE FINAL FILES] Starting for {dealership_name} with order {order_number}")
            logger.info(f"[GENERATE FINAL FILES] Processing {len(vehicles_data)} vehicles")

            # Create output folder with order number
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dealership_slug = dealership_name.replace(' ', '_').replace("'", '')
            output_folder = self.output_base / dealership_name / f"{timestamp}_{order_number}"
            output_folder.mkdir(parents=True, exist_ok=True)

            logger.info(f"[GENERATE FINAL FILES] Output folder: {output_folder}")

            # Step 1: Generate QR codes
            qr_folder = output_folder / "qr_codes"
            qr_folder.mkdir(exist_ok=True)
            qr_paths = self._generate_qr_codes(vehicles_data, dealership_name, qr_folder)
            logger.info(f"[GENERATE FINAL FILES] Generated {len(qr_paths)} QR codes")

            # Step 2: Check for dual template configuration
            dual_template_config = None
            if custom_templates and isinstance(custom_templates, dict):
                if 'new' in custom_templates and 'used' in custom_templates:
                    dual_template_config = custom_templates
                    logger.info(f"[GENERATE FINAL FILES] Dual template detected: NEW={custom_templates['new']}, USED={custom_templates['used']}")

            # Step 3: Generate Adobe CSV(s) - split by condition if dual template config exists
            csv_paths = []
            if dual_template_config:
                # Generate separate CSVs for NEW and USED vehicles
                logger.info(f"[GENERATE FINAL FILES] Generating separate NEW and USED CSVs")

                # Split vehicles by condition
                new_vehicles = []
                used_vehicles = []
                new_qr_paths = []
                used_qr_paths = []

                for idx, vehicle in enumerate(vehicles_data):
                    condition = str(vehicle.get('condition', '')).lower()
                    if condition == 'new':
                        new_vehicles.append(vehicle)
                        new_qr_paths.append(qr_paths[idx])
                    else:
                        used_vehicles.append(vehicle)
                        used_qr_paths.append(qr_paths[idx])

                logger.info(f"[GENERATE FINAL FILES] Split: {len(new_vehicles)} NEW, {len(used_vehicles)} USED")

                # Generate NEW CSV if there are new vehicles
                if new_vehicles:
                    new_csv_path = self._generate_adobe_csv(
                        new_vehicles,
                        dealership_name,
                        dual_template_config['new'],
                        output_folder,
                        new_qr_paths,
                        suffix='_NEW'
                    )
                    csv_paths.append(new_csv_path)
                    logger.info(f"[GENERATE FINAL FILES] Generated NEW CSV: {new_csv_path}")

                # Generate USED CSV if there are used vehicles
                if used_vehicles:
                    used_csv_path = self._generate_adobe_csv(
                        used_vehicles,
                        dealership_name,
                        dual_template_config['used'],
                        output_folder,
                        used_qr_paths,
                        suffix='_USED'
                    )
                    csv_paths.append(used_csv_path)
                    logger.info(f"[GENERATE FINAL FILES] Generated USED CSV: {used_csv_path}")

                # Set primary CSV path for backward compatibility
                csv_path = csv_paths[0] if csv_paths else None
            else:
                # Single template - generate one CSV
                if not template_type:
                    if custom_templates:
                        # Use custom template for 'used' vehicles (CAO primarily processes used)
                        template_type = custom_templates.get('used', '') or custom_templates.get('new', '')
                        if not template_type:
                            template_type = self._get_dealership_template_config(dealership_name)
                    else:
                        template_type = self._get_dealership_template_config(dealership_name)

                logger.info(f"[GENERATE FINAL FILES] Using template type: {template_type}")

                csv_path = self._generate_adobe_csv(
                    vehicles_data,
                    dealership_name,
                    template_type,
                    output_folder,
                    qr_paths
                )
                csv_paths = [csv_path]
                logger.info(f"[GENERATE FINAL FILES] Generated CSV: {csv_path}")

            # Step 4: Generate billing sheet CSV
            billing_path = self._generate_billing_sheet_csv(
                vehicles_data,
                dealership_name,
                output_folder,
                timestamp
            )
            logger.info(f"[GENERATE FINAL FILES] Generated billing sheet: {billing_path}")

            # Step 5: Update VIN log with order number (if not skipping)
            if not skip_vin_logging:
                vins = [v.get('vin', '') for v in vehicles_data if v.get('vin')]
                if vins:
                    self._update_vin_history(dealership_name, vins)
                    logger.info(f"[GENERATE FINAL FILES] Updated VIN log for {len(vins)} vehicles")

            return {
                'success': True,
                'output_folder': str(output_folder),
                'csv_path': str(csv_path) if csv_path else None,
                'csv_paths': [str(p) for p in csv_paths] if csv_paths else [],
                'billing_path': str(billing_path),
                'qr_folder': str(qr_folder),
                'qr_paths': qr_paths,
                'qr_codes_generated': len(qr_paths),
                'order_number': order_number,
                'dealership_name': dealership_name
            }

        except Exception as e:
            logger.error(f"[GENERATE FINAL FILES] Error: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

# Test the correct processor
if __name__ == "__main__":
    processor = CorrectOrderProcessor()
    
    # Test CAO order with Dave Sinclair Lincoln
    result = processor.process_cao_order("Dave Sinclair Lincoln", "shortcut_pack")
    print(json.dumps(result, indent=2))

