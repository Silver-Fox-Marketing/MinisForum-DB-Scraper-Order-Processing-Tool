#!/usr/bin/env python3
"""
Scraper 18 Web Integration Controller
=====================================

Integrates the proven scraper 18 system directly into our web GUI.
Replaces the config.csv file with web GUI dealership selection and
provides real-time progress updates to the interface.

Author: Silver Fox Assistant
Created: 2025-08-01
Based on: vehicle_scraper 18/main.py (proven working system)
"""

import os
import sys
import json
import logging
import datetime
import threading
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add scraper18_integration to path
current_dir = Path(__file__).parent
scraper18_dir = current_dir / 'scraper18_integration'
sys.path.insert(0, str(scraper18_dir))
sys.path.insert(0, str(scraper18_dir / 'scrapers'))

# Import ALL scraper 18 modules exactly as the original main.py does
try:
    from scrapers.joemachensnissan import *
    from scrapers.joemachenscdjr import *
    from scrapers.joemachenshyundai import *
    from scrapers.kiaofcolumbia import *
    from scrapers.porschestlouis import *
    from scrapers.auffenberghyundai import *
    from scrapers.hondafrontenac import *
    from scrapers.bommaritocadillac import *
    from scrapers.pappastoyota import *
    from scrapers.serrahondaofallon import *
    from scrapers.southcountyautos import *
    from scrapers.glendalechryslerjeep import *
    from scrapers.davesinclairlincolnsouth import *
    from scrapers.suntrupkiasouth import *
    from scrapers.columbiabmw import *
    from scrapers.rustydrewingcadillac import *
    from scrapers.rustydrewingchevroletbuickgmc import *
    from scrapers.pundmannford import *
    from scrapers.bmwofweststlouis import *
    from scrapers.bommaritowestcounty import *
    from scrapers.hwkia import *
    from scrapers.wcvolvocars import *
    from scrapers.joemachenstoyota import *
    from scrapers.suntruphyundaisouth import *
    from scrapers.landroverranchomirage import *
    from scrapers.miniofstlouis import *
    from scrapers.suntrupfordkirkwood import *
    from scrapers.thoroughbredford import *
    from scrapers.spiritlexus import *
    from scrapers.frankletahonda import *
    from scrapers.columbiahonda import *
    from scrapers.davesinclairlincolnstpeters import *
    from scrapers.weberchev import *
    from scrapers.suntrupbuickgmc import *
    from scrapers.suntrupfordwest import *

    from scrapers.helper_class import *
    
    # Import database system for direct integration
    sys.path.insert(0, str(current_dir.parent / 'scripts'))
    from csv_importer_complete import CompleteCSVImporter
    
    print("OK All scraper 18 modules imported successfully")
    
except Exception as e:
    print(f"ERROR importing scraper 18 modules: {e}")
    print("WARNING: This will prevent scraper execution")

