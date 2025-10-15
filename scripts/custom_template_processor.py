"""
Custom Template Processor - COMPLETELY SEPARATE FROM EXISTING SYSTEM
This processes orders using custom templates without touching existing order processing logic
Can be tested independently and integrated only when ready
"""

import json
import logging
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys
sys.path.append('.')
from database_connection import db_manager
from template_resolver import template_resolver

logger = logging.getLogger(__name__)

class CustomTemplateProcessor:
    """
    Processes orders using custom templates
    COMPLETELY SEPARATE from existing OrderProcessingSystem
    """

    def process_custom_template_order(self, dealership_name: str, vehicle_condition: str = None) -> Dict[str, Any]:
        """
        Process order using custom template (if available)
        This is a SEPARATE processing path from existing system

        Args:
            dealership_name: Name of dealership
            vehicle_condition: Optional vehicle condition filter

        Returns:
            Dict with success status and results
        """
        try:
            logger.info(f"[CUSTOM TEMPLATE] Processing order for {dealership_name} (condition: {vehicle_condition})")

            # Step 1: Check if dealership has custom template
            template_result = template_resolver.get_template(dealership_name, vehicle_condition)

            if template_result['type'] != 'custom':
                return {
                    'success': False,
                    'error': 'No custom template configured for this dealership',
                    'fallback_to_legacy': True
                }

            template_data = template_result['template_data']
            logger.info(f"[CUSTOM TEMPLATE] Using template: {template_data['template_name']}")

            # Step 2: Get vehicle data (using same query logic as existing system)
            vehicles = self._get_dealership_vehicles(dealership_name)
            if not vehicles:
                return {
                    'success': False,
                    'error': 'No vehicles found for dealership'
                }

            # Step 3: Filter vehicles based on VIN log (same logic as existing)
            filtered_vehicles = self._filter_by_vin_log(vehicles, dealership_name)

            if not filtered_vehicles:
                return {
                    'success': False,
                    'error': 'No new vehicles found (all vehicles already processed)'
                }

            # Step 4: Render vehicles using custom template
            rendered_vehicles = template_resolver.render_custom_template(template_data, filtered_vehicles)

            # Step 5: Generate QR codes (if template requires them)
            qr_paths = []
            if self._template_needs_qr_codes(template_data):
                qr_paths = self._generate_qr_codes_for_vehicles(filtered_vehicles, dealership_name)

                # Add QR paths to rendered vehicles
                for i, vehicle in enumerate(rendered_vehicles):
                    if i < len(qr_paths):
                        vehicle['@QR'] = qr_paths[i]

            # Step 6: Generate CSV using custom template format
            output_folder = Path('orders')
            csv_path = self._generate_custom_csv(rendered_vehicles, dealership_name, template_data, output_folder)

            # Step 7: Log VINs to prevent reprocessing (if not in test mode)
            processed_vins = [v['vin'] for v in filtered_vehicles]
            self._log_processed_vins(processed_vins, dealership_name)

            return {
                'success': True,
                'template_name': template_data['template_name'],
                'vehicle_count': len(filtered_vehicles),
                'csv_path': str(csv_path),
                'qr_codes_generated': len(qr_paths),
                'vehicles_processed': processed_vins
            }

        except Exception as e:
            logger.error(f"[CUSTOM TEMPLATE] Error processing order: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _get_dealership_vehicles(self, dealership_name: str) -> List[Dict]:
        """
        Get vehicles for dealership (same query as existing system)
        """
        try:
            query = """
                SELECT nvd.*, rvd.status as raw_status FROM normalized_vehicle_data nvd
                JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                JOIN scraper_imports si ON rvd.import_id = si.import_id
                WHERE nvd.location = %s
                AND nvd.on_lot_status IN ('onlot', 'on lot')
                AND si.status = 'active'
                ORDER BY nvd.created_at DESC
            """

            vehicles = db_manager.execute_query(query, (dealership_name,))
            return vehicles or []

        except Exception as e:
            logger.error(f"[CUSTOM TEMPLATE] Error getting vehicles: {e}")
            return []

    def _filter_by_vin_log(self, vehicles: List[Dict], dealership_name: str) -> List[Dict]:
        """
        Filter out vehicles that have already been processed
        """
        try:
            # Get VIN log table name
            table_slug = dealership_name.lower().replace(' ', '_').replace("'", '').replace('&', 'and')
            vin_log_table = f"{table_slug}_vin_log"

            # Get already processed VINs
            processed_vins = db_manager.execute_query(f"""
                SELECT DISTINCT vin FROM {vin_log_table}
                WHERE vin IS NOT NULL
            """)

            processed_vin_set = {v['vin'] for v in processed_vins} if processed_vins else set()

            # Filter out already processed vehicles
            new_vehicles = [v for v in vehicles if v['vin'] not in processed_vin_set]

            logger.info(f"[CUSTOM TEMPLATE] Filtered {len(vehicles)} -> {len(new_vehicles)} new vehicles")
            return new_vehicles

        except Exception as e:
            logger.error(f"[CUSTOM TEMPLATE] Error filtering by VIN log: {e}")
            return vehicles  # Return all vehicles if filtering fails

    def _template_needs_qr_codes(self, template_data: Dict) -> bool:
        """
        Check if template requires QR codes
        """
        try:
            columns = template_data.get('fields', {}).get('columns', [])
            for column in columns:
                if column.get('key') == 'qr_code' or column.get('type') == 'special':
                    return True
            return False
        except:
            return False

    def _generate_qr_codes_for_vehicles(self, vehicles: List[Dict], dealership_name: str) -> List[str]:
        """
        Generate QR codes for vehicles
        """
        try:
            # Import QR generator from existing system
            from qr_code_generator import QRCodeGenerator
            qr_generator = QRCodeGenerator()

            qr_paths = []
            for vehicle in vehicles:
                vehicle_url = vehicle.get('vehicle_url', '')
                if vehicle_url:
                    # Add UTM parameters
                    if '?' in vehicle_url:
                        full_url = f"{vehicle_url}&utm_source=SilverFox&utm_medium=VDP_ShortCut"
                    else:
                        full_url = f"{vehicle_url}?utm_source=SilverFox&utm_medium=VDP_ShortCut"

                    # Generate QR code
                    qr_path = qr_generator.generate_qr_code(
                        full_url,
                        dealership_name,
                        vehicle.get('stock', vehicle.get('vin', ''))
                    )
                    qr_paths.append(qr_path)
                else:
                    qr_paths.append('')

            logger.info(f"[CUSTOM TEMPLATE] Generated {len(qr_paths)} QR codes")
            return qr_paths

        except Exception as e:
            logger.error(f"[CUSTOM TEMPLATE] Error generating QR codes: {e}")
            return []

    def _generate_custom_csv(self, rendered_vehicles: List[Dict], dealership_name: str,
                           template_data: Dict, output_folder: Path) -> Path:
        """
        Generate CSV using custom template format
        """
        try:
            # Create output folder if it doesn't exist
            output_folder.mkdir(parents=True, exist_ok=True)

            # Generate filename
            template_name = template_data['template_name'].replace(' ', '_')
            date_str = datetime.now().strftime('%m.%d')
            clean_name = dealership_name.upper().replace(' ', '_').replace("'", '')
            filename = f"{clean_name}_CUSTOM_{template_name}_{date_str}.csv"
            csv_path = output_folder / filename

            # Write CSV
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                if rendered_vehicles:
                    fieldnames = list(rendered_vehicles[0].keys())
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rendered_vehicles)

            logger.info(f"[CUSTOM TEMPLATE] Generated CSV: {csv_path}")
            return csv_path

        except Exception as e:
            logger.error(f"[CUSTOM TEMPLATE] Error generating CSV: {e}")
            raise

    def _log_processed_vins(self, vins: List[str], dealership_name: str):
        """
        Log processed VINs to prevent reprocessing
        """
        try:
            # Get VIN log table name
            table_slug = dealership_name.lower().replace(' ', '_').replace("'", '').replace('&', 'and')
            vin_log_table = f"{table_slug}_vin_log"

            # Insert VINs
            for vin in vins:
                db_manager.execute_query(f"""
                    INSERT INTO {vin_log_table}
                    (vin, order_number, processed_date, order_type, template_type, import_source)
                    VALUES (%s, %s, CURRENT_DATE, %s, %s, %s)
                """, (vin, 'CUSTOM_TEMPLATE', 'CAO', 'custom_template', 'Custom Template System'))

            logger.info(f"[CUSTOM TEMPLATE] Logged {len(vins)} VINs to {vin_log_table}")

        except Exception as e:
            logger.error(f"[CUSTOM TEMPLATE] Error logging VINs: {e}")

    def test_custom_template_preview(self, dealership_name: str, template_id: int,
                                   sample_vin: str = None) -> Dict[str, Any]:
        """
        Test/preview custom template without processing full order
        Safe testing function that doesn't modify any data
        """
        try:
            # Get template
            template_data = template_resolver.get_template_info(template_id)
            if not template_data:
                return {'success': False, 'error': 'Template not found'}

            # Get sample vehicles (limit to 5 for testing)
            vehicles = self._get_dealership_vehicles(dealership_name)
            if not vehicles:
                return {'success': False, 'error': 'No vehicles found'}

            # Use specific VIN if provided
            if sample_vin:
                vehicles = [v for v in vehicles if v['vin'] == sample_vin]
                if not vehicles:
                    return {'success': False, 'error': 'Sample VIN not found'}

            # Limit to first 5 for preview
            sample_vehicles = vehicles[:5]

            # Render using custom template
            rendered = template_resolver.render_custom_template(template_data, sample_vehicles)

            return {
                'success': True,
                'template_name': template_data['template_name'],
                'sample_count': len(rendered),
                'preview_data': rendered,
                'original_vehicles': sample_vehicles
            }

        except Exception as e:
            logger.error(f"[CUSTOM TEMPLATE] Error in preview: {e}")
            return {'success': False, 'error': str(e)}

# Global instance for testing
custom_template_processor = CustomTemplateProcessor()