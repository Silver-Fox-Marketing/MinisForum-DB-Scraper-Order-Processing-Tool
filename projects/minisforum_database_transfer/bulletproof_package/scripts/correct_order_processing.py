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
            # REMOVED: 'HW Kia': 'HW Kia of West County',  # This was causing VIN logging issues
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
    
    def process_cao_order(self, dealership_name: str, template_type: str = None, skip_vin_logging: bool = False) -> Dict[str, Any]:
        """
        Process CAO (Comparative Analysis Order)
        
        Steps from reference:
        1. Get filtered vehicles based on dealership requirements
        2. Compare VIN lists to find NEW vehicles on lot
        3. Generate QR codes for new vehicles
        4. Output QR file paths + Adobe CSV
        """
        
        # Get template type from config if not specified
        if template_type is None:
            template_type = self._get_dealership_template_config(dealership_name)

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
            
            # Step 5: Generate CSV files based on template type configuration
            csv_files = {}

            # Check if dealership has mixed template types (different for new vs used)
            new_template = self._get_dealership_template_config(dealership_name, 'new')
            used_template = self._get_dealership_template_config(dealership_name, 'used')

            if new_template != used_template:
                # Use mixed template processing for dealerships with different templates
                csv_path = self._process_mixed_template_output(new_vehicles, dealership_name, order_folder, qr_paths)
            else:
                # Use simple single template processing for most dealerships
                csv_path = self._generate_adobe_csv(new_vehicles, dealership_name, new_template, order_folder, qr_paths)

            # If multiple CSV files were generated, csv_path will be the primary file
            if isinstance(csv_path, dict):
                csv_files = csv_path
                csv_path = csv_files.get('primary_csv') or list(csv_files.values())[0]
            
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
                'csv_file': str(csv_path) if not isinstance(csv_path, dict) else str(csv_path.get('primary_csv', '')),
                'export_file': str(csv_path) if not isinstance(csv_path, dict) else str(csv_path.get('primary_csv', '')),
                'download_csv': f"/download_csv/{csv_path.name}" if hasattr(csv_path, 'name') else f"/download_csv/{Path(csv_path.get('primary_csv', '')).name}" if isinstance(csv_path, dict) else f"/download_csv/{Path(csv_path).name}",
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

    def prepare_cao_data(self, dealership_name: str, template_type: str = None) -> Dict[str, Any]:
        """
        PHASE 1: Prepare CAO data for review (no file generation)

        Returns vehicle data that can be reviewed and edited before final file generation.
        This replaces the immediate file generation in the wizard workflow.
        """

        # Get template type from config if not specified
        if template_type is None:
            template_type = self._get_dealership_template_config(dealership_name)

        logger.info(f"[CAO PREPARE] Preparing data for {dealership_name} - {template_type}")

        try:
            # Step 1: Get all current vehicles for dealership
            current_vehicles = self._get_dealership_vehicles(dealership_name)
            if not current_vehicles:
                return {'success': False, 'error': 'No vehicles found'}

            logger.info(f"[CAO PREPARE] Found {len(current_vehicles)} total vehicles for {dealership_name}")

            # Step 2: Compare VIN lists to find NEW vehicles (Enhanced Logic)
            current_vins = [v['vin'] for v in current_vehicles]
            logger.info(f"[CAO PREPARE] Current VINs: {current_vins[:5]}..." if len(current_vins) > 5 else f"[CAO PREPARE] Current VINs: {current_vins}")

            new_vins = self._find_new_vehicles_enhanced(dealership_name, current_vins, current_vehicles)
            logger.info(f"[CAO PREPARE] NEW VINs after comparison: {new_vins[:5]}..." if len(new_vins) > 5 else f"[CAO PREPARE] NEW VINs after comparison: {new_vins}")

            # Filter to only NEW vehicles
            new_vehicles = [v for v in current_vehicles if v['vin'] in new_vins]
            logger.info(f"[CAO PREPARE] Found {len(new_vehicles)} NEW vehicles for review: {dealership_name}")

            if not new_vehicles:
                return {'success': True, 'new_vehicles': 0, 'message': 'No new vehicles to process'}

            # Return prepared data for review - NO FILE GENERATION YET
            result = {
                'success': True,
                'dealership': dealership_name,
                'template_type': template_type,
                'total_vehicles': len(current_vehicles),
                'new_vehicles': len(new_vehicles),
                'vehicle_count': len(new_vehicles),
                'vehicles_data': new_vehicles,  # Raw vehicle data for review
                'vehicles_for_review': new_vehicles,  # Alias for clarity
                'phase': 'data_prepared',
                'ready_for_review': True
            }

            return result

        except Exception as e:
            logger.error(f"Error preparing CAO data: {e}")
            return {'success': False, 'error': str(e)}

    def prepare_list_data(self, dealership_name: str, vin_list: List[str], template_type: str = None) -> Dict[str, Any]:
        """
        PHASE 1: Prepare LIST data for review (with VIN validation)

        Validates VINs against scraper data and returns only valid vehicles for review.
        Invalid VINs are filtered out before the review stage.
        """

        # Get template type from config if not specified
        if template_type is None:
            template_type = self._get_dealership_template_config(dealership_name)

        logger.info(f"[LIST PREPARE] Preparing LIST data for {dealership_name} with {len(vin_list)} VINs - Template: {template_type}")

        try:
            # LIST orders: Validate VINs against scraper data - only include VINs that exist in inventory
            # CRITICAL: Filter out VINs not found in scraper data to prevent "Unknown" records in review stage
            valid_vehicles = []
            valid_vins = []
            invalid_vins = []

            for vin in vin_list:
                # Try to get vehicle data from active scraper data only
                vehicle_data = db_manager.execute_query("""
                    SELECT nvd.* FROM normalized_vehicle_data nvd
                    JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                    JOIN scraper_imports si ON rvd.import_id = si.import_id
                    WHERE nvd.vin = %s AND nvd.location = %s AND si.status = 'active'
                    ORDER BY rvd.import_timestamp DESC
                    LIMIT 1
                """, (vin, dealership_name))

                if vehicle_data:
                    # VIN found in active scraper data - include it
                    valid_vehicles.append(vehicle_data[0])
                    valid_vins.append(vin)
                    logger.info(f"[LIST PREPARE] VIN found in scraper data: {vin}")
                else:
                    # VIN NOT found in scraper data - exclude from review stage
                    invalid_vins.append(vin)
                    logger.warning(f"[LIST PREPARE] VIN not found in scraper data, excluding: {vin}")

            # Log validation results
            logger.info(f"[LIST PREPARE] Valid VINs (found in scraper data): {len(valid_vins)}")
            logger.info(f"[LIST PREPARE] Invalid VINs (not in scraper data): {len(invalid_vins)}")
            if invalid_vins:
                logger.info(f"[LIST PREPARE] Excluded VINs: {invalid_vins}")

            if not valid_vehicles:
                return {
                    'success': False,
                    'error': f'No valid VINs found in scraper data. Excluded VINs: {invalid_vins}'
                }

            # CRITICAL FIX: Format vehicles for preview to match CSV template output format
            # This ensures the review stage shows the same formatted data that appears in the final CSV
            formatted_vehicles_for_preview = self._format_vehicles_for_preview(valid_vehicles, dealership_name)
            logger.info(f"[LIST PREPARE] Formatted {len(formatted_vehicles_for_preview)} vehicles for review stage")

            # Return prepared data for review - with formatted vehicles for preview
            result = {
                'success': True,
                'dealership': dealership_name,
                'template_type': template_type,
                'total_vins_requested': len(vin_list),
                'valid_vins': len(valid_vins),
                'invalid_vins': len(invalid_vins),
                'excluded_vins': invalid_vins,
                'vehicle_count': len(valid_vehicles),
                'vehicles_data': valid_vehicles,  # Raw valid vehicle data for processing
                'vehicles_for_review': formatted_vehicles_for_preview,  # FORMATTED vehicles for preview
                'original_vin_list': vin_list,  # Keep original list for billing
                'filtered_vin_list': valid_vins,  # Valid VINs only
                'phase': 'data_prepared',
                'ready_for_review': True
            }

            logger.info(f"[LIST PREPARE] Successfully prepared {len(valid_vehicles)} vehicles for review (excluded {len(invalid_vins)} invalid VINs)")
            return result

        except Exception as e:
            logger.error(f"Error preparing LIST data: {e}")
            return {'success': False, 'error': str(e)}

    def _convert_qr_path_for_nicks_computer(self, local_qr_path: str, dealership_name: str, qr_index: int) -> str:
        """
        Convert local QR file path to Nick's computer path for VDP CSV compatibility.

        Args:
            local_qr_path: Local path like 'C:\\...\\Dealership_Name_QR_Code_1.png'
            dealership_name: Name of dealership for consistent naming
            qr_index: QR code index (1, 2, 3, etc.)

        Returns:
            Nick's computer path: 'C:\\Users\\Nick_Workstation\\Documents\\QRS\\Dealership_Name_QR_Code_1.PNG'
        """
        if not local_qr_path:
            return ''

        # Clean dealership name for consistent filename
        clean_dealership = dealership_name.replace(' ', '_').replace("'", "")

        # Generate filename using the standard naming system
        qr_filename = f"{clean_dealership}_QR_Code_{qr_index}.PNG"

        # Construct Nick's computer path
        nicks_qr_path = f"C:\\Users\\Nick_Workstation\\Documents\\QRS\\{qr_filename}"

        logger.debug(f"[QR PATH] Converted {local_qr_path} -> {nicks_qr_path}")
        return nicks_qr_path

    def _detect_data_format(self, vehicles_data: List[Dict]) -> str:
        """
        Detect if data is raw DB records or template-formatted data.

        Returns:
            'template_formatted': Data from review stage with template fields
            'raw_database': Raw database records needing normalization
            'unknown': Cannot determine format
        """
        if not vehicles_data:
            return 'unknown'

        sample = vehicles_data[0]

        # Template-formatted data has these key indicators
        if 'YEARMODEL' in sample or '@QR' in sample or 'QRYEARMODEL' in sample:
            logger.info(f"[DATA FORMAT] Detected template-formatted data - sample keys: {list(sample.keys())}")
            return 'template_formatted'

        # Raw DB data has these fields
        elif 'year' in sample and 'make' in sample and 'model' in sample:
            logger.info(f"[DATA FORMAT] Detected raw database data - sample keys: {list(sample.keys())}")
            return 'raw_database'

        else:
            logger.warning(f"[DATA FORMAT] Unknown data format - sample keys: {list(sample.keys())}")
            return 'unknown'

    def generate_final_files(self, dealership_name: str, vehicles_data: List[Dict], order_number: str, template_type: str = None, skip_vin_logging: bool = False) -> Dict[str, Any]:
        """
        PHASE 2: Generate final files from prepared data + order number

        Takes the prepared vehicle data from phase 1, applies any edits from review,
        and generates the final CSV files, QR codes, and applies order number to VIN log.

        ENHANCED: Now handles both raw database records and template-formatted data
        """

        # Get template type from config if not specified
        if template_type is None:
            template_type = self._get_dealership_template_config(dealership_name)

        logger.info(f"[CAO GENERATE] Generating final files for {dealership_name} - Order: {order_number}")
        logger.info(f"[CAO GENERATE] Received {len(vehicles_data)} vehicles for processing")

        # Detect data format and route processing accordingly
        data_format = self._detect_data_format(vehicles_data)

        if data_format == 'template_formatted':
            # Data is already normalized - use direct template processing
            logger.info(f"[CAO GENERATE] Using template-formatted data processing path")
            return self._generate_from_template_data(dealership_name, vehicles_data, order_number, template_type, skip_vin_logging)
        else:
            # Raw data or unknown - continue with existing normalization process
            logger.info(f"[CAO GENERATE] Using raw database processing path (format: {data_format})")
            return self._generate_from_raw_data(dealership_name, vehicles_data, order_number, template_type, skip_vin_logging)

    def _generate_from_raw_data(self, dealership_name: str, vehicles_data: List[Dict], order_number: str, template_type: str, skip_vin_logging: bool) -> Dict[str, Any]:
        """
        Handle raw database records - existing processing logic preserved
        """
        # Log sample vehicle data to verify edits are present
        if vehicles_data:
            logger.info(f"[CAO GENERATE] Sample vehicle data keys: {list(vehicles_data[0].keys())}")
            logger.info(f"[CAO GENERATE] Sample vehicle data: {vehicles_data[0]}")

        try:
            if not vehicles_data:
                return {'success': False, 'error': 'No vehicle data provided for file generation'}

            # Step 1: Create output folders with order number in timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # Include order number in folder name for organization
            folder_name = f"{dealership_name.replace(' ', '_')}_{order_number}_{timestamp}"
            order_folder = self.output_base / folder_name
            qr_folder = order_folder / "qr_codes"

            order_folder.mkdir(parents=True, exist_ok=True)
            qr_folder.mkdir(exist_ok=True)

            # Step 2: Generate QR codes for vehicle URLs
            qr_paths = self._generate_qr_codes(vehicles_data, dealership_name, qr_folder)

            # Step 3: Generate CSV files based on template type configuration
            csv_files = {}

            # Check if dealership has mixed template types (different for new vs used)
            new_template = self._get_dealership_template_config(dealership_name, 'new')
            used_template = self._get_dealership_template_config(dealership_name, 'used')

            if new_template != used_template:
                # Use mixed template processing for dealerships with different templates
                csv_path = self._process_mixed_template_output(vehicles_data, dealership_name, order_folder, qr_paths)
            else:
                # Use simple single template processing for most dealerships
                csv_path = self._generate_adobe_csv(vehicles_data, dealership_name, new_template, order_folder, qr_paths)

            # If multiple CSV files were generated, csv_path will be the primary file
            if isinstance(csv_path, dict):
                csv_files = csv_path
                csv_path = csv_files.get('primary_csv') or list(csv_files.values())[0]

            # Step 4: Generate billing sheet CSV automatically after QR codes
            billing_csv_path = self._generate_billing_sheet_csv(vehicles_data, dealership_name, order_folder, timestamp)

            # Step 5: CRITICAL - Log processed vehicle VINs to history database WITH ORDER NUMBER
            if skip_vin_logging:
                logger.info("Skipping VIN logging - test data processing")
                vin_logging_result = {'success': True, 'vins_logged': 0, 'duplicates_skipped': 0, 'errors': []}
            else:
                # Log VINs with the user-provided order number
                vin_logging_result = self._log_processed_vins_to_history(vehicles_data, dealership_name, 'CAO_ORDER', order_number)

            # Build return result
            result = {
                'success': True,
                'dealership': dealership_name,
                'order_number': order_number,
                'template_type': template_type,
                'vehicle_count': len(vehicles_data),
                'qr_codes_generated': len(qr_paths),
                'qr_folder': str(qr_folder),
                'csv_file': str(csv_path) if not isinstance(csv_path, dict) else str(csv_path.get('primary_csv', '')),
                'export_file': str(csv_path) if not isinstance(csv_path, dict) else str(csv_path.get('primary_csv', '')),
                'download_csv': f"/download_csv/{csv_path.name}" if hasattr(csv_path, 'name') else f"/download_csv/{Path(csv_path.get('primary_csv', '')).name}" if isinstance(csv_path, dict) else f"/download_csv/{Path(csv_path).name}",
                'billing_csv_file': str(billing_csv_path),
                'download_billing_csv': f"/download_csv/{billing_csv_path.name}",
                'timestamp': timestamp,
                'vins_logged_to_history': vin_logging_result['vins_logged'],
                'duplicate_vins_skipped': vin_logging_result['duplicates_skipped'],
                'vin_logging_success': vin_logging_result['success'],
                'phase': 'files_generated'
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
            logger.error(f"Error generating final files: {e}")
            return {'success': False, 'error': str(e)}

    def _generate_from_template_data(self, dealership_name: str, vehicles_data: List[Dict], order_number: str, template_type: str, skip_vin_logging: bool) -> Dict[str, Any]:
        """
        Handle already-normalized template data from review stage.
        Data is already in correct template format with fields like YEARMODEL, TRIM, PRICE.
        """
        logger.info(f"[CAO TEMPLATE] Processing template-formatted data for {dealership_name}")

        # Log sample vehicle data for debugging
        if vehicles_data:
            logger.info(f"[CAO TEMPLATE] Sample keys: {list(vehicles_data[0].keys())}")
            logger.info(f"[CAO TEMPLATE] Sample data: {vehicles_data[0]}")

        try:
            if not vehicles_data:
                return {'success': False, 'error': 'No vehicle data provided for file generation'}

            # Step 1: Create output folders with order number in timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            folder_name = f"{dealership_name.replace(' ', '_')}_{order_number}_{timestamp}"
            order_folder = self.output_base / folder_name
            qr_folder = order_folder / "qr_codes"

            order_folder.mkdir(parents=True, exist_ok=True)
            qr_folder.mkdir(exist_ok=True)

            # Step 2: Generate QR codes using same logic as OLD method
            # Get original vehicle data from database using VINs from template data
            from database_connection import db_manager

            # Map dealership names to match database entries
            def map_dealership_name(name):
                name_mapping = {
                    'South County DCJR': 'South County Dodge Chrysler Jeep RAM',
                    'Glendale Subaru': 'Glendale Chrysler Jeep Dodge Ram',
                    'CDJR of Columbia': 'CDJR of Columbia'
                }
                return name_mapping.get(name, name)

            db_dealership_name = map_dealership_name(dealership_name)
            original_vehicles = []
            for vehicle in vehicles_data:
                vin = self._extract_vin_from_template_data(vehicle)
                if vin:
                    original_vehicle_data = db_manager.execute_query("""
                        SELECT nvd.*, rvd.status as raw_status FROM normalized_vehicle_data nvd
                        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                        JOIN scraper_imports si ON rvd.import_id = si.import_id
                        WHERE nvd.vin = %s AND nvd.location = %s AND si.status = 'active'
                        ORDER BY rvd.import_timestamp DESC
                        LIMIT 1
                    """, (vin, db_dealership_name))
                    if original_vehicle_data:
                        original_vehicles.append(original_vehicle_data[0])
                    else:
                        logger.warning(f"No original vehicle data found for VIN {vin} at {db_dealership_name}")

            logger.info(f"[QR DEBUG] Found {len(original_vehicles)} original vehicle records for QR generation")
            if original_vehicles:
                sample_vehicle = original_vehicles[0]
                sample_url = sample_vehicle.get('vehicle_url', '[NO URL]')
                logger.info(f"[QR DEBUG] Sample vehicle URL: {sample_url}")

            # DIRECT REPLACEMENT: Use the exact same QR generation as OLD method process_cao_order
            logger.info(f"[QR DEBUG] Calling OLD method _generate_qr_codes with {len(original_vehicles)} vehicles")

            # This is the exact same call that process_cao_order uses - line-for-line copy
            qr_paths = self._generate_qr_codes(original_vehicles, dealership_name, qr_folder)

            logger.info(f"[QR DEBUG] Generated {len(qr_paths)} QR codes using OLD method logic")

            # Step 3: Generate CSV files using same logic as OLD method (VDP Shortcut Pack format)
            # Check if dealership uses mixed templates (different for new/used)
            new_template = self._get_dealership_template_config(dealership_name, 'new')
            used_template = self._get_dealership_template_config(dealership_name, 'used')

            csv_files = {}
            if new_template != used_template:
                # Use mixed template processing for dealerships with different templates
                csv_path = self._process_mixed_template_output(vehicles_data, dealership_name, order_folder, qr_paths)
            else:
                # Use simple single template processing for most dealerships (VDP Shortcut Pack format)
                csv_path = self._generate_adobe_csv(vehicles_data, dealership_name, template_type, order_folder, qr_paths)

            # Handle multiple CSV files (same as OLD method)
            if isinstance(csv_path, dict):
                csv_files = csv_path
                csv_path = csv_files.get('primary_csv') or list(csv_files.values())[0]

            # Step 4: Generate billing sheet CSV
            billing_csv_path = self._generate_billing_sheet_csv(vehicles_data, dealership_name, order_folder, timestamp)

            # Step 5: Extract VINs from template data for logging
            if skip_vin_logging:
                logger.info("Skipping VIN logging - test data processing")
                vin_logging_result = {'success': True, 'vins_logged': 0, 'duplicates_skipped': 0, 'errors': []}
            else:
                # Extract VINs from template data - they may be in VIN field or embedded in other fields
                vin_logging_result = self._log_template_vins_to_history(vehicles_data, dealership_name, 'CAO_ORDER', order_number)

            # Build return result
            result = {
                'success': True,
                'dealership': dealership_name,
                'order_number': order_number,
                'template_type': template_type,
                'vehicle_count': len(vehicles_data),
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
                'vin_logging_success': vin_logging_result['success'],
                'phase': 'files_generated'
            }

            return result

        except Exception as e:
            logger.error(f"Error generating files from template data: {e}")
            return {'success': False, 'error': str(e)}

    def _generate_qr_codes_for_template_data(self, vehicles: List[Dict], dealership_name: str, output_folder: Path) -> List[str]:
        """
        Generate QR codes for template-formatted vehicle data.
        Template data may already have @QR paths, but we need to generate actual QR files.
        """
        import traceback
        logger.info(f"[QR TRACE 2] _generate_qr_codes_for_template_data() CALLED with {len(vehicles)} vehicles for {dealership_name}")
        logger.info(f"[QR TRACE 2] Call stack: {' -> '.join([frame.filename.split('/')[-1] + ':' + str(frame.lineno) for frame in traceback.extract_stack()[-5:]])}")
        if vehicles:
            logger.info(f"[QR TRACE 2] Sample vehicle keys: {list(vehicles[0].keys())}")
            logger.info(f"[QR TRACE 2] Sample vehicle VIN: {vehicles[0].get('vin', 'NO_VIN')}")
            logger.info(f"[QR TRACE 2] Sample vehicle data: {str(vehicles[0])[:200]}...")
        from database_connection import db_manager
        qr_paths = []
        clean_name = dealership_name.replace(' ', '_')

        for idx, vehicle in enumerate(vehicles, 1):
            try:
                # Extract VIN from template data - may be in VIN field or embedded in other fields
                vin = self._extract_vin_from_template_data(vehicle)
                if not vin:
                    logger.warning(f"Cannot extract VIN from template data for vehicle {idx}")
                    continue

                # CRITICAL FIX: Get original vehicle data from database using VIN (same as OLD method)
                # This ensures we have access to vehicle_url and all original fields for QR generation
                original_vehicle_data = db_manager.execute_query("""
                    SELECT nvd.* FROM normalized_vehicle_data nvd
                    JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                    JOIN scraper_imports si ON rvd.import_id = si.import_id
                    WHERE nvd.vin = %s AND nvd.location = %s AND si.status = 'active'
                    ORDER BY rvd.import_timestamp DESC
                    LIMIT 1
                """, (vin, dealership_name))

                if not original_vehicle_data:
                    logger.warning(f"Cannot find original vehicle data for VIN {vin}")
                    continue

                # Use original vehicle data for QR generation (same as OLD method)
                original_vehicle = original_vehicle_data[0]
                qr_content = self._get_vehicle_qr_content(original_vehicle, dealership_name)

                if not qr_content:
                    logger.warning(f"No valid QR content for template vehicle {idx} (VIN: {vin})")
                    continue

                # Generate QR code using same specs as raw data
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=0,
                )
                qr.add_data(qr_content)
                qr.make(fit=True)

                # Create QR image with exact color specification
                img = qr.make_image(fill_color=(50, 50, 50), back_color="white")
                img = img.resize((388, 388), Image.Resampling.LANCZOS)

                # Save QR code
                filename = f"{clean_name}_QR_Code_{idx}.png"
                filepath = output_folder / filename
                img.save(filepath, format='PNG')

                qr_paths.append(str(filepath))
                logger.debug(f"Generated QR for template vehicle {idx}: {qr_content}")

            except Exception as e:
                logger.error(f"Error generating QR for template vehicle {idx}: {e}")

        logger.info(f"Generated {len(qr_paths)} QR codes for template data")
        return qr_paths

    def _extract_vin_from_template_data(self, vehicle: Dict) -> str:
        """Extract VIN from template-formatted vehicle data."""
        # Try direct VIN field first
        vin = vehicle.get('VIN', '').strip()
        if vin and vin not in ['', 'USED -', 'NEW -']:
            # Remove prefix if present
            if vin.startswith('USED - '):
                vin = vin[7:]
            elif vin.startswith('NEW - '):
                vin = vin[6:]
            return vin

        # Try other potential VIN fields
        for field in ['vin', 'Vin', 'vehicle_vin']:
            vin = vehicle.get(field, '').strip()
            if vin and len(vin) == 17:  # Standard VIN length
                return vin

        return ''

    def _get_qr_content_from_template_data(self, vehicle: Dict, dealership_name: str) -> str:
        """Get QR content from template-formatted vehicle data."""
        # Try to extract usable information for QR generation
        vin = self._extract_vin_from_template_data(vehicle)

        # Extract stock number from template data
        stock = vehicle.get('STOCK', '').strip()
        if not stock:
            stock = vehicle.get('stock', '').strip()

        # For template data, fallback to VIN or stock if no specific URL
        if vin:
            return vin
        elif stock:
            return stock
        else:
            logger.warning(f"No VIN or stock found in template data: {list(vehicle.keys())}")
            return f"Vehicle_{dealership_name.replace(' ', '_')}"

    def _generate_csv_from_template_data(self, vehicles: List[Dict], dealership_name: str, template_type: str, output_folder: Path, qr_paths: List[str]) -> Path:
        """
        Generate CSV directly from template-formatted data with correct template type formatting.
        """
        logger.info(f"[CSV TEMPLATE] Generating CSV from template data for {dealership_name} with template type: {template_type}")

        # Determine filename abbreviation based on template type (matching original logic)
        if template_type == "shortcut_pack":
            abbr = "SCP"
        elif template_type == "shortcut":
            abbr = "SC"
        else:
            abbr = template_type.upper()[:3]

        # Generate filename with correct abbreviation
        clean_name_upper = dealership_name.upper().replace(' ', '_').replace("'", '')
        date_str = datetime.now().strftime('%m.%d')
        filename = f"{clean_name_upper}_{abbr}_{date_str} - CSV.csv"
        csv_path = output_folder / filename

        logger.info(f"[CSV TEMPLATE] Template type '{template_type}' -> abbreviation '{abbr}' -> filename: {filename}")

        if not vehicles:
            raise ValueError("No vehicles provided for CSV generation")

        # Write CSV with correct format based on template type
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:

            if template_type == "shortcut":
                # Shortcut format: STOCK,MODEL,@QR (simplified 3-column format)
                writer = csv.writer(csvfile)
                writer.writerow(['STOCK', 'MODEL', '@QR'])

                for idx, vehicle in enumerate(vehicles, 1):
                    # Extract data for shortcut format from template data
                    stock = vehicle.get('STOCK', '')
                    # For MODEL, use YEARMODEL if available, otherwise combine year/make/model
                    model = vehicle.get('YEARMODEL', vehicle.get('MODEL', ''))
                    local_qr_path = vehicle.get('@QR', '')

                    # Convert local QR path to Nick's computer path for VDP compatibility
                    nicks_qr_path = self._convert_qr_path_for_nicks_computer(local_qr_path, dealership_name, idx)

                    writer.writerow([stock, model, nicks_qr_path])

                logger.info(f"[CSV TEMPLATE] Generated shortcut format CSV with {len(vehicles)} vehicles")

            elif template_type == "shortcut_pack":
                # Shortcut Pack format: Full template data with converted QR paths
                fieldnames = list(vehicles[0].keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for idx, vehicle in enumerate(vehicles, 1):
                    # Convert QR paths to Nick's computer paths
                    vehicle_copy = vehicle.copy()
                    if '@QR' in vehicle_copy:
                        local_qr_path = vehicle_copy.get('@QR', '')
                        vehicle_copy['@QR'] = self._convert_qr_path_for_nicks_computer(local_qr_path, dealership_name, idx)

                    # Handle @QR2 field if present (used in some formats)
                    if '@QR2' in vehicle_copy:
                        local_qr_path2 = vehicle_copy.get('@QR2', '')
                        vehicle_copy['@QR2'] = self._convert_qr_path_for_nicks_computer(local_qr_path2, dealership_name, idx)

                    writer.writerow(vehicle_copy)

                logger.info(f"[CSV TEMPLATE] Generated shortcut_pack format CSV with {len(vehicles)} vehicles")

            else:
                # Other template types: Use full template data
                fieldnames = list(vehicles[0].keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for vehicle in vehicles:
                    writer.writerow(vehicle)

                logger.info(f"[CSV TEMPLATE] Generated {template_type} format CSV with {len(vehicles)} vehicles")

        logger.info(f"[CSV TEMPLATE] Successfully generated CSV: {csv_path}")
        return csv_path

    def _log_template_vins_to_history(self, vehicles: List[Dict], dealership_name: str, order_type: str, order_number: str) -> Dict[str, Any]:
        """
        Extract VINs from template data and log to history.
        """
        logger.info(f"[VIN LOG TEMPLATE] Logging VINs from template data for {dealership_name}")

        vins_to_log = []
        for vehicle in vehicles:
            vin = self._extract_vin_from_template_data(vehicle)
            if vin:
                vins_to_log.append(vin)

        if not vins_to_log:
            logger.warning(f"[VIN LOG TEMPLATE] No VINs extracted from template data")
            return {'success': True, 'vins_logged': 0, 'duplicates_skipped': 0, 'errors': []}

        logger.info(f"[VIN LOG TEMPLATE] Extracted {len(vins_to_log)} VINs to log")

        # Use existing VIN logging method with extracted VINs
        # Create minimal vehicle records for logging
        vin_records = [{'vin': vin} for vin in vins_to_log]
        return self._log_processed_vins_to_history(vin_records, dealership_name, order_type, order_number)

    def process_list_order(self, dealership_name: str, vin_list: List[str], template_type: str = None, skip_vin_logging: bool = False) -> Dict[str, Any]:
        """
        Process List Order (transcribed VINs from installers)
        """
        
        # Get template type from config if not specified
        if template_type is None:
            template_type = self._get_dealership_template_config(dealership_name)

        logger.info(f"[LIST] Processing {dealership_name} with {len(vin_list)} VINs - Template: {template_type}")
        
        try:
            # LIST orders: Validate VINs against scraper data - only include VINs that exist in inventory
            # CRITICAL: Filter out VINs not found in scraper data to prevent "Unknown" records in review stage
            vehicles = []
            valid_vins = []
            invalid_vins = []

            for vin in vin_list:
                # Try to get vehicle data from active scraper data only
                # Correct table relationship: normalized_vehicle_data -> raw_vehicle_data -> scraper_imports
                vehicle_data = db_manager.execute_query("""
                    SELECT nvd.* FROM normalized_vehicle_data nvd
                    JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                    JOIN scraper_imports si ON rvd.import_id = si.import_id
                    WHERE nvd.vin = %s AND nvd.location = %s AND si.status = 'active'
                    ORDER BY rvd.import_timestamp DESC
                    LIMIT 1
                """, (vin, dealership_name))

                if vehicle_data:
                    # VIN found in active scraper data - include it
                    vehicles.append(vehicle_data[0])
                    valid_vins.append(vin)
                    logger.info(f"[LIST VALIDATION] VIN found in scraper data: {vin}")
                else:
                    # VIN NOT found in scraper data - exclude from processing
                    invalid_vins.append(vin)
                    logger.warning(f"[LIST VALIDATION] VIN not found in scraper data, excluding: {vin}")

            # Log validation results
            logger.info(f"[LIST VALIDATION] Valid VINs (found in scraper data): {len(valid_vins)}")
            logger.info(f"[LIST VALIDATION] Invalid VINs (not in scraper data): {len(invalid_vins)}")
            if invalid_vins:
                logger.info(f"[LIST VALIDATION] Excluded VINs: {invalid_vins}")

            logger.info(f"Created {len(vehicles)} vehicle records for LIST processing (filtered)")
            
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
            
            # Generate CSV files based on template type configuration
            csv_files = {}

            # Check if dealership has mixed template types (different for new vs used)
            new_template = self._get_dealership_template_config(dealership_name, 'new')
            used_template = self._get_dealership_template_config(dealership_name, 'used')

            if new_template != used_template:
                # Use mixed template processing for dealerships with different templates
                csv_path = self._process_mixed_template_output(filtered_vehicles, dealership_name, order_folder, qr_paths)
            else:
                # Use simple single template processing for most dealerships
                csv_path = self._generate_adobe_csv(filtered_vehicles, dealership_name, new_template, order_folder, qr_paths)

            # If multiple CSV files were generated, csv_path will be the primary file
            if isinstance(csv_path, dict):
                csv_files = csv_path
                csv_path = csv_files.get('primary_csv') or list(csv_files.values())[0]
            
            # Generate billing sheet CSV automatically after QR codes with ordered/produced logic
            billing_csv_path = self._generate_billing_sheet_csv(filtered_vehicles, dealership_name, order_folder, timestamp, original_vin_list=vin_list, filtered_vin_list=valid_vins)
            
            # CRITICAL: Log processed vehicle VINs to history database for future order accuracy - use filtered vehicles (unless testing)
            if skip_vin_logging:
                logger.info("Skipping VIN logging - test data processing")
                vin_logging_result = {'success': True, 'vins_logged': 0, 'duplicates_skipped': 0, 'errors': []}
            else:
                vin_logging_result = self._log_processed_vins_to_history(filtered_vehicles, dealership_name, 'LIST_ORDER')

            # CRITICAL FIX: Format vehicles for preview to match CSV template output format
            # This ensures the review stage shows the same formatted data that appears in the final CSV
            formatted_vehicles_for_preview = self._format_vehicles_for_preview(filtered_vehicles, dealership_name)
            logger.info(f"[LIST PREVIEW] Formatted {len(formatted_vehicles_for_preview)} vehicles for review stage")

            # Build return result
            result = {
                'success': True,
                'dealership': dealership_name,
                'template_type': template_type,
                'vehicles_requested': len(vin_list),  # Original VIN count from user input
                'vehicles_processed': len(filtered_vehicles),
                'vehicle_count': len(filtered_vehicles),
                'vehicles_filtered_out': len(vehicles) - len(filtered_vehicles),
                'valid_vins': len(valid_vins),  # VINs found in scraper data
                'invalid_vins': len(invalid_vins),  # VINs NOT found in scraper data
                'invalid_vin_list': invalid_vins,  # List of excluded VINs for user feedback
                'vehicles_data': filtered_vehicles,  # Raw vehicles for CSV generation
                'vehicles_for_review': formatted_vehicles_for_preview,  # CRITICAL FIX: Formatted vehicles for preview stage
                'qr_codes_generated': len(qr_paths),
                'qr_folder': str(qr_folder),
                'csv_file': str(csv_path) if not isinstance(csv_path, dict) else str(csv_path.get('primary_csv', '')),
                'export_file': str(csv_path) if not isinstance(csv_path, dict) else str(csv_path.get('primary_csv', '')),
                'download_csv': f"/download_csv/{csv_path.name}" if hasattr(csv_path, 'name') else f"/download_csv/{Path(csv_path.get('primary_csv', '')).name}" if isinstance(csv_path, dict) else f"/download_csv/{Path(csv_path).name}",
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

    def process_maintenance_order(self, dealership_name: str, vin_list: List[str], template_type: str = None, skip_vin_logging: bool = False) -> Dict[str, Any]:
        """
        Process Maintenance Order (CAO + LIST combination for re-graphics)

        Logic:
        1. Get CAO vehicles (filtered vehicles, APPLY vinlog exclusions - normal CAO behavior)
        2. Get LIST vehicles (manual VINs, IGNORE vinlog exclusions - allows re-graphics)
        3. Combine both datasets intelligently (no duplicates)
        4. Process combined set for graphics generation

        Args:
            dealership_name: Name of the dealership
            vin_list: Manual VINs from installer inspection
            template_type: Optional template override
            skip_vin_logging: Whether to skip VIN logging (for testing)
        """

        # Get template type from config if not specified
        if template_type is None:
            template_type = self._get_dealership_template_config(dealership_name)

        logger.info(f"[MAINTENANCE] Processing {dealership_name} - CAO + LIST combination - Template: {template_type}")
        logger.info(f"[MAINTENANCE] Manual VIN list provided: {len(vin_list)} VINs")

        try:
            # STEP 1: Get CAO vehicles WITH vinlog exclusion (normal CAO behavior)
            logger.info(f"[MAINTENANCE] Step 1: Getting CAO vehicles (applying vinlog exclusions)")

            # Get current vehicles and apply normal CAO logic (includes vinlog exclusion)
            current_vehicles = self._get_dealership_vehicles(dealership_name)
            if not current_vehicles:
                logger.warning(f"[MAINTENANCE] No current vehicles found for {dealership_name}")
                cao_vehicles = []
            else:
                # Apply normal CAO processing with vinlog exclusion
                current_vins = [v['vin'] for v in current_vehicles]
                new_vins = self._find_new_vehicles_enhanced(dealership_name, current_vins, current_vehicles)
                cao_vehicles = [v for v in current_vehicles if v['vin'] in new_vins]
                logger.info(f"[MAINTENANCE] CAO portion: {len(cao_vehicles)} vehicles after filtering (vinlog applied)")

            # STEP 2: Get LIST vehicles WITHOUT vinlog exclusion (allows re-graphics)
            logger.info(f"[MAINTENANCE] Step 2: Getting LIST vehicles (ignoring vinlog exclusions)")

            list_vehicles = []
            valid_list_vins = []
            excluded_list_vins = []

            # Handle case where no manual VIN list is provided (skip manual VIN entries)
            if not vin_list:
                logger.info(f"[MAINTENANCE] No manual VIN list provided - processing CAO only")
            else:
                logger.info(f"[MAINTENANCE] Processing {len(vin_list)} manual VINs from installer")

            for vin in vin_list:
                # First check if VIN exists in scraper data
                vehicle_data = db_manager.execute_query("""
                    SELECT nvd.* FROM normalized_vehicle_data nvd
                    JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                    JOIN scraper_imports si ON rvd.import_id = si.import_id
                    WHERE nvd.vin = %s AND nvd.location = %s AND si.status = 'active'
                    ORDER BY rvd.import_timestamp DESC
                    LIMIT 1
                """, (vin, dealership_name))

                if not vehicle_data:
                    logger.warning(f"[MAINTENANCE] LIST VIN not found in scraper data, excluding: {vin}")
                    continue

                # IGNORE vinlog exclusion for LIST portion (allows re-graphics)
                # Include all VINs from manual list that exist in scraper data
                list_vehicles.append(vehicle_data[0])
                valid_list_vins.append(vin)
                logger.info(f"[MAINTENANCE] LIST VIN included (ignoring history): {vin}")

            logger.info(f"[MAINTENANCE] LIST portion: {len(list_vehicles)} vehicles from manual list (history ignored)")
            logger.info(f"[MAINTENANCE] LIST excluded (not in scraper data): {len(excluded_list_vins)} VINs")

            # STEP 3: Combine CAO and LIST vehicles (remove duplicates)
            logger.info(f"[MAINTENANCE] Step 3: Combining CAO and LIST vehicles")

            # Create combined set, avoiding duplicates by VIN
            combined_vehicles = []
            combined_vins = set()

            # Add CAO vehicles first
            for vehicle in cao_vehicles:
                vin = vehicle.get('vin')
                if vin and vin not in combined_vins:
                    combined_vehicles.append(vehicle)
                    combined_vins.add(vin)

            # Add LIST vehicles that aren't already in CAO
            for vehicle in list_vehicles:
                vin = vehicle.get('vin')
                if vin and vin not in combined_vins:
                    combined_vehicles.append(vehicle)
                    combined_vins.add(vin)

            logger.info(f"[MAINTENANCE] Combined total: {len(combined_vehicles)} unique vehicles")
            logger.info(f"[MAINTENANCE] CAO contributed: {len(cao_vehicles)} vehicles")
            logger.info(f"[MAINTENANCE] LIST contributed: {len([v for v in list_vehicles if v.get('vin') not in [c.get('vin') for c in cao_vehicles]])} additional vehicles")

            if not combined_vehicles:
                return {
                    'success': True,
                    'vehicles': [],
                    'total_vehicles': 0,
                    'cao_vehicles': len(cao_vehicles),
                    'list_vehicles': len(list_vehicles),
                    'excluded_list_vehicles': len(excluded_list_vins),
                    'qr_codes': [],
                    'csv_path': '',
                    'billing_csv_path': '',
                    'csv_files': {},
                    'order_folder': '',
                    'template_type': template_type,
                    'vin_logging': {'success': True, 'vins_logged': 0, 'duplicates_skipped': 0, 'errors': []},
                    'order_type': 'MAINTENANCE',
                    'new_vehicles': 0,
                    'message': 'No vehicles to process for maintenance order'
                }

            # STEP 4: Process combined vehicles (same as CAO/LIST processing)
            logger.info(f"[MAINTENANCE] Step 4: Processing {len(combined_vehicles)} combined vehicles")

            # Create output folders
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            order_folder = self.output_base / dealership_name.replace(' ', '_') / timestamp
            qr_folder = order_folder / "qr_codes"

            order_folder.mkdir(parents=True, exist_ok=True)
            qr_folder.mkdir(exist_ok=True)

            # Generate QR codes
            qr_paths = self._generate_qr_codes(combined_vehicles, dealership_name, qr_folder)

            # Generate CSV files based on template type configuration
            csv_files = {}
            new_template = self._get_dealership_template_config(dealership_name, 'new')
            used_template = self._get_dealership_template_config(dealership_name, 'used')

            if new_template != used_template:
                # Use mixed template processing
                csv_path = self._process_mixed_template_output(combined_vehicles, dealership_name, order_folder, qr_paths)
            else:
                # Use single template processing
                csv_path = self._generate_adobe_csv(combined_vehicles, dealership_name, new_template, order_folder, qr_paths)

            if isinstance(csv_path, dict):
                csv_files = csv_path
                csv_path = csv_files.get('primary_csv') or list(csv_files.values())[0]

            # Generate billing sheet
            billing_csv_path = self._generate_billing_sheet_csv(
                combined_vehicles, dealership_name, order_folder, timestamp,
                original_vin_list=vin_list, filtered_vin_list=valid_list_vins
            )

            # Log processed VINs to history (unless testing)
            if skip_vin_logging:
                logger.info("[MAINTENANCE] Skipping VIN logging - test data processing")
                vin_logging_result = {'success': True, 'vins_logged': 0, 'duplicates_skipped': 0, 'errors': []}
            else:
                vin_logging_result = self._log_processed_vins_to_history(combined_vehicles, dealership_name, 'MAINTENANCE_ORDER')

            # Format vehicles for preview
            formatted_vehicles = self._format_vehicles_for_preview(combined_vehicles, dealership_name)

            # Build return result matching CAO/LIST structure
            result = {
                'success': True,
                'dealership': dealership_name,
                'template_type': template_type,
                'total_vehicles': len(combined_vehicles),
                'new_vehicles': len(combined_vehicles),
                'vehicle_count': len(combined_vehicles),
                'vehicles': formatted_vehicles,
                'qr_codes_generated': len(qr_paths),
                'qr_folder': str(qr_folder),
                'csv_file': str(csv_path) if not isinstance(csv_path, dict) else str(csv_path.get('primary_csv', '')),
                'export_file': str(csv_path) if not isinstance(csv_path, dict) else str(csv_path.get('primary_csv', '')),
                'download_csv': f"/download_csv/{csv_path.name}" if hasattr(csv_path, 'name') else f"/download_csv/{Path(csv_path.get('primary_csv', '')).name}" if isinstance(csv_path, dict) else f"/download_csv/{Path(csv_path).name}",
                'billing_csv_file': str(billing_csv_path),
                'download_billing_csv': f"/download_csv/{billing_csv_path.name}",
                'timestamp': timestamp,
                'vins_logged_to_history': vin_logging_result['vins_logged'],
                'duplicate_vins_skipped': vin_logging_result['duplicates_skipped'],
                'vin_logging_success': vin_logging_result['success'],
                'order_type': 'MAINTENANCE',
                'cao_vehicles': len(cao_vehicles),
                'list_vehicles': len(list_vehicles),
                'excluded_list_vehicles': len(excluded_list_vins)
            }

            # Add dual CSV information if present
            if csv_files:
                result['csv_files'] = csv_files
                if 'used_csv' in csv_files:
                    result['used_csv_file'] = csv_files['used_csv']
                    result['download_used_csv'] = f"/download_csv/{Path(csv_files['used_csv']).name}"
                if 'new_csv' in csv_files:
                    result['new_csv_file'] = csv_files['new_csv']
                    result['download_new_csv'] = f"/download_csv/{Path(csv_files['new_csv']).name}"

            return result

        except Exception as e:
            logger.error(f"Error processing maintenance order: {e}")
            return {'success': False, 'error': str(e)}

    def _format_vehicles_for_preview(self, vehicles: List[Dict], dealership_name: str) -> List[Dict]:
        """
        Format vehicle data for preview stage to match CSV template output format.
        This ensures the review stage shows the same formatted data that appears in the final CSV.
        """
        formatted_vehicles = []

        for vehicle in vehicles:
            # Extract raw database fields
            year = vehicle.get('year', '')
            make = vehicle.get('make', '')
            model = vehicle.get('model', '')
            trim = vehicle.get('trim', '')
            stock = vehicle.get('stock', vehicle.get('stock_number', ''))
            vin = vehicle.get('vin', '')
            vehicle_condition = vehicle.get('vehicle_condition', '')

            # Apply same formatting logic as CSV template
            type_prefix = self._get_type_prefix(vehicle_condition)

            # Format YEARMAKE field (same as line 1849-1853 in CSV generation)
            if type_prefix == "NEW":
                yearmake = f"NEW {year} {make}"
            else:
                yearmake = f"{year} {make}"

            # Format STOCK field (same as line 1864 in CSV generation)
            stock_formatted = f"{year} {model} - {stock}"

            # Format VIN field (same as line 1868 in CSV generation)
            vin_formatted = f"{type_prefix} - {vin}"

            # Create formatted vehicle record for preview
            formatted_vehicle = {
                'YEARMAKE': yearmake,
                'MODEL': model,
                'TRIM': trim,
                'STOCK': stock_formatted,
                'VIN': vin_formatted,
                # Preserve original fields for CSV generation
                'year': year,
                'make': make,
                'model': model,
                'trim': trim,
                'stock': stock,
                'vin': vin,
                'vehicle_condition': vehicle_condition,
                'raw_status': vehicle.get('raw_status', ''),
                # Preserve other necessary fields
                **{k: v for k, v in vehicle.items() if k not in ['year', 'make', 'model', 'trim', 'stock', 'vin', 'vehicle_condition', 'raw_status']}
            }

            formatted_vehicles.append(formatted_vehicle)

            logger.info(f"[LIST PREVIEW FORMAT] {vin}: {yearmake} | {model} | {trim} | {stock_formatted} | {vin_formatted}")

        logger.info(f"[LIST PREVIEW FORMAT] Formatted {len(formatted_vehicles)} vehicles for preview")
        return formatted_vehicles

    def _log_processed_vins_to_history(self, vehicles: List[Dict], dealership_name: str, order_type: str, order_number: str = None) -> Dict[str, Any]:
        """
        Log VINs of vehicles that were actually processed in the order output.
        This is CRITICAL for preventing duplicate processing in future orders.

        Args:
            vehicles: List of vehicle dictionaries that were processed
            dealership_name: Name of the dealership
            order_type: 'CAO_ORDER' or 'LIST_ORDER'
            order_number: Optional order number from user input. If not provided, generates timestamp-based number.
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

                    # Use provided order number or generate timestamp-based one
                    if order_number is None:
                        order_number = datetime.now().strftime('%Y%m%d_%H%M%S')
                    processed_date = datetime.now().strftime('%Y-%m-%d')

                    # Check if VIN already exists for this dealership (prevent duplicates)
                    check_query = f"""
                        SELECT id FROM {vin_log_table}
                        WHERE vin = %s AND processed_date = %s
                    """
                    existing = db_manager.execute_query(check_query, (vin, processed_date))

                    if existing:
                        duplicates_skipped += 1
                        logger.debug(f"VIN {vin} already logged for {dealership_name} today, skipping")
                        continue

                    # Insert processed VIN into dealership-specific VIN log table
                    insert_query = f"""
                        INSERT INTO {vin_log_table} (vin, order_number, processed_date, order_type)
                        VALUES (%s, %s, %s, %s)
                    """
                    db_manager.execute_query(insert_query, (vin, order_number, processed_date, order_type))
                    
                    vins_logged += 1
                    logger.info(f"Successfully logged processed VIN {vin} from {order_type} for {dealership_name}")
                    
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

        # Apply brand filter - CRITICAL FIX for required_brands
        required_brands = filtering_rules.get('required_brands', [])
        if required_brands:
            brand_conditions = []
            for brand in required_brands:
                brand_conditions.append("LOWER(nvd.make) = LOWER(%s)")
                params.append(brand)
            query += f" AND ({' OR '.join(brand_conditions)})"

        # Apply seasoning filter at SQL level for better performance
        # Support both modern days_on_lot and legacy seasoning_days formats
        days_on_lot_config = filtering_rules.get('days_on_lot', {})
        legacy_seasoning = filtering_rules.get('seasoning_days', 0)

        if days_on_lot_config and days_on_lot_config.get('min', 0) > 0:
            min_days = days_on_lot_config['min']
            query += " AND nvd.date_in_stock IS NOT NULL AND nvd.date_in_stock <= CURRENT_DATE - INTERVAL '%s days'"
            params.append(min_days)
        elif legacy_seasoning > 0:
            query += " AND nvd.date_in_stock IS NOT NULL AND nvd.date_in_stock <= CURRENT_DATE - INTERVAL '%s days'"
            params.append(legacy_seasoning)

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
    
    def _get_dealership_template_config(self, dealership_name: str, vehicle_condition: str = None) -> str:
        """
        Get template type (shortcut or shortcut_pack) for a dealership based on vehicle condition.
        Returns 'shortcut_pack' as default if no specific config is found.
        """
        # Get dealership config
        config = db_manager.execute_query("""
            SELECT output_rules FROM dealership_configs
            WHERE name = %s AND is_active = true
            ORDER BY updated_at DESC NULLS LAST
            LIMIT 1
        """, (dealership_name,))

        if config and config[0]['output_rules']:
            output_rules = config[0]['output_rules']
            if isinstance(output_rules, str):
                output_rules = json.loads(output_rules)

            # Debug logging for Porsche
            if dealership_name == "Porsche St. Louis":
                logger.info(f"[DEBUG] Porsche output_rules: {output_rules}")
                if 'template_types' in output_rules:
                    logger.info(f"[DEBUG] Porsche template_types: {output_rules['template_types']}")

            # Check for template_type settings
            if 'template_types' in output_rules:
                template_types = output_rules['template_types']

                # If vehicle_condition is specified, check for condition-specific template
                if vehicle_condition:
                    # Normalize condition for lookup
                    if vehicle_condition.lower() in ['new']:
                        result = template_types.get('new', 'shortcut_pack')
                        logger.info(f"[DEBUG] {dealership_name} - Using 'new' template: {result}")
                        return result
                    elif vehicle_condition.lower() in ['used', 'po', 'cpo', 'certified', 'pre-owned']:
                        result = template_types.get('used', 'shortcut_pack')
                        logger.info(f"[DEBUG] {dealership_name} - Using 'used' template: {result}")
                        return result

                # Return default template type if specified
                result = template_types.get('default', 'shortcut_pack')
                logger.info(f"[DEBUG] {dealership_name} - Using 'default' template: {result} (vehicle_condition={vehicle_condition})")
                return result

        # Default to shortcut_pack if no config found
        logger.info(f"[DEBUG] {dealership_name} - No config found, using default: shortcut_pack")
        return 'shortcut_pack'

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
                
                # Minimum seasoning filter now applied at SQL level for better performance
                # Only check maximum days on lot here (post-query) since SQL handles minimum
                days_on_lot_config = filtering_rules.get('days_on_lot', {})
                if days_on_lot_config and days_on_lot_config.get('max', 999) < 999:
                    max_days = days_on_lot_config['max']
                    date_in_stock = vehicle.get('date_in_stock')

                    if date_in_stock:
                        try:
                            if isinstance(date_in_stock, str):
                                stock_date = datetime.strptime(date_in_stock, '%Y-%m-%d')
                                actual_days_on_lot = (datetime.now() - stock_date).days
                            elif hasattr(date_in_stock, 'days'):  # date object
                                actual_days_on_lot = (datetime.now().date() - date_in_stock).days
                            else:  # datetime object
                                actual_days_on_lot = (datetime.now() - date_in_stock).days

                            if actual_days_on_lot > max_days:
                                logger.info(f"[DAYS_ON_LOT] Skipping VIN {vehicle.get('vin')} - {actual_days_on_lot} days on lot exceeds maximum: {max_days}")
                                continue
                        except (ValueError, AttributeError) as e:
                            logger.warning(f"[DAYS_ON_LOT] Could not calculate days for VIN {vehicle.get('vin')}: {e}")

                # Legacy seasoning_days minimum filter is now handled at SQL level

                # Brand filter is now applied at SQL level for better performance
                # No need for post-query brand filtering

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
        import traceback
        logger.info(f"[QR TRACE 1] _generate_qr_codes() CALLED with {len(vehicles)} vehicles for {dealership_name}")
        logger.info(f"[QR TRACE 1] Call stack: {' -> '.join([frame.filename.split('/')[-1] + ':' + str(frame.lineno) for frame in traceback.extract_stack()[-5:]])}")
        if vehicles:
            logger.info(f"[QR TRACE 1] Sample vehicle keys: {list(vehicles[0].keys())}")
            logger.info(f"[QR TRACE 1] Sample vehicle VIN: {vehicles[0].get('vin', 'NO_VIN')}")
            logger.info(f"[QR TRACE 1] Sample vehicle URL: {vehicles[0].get('vehicle_url', 'NO_URL')[:50]}...")
        
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
        Only appends UTM parameters to actual URLs.
        """

        vin = vehicle.get('vin', '').strip()
        stock = vehicle.get('stock', '').strip()
        url = vehicle.get('vehicle_url', '').strip()

        # If we have a URL, use it with UTM parameters
        if url:
            url_with_utm = self._add_utm_parameters(url)
            logger.info(f"[QR CONTENT] Using vehicle URL: {url_with_utm}")
            return url_with_utm

        # Otherwise, use VIN (no UTM - it's not a URL)
        if vin:
            logger.info(f"[QR CONTENT] Using VIN: {vin}")
            return vin

        # Fallback to stock number (no UTM - it's not a URL)
        if stock:
            logger.debug(f"Using stock number: {stock}")
            return stock

        logger.warning("No suitable QR content found for vehicle")
        return ""

    def _add_utm_parameters(self, url: str) -> str:
        """
        Add Silver Fox UTM parameters to a URL for Google Analytics tracking.

        Args:
            url: The base URL to add parameters to

        Returns:
            URL with UTM parameters appended
        """
        if not url:
            return url

        utm_params = "utm_source=SilverFox&utm_medium=VDP_ShortCut"

        # Check if URL already has query parameters
        if '?' in url:
            return f"{url}&{utm_params}"
        else:
            return f"{url}?{utm_params}"

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

        # Get dealership output_rules for template variant and price markup
        output_rules = {}
        config = db_manager.execute_query("""
            SELECT output_rules FROM dealership_configs
            WHERE name = %s AND is_active = true
            ORDER BY updated_at DESC NULLS LAST
            LIMIT 1
        """, (dealership_name,))

        if config and config[0]['output_rules']:
            output_rules = config[0]['output_rules']
            if isinstance(output_rules, str):
                output_rules = json.loads(output_rules)

        template_variant = output_rules.get('template_variant', 'standard')
        price_markup = output_rules.get('price_markup', 0)

        logger.info(f"Using template variant: {template_variant}, price markup: ${price_markup}")

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

        logger.info(f"[CAO CSV] About to write CSV file: {csv_path}")
        logger.info(f"[CAO CSV] Writing {len(vehicles)} vehicles to CSV")
        logger.info(f"[CAO CSV] Template type: {template_type}")
        if vehicles:
            logger.info(f"[CAO CSV] Sample vehicle data for CSV writing: {vehicles[0]}")

        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            
            if template_type == "shortcut":
                # Shortcut format: STOCK,MODEL,@QR (simplified 3-column format)
                writer = csv.writer(csvfile)
                writer.writerow(['STOCK', 'MODEL', '@QR'])

                for idx, vehicle in enumerate(vehicles):
                    year = vehicle.get('year', '')
                    make = vehicle.get('make', '')
                    model = vehicle.get('model', '')
                    stock = vehicle.get('stock', '')
                    type_prefix = self._get_type_prefix(vehicle.get('vehicle_condition', ''))
                    vin = vehicle.get('vin', '')

                    qr_path = qr_paths[idx] if idx < len(qr_paths) else ''
                    # Convert QR path for Nick's computer compatibility
                    nicks_qr_path = self._convert_qr_path_for_nicks_computer(qr_path, dealership_name, idx)

                    # Format: "YEAR MODEL - STOCK" for stock column
                    stock_field = f"{year} {model} - {stock}"
                    # Format: "CONDITION - VIN" for model column
                    model_field = f"{type_prefix} - {vin}"

                    writer.writerow([stock_field, model_field, nicks_qr_path])
            
            elif template_type == "shortcut_pack":
                writer = csv.writer(csvfile)

                # Check for Glendale format variant
                if template_variant == 'glendale_format':
                    # Glendale format: YEARMODEL,TRIM,PRICE,STOCK,VIN,@QR,QRYEARMODEL,QRSTOCK,@QR2,MISC
                    writer.writerow(['YEARMODEL', 'TRIM', 'PRICE', 'STOCK', 'VIN', '@QR', 'QRYEARMODEL', 'QRSTOCK', '@QR2', 'MISC'])

                    for idx, vehicle in enumerate(vehicles):
                        year = vehicle.get('year', '')
                        model = vehicle.get('model', '')
                        trim = vehicle.get('trim', '')
                        stock = vehicle.get('stock', '')
                        vin = vehicle.get('vin', '')
                        price = vehicle.get('price', 0)
                        type_prefix = self._get_type_prefix(vehicle.get('vehicle_condition', ''))

                        qr_path = qr_paths[idx] if idx < len(qr_paths) else ''
                        # Convert QR path for Nick's computer compatibility
                        nicks_qr_path = self._convert_qr_path_for_nicks_computer(qr_path, dealership_name, idx)

                        # Apply price markup if configured
                        if price and price_markup:
                            try:
                                price_value = float(price) + float(price_markup)
                                # Format price with comma and no decimal
                                price_str = f"{int(price_value):,}"
                            except (ValueError, TypeError):
                                price_str = ''
                        elif price:
                            try:
                                # Format price with comma and no decimal
                                price_str = f"{int(float(price)):,}"
                            except (ValueError, TypeError):
                                price_str = ''
                        else:
                            price_str = ''

                        # Format YEARMODEL (combines year and model in uppercase)
                        yearmodel = f"{year} {model.upper()}"

                        # Common fields
                        stock_field = f"{year} {model.upper()} - {stock}"
                        vin_field = f"{type_prefix} - {vin}"
                        qryearmodel = f"{year} {model.upper()} - {stock}"
                        qrstock = f"{type_prefix} - {vin}"
                        misc = f"{year} {model.title()} - {vin} - {stock}"

                        writer.writerow([
                            yearmodel, trim, price_str, stock_field, vin_field, nicks_qr_path,
                            qryearmodel, qrstock, nicks_qr_path, misc
                        ])

                else:
                    # Standard Shortcut Pack format: YEARMAKE,MODEL,TRIM,STOCK,VIN,@QR,QRYEARMODEL,QRSTOCK,@QR2,MISC
                    writer.writerow(['YEARMAKE', 'MODEL', 'TRIM', 'STOCK', 'VIN', '@QR', 'QRYEARMODEL', 'QRSTOCK', '@QR2', 'MISC'])

                    for idx, vehicle in enumerate(vehicles):
                        # CRITICAL FIX: Check for directly preserved CSV column values first
                        # This preserves any direct edits made to final output columns
                        if 'YEARMAKE' in vehicle:
                            # Use direct CSV value if available (preserves user edits)
                            yearmake_direct = str(vehicle.get('YEARMAKE', ''))
                        else:
                            yearmake_direct = None

                        # Get primitive fields for reconstruction (fallback)
                        year = vehicle.get('year', '')
                        make = vehicle.get('make', '')
                        model = vehicle.get('model', '')
                        trim = vehicle.get('trim', '')
                        stock = vehicle.get('stock', vehicle.get('stock_number', ''))  # CRITICAL FIX: Check both field names
                        vin = vehicle.get('vin', '')
                        raw_status = vehicle.get('raw_status', 'N/A')  # Get raw_status from database query
                        type_prefix = self._get_type_prefix(vehicle.get('vehicle_condition', ''))

                        qr_path = qr_paths[idx] if idx < len(qr_paths) else ''
                        # Convert QR path for Nick's computer compatibility
                        nicks_qr_path = self._convert_qr_path_for_nicks_computer(qr_path, dealership_name, idx)

                        # CRITICAL FIX: Use directly preserved CSV values when available, otherwise reconstruct
                        # This preserves any direct edits made to final output columns

                        # YEARMAKE field
                        if yearmake_direct:
                            yearmake = yearmake_direct  # Use direct edit
                            logger.info(f"[CAO CSV PRESERVE] Using direct YEARMAKE edit: {yearmake}")
                        elif type_prefix == "NEW":
                            yearmake = f"NEW {year} {make}"  # Reconstruct for new vehicles
                            logger.info(f"[CAO CSV PRESERVE] Reconstructed NEW YEARMAKE: {yearmake}")
                        else:
                            yearmake = f"{year} {make}"  # Reconstruct for used vehicles
                            logger.info(f"[CAO CSV PRESERVE] Reconstructed USED YEARMAKE: {yearmake}")

                        # MODEL field
                        model_final = str(vehicle.get('MODEL', model))  # Use direct edit or fallback
                        logger.info(f"[CAO CSV PRESERVE] MODEL: {model_final} (from edit: {vehicle.get('MODEL')}, fallback: {model})")

                        # TRIM field
                        trim_final = str(vehicle.get('TRIM', trim))  # Use direct edit or fallback
                        logger.info(f"[CAO CSV PRESERVE] TRIM: {trim_final} (from edit: {vehicle.get('TRIM')}, fallback: {trim})")

                        # STOCK field
                        stock_final = str(vehicle.get('STOCK', f"{year} {model} - {stock}"))  # Use direct edit or fallback
                        logger.info(f"[CAO CSV PRESERVE] STOCK: {stock_final} (from edit: {vehicle.get('STOCK')}, fallback: {year} {model} - {stock})")

                        # VIN field
                        vin_final = str(vehicle.get('VIN', f"{type_prefix} - {vin}"))  # Use direct edit or fallback
                        logger.info(f"[CAO CSV PRESERVE] VIN: {vin_final} (from edit: {vehicle.get('VIN')}, fallback: {type_prefix} - {vin})")

                        # Other fields (reconstructed for QR generation)
                        qryearmodel = f"{year} {model} - {stock}"
                        qrstock = f"{type_prefix} - {vin}"
                        misc_final = str(vehicle.get('MISC', f"{year} {model.title()} - {vin} - {stock}"))  # Use direct edit or fallback
                        logger.info(f"[CAO CSV PRESERVE] MISC: {misc_final} (from edit: {vehicle.get('MISC')}, fallback: {year} {model.title()} - {vin} - {stock})")

                        writer.writerow([
                            yearmake, model_final, trim_final, stock_final, vin_final, nicks_qr_path,
                            qryearmodel, qrstock, nicks_qr_path, misc_final
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

    def _process_mixed_template_output(self, vehicles: List[Dict], dealership_name: str,
                                      order_folder: Path, qr_paths: List[str]) -> str:
        """
        Universal processing for dealerships with mixed template types.
        Separates vehicles by condition (new/used) and generates appropriate CSV files
        based on each condition's template type configuration.
        """
        logger.info(f"[MIXED TEMPLATE] Processing {len(vehicles)} vehicles for {dealership_name}")

        # Separate vehicles by condition
        new_vehicles = []
        used_vehicles = []

        for vehicle in vehicles:
            condition = vehicle.get('vehicle_condition', '').lower()

            if condition == 'new':
                new_vehicles.append(vehicle)
            else:
                # All non-new vehicles (including certified, cpo, po, pre-owned, used)
                used_vehicles.append(vehicle)

        logger.info(f"[MIXED TEMPLATE] Split: {len(new_vehicles)} new vehicles, {len(used_vehicles)} used vehicles")

        # Get template types for each condition
        new_template = self._get_dealership_template_config(dealership_name, 'new')
        used_template = self._get_dealership_template_config(dealership_name, 'used')

        logger.info(f"[MIXED TEMPLATE] Templates: new={new_template}, used={used_template}")

        csv_files = {}
        qr_index = 0

        # Generate CSV for new vehicles if any exist
        if new_vehicles:
            new_qr_paths = qr_paths[qr_index:qr_index + len(new_vehicles)]
            new_csv_path = self._generate_adobe_csv(new_vehicles, dealership_name, new_template, order_folder, new_qr_paths)
            csv_files['new_csv'] = new_csv_path
            qr_index += len(new_vehicles)
            logger.info(f"[MIXED TEMPLATE] Generated new vehicles CSV ({new_template}): {new_csv_path.name}")

        # Generate CSV for used vehicles if any exist
        if used_vehicles:
            used_qr_paths = qr_paths[qr_index:qr_index + len(used_vehicles)]
            used_csv_path = self._generate_adobe_csv(used_vehicles, dealership_name, used_template, order_folder, used_qr_paths)
            csv_files['used_csv'] = used_csv_path
            logger.info(f"[MIXED TEMPLATE] Generated used vehicles CSV ({used_template}): {used_csv_path.name}")

        # If only one template type or all vehicles use same template, return single CSV path
        if len(csv_files) == 1:
            return list(csv_files.values())[0]

        # If multiple CSV files generated, return dict with primary_csv for legacy compatibility
        if csv_files:
            csv_files['primary_csv'] = csv_files.get('used_csv') or csv_files.get('new_csv')
            return csv_files

        # Fallback: generate single CSV using default template
        default_template = self._get_dealership_template_config(dealership_name)
        return self._generate_adobe_csv(vehicles, dealership_name, default_template, order_folder, qr_paths)

    def _generate_billing_sheet_csv(self, vehicles: List[Dict], dealership_name: str, output_folder: Path, timestamp: str, original_vin_list: List[str] = None, filtered_vin_list: List[str] = None) -> Path:
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

        for vehicle in vehicles:
            vtype = vehicle.get('vehicle_condition', '').lower()

            # Simple NEW/USED determination
            if 'new' in vtype:
                new_count += 1
            else:
                # Everything else (including cpo, certified, po, pre-owned) is USED
                used_count += 1

        # Prepare ORDERED and PRODUCED VIN lists for billing CSV - strip "NEW" prefixes and " - " separators
        def strip_new_prefix(vin: str) -> str:
            """Strip 'NEW' prefix and ' - ' separator from VIN if present"""
            if not isinstance(vin, str):
                return vin

            # Strip patterns like "NEW - 1GTUUCED3RZ262350" or "USED - 1GTUUCED3RZ262350"
            if vin.upper().startswith('NEW - '):
                return vin[6:].strip()  # Remove "NEW - " and any whitespace
            elif vin.upper().startswith('USED - '):
                return vin[7:].strip()  # Remove "USED - " and any whitespace
            elif vin.upper().startswith('NEW'):
                return vin[3:].strip()  # Remove just "NEW" and any whitespace
            return vin

        ordered_vins = [strip_new_prefix(vin) for vin in (original_vin_list if original_vin_list else [])]
        produced_vins = [strip_new_prefix(vin) for vin in (filtered_vin_list if filtered_vin_list else [])]

        # DEBUG: Log what we received
        logger.info(f"[BILLING DEBUG] original_vin_list: {original_vin_list}")
        logger.info(f"[BILLING DEBUG] filtered_vin_list: {filtered_vin_list}")
        logger.info(f"[BILLING DEBUG] ordered_vins: {ordered_vins}")
        logger.info(f"[BILLING DEBUG] produced_vins: {produced_vins}")

        total_vehicles = len(vehicles)

        # Write billing CSV in EXACT format from example
        with open(billing_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header row - EXACT format
            writer.writerow(['Totals:', '', '', 'DUPLICATES', '', '', '', 'ORDERED', 'PRODUCED'])

            # Summary rows with proper ORDERED/PRODUCED logic
            writer.writerow(['Total Ordered', len(ordered_vins), '', '', '', '', '',
                           ordered_vins[0] if len(ordered_vins) > 0 else '',
                           produced_vins[0] if len(produced_vins) > 0 else ''])

            writer.writerow(['Total Produced:', len(produced_vins), '', '', '', '', '',
                           ordered_vins[1] if len(ordered_vins) > 1 else '',
                           produced_vins[1] if len(produced_vins) > 1 else ''])

            writer.writerow(['Total New:', new_count, '', '', '', '', '',
                           ordered_vins[2] if len(ordered_vins) > 2 else '',
                           produced_vins[2] if len(produced_vins) > 2 else ''])

            writer.writerow(['Total Used:', used_count, '', '', '', '', '',
                           ordered_vins[3] if len(ordered_vins) > 3 else '',
                           produced_vins[3] if len(produced_vins) > 3 else ''])

            writer.writerow(['', '', '', '', '', '', '',
                           ordered_vins[4] if len(ordered_vins) > 4 else '',
                           produced_vins[4] if len(produced_vins) > 4 else ''])

            writer.writerow(['Used Duplicates:', 0, '', '', '', '', '',
                           ordered_vins[5] if len(ordered_vins) > 5 else '',
                           produced_vins[5] if len(produced_vins) > 5 else ''])

            writer.writerow(['New Duplicates', 0, '', '', '', '', '',
                           ordered_vins[6] if len(ordered_vins) > 6 else '',
                           produced_vins[6] if len(produced_vins) > 6 else ''])

            writer.writerow(['Duplicates:', 0, '', '', '', '', '',
                           ordered_vins[7] if len(ordered_vins) > 7 else '',
                           produced_vins[7] if len(produced_vins) > 7 else ''])

            # Fill in remaining VINs if there are more than 8 - populate both ORDERED and PRODUCED columns
            max_vins = max(len(ordered_vins), len(produced_vins))
            for i in range(8, max_vins):
                writer.writerow(['', '', '', '', '', '', '',
                               ordered_vins[i] if i < len(ordered_vins) else '',
                               produced_vins[i] if i < len(produced_vins) else ''])

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