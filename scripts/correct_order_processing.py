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
        self.output_base = Path("orders")
        self.output_base.mkdir(exist_ok=True)
        
        # Map dealership config names to actual data location names
        self.dealership_name_mapping = {
            'Dave Sinclair Lincoln South': 'Dave Sinclair Lincoln',
            'BMW of West St. Louis': 'BMW of West St. Louis', 
            'Columbia Honda': 'Columbia Honda'
        }
        
        # Reverse mapping for VIN history lookups
        self.vin_history_name_variations = {
            'Dave Sinclair Lincoln South': ['Dave Sinclair Lincoln South', 'Dave Sinclair Lincoln'],
            'Dave Sinclair Lincoln': ['Dave Sinclair Lincoln South', 'Dave Sinclair Lincoln'],
            'BMW of West St. Louis': ['BMW of West St. Louis'],
            'Columbia Honda': ['Columbia Honda']
        }
    
    def process_cao_order(self, dealership_name: str, template_type: str = "shortcut_pack") -> Dict[str, Any]:
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
            
            # Step 6: Update VIN history for next comparison (Enhanced)
            self._update_vin_history_enhanced(dealership_name, new_vehicles)
            
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
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Error processing CAO order: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_list_order(self, dealership_name: str, vin_list: List[str], template_type: str = "shortcut_pack") -> Dict[str, Any]:
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
            
            if not vehicles:
                return {'success': False, 'error': 'No vehicles found for provided VINs'}
            
            # Create output folders
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            order_folder = self.output_base / dealership_name.replace(' ', '_') / timestamp
            qr_folder = order_folder / "qr_codes"
            
            order_folder.mkdir(parents=True, exist_ok=True)
            qr_folder.mkdir(exist_ok=True)
            
            # Generate QR codes
            qr_paths = self._generate_qr_codes(vehicles, dealership_name, qr_folder)
            
            # Generate Adobe CSV
            csv_path = self._generate_adobe_csv(vehicles, dealership_name, template_type, order_folder, qr_paths)
            
            return {
                'success': True,
                'dealership': dealership_name,
                'template_type': template_type,
                'vehicles_processed': len(vehicles),
                'qr_codes_generated': len(qr_paths),
                'qr_folder': str(qr_folder),
                'csv_file': str(csv_path),
                'download_csv': f"/download_csv/{csv_path.name}",
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Error processing list order: {e}")
            return {'success': False, 'error': str(e)}
    
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
        query = "SELECT * FROM raw_vehicle_data WHERE location = %s"
        params = [actual_location_name]
        
        # Apply vehicle type filter
        vehicle_types = filtering_rules.get('vehicle_types', ['new', 'used', 'certified'])
        if vehicle_types and 'all' not in vehicle_types:
            type_conditions = []
            for vtype in vehicle_types:
                if vtype == 'certified':
                    type_conditions.append("(type ILIKE '%certified%' OR type ILIKE '%cpo%')")
                else:
                    type_conditions.append("type ILIKE %s")
                    params.append(f'%{vtype}%')
            if type_conditions:
                query += f" AND ({' OR '.join(type_conditions)})"
        
        # Apply year filter
        min_year = filtering_rules.get('min_year')
        if min_year:
            query += " AND year >= %s"
            params.append(min_year)
        
        # Apply price filter (skip for now to avoid casting issues)
        # min_price = filtering_rules.get('min_price', 0)
        # if min_price > 0:
        #     query += " AND CAST(REPLACE(REPLACE(price, '$', ''), ',', '') AS INTEGER) >= %s"
        #     params.append(min_price)
        
        query += " ORDER BY import_timestamp DESC"
        
        logger.info(f"Query: {query}")
        logger.info(f"Params: {params}")
        
        try:
            result = db_manager.execute_query(query, tuple(params))
            logger.info(f"Query returned {len(result)} vehicles")
            return result
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            # Fallback to simple query
            return db_manager.execute_query("SELECT * FROM raw_vehicle_data WHERE location = %s LIMIT 100", (actual_location_name,))
    
    def _find_new_vehicles(self, dealership_name: str, current_vins: List[str]) -> List[str]:
        """Compare with last order to find NEW vehicles"""
        
        # Map dealership config name to actual data location name
        actual_location_name = self.dealership_name_mapping.get(dealership_name, dealership_name)
        
        # Get previous VINs from last order - check both names for compatibility
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
        """Generate QR codes for vehicle URLs"""
        
        qr_paths = []
        clean_name = dealership_name.replace(' ', '_')
        
        for idx, vehicle in enumerate(vehicles, 1):
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
                
                # Create QR image - 388x388 as per reference
                img = qr.make_image(fill_color="rgb(50,50,50)", back_color="white")
                img = img.resize((388, 388), Image.Resampling.LANCZOS)
                
                # Save with exact naming convention from reference
                filename = f"{clean_name}_QR_Code_{idx}.PNG"
                filepath = output_folder / filename
                img.save(filepath)
                
                qr_paths.append(str(filepath))
                
            except Exception as e:
                logger.error(f"Error generating QR for {vehicle.get('vin')}: {e}")
        
        logger.info(f"Generated {len(qr_paths)} QR codes")
        return qr_paths
    
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
        Enhanced VIN comparison that handles cross-dealership and relisted scenarios
        
        Logic:
        - Different dealership: Always process 
        - Same dealership + different vehicle type: Always process
        - Same dealership + same type: Check time window (7 days)
        - Same dealership + any type within 1 day: Skip (too recent)
        """
        
        # Get all possible name variations for this dealership
        dealership_variations = self.vin_history_name_variations.get(dealership_name, [dealership_name])
        actual_location_name = self.dealership_name_mapping.get(dealership_name, dealership_name)
        
        logger.info(f"Checking VIN history for dealership variations: {dealership_variations}")
        
        new_vins = []
        
        for vehicle in current_vehicles:
            vin = vehicle.get('vin')
            current_type = self._normalize_vehicle_type(vehicle.get('type', 'unknown'))
            
            if not vin:
                continue
                
            # Check VIN history with enhanced logic
            history = db_manager.execute_query("""
                SELECT dealership_name, vehicle_type, order_date,
                       (CURRENT_DATE - order_date) as days_ago
                FROM vin_history 
                WHERE vin = %s 
                ORDER BY order_date DESC 
                LIMIT 10
            """, (vin,))
            
            should_process = True
            
            if history:
                for record in history:
                    prev_dealership = record['dealership_name']
                    prev_type = record['vehicle_type'] or 'unknown'
                    days_ago = record['days_ago']
                    
                    # Check if this is the same dealership (using all variations)
                    is_same_dealership = prev_dealership in dealership_variations
                    
                    if is_same_dealership:
                        # Rule 1: Skip if same dealership, any type, processed within 1 day
                        if days_ago <= 1:
                            logger.info(f"Skipping {vin}: Same dealership ({prev_dealership}) processed {days_ago} days ago")
                            should_process = False
                            break
                        
                        # Rule 2: Skip if same dealership, same type, processed within 7 days  
                        elif prev_type == current_type and days_ago <= 7:
                            logger.info(f"Skipping {vin}: Same dealership+type ({prev_dealership}, {prev_type}) processed {days_ago} days ago")
                            should_process = False
                            break
                            
                        # Rule 4: Process if same dealership but different type (status change)
                        elif prev_type != current_type:
                            logger.info(f"Processing {vin}: Status change at {prev_dealership} ({prev_type} -> {current_type})")
                            should_process = True
                            break
                    else:
                        # Rule 3: Process if different dealership (cross-dealership opportunity)
                        logger.info(f"Processing {vin}: Cross-dealership opportunity ({prev_dealership} -> {dealership_name})")
                        should_process = True
                        break
            else:
                # No history = definitely new
                logger.info(f"Processing {vin}: No previous history")
                should_process = True
            
            if should_process:
                new_vins.append(vin)
        
        logger.info(f"Enhanced logic: {len(current_vins)} current, {len(new_vins)} need processing")
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