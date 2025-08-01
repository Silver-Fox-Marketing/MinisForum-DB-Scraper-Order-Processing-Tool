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

scrapers_path = current_file.parent.parent / "scrapers"  # Point to bulletproof package scrapers
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
            'Audi Ranch Mirage': 'audiranchomirage.py',
            'Auffenberg Hyundai': 'auffenberghyundai.py',
            'BMW of West St. Louis': 'bmwofweststlouis.py',
            'Bommarito Cadillac': 'bommaritocadillac.py',
            'Bommarito West County': 'bommaritowestcounty.py',
            'Columbia BMW': 'columbiabmw.py',
            'Columbia Honda': 'columbiahonda.py',
            'Dave Sinclair Lincoln South': 'davesinclairlincolnsouth.py',
            'Dave Sinclair Lincoln St. Peters': 'davesinclairlincolnstpeters.py',
            'Frank Leta Honda': 'frankletahonda.py',
            'Glendale Chrysler Jeep': 'glendalechryslerjeep.py',
            'Honda of Frontenac': 'hondafrontenac.py',
            'H&W Kia': 'hwkia.py',
            'Indigo Auto Group': 'indigoautogroup.py',
            'Jaguar Ranch Mirage': 'jaguarranchomirage.py',
            'Joe Machens CDJR': 'joemachenscdjr.py',
            'Joe Machens Hyundai': 'joemachenshyundai.py',
            'Joe Machens Nissan': 'joemachensnissan.py',
            'Joe Machens Toyota': 'joemachenstoyota.py',
            'Kia of Columbia': 'kiaofcolumbia.py',
            'Land Rover Ranch Mirage': 'landroverranchomirage.py',
            'Mini of St. Louis': 'miniofstlouis.py',
            'Pappas Toyota': 'pappastoyota.py',
            'Porsche St. Louis': 'porschestlouis.py',
            'Pundmann Ford': 'pundmannford.py',
            'Rusty Drewing Cadillac': 'rustydrewingcadillac.py',
            'Rusty Drewing Chevrolet Buick GMC': 'rustydrewingchevroletbuickgmc.py',
            'Serra Honda O\'Fallon': 'serrahondaofallon.py',
            'South County Autos': 'southcountyautos.py',
            'Spirit Lexus': 'spiritlexus.py',
            'Stehouwer Auto': 'stehouwerauto.py',
            'Suntrup Buick GMC': 'suntrupbuickgmc.py',
            'Suntrup Ford Kirkwood': 'suntrupfordkirkwood.py',
            'Suntrup Ford West': 'suntrupfordwest.py',
            'Suntrup Hyundai South': 'suntruphyundaisouth.py',
            'Suntrup Kia South': 'suntrupkiasouth.py',
            'Thoroughbred Ford': 'thoroughbredford.py',
            'Twin City Toyota': 'twincitytoyota.py',
            'West County Volvo Cars': 'wcvolvocars.py',
            'Weber Chevrolet': 'weberchev.py'
        }
        
                # Expected vehicle counts for progress estimation
        self.expected_vehicle_counts = {
            'Test Integration Dealer': 5,
            'Audi Ranch Mirage': 30,
            'Auffenberg Hyundai': 35,
            'BMW of West St. Louis': 55,
            'Bommarito Cadillac': 25,
            'Bommarito West County': 40,
            'Columbia BMW': 35,
            'Columbia Honda': 40,
            'Dave Sinclair Lincoln South': 25,
            'Dave Sinclair Lincoln St. Peters': 20,
            'Frank Leta Honda': 45,
            'Glendale Chrysler Jeep': 35,
            'Honda of Frontenac': 30,
            'H&W Kia': 25,
            'Indigo Auto Group': 50,
            'Jaguar Ranch Mirage': 15,
            'Joe Machens CDJR': 35,
            'Joe Machens Hyundai': 30,
            'Joe Machens Nissan': 25,
            'Joe Machens Toyota': 40,
            'Kia of Columbia': 20,
            'Land Rover Ranch Mirage': 15,
            'Mini of St. Louis': 20,
            'Pappas Toyota': 35,
            'Porsche St. Louis': 20,
            'Pundmann Ford': 30,
            'Rusty Drewing Cadillac': 25,
            'Rusty Drewing Chevrolet Buick GMC': 45,
            'Serra Honda O\'Fallon': 35,
            'South County Autos': 25,
            'Spirit Lexus': 30,
            'Stehouwer Auto': 20,
            'Suntrup Buick GMC': 35,
            'Suntrup Ford Kirkwood': 40,
            'Suntrup Ford West': 45,
            'Suntrup Hyundai South': 30,
            'Suntrup Kia South': 25,
            'Thoroughbred Ford': 35,
            'Twin City Toyota': 30,
            'West County Volvo Cars': 25,
            'Weber Chevrolet': 40
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
        """Run a real scraper using the enhanced controller with bulletproof error handling"""
        try:
            # Import enhanced controller
            from enhanced_scraper_controller import EnhancedScraperController
            
            # Start progress reporting
            expected_vehicles = self.expected_vehicle_counts.get(dealership_name, 30)
            self.progress_reporter.start_scraper(dealership_name, expected_vehicles)
            
            self.logger.info(f"Running enhanced scraper for: {dealership_name}")
            
            # Map display name to site name for the enhanced controller
            display_to_site_mapping = {
                'Test Integration Dealer': 'test_integration_dealer.com',
                'Audi Ranch Mirage': 'audiranchomirage.com',
                'Auffenberg Hyundai': 'auffenberghyundai.com',
                'BMW of West St. Louis': 'bmwofweststlouis.com',
                'Bommarito Cadillac': 'bommaritocadillac.com',
                'Bommarito West County': 'bommaritowestcounty.com',
                'Columbia BMW': 'columbiabmw.com',
                'Columbia Honda': 'columbiahonda.com',
                'Dave Sinclair Lincoln South': 'davesinclairlincolnsouth.com',
                'Dave Sinclair Lincoln St. Peters': 'davesinclairlincolnstpeters.com',
                'Frank Leta Honda': 'frankletahonda.com',
                'Glendale Chrysler Jeep': 'glendalechryslerjeep.net',
                'Honda of Frontenac': 'hondafrontenac.com',
                'H&W Kia': 'hwkia.com',
                'Indigo Auto Group': 'indigoautogroup.com',
                'Jaguar Ranch Mirage': 'jaguarranchomirage.com',
                'Joe Machens CDJR': 'joemachenscdjr.com',
                'Joe Machens Hyundai': 'joemachenshyundai.com',
                'Joe Machens Nissan': 'joemachensnissan.com',
                'Joe Machens Toyota': 'joemachenstoyota.com',
                'Kia of Columbia': 'kiaofcolumbia.com',
                'Land Rover Ranch Mirage': 'landroverranchomirage.com',
                'Mini of St. Louis': 'miniofstlouis.com',
                'Pappas Toyota': 'pappastoyota.com',
                'Porsche St. Louis': 'porschestlouis.com',
                'Pundmann Ford': 'pundmannford.com',
                'Rusty Drewing Cadillac': 'rustydrewingcadillac.com',
                'Rusty Drewing Chevrolet Buick GMC': 'rustydrewingchevroletbuickgmc.com',
                "Serra Honda O'Fallon": 'serrahondaofallon.com',
                'South County Autos': 'southcountyautos.com',
                'Spirit Lexus': 'spiritlexus.com',
                'Stehouwer Auto': 'stehouwerauto.com',
                'Suntrup Buick GMC': 'suntrupbuickgmc.com',
                'Suntrup Ford Kirkwood': 'suntrupfordkirkwood.com',
                'Suntrup Ford West': 'suntrupfordwest.com',
                'Suntrup Hyundai South': 'suntruphyundaisouth.com',
                'Suntrup Kia South': 'suntrupkiasouth.com',
                'Thoroughbred Ford': 'thoroughbredford.com',
                'Twin City Toyota': 'twincitytoyota.com',
                'West County Volvo Cars': 'wcvolvocars.com',
                'Weber Chevrolet': 'weberchev.com'
            }
            
            site_name = display_to_site_mapping.get(dealership_name)
            if not site_name:
                self.logger.warning(f"No site mapping available for {dealership_name}")
                result = {'success': False, 'error': 'No site mapping available', 'vehicles': []}
                self.progress_reporter.complete_scraper(dealership_name, result)
                return result
            
            # Create progress callback for enhanced controller
            def progress_callback(message):
                self.progress_reporter.update_scraper_progress(dealership_name, f"[ENHANCED] {message}")
            
            # Initialize enhanced controller
            controller = EnhancedScraperController(progress_callback)
            
            # Pass the progress reporter to the controller for real-time updates
            controller.current_progress_reporter = self.progress_reporter
            
            # Run the scraper using the bulletproof controller
            self.progress_reporter.update_scraper_progress(dealership_name, "[ENHANCED] Starting bulletproof scraper...")
            
            start_time = datetime.now()
            scraper_result = controller.run_single_scraper(site_name, force_run=True)
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            
            if scraper_result['success']:
                # Enhanced controller succeeded - convert to expected format
                result = {
                    'success': True,
                    'dealership_name': dealership_name,
                    'vehicle_count': 0,  # Will be updated after parsing CSV
                    'duration_seconds': duration,
                    'data_source': 'enhanced_scraper_controller_real_data',
                    'is_real_data': True,
                    'vehicles': [],  # Will be populated from CSV output
                    'scraper_class': 'EnhancedScraperController',
                    'scraped_at': datetime.now().isoformat(),
                    'controller_result': scraper_result
                }
                
                self.logger.info(f"Enhanced scraper completed for {dealership_name} in {duration:.1f}s")
                self.progress_reporter.update_scraper_progress(dealership_name, "[SUCCESS] Enhanced scraper completed!")
                
            else:
                # Enhanced controller failed - return error
                result = {
                    'success': False,
                    'error': scraper_result.get('error', 'Enhanced controller failed'),
                    'dealership_name': dealership_name,
                    'vehicles': [],
                    'controller_result': scraper_result
                }
                
                self.logger.error(f"Enhanced scraper failed for {dealership_name}: {result['error']}")
            
            # Complete progress reporting
            self.progress_reporter.complete_scraper(dealership_name, result)
            return result
            
        except Exception as e:
            self.logger.error(f"Error in enhanced scraper integration for {dealership_name}: {e}")
            result = {
                'success': False, 
                'error': f"Enhanced scraper integration error: {str(e)}", 
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