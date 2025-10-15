"""
Template Resolver Service
Safely integrates custom templates while preserving existing hardcoded logic
Falls back to legacy templates if custom templates are not available
"""

import json
import logging
from typing import Dict, Optional, Any, List
from pathlib import Path
import sys
sys.path.append('.')
from database_connection import db_manager

logger = logging.getLogger(__name__)

class TemplateResolver:
    """
    Resolves template configuration for dealerships
    Priority order:
    1. Custom template from template_configs table
    2. Legacy template from dealership_configs.output_rules
    3. Default 'shortcut_pack' template
    """

    def __init__(self):
        self.template_cache = {}
        self.legacy_cache = {}

    def get_template(self, dealership_name: str, vehicle_condition: Optional[str] = None) -> Dict[str, Any]:
        """
        Get template configuration for a dealership
        Returns either custom template data or legacy template type string

        Args:
            dealership_name: Name of the dealership
            vehicle_condition: Optional condition (new/used/cpo) for condition-specific templates

        Returns:
            Dict with template information:
            {
                'type': 'custom' or 'legacy',
                'template_type': 'shortcut'/'shortcut_pack' or template_id,
                'template_data': Full template config if custom, None if legacy
            }
        """
        logger.info(f"[TEMPLATE RESOLVER] Getting template for {dealership_name} (condition: {vehicle_condition})")

        # Step 1: Try to get custom template
        custom_template = self._get_custom_template(dealership_name, vehicle_condition)
        if custom_template:
            logger.info(f"[TEMPLATE RESOLVER] Found custom template: {custom_template.get('template_name')}")
            return {
                'type': 'custom',
                'template_id': custom_template['id'],
                'template_name': custom_template['template_name'],
                'template_data': custom_template
            }

        # Step 2: Fall back to legacy template
        legacy_template = self._get_legacy_template(dealership_name, vehicle_condition)
        logger.info(f"[TEMPLATE RESOLVER] Using legacy template: {legacy_template}")
        return {
            'type': 'legacy',
            'template_type': legacy_template,
            'template_data': None
        }

    def _get_custom_template(self, dealership_name: str, vehicle_condition: Optional[str] = None) -> Optional[Dict]:
        """
        Get custom template from template_configs table
        """
        try:
            # Check cache first
            cache_key = f"{dealership_name}:{vehicle_condition or 'default'}"
            if cache_key in self.template_cache:
                return self.template_cache[cache_key]

            # Query for custom template mapping
            if vehicle_condition:
                # Check for condition-specific template first
                result = db_manager.execute_query("""
                    SELECT tc.*
                    FROM template_configs tc
                    JOIN dealership_template_mapping dtm ON tc.id = dtm.template_id
                    WHERE dtm.dealership_name = %s
                    AND dtm.vehicle_condition = %s
                    AND tc.is_active = true
                    ORDER BY dtm.priority DESC
                    LIMIT 1
                """, (dealership_name, vehicle_condition))

                if result:
                    self.template_cache[cache_key] = result[0]
                    return result[0]

            # Check for default template for dealership
            result = db_manager.execute_query("""
                SELECT tc.*
                FROM template_configs tc
                JOIN dealership_template_mapping dtm ON tc.id = dtm.template_id
                WHERE dtm.dealership_name = %s
                AND dtm.vehicle_condition IS NULL
                AND tc.is_active = true
                ORDER BY dtm.priority DESC
                LIMIT 1
            """, (dealership_name,))

            if result:
                self.template_cache[cache_key] = result[0]
                return result[0]

            return None

        except Exception as e:
            logger.error(f"[TEMPLATE RESOLVER] Error getting custom template: {e}")
            return None

    def _get_legacy_template(self, dealership_name: str, vehicle_condition: Optional[str] = None) -> str:
        """
        Get legacy template type from dealership_configs.output_rules
        This preserves existing functionality
        """
        try:
            # Check cache first
            cache_key = f"{dealership_name}:{vehicle_condition or 'default'}"
            if cache_key in self.legacy_cache:
                return self.legacy_cache[cache_key]

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

                # Check for template_type settings
                if 'template_types' in output_rules:
                    template_types = output_rules['template_types']

                    # If vehicle_condition is specified, check for condition-specific template
                    if vehicle_condition:
                        # Normalize condition for lookup
                        condition_map = {
                            'new': 'new',
                            'used': 'used',
                            'po': 'used',
                            'cpo': 'used',
                            'certified': 'used',
                            'pre-owned': 'used'
                        }
                        lookup_condition = condition_map.get(vehicle_condition, vehicle_condition)

                        if lookup_condition in template_types:
                            template_type = template_types[lookup_condition]
                            self.legacy_cache[cache_key] = template_type
                            return template_type

                    # Return default if exists
                    if 'default' in template_types:
                        template_type = template_types['default']
                        self.legacy_cache[cache_key] = template_type
                        return template_type

            # Default to shortcut_pack if nothing found
            self.legacy_cache[cache_key] = 'shortcut_pack'
            return 'shortcut_pack'

        except Exception as e:
            logger.error(f"[TEMPLATE RESOLVER] Error getting legacy template: {e}")
            return 'shortcut_pack'

    def render_custom_template(self, template_data: Dict, vehicles: List[Dict]) -> List[Dict]:
        """
        Render vehicles using custom template format

        Args:
            template_data: Template configuration from database
            vehicles: List of vehicle data dictionaries

        Returns:
            List of formatted vehicle dictionaries based on template
        """
        try:
            template_fields = template_data.get('fields', {})
            columns = template_fields.get('columns', [])

            rendered_vehicles = []

            for vehicle in vehicles:
                rendered_vehicle = {}

                for field_config in columns:
                    field_key = field_config['key']
                    field_type = field_config.get('type', 'text')

                    if field_type == 'concatenated':
                        # Handle concatenated fields
                        format_str = field_config.get('format', '')
                        value = self._render_concatenated_field(format_str, vehicle)
                        rendered_vehicle[field_key] = value

                    elif field_type == 'calculated':
                        # Handle calculated fields
                        value = self._render_calculated_field(field_config, vehicle)
                        rendered_vehicle[field_key] = value

                    elif field_type == 'special':
                        # Handle special fields like QR code
                        if field_key == 'qr_code':
                            # QR path will be handled by the order processor
                            rendered_vehicle['@QR'] = ''
                        else:
                            rendered_vehicle[field_key] = ''

                    else:
                        # Direct field mapping
                        source = field_config.get('source', field_key)
                        value = vehicle.get(source, '')

                        # Apply formatting if specified
                        if field_config.get('format'):
                            value = self._apply_format(value, field_config['format'], field_type)

                        rendered_vehicle[field_key.upper()] = value

                rendered_vehicles.append(rendered_vehicle)

            return rendered_vehicles

        except Exception as e:
            logger.error(f"[TEMPLATE RESOLVER] Error rendering custom template: {e}")
            raise

    def _render_concatenated_field(self, format_str: str, vehicle: Dict) -> str:
        """
        Render a concatenated field by replacing placeholders with vehicle data
        """
        result = format_str
        for key, value in vehicle.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value) if value else '')
        return result

    def _render_calculated_field(self, field_config: Dict, vehicle: Dict) -> Any:
        """
        Calculate field value based on configuration
        """
        field_key = field_config['key']

        if field_key == 'days_on_lot':
            # Calculate days on lot
            date_in_stock = vehicle.get('date_in_stock')
            if date_in_stock:
                from datetime import datetime
                try:
                    if isinstance(date_in_stock, str):
                        stock_date = datetime.strptime(date_in_stock, '%Y-%m-%d')
                    else:
                        stock_date = date_in_stock
                    days = (datetime.now() - stock_date).days
                    return days
                except:
                    return 0
            return 0

        return ''

    def _apply_format(self, value: Any, format_str: str, field_type: str) -> str:
        """
        Apply formatting to a field value
        """
        if value is None or value == '':
            return ''

        if field_type == 'number' and '$' in format_str:
            # Currency formatting
            try:
                return f"${float(value):,.0f}"
            except:
                return str(value)

        return str(value)

    def get_template_info(self, template_id: int) -> Optional[Dict]:
        """
        Get full template information by ID
        """
        try:
            result = db_manager.execute_query("""
                SELECT * FROM template_configs
                WHERE id = %s AND is_active = true
            """, (template_id,))

            if result:
                return result[0]
            return None

        except Exception as e:
            logger.error(f"[TEMPLATE RESOLVER] Error getting template info: {e}")
            return None

    def clear_cache(self):
        """
        Clear template caches (useful when templates are updated)
        """
        self.template_cache.clear()
        self.legacy_cache.clear()
        logger.info("[TEMPLATE RESOLVER] Cache cleared")

# Global instance
template_resolver = TemplateResolver()