class Scraper18WebController:
    """
    Controller that integrates scraper 18 system with web GUI
    Preserves ALL original scraper logic while adding web integration
    """
    
    def __init__(self, socketio=None):
        """Initialize the scraper 18 web controller"""
        self.socketio = socketio
        self.logger = logging.getLogger(__name__)
        
        # Initialize helper exactly like scraper 18
        self.helper = Helper()
        
        # Initialize CSV importer for database integration
        try:
            self.csv_importer = CompleteCSVImporter()
            self.database_integration_enabled = True
            self.logger.info("Database integration enabled")
        except Exception as e:
            self.logger.warning(f"Database integration disabled: {e}")
            self.csv_importer = None
            self.database_integration_enabled = False
        
        # Set up paths relative to scraper18_integration directory
        self.scraper18_dir = scraper18_dir
        
        # Dealership display name to site name mapping (36 Active Scrapers)
        self.display_to_site_mapping = {
            'Auffenberg Hyundai': 'auffenberghyundai.com',
            'BMW of West St. Louis': 'bmwofweststlouis.com',
            'Bommarito Cadillac': 'bommaritocadillac.com',
            'Bommarito West County': 'bommaritowestcounty.com',
            'Columbia BMW': 'columbiabmw.com',
            'Columbia Honda': 'columbiahonda.com',
            'Dave Sinclair Lincoln': 'davesinclairlincolnsouth.com',  # Using South location as primary
            'Dave Sinclair Lincoln South': 'davesinclairlincolnsouth.com',
            'Dave Sinclair Lincoln St. Peters': 'davesinclairlincolnstpeters.com',
            'Frank Leta Honda': 'frankletahonda.com',
            'Glendale Chrysler Jeep': 'glendalechryslerjeep.net',
            'HW Kia': 'hwkia.com',
            'Honda of Frontenac': 'hondafrontenac.com',
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
            'Serra Honda O\'Fallon': 'serrahondaofallon.com',
            'South County Autos': 'southcountyautos.com',
            'Spirit Lexus': 'spiritlexus.com',
            'Suntrup Buick GMC': 'suntrupbuickgmc.com',
            'Suntrup Ford Kirkwood': 'suntrupfordkirkwood.com',
            'Suntrup Ford West': 'suntrupfordwest.com',
            'Suntrup Hyundai South': 'suntruphyundaisouth.com',
            'Suntrup Kia South': 'suntrupkiasouth.com',
            'Thoroughbred Ford': 'thoroughbredford.com',
            'Weber Chevrolet': 'weberchev.com',
            'West County Volvo Cars': 'wcvolvocars.com'
        }
        
        self.logger.info(f"Scraper18WebController initialized with {len(self.display_to_site_mapping)} dealerships")
    
    def setup_output_directories(self, dealership_name: str = None):
        """Set up output directories with separate CSV files per dealership"""
        try:
            # Change to scraper18_integration directory for proper relative paths
            original_cwd = os.getcwd()
            os.chdir(self.scraper18_dir)
            
            # Set up directories exactly like original main.py
            data_folder = self.helper.checking_folder_existence('./output_data/')
            date_str = str(datetime.datetime.now()).split()[0]
            data_folder = self.helper.checking_folder_existence(f'{data_folder}{date_str}/')
            log_folder = self.helper.checking_folder_existence(f'{data_folder}/log/')
            
            # Use separate CSV file per dealership to avoid cross-contamination
            if dealership_name:
                safe_dealership_name = dealership_name.replace(' ', '_').replace('.', '').replace('&', 'and')
                output_file = f'{data_folder}complete_data_{safe_dealership_name}.csv'
            else:
                output_file = f'{data_folder}complete_data.csv'
            sites_processed_file = f'{log_folder}sites_processed.json'
            
            # Return to original directory
            os.chdir(original_cwd)
            
            return {
                'data_folder': data_folder,
                'log_folder': log_folder, 
                'output_file': output_file,
                'sites_processed_file': sites_processed_file
            }
            
        except Exception as e:
            self.logger.error(f"Error setting up output directories: {e}")
            raise
    
    def get_sites_processed_data(self, sites_processed_file):
        """Get sites processed data exactly like scraper 18"""
        try:
            original_cwd = os.getcwd()
            os.chdir(self.scraper18_dir)
            
            sites_processed_data = self.helper.json_exist_data(sites_processed_file)
            
            os.chdir(original_cwd)
            return sites_processed_data
            
        except Exception as e:
            self.logger.error(f"Error getting sites processed data: {e}")
            return []
    
    def update_sites_processed_data(self, sites_processed_data, sites_processed_file, site_name):
        """Update sites processed data exactly like scraper 18"""
        try:
            original_cwd = os.getcwd()
            os.chdir(self.scraper18_dir)
            
            sites_processed_data.append(site_name)
            self.helper.write_json_file(sites_processed_data, sites_processed_file)
            
            os.chdir(original_cwd)
            return sites_processed_data
            
        except Exception as e:
            self.logger.error(f"Error updating sites processed data: {e}")
            return sites_processed_data
    
    def emit_progress(self, message, dealership_name, progress_type='info'):
        """Emit progress update to web interface"""
        if self.socketio:
            self.socketio.emit('scraper_output', {
                'message': message,
                'dealership': dealership_name,
                'timestamp': datetime.datetime.now().strftime('%H:%M:%S'),
                'type': progress_type
            })
    
    def _add_dealer_name_to_csv(self, csv_file_path: str, dealer_name: str):
        """Add dealer_name column to CSV file (safe since each CSV is per-dealership)"""
        import pandas as pd
        
        try:
            # Read the CSV file
            df = pd.read_csv(csv_file_path, dtype=str, keep_default_na=False)
            
            # Add dealer_name column - safe since this CSV only contains this dealership's data
            df['dealer_name'] = dealer_name
            
            # Save the modified CSV back to file
            df.to_csv(csv_file_path, index=False)
            self.logger.info(f"Added dealer_name '{dealer_name}' to dedicated CSV: {csv_file_path}")
                
        except Exception as e:
            self.logger.error(f"Error adding dealer_name to CSV {csv_file_path}: {e}")
            raise
    
    def run_single_scraper(self, dealership_name: str, force_run: bool = False) -> Dict[str, Any]:
        """
        Run a single scraper using the exact scraper 18 logic
        This preserves ALL original functionality while adding web integration
        """
        result = {
            'dealership_name': dealership_name,
            'success': False,
            'error': None,
            'start_time': datetime.datetime.now(),
            'end_time': None,
            'vehicles_processed': 0,
            'duration_seconds': 0
        }
        
        try:
            # Convert display name to site name
            site_name = self.display_to_site_mapping.get(dealership_name)
            if not site_name:
                result['error'] = f"Unknown dealership: {dealership_name}"
                return result
            
            self.emit_progress(f"🚀 STARTING: {dealership_name}", dealership_name, 'start')
            
            # Set up directories with separate CSV per dealership
            paths = self.setup_output_directories(dealership_name)
            data_folder = paths['data_folder']
            output_file = paths['output_file']
            sites_processed_file = paths['sites_processed_file']
            
            # Get processed sites data exactly like scraper 18
            sites_processed_data = self.get_sites_processed_data(sites_processed_file)
            
            # Check if already processed (unless force_run)
            if not force_run and site_name in sites_processed_data:
                result['error'] = "Site already processed (use force_run to override)"
                self.emit_progress(f"⏭️  SKIPPED: {dealership_name} - Already processed", dealership_name, 'skip')
                return result
            
            self.emit_progress(f"🔧 INITIALIZING: {dealership_name} scraper", dealership_name, 'init')
            
            # Change to scraper18_integration directory for proper execution
            original_cwd = os.getcwd()
            os.chdir(self.scraper18_dir)
            
            try:
                # Execute scraper using EXACT logic from scraper 18 main.py
                self.emit_progress(f"EXECUTING: {dealership_name} scraper logic", dealership_name, 'execute')
                
                # Enhanced error handling: wrap each scraper execution individually
                scraper_executed = False
                scraper_error = None
                
                try:
                    if site_name == 'joemachensnissan.com':
                        JOEMACHENSNISSAN(data_folder, output_file).start_scraping_joemachensnissan()
                    elif site_name == 'joemachenscdjr.com':
                        JOEMACHENSCDJR(data_folder, output_file).start_scraping_joemachenscdjr()
                    elif site_name == 'joemachenshyundai.com':
                        JOEMACHENSHYUNDAI(data_folder, output_file).start_scraping_joemachenshyundai()
                    elif site_name == 'kiaofcolumbia.com':
                        KIAOFCOLUMBIA(data_folder, output_file).start_scraping_kiaofcolumbia()
                    elif site_name == 'porschestlouis.com':
                        PORSCHESTLOUIS(data_folder, output_file).start_scraping_porschestlouis()
                    elif site_name == 'auffenberghyundai.com':
                        AUFFENBERGHYUNDAI(data_folder, output_file).start_scraping_auffenberghyundai()
                    elif site_name == 'hondafrontenac.com':
                        HONDAFRONTENAC(data_folder, output_file).start_scraping_hondafrontenac()
                    elif site_name == 'bommaritocadillac.com':
                        BOMMARITOCADILLAC(data_folder, output_file).start_scraping_bommaritocadillac()
                    elif site_name == 'pappastoyota.com':
                        PAPPASTOYOTA(data_folder, output_file).start_scraping_pappastoyota()
                    elif site_name == 'serrahondaofallon.com':
                        SERRAHONDAOFALLON(data_folder, output_file).start_scraping_serrahondaofallon()
                    elif site_name == 'southcountyautos.com':
                        SOUTHCOUNTYAUTOS(data_folder, output_file).start_scraping_southcountyautos()
                    elif site_name == 'glendalechryslerjeep.net':
                        GLENDALECHRYSLERJEEP(data_folder, output_file).start_scraping_glendalechryslerjeep()
                    elif site_name == 'davesinclairlincolnsouth.com':
                        DAVESINCLAIRLINCOLNSOUTH(data_folder, output_file).start_scraping_davesinclairlincolnsouth()
                    elif site_name == 'suntrupkiasouth.com':
                        SUNTRUPKIASOUTH(data_folder, output_file).start_scraping_suntrupkiasouth()
                    elif site_name == 'columbiabmw.com':
                        COLUMBIABMW(data_folder, output_file).start_scraping_columbiabmw()
                    elif site_name == 'rustydrewingcadillac.com':
                        RUSTYDREWINGCADILLAC(data_folder, output_file).start_scraping_rustydrewingcadillac()
                    elif site_name == 'rustydrewingchevroletbuickgmc.com':
                        RUSTYDREWINGCHEVROLETBUICKGMC(data_folder, output_file).start_scraping_rustydrewingchevroletbuickgmc()
                    elif site_name == 'pundmannford.com':
                        PUNDMANNFORD(data_folder, output_file).start_scraping_pundmannford()
                    elif site_name == 'bmwofweststlouis.com':
                        BMWOFWESTSTLOUIS(data_folder, output_file).start_scraping_bmwofweststlouis()
                    elif site_name == 'bommaritowestcounty.com':
                        BOMMARITOWESTCOUNTY(data_folder, output_file).start_scraping_bommaritowestcounty()
                    elif site_name == 'hwkia.com':
                        HWKIA(data_folder, output_file).start_scraping_hwkia()
                    elif site_name == 'wcvolvocars.com':
                        WCVOLVOCARS(data_folder, output_file).start_scraping_wcvolvocars()
                    elif site_name == 'joemachenstoyota.com':
                        JOEMACHENSTOYOTA(data_folder, output_file).start_scraping_joemachenstoyota()
                    elif site_name == 'suntruphyundaisouth.com':
                        SUNTRUPHYUNDAISOUTH(data_folder, output_file).start_scraping_suntruphyundaisouth()
                    elif site_name == 'landroverranchomirage.com':
                        LANDROVERRANCHOMIRAGE(data_folder, output_file).start_scraping_landroverranchomirage()
                    elif site_name == 'miniofstlouis.com':
                        MINIOFSTLOUIS(data_folder, output_file).start_scraping_miniofstlouis()
                    elif site_name == 'suntrupfordkirkwood.com':
                        SUNTRUPFORDKIRKWOOD(data_folder, output_file).start_scraping_suntrupfordkirkwood()
                    elif site_name == 'thoroughbredford.com':
                        THOROUGHBREDFORD(data_folder, output_file).start_scraping_thoroughbredford()
                    elif site_name == 'spiritlexus.com':
                        SPIRITLEXUS(data_folder, output_file).start_scraping_spiritlexus()
                    elif site_name == 'frankletahonda.com':
                        FRANKLETAHONDA(data_folder, output_file).start_scraping_frankletahonda()
                    elif site_name == 'columbiahonda.com':
                        COLUMBIAHONDA(data_folder, output_file).start_scraping_columbiahonda()
                    elif site_name == 'davesinclairlincolnstpeters.com':
                        DAVESINCLAIRLINCOLNSTPETERS(data_folder, output_file).start_scraping_davesinclairlincolnstpeters()
                    elif site_name == 'weberchev.com':
                        WEBERCHEV(data_folder, output_file).start_scraping_weberchev()
                    elif site_name == 'suntrupbuickgmc.com':
                        SUNTRUPBUICKGMC(data_folder, output_file).start_scraping_suntrupbuickgmc()
                    elif site_name == 'suntrupfordwest.com':
                        SUNTRUPFORDWEST(data_folder, output_file).start_scraping_suntrupfordwest()
                    else:
                        raise ValueError(f"Unknown site_name: {site_name}")
                    
                    # If we reach here, scraper executed successfully
                    scraper_executed = True
                    
                except Exception as scraper_e:
                    # Individual scraper failed - log but don't crash entire system
                    scraper_error = str(scraper_e)
                    self.emit_progress(f"SCRAPER ERROR: {dealership_name} failed - {scraper_error}", dealership_name, 'scraper_error')
                    self.logger.error(f"Individual scraper error for {dealership_name}: {scraper_e}", exc_info=True)
                    scraper_executed = False
                
                # Continue processing even if scraper failed
                if scraper_executed:
                    # Update processed sites exactly like scraper 18
                    sites_processed_data = self.update_sites_processed_data(sites_processed_data, sites_processed_file, site_name)
                    
                    self.emit_progress(f"SUCCESS: {dealership_name} scraping completed!", dealership_name, 'success')
                    
                    # Import scraped data directly into database
                    if self.database_integration_enabled:
                        try:
                            self.emit_progress(f"📊 IMPORTING: {dealership_name} data into database", dealership_name, 'import')
                            
                            # Add dealer_name column to CSV before importing
                            self._add_dealer_name_to_csv(output_file, dealership_name)
                            
                            # Import the CSV data from the output file
                            import_result = self.csv_importer.import_complete_csv(output_file)
                            
                            # Check if import was successful
                            vehicles_imported = import_result.get('imported_rows', 0)
                            if vehicles_imported > 0:
                                result['vehicles_processed'] = vehicles_imported
                                self.emit_progress(f"DATABASE: {dealership_name} - {vehicles_imported} vehicles imported", dealership_name, 'import_success')
                                self.logger.info(f"Successfully imported {vehicles_imported} vehicles from {dealership_name}")
                            else:
                                # Get first few validation errors for debugging
                                validation_errors = import_result.get('errors', [])[:3]  # First 3 errors
                                error_msg = f"No vehicles imported. Total rows: {import_result.get('total_rows', 0)}, Skipped: {import_result.get('skipped_rows', 0)}"
                                if validation_errors:
                                    error_msg += f" Sample errors: {validation_errors}"
                                self.emit_progress(f"DATABASE ERROR: {dealership_name} import failed - {error_msg}", dealership_name, 'import_error')
                                self.logger.error(f"Database import failed for {dealership_name}: {error_msg}")
                                
                        except Exception as import_e:
                            self.emit_progress(f"DATABASE ERROR: {dealership_name} import error - {str(import_e)}", dealership_name, 'import_error')
                            self.logger.error(f"Database import exception for {dealership_name}: {import_e}")
                    else:
                        self.emit_progress(f"DATABASE WARNING: Integration disabled - CSV saved to {output_file}", dealership_name, 'warning')
                    
                    # Success!
                    result['success'] = True
                else:
                    # Scraper failed, but system continues
                    result['success'] = False
                    result['error'] = f"Scraper execution failed: {scraper_error}"
                    self.emit_progress(f"FAILED: {dealership_name} scraper failed but system continues", dealership_name, 'failed')
                
            finally:
                # Always return to original directory
                os.chdir(original_cwd)
                
        except Exception as e:
            result['error'] = str(e)
            self.emit_progress(f"ERROR: {dealership_name} failed - {str(e)}", dealership_name, 'error')
            self.logger.error(f"Error running scraper for {dealership_name}: {e}")
            
        finally:
            result['end_time'] = datetime.datetime.now()
            result['duration_seconds'] = (result['end_time'] - result['start_time']).total_seconds()
        
        return result
    
    def run_multiple_scrapers(self, dealership_names: List[str], force_run: bool = False) -> Dict[str, Any]:
        """Run multiple scrapers in sequence"""
        session_result = {
            'start_time': datetime.datetime.now(),
            'total_scrapers': len(dealership_names),
            'successful_scrapers': 0,
            'failed_scrapers': 0,
            'results': {},
            'errors': []
        }
        
        # Emit session start
        if self.socketio:
            self.socketio.emit('scraper_session_start', {
                'total_scrapers': len(dealership_names),
                'scrapers': dealership_names
            })
        
        for index, dealership_name in enumerate(dealership_names):
            try:
                print(f"{index + 1} / {len(dealership_names)} : {dealership_name} : starting")
                
                # Emit individual scraper start
                if self.socketio:
                    self.socketio.emit('scraper_start', {
                        'scraper_name': dealership_name,
                        'progress': index + 1,
                        'total': len(dealership_names)
                    })
                
                # Run the scraper with system-level error handling
                try:
                    result = self.run_single_scraper(dealership_name, force_run)
                    session_result['results'][dealership_name] = result
                except Exception as system_e:
                    # System-level error - create error result and continue
                    result = {
                        'dealership_name': dealership_name,
                        'success': False,
                        'error': f"System error: {str(system_e)}",
                        'start_time': datetime.datetime.now(),
                        'end_time': datetime.datetime.now(),
                        'vehicles_processed': 0,
                        'duration_seconds': 0
                    }
                    session_result['results'][dealership_name] = result
                    self.logger.error(f"System-level error for {dealership_name}: {system_e}", exc_info=True)
                
                if result['success']:
                    session_result['successful_scrapers'] += 1
                    
                    # Emit scraper completion
                    if self.socketio:
                        self.socketio.emit('scraper_complete', {
                            'scraper_name': dealership_name,
                            'success': True,
                            'vehicles_processed': result['vehicles_processed'],
                            'duration': result['duration_seconds']
                        })
                else:
                    session_result['failed_scrapers'] += 1
                    session_result['errors'].append(f"{dealership_name}: {result['error']}")
                    
                    # Emit scraper failure
                    if self.socketio:
                        self.socketio.emit('scraper_complete', {
                            'scraper_name': dealership_name,
                            'success': False,
                            'error': result['error'],
                            'duration': result['duration_seconds']
                        })
                
                print('-' * 50)
                print()
                
            except Exception as e:
                session_result['failed_scrapers'] += 1
                session_result['errors'].append(f"{dealership_name}: System error - {str(e)}")
                self.logger.error(f"System error running {dealership_name}: {e}")
        
        # Complete session
        session_result['end_time'] = datetime.datetime.now()
        session_result['total_duration'] = (session_result['end_time'] - session_result['start_time']).total_seconds()
        session_result['success_rate'] = (session_result['successful_scrapers'] / session_result['total_scrapers']) * 100
        
        # Emit session completion
        if self.socketio:
            self.socketio.emit('scraper_session_complete', {
                'total_scrapers': session_result['total_scrapers'],
                'successful_scrapers': session_result['successful_scrapers'], 
                'failed_scrapers': session_result['failed_scrapers'],
                'success_rate': session_result['success_rate'],
                'duration': session_result['total_duration']
            })
        
        return session_result
    
    def get_available_dealerships(self) -> List[str]:
        """Get list of available dealerships"""
        return list(self.display_to_site_mapping.keys())

# Create global instance for web integration
scraper18_controller = Scraper18WebController()

def test_scraper18_controller():
    """Test the scraper18 controller"""
    print("Testing Scraper18WebController...")
    
    available = scraper18_controller.get_available_dealerships()
    print(f"Available dealerships: {len(available)}")
    print(f"First 5: {available[:5]}")
    
    # Test single scraper
    # result = scraper18_controller.run_single_scraper('Columbia Honda', force_run=True)
    # print(f"Test result: {result}")

if __name__ == "__main__":
    test_scraper18_controller()