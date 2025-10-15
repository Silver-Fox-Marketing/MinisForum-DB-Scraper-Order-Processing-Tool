#!/usr/bin/env python3
"""
Scraper18 Controller
====================

Integration controller that bridges the vehicle_scraper 18 system with
the order processing system. Provides a unified interface to run scrapers
and import data directly into the database.

Author: Silver Fox Assistant
Created: 2025-09-26
"""

import os
import sys
import json
import logging
import subprocess
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add paths to access vehicle_scraper 18 system
current_file = Path(__file__).resolve()
scripts_dir = current_file.parent
bulletproof_dir = scripts_dir.parent
projects_dir = bulletproof_dir.parent.parent

# Path to vehicle_scraper 18 system
scraper18_path = projects_dir / "shared_resources" / "vehicle_scraper 18"
scraper18_scrapers = scraper18_path / "scrapers"

# Add to Python path
sys.path.insert(0, str(scraper18_path))
sys.path.insert(0, str(scraper18_scrapers))

# Import database and progress modules from current system
from database_connection import db_manager
from realtime_scraper_progress import ScraperProgressReporter
from scraper_data_normalizer import normalizer
from scraper_import_manager import ScraperImportManager

class Scraper18WebController:
    """Controller for integrating vehicle_scraper 18 with the order processing system"""

    def __init__(self, socketio=None):
        self.logger = logging.getLogger(__name__)
        self.socketio = socketio
        self.scraper18_path = scraper18_path
        self.scrapers_path = scraper18_scrapers
        self.progress_reporter = ScraperProgressReporter(socketio) if socketio else None
        self.import_manager = ScraperImportManager()

        # Map dealership names to scraper filenames (without .py)
        self.scraper_mapping = {
            'Audi Ranch Mirage': 'audiranchomirage',
            'Auffenberg Hyundai': 'auffenberghyundai',
            'BMW of West St. Louis': 'bmwofweststlouis',
            'Bommarito Cadillac': 'bommaritocadillac',
            'Bommarito West County PO': 'bommaritowestcounty',
            'Columbia BMW': 'columbiabmw',
            'Columbia Honda': 'columbiahonda',
            'Dave Sinclair Lincoln South': 'davesinclairlincolnsouth',
            'Dave Sinclair Lincoln St. Peters': 'davesinclairlincolnstpeters',
            'Frank Leta Honda': 'frankletahonda',
            'Glendale Chrysler Jeep': 'glendalechryslerjeep',
            'Honda of Frontenac': 'hondafrontenac',
            'H&W Kia': 'hwkia',
            'Indigo Auto Group': 'indigoautogroup',
            'Jaguar Ranch Mirage': 'jaguarranchomirage',
            'CDJR of Columbia': 'joemachenscdjr',
            'Joe Machens Hyundai': 'joemachenshyundai',
            'Joe Machens Nissan': 'joemachensnissan',
            'Joe Machens Toyota': 'joemachenstoyota',
            'Kia of Columbia': 'kiaofcolumbia',
            'Land Rover Ranch Mirage': 'landroverranchomirage',
            'Mini of St. Louis': 'miniofstlouis',
            'Pappas Toyota': 'pappastoyota',
            'Porsche St. Louis': 'porschestlouis',
            'Pundmann Ford': 'pundmannford',
            'Rusty Drewing Cadillac': 'rustydrewingcadillac',
            'Rusty Drewing Chevrolet Buick GMC': 'rustydrewingchevroletbuickgmc',
            'Serra Honda O\'Fallon': 'serrahondaofallon',
            'South County Autos': 'southcountyautos',
            'Spirit Lexus': 'spiritlexus',
            'Stehouwer Auto': 'stehouwerauto',
            'Suntrup Buick GMC': 'suntrupbuickgmc',
            'Suntrup Ford Kirkwood': 'suntrupfordkirkwood',
            'Suntrup Ford West': 'suntrupfordwest',
            'Suntrup Hyundai South': 'suntruphyundaisouth',
            'Suntrup Kia South': 'suntrupkiasouth',
            'Thoroughbred Ford': 'thoroughbredford',
            'Twin City Toyota': 'twincitytoyota',
            'Volvo Cars West County': 'wcvolvocars',
            'Weber Chevrolet': 'weberchev'
        }

        print(f"[OK] Scraper18Controller initialized")
        print(f"[INFO] Scraper18 path: {self.scraper18_path}")
        print(f"[INFO] Scrapers available: {len(self.scraper_mapping)}")

    def get_available_scrapers(self):
        """Get list of all available scrapers that exist in the scraper18 system"""
        available = []

        for dealership_name, scraper_name in self.scraper_mapping.items():
            scraper_file = self.scrapers_path / f"{scraper_name}.py"
            if scraper_file.exists():
                available.append({
                    'dealership': dealership_name,
                    'scraper': scraper_name,
                    'path': str(scraper_file),
                    'status': 'available'
                })
            else:
                self.logger.warning(f"Scraper file not found: {scraper_file}")

        return available

    def run_scraper(self, dealership_name: str, import_to_db: bool = True):
        """
        Run a scraper from vehicle_scraper 18 and optionally import to database

        Args:
            dealership_name: Name of the dealership to scrape
            import_to_db: Whether to import results to database

        Returns:
            dict: Result status and details
        """
        try:
            # Get scraper name
            scraper_name = self.scraper_mapping.get(dealership_name)
            if not scraper_name:
                return {
                    'status': 'error',
                    'message': f'No scraper configured for {dealership_name}'
                }

            # Check if scraper file exists
            scraper_file = self.scrapers_path / f"{scraper_name}.py"
            if not scraper_file.exists():
                return {
                    'status': 'error',
                    'message': f'Scraper file not found: {scraper_file}'
                }

            # Setup output directory
            today = datetime.now().strftime('%Y-%m-%d')
            output_dir = self.scraper18_path / 'output_data' / today
            output_dir.mkdir(parents=True, exist_ok=True)

            output_file = output_dir / f"{scraper_name}_vehicles.csv"

            # Report progress
            if self.progress_reporter:
                self.progress_reporter.report_progress(
                    dealership_name,
                    'starting',
                    0,
                    f"Starting scraper for {dealership_name}"
                )

            # Create runner script
            runner_script = self._create_runner_script(scraper_name, str(output_dir), str(output_file))
            temp_script = self.scraper18_path / f"temp_run_{scraper_name}.py"

            with open(temp_script, 'w') as f:
                f.write(runner_script)

            # Run the scraper
            print(f"[INFO] Running scraper: {scraper_name}")
            result = subprocess.run(
                [sys.executable, str(temp_script)],
                cwd=str(self.scraper18_path),
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )

            # Clean up temp script
            if temp_script.exists():
                os.remove(temp_script)

            # Check result
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else result.stdout
                self.logger.error(f"Scraper failed: {error_msg}")

                if self.progress_reporter:
                    self.progress_reporter.report_progress(
                        dealership_name,
                        'error',
                        0,
                        f"Scraper failed: {error_msg[:200]}"
                    )

                return {
                    'status': 'error',
                    'message': f'Scraper failed: {error_msg[:500]}'
                }

            print(f"[SUCCESS] Scraper completed: {scraper_name}")

            # Import to database if requested
            if import_to_db and output_file.exists():
                import_result = self._import_to_database(dealership_name, str(output_file))

                if self.progress_reporter:
                    self.progress_reporter.report_progress(
                        dealership_name,
                        'complete',
                        100,
                        f"Scraper completed and data imported"
                    )

                return {
                    'status': 'success',
                    'output_file': str(output_file),
                    'import_result': import_result
                }

            if self.progress_reporter:
                self.progress_reporter.report_progress(
                    dealership_name,
                    'complete',
                    100,
                    f"Scraper completed"
                )

            return {
                'status': 'success',
                'output_file': str(output_file)
            }

        except subprocess.TimeoutExpired:
            error_msg = f"Scraper timeout after 30 minutes"
            self.logger.error(error_msg)

            if self.progress_reporter:
                self.progress_reporter.report_progress(
                    dealership_name,
                    'error',
                    0,
                    error_msg
                )

            return {
                'status': 'error',
                'message': error_msg
            }

        except Exception as e:
            error_msg = f"Error running scraper: {str(e)}"
            self.logger.error(error_msg)

            if self.progress_reporter:
                self.progress_reporter.report_progress(
                    dealership_name,
                    'error',
                    0,
                    error_msg
                )

            return {
                'status': 'error',
                'message': error_msg
            }

    def _create_runner_script(self, scraper_name: str, output_dir: str, output_file: str) -> str:
        """Create a Python script to run the scraper"""
        # Use forward slashes to avoid escape sequence issues
        output_dir = output_dir.replace('\\', '/')
        output_file = output_file.replace('\\', '/')

        return f"""
import sys
import os

# Set up the environment for the scrapers package
original_cwd = os.getcwd()
scraper_root = os.getcwd()  # Should be the vehicle_scraper 18 directory

# Add the parent directory to Python path to allow 'scrapers' package import
sys.path.insert(0, scraper_root)

try:
    # Import the scrapers package and specific scraper
    from scrapers import {scraper_name}

    # Initialize data
    data_folder = '{output_dir}/'
    output_file = '{output_file}'

    # Create the scraper class name (uppercase version)
    class_name = '{scraper_name.upper()}'

    # Get the class from the module
    scraper_class = getattr({scraper_name}, class_name)

    print(f'[START] Starting {{class_name}} scraper')
    print(f'[OUTPUT] Data will be saved to: {{output_file}}')

    # Instantiate and run the scraper
    scraper_instance = scraper_class(data_folder, output_file)

    # Run the scraper method
    scraper_method = getattr(scraper_instance, f'start_scraping_{scraper_name}')
    scraper_method()

    print('[SUCCESS] Scraper completed successfully')

except Exception as e:
    print(f'[ERROR] Scraper failed: {{str(e)}}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    # Restore original working directory
    if original_cwd != os.getcwd():
        os.chdir(original_cwd)
"""

    def _import_to_database(self, dealership_name: str, csv_file: str) -> dict:
        """Import scraped data from CSV to database"""
        try:
            # Create import record
            import_id = self.import_manager.create_import(
                source=f"scraper18_{dealership_name.lower().replace(' ', '_')}",
                vehicle_count=0  # Will be updated after import
            )

            # Read and import CSV data
            import csv
            vehicles_imported = 0

            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    # Normalize and store vehicle data
                    normalized = normalizer.normalize_vehicle_data(row, dealership_name)

                    if normalized:
                        # Store in database
                        self._store_vehicle(normalized, import_id)
                        vehicles_imported += 1

            # Update import record
            self.import_manager.update_import_count(import_id, vehicles_imported)
            self.import_manager.complete_import(import_id, vehicles_imported)

            return {
                'import_id': import_id,
                'vehicles_imported': vehicles_imported,
                'status': 'success'
            }

        except Exception as e:
            self.logger.error(f"Database import failed: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _store_vehicle(self, vehicle_data: dict, import_id: int):
        """Store vehicle in database"""
        try:
            # Store raw data
            raw_query = """
                INSERT INTO raw_vehicle_data (
                    import_id, vin, stock_number, vehicle_type, year, make, model,
                    trim, exterior_color, status, price, body_style, fuel_type,
                    msrp, date_in_stock, location, raw_json
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """

            raw_params = (
                import_id,
                vehicle_data.get('vin'),
                vehicle_data.get('stock'),
                vehicle_data.get('type'),
                vehicle_data.get('year'),
                vehicle_data.get('make'),
                vehicle_data.get('model'),
                vehicle_data.get('trim'),
                vehicle_data.get('exterior_color'),
                vehicle_data.get('status'),
                vehicle_data.get('price'),
                vehicle_data.get('body_style'),
                vehicle_data.get('fuel_type'),
                vehicle_data.get('msrp'),
                vehicle_data.get('date_in_stock'),
                vehicle_data.get('location'),
                json.dumps(vehicle_data)
            )

            raw_result = db_manager.execute_query(raw_query, raw_params)

            if raw_result:
                raw_data_id = raw_result[0]['id']

                # Store normalized data
                norm_query = """
                    INSERT INTO normalized_vehicle_data (
                        raw_data_id, vin, stock_number, vehicle_condition, year, make,
                        model, trim, exterior_color, interior_color, price, msrp,
                        mileage, body_style, fuel_type, transmission, drivetrain,
                        engine, location, date_in_stock, days_in_stock, import_timestamp
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """

                norm_params = (
                    raw_data_id,
                    vehicle_data.get('vin'),
                    vehicle_data.get('stock'),
                    vehicle_data.get('condition', vehicle_data.get('type', 'used')),
                    vehicle_data.get('year'),
                    vehicle_data.get('make'),
                    vehicle_data.get('model'),
                    vehicle_data.get('trim'),
                    vehicle_data.get('exterior_color'),
                    vehicle_data.get('interior_color'),
                    vehicle_data.get('price'),
                    vehicle_data.get('msrp'),
                    vehicle_data.get('mileage'),
                    vehicle_data.get('body_style'),
                    vehicle_data.get('fuel_type'),
                    vehicle_data.get('transmission'),
                    vehicle_data.get('drivetrain'),
                    vehicle_data.get('engine'),
                    vehicle_data.get('location'),
                    vehicle_data.get('date_in_stock'),
                    vehicle_data.get('days_in_stock', 0)
                )

                db_manager.execute_query(norm_query, norm_params)

        except Exception as e:
            self.logger.error(f"Failed to store vehicle: {str(e)}")
            raise

    def run_all_scrapers(self, dealerships: List[str] = None):
        """Run multiple scrapers in sequence and consolidate output"""
        import csv
        import os

        if not dealerships:
            dealerships = list(self.scraper_mapping.keys())

        results = {}

        # Setup consolidated output
        today = datetime.now().strftime('%Y-%m-%d')
        output_dir = self.scraper18_path / 'output_data' / today
        output_dir.mkdir(parents=True, exist_ok=True)

        consolidated_file = output_dir / 'complete_data.csv'
        all_vehicle_data = []
        headers_written = False

        for dealership in dealerships:
            print(f"[INFO] Running scraper for {dealership}")
            result = self.run_scraper(dealership, import_to_db=False)  # Don't import yet
            results[dealership] = result

            # If scraper succeeded, read its output and add to consolidated data
            if result.get('status') == 'success' and 'output_file' in result:
                individual_file = result['output_file']
                if os.path.exists(individual_file):
                    try:
                        with open(individual_file, 'r', encoding='utf-8-sig') as f:
                            reader = csv.DictReader(f)

                            # Get headers from first successful file
                            if not headers_written:
                                headers = reader.fieldnames
                                headers_written = True

                            # Add all rows to consolidated data
                            for row in reader:
                                all_vehicle_data.append(row)

                        print(f"[OK] Added data from {dealership} to consolidated output")

                        # Remove individual file to keep only consolidated output
                        os.remove(individual_file)

                    except Exception as e:
                        print(f"[ERROR] Failed to process {dealership} output: {e}")

            # Brief pause between scrapers
            time.sleep(2)

        # Write consolidated output file
        if all_vehicle_data and headers_written:
            try:
                with open(consolidated_file, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(all_vehicle_data)

                print(f"[SUCCESS] Consolidated output written to: {consolidated_file}")
                print(f"[INFO] Total vehicles scraped: {len(all_vehicle_data)}")

                # Now import the consolidated file to database
                import_result = self._import_consolidated_to_database(str(consolidated_file))

                results['consolidated'] = {
                    'status': 'success',
                    'output_file': str(consolidated_file),
                    'total_vehicles': len(all_vehicle_data),
                    'import_result': import_result
                }

            except Exception as e:
                print(f"[ERROR] Failed to write consolidated file: {e}")
                results['consolidated'] = {
                    'status': 'error',
                    'message': f'Failed to write consolidated file: {e}'
                }
        else:
            print("[WARNING] No vehicle data collected from any scrapers")
            results['consolidated'] = {
                'status': 'warning',
                'message': 'No vehicle data collected from any scrapers'
            }

        return results

    def _import_consolidated_to_database(self, csv_file: str) -> dict:
        """Import consolidated CSV data to database with proper import management"""
        try:
            # Create a single import record for all consolidated data
            import_id = self.import_manager.create_import(
                source="scraper18_consolidated_all_dealerships",
                vehicle_count=0  # Will be updated after import
            )

            # Read and import CSV data
            import csv
            vehicles_imported = 0
            dealership_counts = {}

            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    # Determine dealership from the row data
                    dealership_name = row.get('location', 'Unknown')

                    # Track counts per dealership
                    if dealership_name not in dealership_counts:
                        dealership_counts[dealership_name] = 0

                    # Normalize and store vehicle data
                    normalized = normalizer.normalize_vehicle_data(row, dealership_name)

                    if normalized:
                        # Store in database
                        self._store_vehicle(normalized, import_id)
                        vehicles_imported += 1
                        dealership_counts[dealership_name] += 1

            # Update import record
            self.import_manager.update_import_count(import_id, vehicles_imported)
            self.import_manager.complete_import(import_id, vehicles_imported)

            print(f"[DATABASE] Imported {vehicles_imported} vehicles from consolidated file")
            for dealership, count in dealership_counts.items():
                print(f"[DATABASE]   - {dealership}: {count} vehicles")

            return {
                'import_id': import_id,
                'vehicles_imported': vehicles_imported,
                'dealership_breakdown': dealership_counts,
                'status': 'success'
            }

        except Exception as e:
            self.logger.error(f"Consolidated database import failed: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }