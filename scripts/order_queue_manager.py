#!/usr/bin/env python3
"""
Order Queue Management System
============================

Manages daily order processing queue with template-based CSV generation.
Supports different output formats: Shortcut, Shortcut Pack, Flyout, Custom.

Key Features:
- Daily order queue management
- Template-based CSV output
- NEW prefix for new vehicles in shortcut packs
- Queue status tracking and completion check-off
- Different completion time handling

Author: Silver Fox Assistant  
Created: 2025-07-29
"""

import os
import sys
import json
import csv
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project paths
current_file = Path(__file__).resolve()
scripts_dir = current_file.parent
sys.path.insert(0, str(scripts_dir))

from database_connection import db_manager
from order_processing_workflow import OrderProcessingWorkflow

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OrderQueueManager:
    """Manages daily order processing queue and template-based CSV generation"""
    
    def __init__(self):
        self.workflow = OrderProcessingWorkflow()
        self.templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, Dict]:
        """Load template configurations from database"""
        try:
            templates_data = db_manager.execute_query("""
                SELECT template_name, template_type, csv_headers, field_mappings, 
                       formatting_rules, qr_column_mapping
                FROM template_configurations
                ORDER BY template_name
            """)
            
            templates = {}
            for template in templates_data:
                # Handle JSONB data - PostgreSQL returns as dict or string
                field_mappings = template['field_mappings']
                if isinstance(field_mappings, str):
                    field_mappings = json.loads(field_mappings)
                elif field_mappings is None:
                    field_mappings = {}
                
                formatting_rules = template['formatting_rules']
                if isinstance(formatting_rules, str):
                    formatting_rules = json.loads(formatting_rules)
                elif formatting_rules is None:
                    formatting_rules = {}
                
                templates[template['template_name']] = {
                    'type': template['template_type'],
                    'headers': template['csv_headers'],
                    'field_mappings': field_mappings,
                    'formatting_rules': formatting_rules,
                    'qr_column': template['qr_column_mapping']
                }
            
            logger.info(f"Loaded {len(templates)} templates: {list(templates.keys())}")
            return templates
            
        except Exception as e:
            logger.error(f"Error loading templates: {e}")
            return {}
    
    def populate_daily_queue(self, target_date: date = None) -> int:
        """Populate the order queue for a specific date based on weekly schedule"""
        if target_date is None:
            target_date = date.today()
        
        day_name = target_date.strftime('%A')
        logger.info(f"Populating queue for {target_date} ({day_name})")
        
        # Clear existing pending orders for this date
        db_manager.execute_query("""
            DELETE FROM order_queue 
            WHERE scheduled_date = %s AND status = 'pending'
        """, (target_date,))
        
        orders_added = 0
        
        # Monday CAO orders
        if day_name == 'Monday':
            monday_orders = [
                ('Porsche STL - New & Used', 'CAO', 'Shortcut', ['new', 'used']),
                ('South County DCJR - New & Used', 'CAO', 'Shortcut Pack', ['new', 'used']),
                ('Frank Leta Honda', 'CAO', 'Flyout', ['new', 'used'])
            ]
            orders_added += self._insert_orders(monday_orders, target_date, day_name)
        
        # Tuesday CAO orders
        elif day_name == 'Tuesday':
            tuesday_orders = [
                ('Spirit Lexus', 'CAO', 'Flyout', ['new', 'used']),
                ('Suntrup Ford Kirkwood', 'CAO', 'Flyout', ['new', 'used']),
                ('Suntrup Ford Westport', 'CAO', 'Flyout', ['new', 'used']),
                ('Weber Chevy', 'CAO', 'Custom', ['new', 'used']),
                ('HW KIA - Used', 'CAO', 'Flyout', ['used']),
                ('Volvo Cars West County - New', 'CAO', 'Shortcut', ['new']),
                ('Bommarito West County - Used', 'CAO', 'Flyout', ['used']),
                ('Glendale CDJR - Used', 'CAO', 'Shortcut Pack', ['used']),
                ('Honda of Frontenac - Used', 'CAO', 'Shortcut Pack', ['used'])
            ]
            orders_added += self._insert_orders(tuesday_orders, target_date, day_name)
        
        # Wednesday CAO orders
        elif day_name == 'Wednesday':
            wednesday_orders = [
                ('Pappas Toyota - New & Loaner', 'CAO', 'Shortcut Pack', ['new']),
                ('Porsche STL - New & Used', 'CAO', 'Shortcut', ['new', 'used']),
                ('Serra New & Used', 'CAO', 'Shortcut Pack', ['new', 'used']),
                ('Auffenberg Used', 'CAO', 'Shortcut Pack', ['used']),
                ('Frank Leta Honda', 'CAO', 'Flyout', ['new', 'used']),
                ('Suntrup Buick GMC', 'CAO', 'Shortcut', ['new', 'used'])
            ]
            orders_added += self._insert_orders(wednesday_orders, target_date, day_name)
        
        # Thursday CAO orders
        elif day_name == 'Thursday':
            thursday_orders = [
                ('Spirit Lexus', 'CAO', 'Flyout', ['new', 'used']),
                ('Suntrup Ford Kirkwood', 'CAO', 'Flyout', ['new', 'used']),
                ('Suntrup Ford Westport', 'CAO', 'Flyout', ['new', 'used']),
                ('Weber Chevy', 'CAO', 'Custom', ['new', 'used']),
                ('HW KIA - Used', 'CAO', 'Flyout', ['used']),
                ('Volvo Cars West County - New', 'CAO', 'Shortcut', ['new']),
                ('Bommarito West County - Used', 'CAO', 'Flyout', ['used']),
                ('Glendale CDJR - Used', 'CAO', 'Shortcut Pack', ['used']),
                ('Honda of Frontenac - New & Used', 'CAO', 'Shortcut Pack', ['new', 'used']),
                ('South County DCJR - New & Used', 'CAO', 'Shortcut Pack', ['new', 'used']),
                ('Thoroughbred - Used', 'CAO', 'Shortcut Pack', ['used'])
            ]
            orders_added += self._insert_orders(thursday_orders, target_date, day_name)
        
        logger.info(f"Added {orders_added} orders to queue for {target_date}")
        return orders_added
    
    def _insert_orders(self, orders: List[tuple], target_date: date, day_name: str) -> int:
        """Insert orders into the queue"""
        count = 0
        for dealership, order_type, template_type, vehicle_types in orders:
            try:
                db_manager.execute_query("""
                    INSERT INTO order_queue 
                    (dealership_name, order_type, template_type, vehicle_types, scheduled_date, day_of_week)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (dealership_name, scheduled_date, order_type) DO NOTHING
                """, (dealership, order_type, template_type, vehicle_types, target_date, day_name))
                count += 1
            except Exception as e:
                logger.error(f"Error inserting order {dealership}: {e}")
        return count
    
    def get_daily_queue(self, target_date: date = None) -> List[Dict]:
        """Get the order queue for a specific date"""
        if target_date is None:
            target_date = date.today()
        
        orders = db_manager.execute_query("""
            SELECT queue_id, dealership_name, order_type, template_type, vehicle_types,
                   scheduled_date, day_of_week, priority, status, assigned_to, notes,
                   started_at, completed_at, processing_duration,
                   vehicles_processed, qr_codes_generated, csv_output_path, qr_output_path,
                   created_at, updated_at
            FROM order_queue 
            WHERE scheduled_date = %s
            ORDER BY priority ASC, created_at ASC
        """, (target_date,))
        
        return orders
    
    def update_order_status(self, queue_id: int, status: str, 
                          assigned_to: str = None, notes: str = None) -> bool:
        """Update order status in the queue"""
        try:
            update_fields = ['status = %s', 'updated_at = CURRENT_TIMESTAMP']
            params = [status]
            
            if status == 'in_progress':
                update_fields.append('started_at = CURRENT_TIMESTAMP')
            elif status == 'completed':
                update_fields.append('completed_at = CURRENT_TIMESTAMP')
                update_fields.append('processing_duration = EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at))')
            
            if assigned_to:
                update_fields.append('assigned_to = %s')
                params.append(assigned_to)
            
            if notes:
                update_fields.append('notes = %s')
                params.append(notes)
            
            params.append(queue_id)
            
            db_manager.execute_query(f"""
                UPDATE order_queue 
                SET {', '.join(update_fields)}
                WHERE queue_id = %s
            """, params)
            
            logger.info(f"Updated order {queue_id} status to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            return False
    
    def process_queue_order(self, queue_id: int) -> Dict[str, Any]:
        """Process a specific order from the queue"""
        try:
            # Get order details
            order = db_manager.execute_query("""
                SELECT * FROM order_queue WHERE queue_id = %s
            """, (queue_id,))[0]
            
            logger.info(f"Processing queue order: {order['dealership_name']} ({order['template_type']})")
            
            # Update status to in_progress
            self.update_order_status(queue_id, 'in_progress')
            
            # Get vehicles for this dealership
            vehicles = self.workflow.filter_vehicles_by_type(
                order['dealership_name'], 
                order['vehicle_types']
            )
            
            if not vehicles:
                logger.warning(f"No vehicles found for {order['dealership_name']}")
                self.update_order_status(queue_id, 'failed', notes='No vehicles found')
                return {
                    'success': False,
                    'error': 'No vehicles found',
                    'queue_id': queue_id
                }
            
            # Create output directories
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dealership_clean = order['dealership_name'].replace(' ', '_').replace('/', '_')
            output_base = Path(f"queue_orders/{dealership_clean}/{timestamp}")
            qr_folder = output_base / "qr_codes"
            csv_folder = output_base / "adobe"
            
            qr_folder.mkdir(parents=True, exist_ok=True)
            csv_folder.mkdir(parents=True, exist_ok=True)
            
            # Generate QR codes
            qr_paths = self.workflow.generate_qr_codes(vehicles, order['dealership_name'], qr_folder)
            
            # Generate template-specific CSV
            csv_path = self._generate_template_csv(
                vehicles, 
                order['dealership_name'], 
                order['template_type'],
                csv_folder, 
                qr_paths
            )
            
            # Update order with results
            db_manager.execute_query("""
                UPDATE order_queue 
                SET vehicles_processed = %s, qr_codes_generated = %s,
                    csv_output_path = %s, qr_output_path = %s
                WHERE queue_id = %s
            """, (len(vehicles), len(qr_paths), csv_path, str(qr_folder), queue_id))
            
            # Mark as completed
            self.update_order_status(queue_id, 'completed')
            
            result = {
                'success': True,
                'queue_id': queue_id,
                'dealership': order['dealership_name'],
                'template_type': order['template_type'],
                'vehicles_processed': len(vehicles),
                'qr_codes_generated': len(qr_paths),
                'csv_file': csv_path,
                'qr_folder': str(qr_folder),
                'timestamp': timestamp
            }
            
            logger.info(f"Queue order completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing queue order {queue_id}: {e}")
            self.update_order_status(queue_id, 'failed', notes=str(e))
            return {
                'success': False,
                'error': str(e),
                'queue_id': queue_id
            }
    
    def _generate_template_csv(self, vehicles: List[Dict], dealership_name: str, 
                             template_type: str, output_folder: Path, 
                             qr_paths: List[str]) -> str:
        """Generate CSV file based on template type"""
        
        if template_type not in self.templates:
            logger.warning(f"Template {template_type} not found, using Flyout")
            template_type = 'Flyout'
        
        template = self.templates[template_type]
        logger.info(f"Using template: {template_type}")
        
        # Create filename
        clean_name = dealership_name.replace(' ', '_').replace('/', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{clean_name}_{template_type.lower().replace(' ', '_')}_{timestamp}.csv"
        filepath = output_folder / filename
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write headers
                writer.writerow(template['headers'])
                
                # Create QR path mapping
                qr_path_map = {}
                if qr_paths:
                    for idx, qr_path in enumerate(qr_paths):
                        if idx < len(vehicles):
                            vehicle_vin = vehicles[idx].get('vin', '')
                            if vehicle_vin:
                                qr_path_map[vehicle_vin] = qr_path
                
                # Generate rows based on template type
                if template_type == 'Shortcut':
                    self._write_shortcut_rows(writer, vehicles, qr_path_map)
                elif template_type == 'Shortcut Pack':
                    self._write_shortcut_pack_rows(writer, vehicles, qr_path_map)
                elif template_type == 'Flyout':
                    self._write_flyout_rows(writer, vehicles, qr_path_map)
                else:
                    # Default to flyout format for custom templates
                    self._write_flyout_rows(writer, vehicles, qr_path_map)
            
            logger.info(f"Generated {template_type} CSV: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error generating template CSV: {e}")
            return ""
    
    def _write_shortcut_rows(self, writer, vehicles: List[Dict], qr_path_map: Dict[str, str]):
        """Write CSV rows for Shortcut template"""
        # Headers: QRYEARMODEL,QRSTOCK,@QR2
        for vehicle in vehicles:
            vin = vehicle.get('vin', '')
            qr_path = qr_path_map.get(vin, '')
            
            # QRYEARMODEL: "2025 GLADIATOR - SL533540"
            year_make_model = f"{vehicle.get('year', '')} {vehicle.get('model', '')} - {vehicle.get('stock', '')}"
            
            # QRSTOCK: "NEW - 1C6PJTAG8SL533540" or "USED - 1C6PJTAG8SL533540"
            vehicle_type = vehicle.get('type', '').upper()
            if vehicle_type == 'NEW':
                stock_vin_status = f"NEW - {vin}"
            else:
                stock_vin_status = f"USED - {vin}"
            
            writer.writerow([year_make_model, stock_vin_status, qr_path])
    
    def _write_shortcut_pack_rows(self, writer, vehicles: List[Dict], qr_path_map: Dict[str, str]):
        """Write CSV rows for Shortcut Pack template"""
        # Headers: YEARMAKE,MODEL,TRIM,STOCK,VIN,@QR,QRYEARMODEL,QRSTOCK,@QR2,MISC
        for vehicle in vehicles:
            vin = vehicle.get('vin', '')
            qr_path = qr_path_map.get(vin, '')
            vehicle_type = vehicle.get('type', '').upper()
            
            # CRITICAL: Add "NEW" prefix to year for new vehicles
            year = str(vehicle.get('year', ''))
            if vehicle_type == 'NEW':
                year_make = f"NEW {year} {vehicle.get('make', '')}"
            else:
                year_make = f"{year} {vehicle.get('make', '')}"
            
            model = vehicle.get('model', '')
            trim = vehicle.get('trim', '')
            
            # STOCK: "2022 RENEGADE - NPN70500"
            stock_description = f"{year} {model} - {vehicle.get('stock', '')}"
            
            # VIN: "USED - ZACNJDB19NPN70500"
            vin_status = f"{vehicle_type} - {vin}"
            
            # QRYEARMODEL: Same as STOCK
            year_make_model = stock_description
            
            # QRSTOCK: Same as VIN
            stock_vin_status = vin_status
            
            # MISC: Combined info
            misc = f"{stock_description} - {vin_status}"
            
            writer.writerow([
                year_make, model, trim, stock_description, vin_status, 
                qr_path, year_make_model, stock_vin_status, qr_path, misc
            ])
    
    def _write_flyout_rows(self, writer, vehicles: List[Dict], qr_path_map: Dict[str, str]):
        """Write CSV rows for Flyout template (standard format)"""
        for vehicle in vehicles:
            vin = vehicle.get('vin', '')
            qr_path = qr_path_map.get(vin, '')
            
            row = [
                vin,
                vehicle.get('stock', ''),
                vehicle.get('type', ''),
                vehicle.get('year', ''),
                vehicle.get('make', ''),
                vehicle.get('model', ''),
                vehicle.get('trim', ''),
                vehicle.get('ext_color', ''),
                vehicle.get('status', ''),
                vehicle.get('price', ''),
                vehicle.get('body_style', ''),
                vehicle.get('fuel_type', ''),
                vehicle.get('msrp', ''),
                vehicle.get('date_in_stock', ''),
                vehicle.get('street_address', ''),
                vehicle.get('locality', ''),
                vehicle.get('postal_code', ''),
                vehicle.get('region', ''),
                vehicle.get('country', ''),
                vehicle.get('location', ''),
                vehicle.get('vehicle_url', ''),
                qr_path
            ]
            writer.writerow(row)
    
    def get_queue_summary(self, target_date: date = None) -> Dict[str, Any]:
        """Get summary statistics for the daily queue"""
        if target_date is None:
            target_date = date.today()
        
        try:
            summary = db_manager.execute_query("""
                SELECT 
                    COUNT(*) as total_orders,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_orders,
                    COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress_orders,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_orders,
                    COALESCE(SUM(vehicles_processed), 0) as total_vehicles,
                    COALESCE(SUM(qr_codes_generated), 0) as total_qr_codes,
                    CASE 
                        WHEN COUNT(*) > 0 THEN 
                            ROUND((COUNT(CASE WHEN status = 'completed' THEN 1 END)::DECIMAL / COUNT(*)) * 100, 2)
                        ELSE 0 
                    END as completion_percentage
                FROM order_queue 
                WHERE scheduled_date = %s
            """, (target_date,))[0]
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting queue summary: {e}")
            return {}

def main():
    """Main testing function"""
    logger.info("Testing Order Queue Manager")
    
    queue_manager = OrderQueueManager()
    
    # Populate today's queue
    today = date.today()
    logger.info(f"Populating queue for {today}")
    orders_added = queue_manager.populate_daily_queue(today)
    
    # Get daily queue
    daily_queue = queue_manager.get_daily_queue(today)
    logger.info(f"Daily queue has {len(daily_queue)} orders")
    
    # Show queue summary
    summary = queue_manager.get_queue_summary(today)
    logger.info(f"Queue summary: {summary}")
    
    # Test processing one order if available
    if daily_queue:
        first_order = daily_queue[0]
        logger.info(f"Testing processing of: {first_order['dealership_name']}")
        result = queue_manager.process_queue_order(first_order['queue_id'])
        logger.info(f"Processing result: {result}")

if __name__ == "__main__":
    main()