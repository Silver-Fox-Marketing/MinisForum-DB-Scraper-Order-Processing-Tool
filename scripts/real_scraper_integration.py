#!/usr/bin/env python3
"""
Real Scraper Integration
========================

Integration system to call our real working scrapers and import their data
into the database system. This replaces the CSV-only approach with live scraping.

Author: Silver Fox Assistant
Created: 2025-07-28
"""

import os
import sys
import json
import logging
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project paths - fix path resolution
current_file = Path(__file__).resolve()
print(f"DEBUG: Current file: {current_file}")

# Go up to projects directory
projects_root = current_file.parent.parent.parent.parent
print(f"DEBUG: Projects root: {projects_root}")

scrapers_path = projects_root / "silverfox_scraper_system" / "silverfox_system" / "core" / "scrapers" / "dealerships"
print(f"DEBUG: Scrapers path: {scrapers_path}")
print(f"DEBUG: Scrapers path exists: {scrapers_path.exists()}")

sys.path.insert(0, str(scrapers_path))

from database_connection import db_manager
from realtime_scraper_progress import ScraperProgressReporter

class RealScraperIntegration:
    """Integration system for real working scrapers"""
    
    def __init__(self, socketio=None):
        self.logger = logging.getLogger(__name__)
        self.scrapers_path = scrapers_path
        self.progress_reporter = ScraperProgressReporter(socketio)
        
        print(f"DEBUG: RealScraperIntegration initialized")
        print(f"DEBUG: Scrapers path in class: {self.scrapers_path}")
        print(f"DEBUG: Scrapers path exists in class: {self.scrapers_path.exists()}")
        
        # Map dealership names to their real scraper files
        self.real_scraper_mapping = {
            'Test Integration Dealer': 'test_integration_scraper.py',
            'Columbia Honda': 'columbiahonda_real_working.py',
            'Dave Sinclair Lincoln South': 'davesinclairlincolnsouth_real_working.py', 
            'BMW of West St. Louis': 'bmwofweststlouis_real_working.py'
        }
        
        # Expected vehicle counts for progress estimation
        self.expected_vehicle_counts = {
            'Test Integration Dealer': 5,
            'Columbia Honda': 40,
            'Dave Sinclair Lincoln South': 25,
            'BMW of West St. Louis': 55
        }
        
        print(f"DEBUG: Real scraper mapping: {list(self.real_scraper_mapping.keys())}")
        
        # Check if real scraper files exist
        for dealership, filename in self.real_scraper_mapping.items():
            file_path = self.scrapers_path / filename
            exists = file_path.exists()
            print(f"DEBUG: {dealership} -> {filename} -> exists: {exists}")
            if exists:
                print(f"DEBUG: Full path: {file_path}")
    
    def load_scraper_module(self, scraper_file: Path):
        """Dynamically load a scraper module"""
        try:
            spec = importlib.util.spec_from_file_location("scraper_module", scraper_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        except Exception as e:
            self.logger.error(f"Error loading {scraper_file}: {e}")
            return None
    
    def find_scraper_class(self, module):
        """Find the scraper class in the module"""
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and attr_name.endswith('Scraper'):
                return attr
        return None
    
    def run_real_scraper(self, dealership_name: str) -> Dict[str, Any]:
        """Run a real scraper for a specific dealership with progress reporting"""
        try:
            # Start progress reporting
            expected_vehicles = self.expected_vehicle_counts.get(dealership_name, 30)
            self.progress_reporter.start_scraper(dealership_name, expected_vehicles)
            
            self.logger.info(f"Running real scraper for: {dealership_name}")
            
            # Check if we have a real scraper for this dealership
            scraper_filename = self.real_scraper_mapping.get(dealership_name)
            if not scraper_filename:
                self.logger.warning(f"No real scraper available for {dealership_name}")
                result = {'success': False, 'error': 'No real scraper available', 'vehicles': []}
                self.progress_reporter.complete_scraper(dealership_name, result)
                return result
            
            self.progress_reporter.update_scraper_progress(dealership_name, "[LOCATE] Locating scraper file...")
            
            # Load the scraper module
            scraper_file = self.scrapers_path / scraper_filename
            if not scraper_file.exists():
                self.logger.error(f"Scraper file not found: {scraper_file}")
                result = {'success': False, 'error': 'Scraper file not found', 'vehicles': []}
                self.progress_reporter.complete_scraper(dealership_name, result)
                return result
            
            self.progress_reporter.update_scraper_progress(dealership_name, "[LOAD] Loading scraper module...")
            
            module = self.load_scraper_module(scraper_file)
            if not module:
                result = {'success': False, 'error': 'Failed to load scraper module', 'vehicles': []}
                self.progress_reporter.complete_scraper(dealership_name, result)
                return result
            
            self.progress_reporter.update_scraper_progress(dealership_name, "[FIND] Finding scraper class...")
            
            # Find and instantiate the scraper class
            scraper_class = self.find_scraper_class(module)
            if not scraper_class:
                self.logger.error(f"No scraper class found in {scraper_filename}")
                result = {'success': False, 'error': 'No scraper class found', 'vehicles': []}
                self.progress_reporter.complete_scraper(dealership_name, result)
                return result
            
            self.progress_reporter.update_scraper_progress(dealership_name, f"[INIT] Initializing {scraper_class.__name__}...")
            
            # Run the scraper
            self.logger.info(f"Initializing {scraper_class.__name__}")
            scraper = scraper_class()
            
            self.progress_reporter.update_scraper_progress(dealership_name, "[API] Connecting to dealership API...")
            
            start_time = datetime.now()
            vehicles = scraper.get_all_vehicles()
            end_time = datetime.now()
            
            self.progress_reporter.update_scraper_progress(dealership_name, "[PROCESS] Processing vehicle data...")
            
            duration = (end_time - start_time).total_seconds()
            vehicle_count = len(vehicles) if vehicles else 0
            
            # Check if we got real data or fallback
            data_source = 'unknown'
            if vehicles:
                data_source = vehicles[0].get('data_source', 'unknown')
            
            is_real_data = 'real' in data_source.lower()
            
            result = {
                'success': True,
                'dealership_name': dealership_name,
                'vehicle_count': vehicle_count,
                'duration_seconds': duration,
                'data_source': data_source,
                'is_real_data': is_real_data,
                'vehicles': vehicles,
                'scraper_class': scraper_class.__name__,
                'scraped_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"Scraper completed: {vehicle_count} vehicles in {duration:.1f}s")
            if is_real_data:
                self.logger.info("[SUCCESS] REAL DATA EXTRACTED!")
            else:
                self.logger.warning("[FALLBACK] Using fallback data")
            
            # Complete progress reporting
            self.progress_reporter.complete_scraper(dealership_name, result)
            return result
            
        except Exception as e:
            self.logger.error(f"Error running scraper for {dealership_name}: {e}")
            result = {
                'success': False, 
                'error': str(e), 
                'dealership_name': dealership_name,
                'vehicles': []
            }
            self.progress_reporter.complete_scraper(dealership_name, result)
            return result
    
    def import_vehicles_to_database(self, vehicles: List[Dict], dealership_name: str) -> Dict[str, Any]:
        """Import scraped vehicles into the database"""
        try:
            if not vehicles:
                return {'success': False, 'error': 'No vehicles to import'}
            
            self.logger.info(f"Importing {len(vehicles)} vehicles for {dealership_name}")
            
            imported_count = 0
            updated_count = 0
            
            for vehicle in vehicles:
                try:
                    # Check if vehicle already exists
                    existing = db_manager.execute_query(
                        "SELECT id FROM raw_vehicle_data WHERE vin = %s",
                        (vehicle['vin'],)
                    )
                    
                    if existing:
                        # Update existing vehicle
                        db_manager.execute_query("""
                            UPDATE raw_vehicle_data SET
                                stock = %s,
                                type = %s,
                                year = %s,
                                make = %s,
                                model = %s,
                                trim = %s,
                                ext_color = %s,
                                status = %s,
                                price = %s,
                                msrp = %s,
                                body_style = %s,
                                fuel_type = %s,
                                street_address = %s,
                                locality = %s,
                                postal_code = %s,
                                region = %s,
                                country = %s,
                                location = %s,
                                vehicle_url = %s,
                                import_timestamp = CURRENT_TIMESTAMP
                            WHERE vin = %s
                        """, (
                            vehicle.get('stock_number', ''),
                            vehicle.get('condition', ''),
                            vehicle.get('year', 0),
                            vehicle.get('make', ''),
                            vehicle.get('model', ''),
                            vehicle.get('trim', ''),
                            vehicle.get('exterior_color', ''),
                            vehicle.get('status', ''),
                            vehicle.get('price'),
                            vehicle.get('msrp'),
                            vehicle.get('body_style', ''),
                            vehicle.get('fuel_type', ''),
                            vehicle.get('street_address', ''),
                            vehicle.get('locality', ''),
                            vehicle.get('postal_code', ''),
                            vehicle.get('region', ''),
                            vehicle.get('country', ''),
                            vehicle.get('location', ''),
                            vehicle.get('url', ''),
                            vehicle['vin']
                        ))
                        updated_count += 1
                    else:
                        # Insert new vehicle
                        db_manager.execute_query("""
                            INSERT INTO raw_vehicle_data (
                                vin, stock, type, year, make, model, trim,
                                ext_color, status, price, msrp,
                                body_style, fuel_type, street_address, locality,
                                postal_code, region, country, location, vehicle_url,
                                import_timestamp
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
                            )
                        """, (
                            vehicle['vin'],
                            vehicle.get('stock_number', ''),
                            vehicle.get('condition', ''),
                            vehicle.get('year', 0),
                            vehicle.get('make', ''),
                            vehicle.get('model', ''),
                            vehicle.get('trim', ''),
                            vehicle.get('exterior_color', ''),
                            vehicle.get('status', ''),
                            vehicle.get('price'),
                            vehicle.get('msrp'),
                            vehicle.get('body_style', ''),
                            vehicle.get('fuel_type', ''),
                            vehicle.get('street_address', ''),
                            vehicle.get('locality', ''),
                            vehicle.get('postal_code', ''),
                            vehicle.get('region', ''),
                            vehicle.get('country', ''),
                            vehicle.get('location', ''),
                            vehicle.get('url', '')
                        ))
                        imported_count += 1
                        
                except Exception as e:
                    self.logger.error(f"Error importing vehicle {vehicle.get('vin', 'unknown')}: {e}")
                    continue
            
            self.logger.info(f"Database import complete: {imported_count} new, {updated_count} updated")
            
            return {
                'success': True,
                'imported_count': imported_count,
                'updated_count': updated_count,
                'total_processed': imported_count + updated_count
            }
            
        except Exception as e:
            self.logger.error(f"Error importing vehicles to database: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_all_available_scrapers(self) -> Dict[str, Any]:
        """Run all available real scrapers with progress reporting"""
        scraper_names = list(self.real_scraper_mapping.keys())
        
        # Start session progress reporting
        self.progress_reporter.start_scraping_session(len(scraper_names), scraper_names)
        
        results = {
            'start_time': datetime.now(),
            'dealerships': {},
            'total_vehicles': 0,
            'total_real_data': 0,
            'total_fallback_data': 0,
            'errors': []
        }
        
        for dealership_name in scraper_names:
            self.logger.info(f"Processing dealership: {dealership_name}")
            
            # Run the scraper (includes its own progress reporting)
            scraper_result = self.run_real_scraper(dealership_name)
            
            if scraper_result['success']:
                # Import vehicles to database
                import_result = self.import_vehicles_to_database(
                    scraper_result['vehicles'], 
                    dealership_name
                )
                
                # Record results
                results['dealerships'][dealership_name] = {
                    'scraper_result': scraper_result,
                    'import_result': import_result,
                    'status': 'completed'
                }
                
                results['total_vehicles'] += scraper_result['vehicle_count']
                
                if scraper_result['is_real_data']:
                    results['total_real_data'] += scraper_result['vehicle_count']
                else:
                    results['total_fallback_data'] += scraper_result['vehicle_count']
                    
            else:
                results['dealerships'][dealership_name] = {
                    'status': 'failed',
                    'error': scraper_result.get('error', 'Unknown error')
                }
                results['errors'].append(f"{dealership_name}: {scraper_result.get('error', 'Unknown error')}")
        
        results['end_time'] = datetime.now()
        results['duration'] = (results['end_time'] - results['start_time']).total_seconds()
        
        # Complete session progress reporting
        self.progress_reporter.complete_session(results)
        
        self.logger.info(f"All scrapers completed: {results['total_vehicles']} total vehicles")
        self.logger.info(f"Real data: {results['total_real_data']}, Fallback: {results['total_fallback_data']}")
        
        return results

def test_integration():
    """Test the real scraper integration"""
    logging.basicConfig(level=logging.INFO)
    integration = RealScraperIntegration()
    
    # Test single scraper
    result = integration.run_real_scraper('Columbia Honda')
    print(f"Test result: {result['success']}")
    if result['success']:
        print(f"Vehicles: {result['vehicle_count']}")
        print(f"Data source: {result['data_source']}")
        print(f"Real data: {result['is_real_data']}")

if __name__ == "__main__":
    test_integration()