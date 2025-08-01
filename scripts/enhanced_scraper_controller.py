#!/usr/bin/env python3
"""
Enhanced Scraper Controller for Bulletproof Package
==================================================

Based on the proven scraper 18 main.py controller, this enhanced version:
- Preserves ALL original scraper logic exactly as it works
- Adds robust error handling so one scraper failure doesn't crash the system
- Integrates with bulletproof package database system
- Provides progress reporting and detailed logging
- Supports both individual and batch scraper execution

Author: Silver Fox Assistant 
Created: 2025-08-01
Based on: vehicle_scraper 18/main.py (proven working system)
"""

import os
import sys
import json
import logging
import traceback
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import time

# Add scrapers directory to path
current_dir = Path(__file__).parent
scrapers_dir = current_dir.parent / "scrapers"
sys.path.insert(0, str(scrapers_dir))

# Import all scrapers exactly as scraper 18 does - preserving original logic
try:
    from joemachensnissan import *
    from joemachenscdjr import *
    from joemachenshyundai import *
    from kiaofcolumbia import *
    from porschestlouis import *
    from auffenberghyundai import *
    from hondafrontenac import *
    from bommaritocadillac import *
    from pappastoyota import *
    from twincitytoyota import *
    from serrahondaofallon import *
    from southcountyautos import *
    from glendalechryslerjeep import *
    from davesinclairlincolnsouth import *
    from suntrupkiasouth import *
    from columbiabmw import *
    from rustydrewingcadillac import *
    from rustydrewingchevroletbuickgmc import *
    from pundmannford import *
    from stehouwerauto import *
    from bmwofweststlouis import *
    from bommaritowestcounty import *
    from hwkia import *
    from wcvolvocars import *
    from joemachenstoyota import *
    from suntruphyundaisouth import *
    from landroverranchomirage import *
    from jaguarranchomirage import *
    from indigoautogroup import *
    from miniofstlouis import *
    from suntrupfordkirkwood import *
    from thoroughbredford import *
    from spiritlexus import *
    from frankletahonda import *
    from columbiahonda import *
    from davesinclairlincolnstpeters import *
    from weberchev import *
    from suntrupbuickgmc import *
    from suntrupfordwest import *
    # Add missing scrapers from the 40
    from audiranchomirage import *
    
    from enhanced_helper_class import EnhancedHelper
    from scraper_output_monitor import monitor_scraper_execution
    
    print("OK All scraper modules imported successfully")
    
except Exception as e:
    print(f"ERROR importing scraper modules: {e}")
    print("INFO: Available scrapers will be limited to successfully imported ones")

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dealership_db',
    'user': 'postgres',
    'password': os.environ.get('DEALERSHIP_DB_PASSWORD', ''),
    'port': 5432
}

class EnhancedScraperController:
    """
    Enhanced scraper controller based on scraper 18 proven logic
    Adds error handling and bulletproof package integration
    """
    
    def __init__(self, progress_callback=None):
        """Initialize the enhanced scraper controller"""
        self.progress_callback = progress_callback
        self.helper = EnhancedHelper(DB_CONFIG)
        
        # Setup logging
        self.setup_logging()
        
        # Create output directories
        self.setup_directories()
        
        # Define scraper mapping - EXACTLY as scraper 18 works
        self.scraper_mapping = {
            'joemachensnissan.com': {
                'class': 'JOEMACHENSNISSAN',
                'method': 'start_scraping_joemachensnissan',
                'display_name': 'Joe Machens Nissan'
            },
            'joemachenscdjr.com': {
                'class': 'JOEMACHENSCDJR', 
                'method': 'start_scraping_joemachenscdjr',
                'display_name': 'Joe Machens CDJR'
            },
            'joemachenshyundai.com': {
                'class': 'JOEMACHENSHYUNDAI',
                'method': 'start_scraping_joemachenshyundai', 
                'display_name': 'Joe Machens Hyundai'
            },
            'kiaofcolumbia.com': {
                'class': 'KIAOFCOLUMBIA',
                'method': 'start_scraping_kiaofcolumbia',
                'display_name': 'Kia of Columbia'
            },
            'porschestlouis.com': {
                'class': 'PORSCHESTLOUIS',
                'method': 'start_scraping_porschestlouis',
                'display_name': 'Porsche St. Louis'
            },
            'auffenberghyundai.com': {
                'class': 'AUFFENBERGHYUNDAI',
                'method': 'start_scraping_auffenberghyundai',
                'display_name': 'Auffenberg Hyundai'
            },
            'hondafrontenac.com': {
                'class': 'HONDAFRONTENAC',
                'method': 'start_scraping_hondafrontenac',
                'display_name': 'Honda of Frontenac'
            },
            'bommaritocadillac.com': {
                'class': 'BOMMARITOCADILLAC',
                'method': 'start_scraping_bommaritocadillac',
                'display_name': 'Bommarito Cadillac'
            },
            'pappastoyota.com': {
                'class': 'PAPPASTOYOTA',
                'method': 'start_scraping_pappastoyota',
                'display_name': 'Pappas Toyota'
            },
            'twincitytoyota.com': {
                'class': 'TWINCITYTOYOTA',
                'method': 'start_scraping_twincitytoyota',
                'display_name': 'Twin City Toyota'
            },
            'serrahondaofallon.com': {
                'class': 'SERRAHONDAOFALLON',
                'method': 'start_scraping_serrahondaofallon',
                'display_name': "Serra Honda O'Fallon"
            },
            'southcountyautos.com': {
                'class': 'SOUTHCOUNTYAUTOS',
                'method': 'start_scraping_southcountyautos',
                'display_name': 'South County Autos'
            },
            'glendalechryslerjeep.net': {
                'class': 'GLENDALECHRYSLERJEEP',
                'method': 'start_scraping_glendalechryslerjeep',
                'display_name': 'Glendale Chrysler Jeep'
            },
            'davesinclairlincolnsouth.com': {
                'class': 'DAVESINCLAIRLINCOLNSOUTH',
                'method': 'start_scraping_davesinclairlincolnsouth',
                'display_name': 'Dave Sinclair Lincoln South'
            },
            'suntrupkiasouth.com': {
                'class': 'SUNTRUPKIASOUTH',
                'method': 'start_scraping_suntrupkiasouth',
                'display_name': 'Suntrup Kia South'
            },
            'columbiabmw.com': {
                'class': 'COLUMBIABMW',
                'method': 'start_scraping_columbiabmw',
                'display_name': 'Columbia BMW'
            },
            'rustydrewingcadillac.com': {
                'class': 'RUSTYDREWINGCADILLAC',
                'method': 'start_scraping_rustydrewingcadillac',
                'display_name': 'Rusty Drewing Cadillac'
            },
            'rustydrewingchevroletbuickgmc.com': {
                'class': 'RUSTYDREWINGCHEVROLETBUICKGMC',
                'method': 'start_scraping_rustydrewingchevroletbuickgmc',
                'display_name': 'Rusty Drewing Chevrolet Buick GMC'
            },
            'pundmannford.com': {
                'class': 'PUNDMANNFORD',
                'method': 'start_scraping_pundmannford',
                'display_name': 'Pundmann Ford'
            },
            'stehouwerauto.com': {
                'class': 'STEHOUWERAUTO',
                'method': 'start_scraping_stehouwerauto',
                'display_name': 'Stehouwer Auto'
            },
            'bmwofweststlouis.com': {
                'class': 'BMWOFWESTSTLOUIS',
                'method': 'start_scraping_bmwofweststlouis',
                'display_name': 'BMW of West St. Louis'
            },
            'bommaritowestcounty.com': {
                'class': 'BOMMARITOWESTCOUNTY',
                'method': 'start_scraping_bommaritowestcounty',
                'display_name': 'Bommarito West County'
            },
            'hwkia.com': {
                'class': 'HWKIA',
                'method': 'start_scraping_hwkia',
                'display_name': 'H&W Kia'
            },
            'wcvolvocars.com': {
                'class': 'WCVOLVOCARS',
                'method': 'start_scraping_wcvolvocars',
                'display_name': 'West County Volvo Cars'
            },
            'joemachenstoyota.com': {
                'class': 'JOEMACHENSTOYOTA',
                'method': 'start_scraping_joemachenstoyota',
                'display_name': 'Joe Machens Toyota'
            },
            'suntruphyundaisouth.com': {
                'class': 'SUNTRUPHYUNDAISOUTH',
                'method': 'start_scraping_suntruphyundaisouth',
                'display_name': 'Suntrup Hyundai South'
            },
            'landroverranchomirage.com': {
                'class': 'LANDROVERRANCHOMIRAGE',
                'method': 'start_scraping_landroverranchomirage',
                'display_name': 'Land Rover Ranch Mirage'
            },
            'jaguarranchomirage.com': {
                'class': 'JAGUARRANCHOMIRAGE',
                'method': 'start_scraping_jaguarranchomirage',
                'display_name': 'Jaguar Ranch Mirage'
            },
            'indigoautogroup.com': {
                'class': 'INDIGOAUTOGROUP',
                'method': 'start_scraping_indigoautogroup',
                'display_name': 'Indigo Auto Group'
            },
            'miniofstlouis.com': {
                'class': 'MINIOFSTLOUIS',
                'method': 'start_scraping_miniofstlouis',
                'display_name': 'Mini of St. Louis'
            },
            'suntrupfordkirkwood.com': {
                'class': 'SUNTRUPFORDKIRKWOOD',
                'method': 'start_scraping_suntrupfordkirkwood',
                'display_name': 'Suntrup Ford Kirkwood'
            },
            'thoroughbredford.com': {
                'class': 'THOROUGHBREDFORD',
                'method': 'start_scraping_thoroughbredford',
                'display_name': 'Thoroughbred Ford'
            },
            'spiritlexus.com': {
                'class': 'SPIRITLEXUS',
                'method': 'start_scraping_spiritlexus',
                'display_name': 'Spirit Lexus'
            },
            'frankletahonda.com': {
                'class': 'FRANKLETAHONDA',
                'method': 'start_scraping_frankletahonda',
                'display_name': 'Frank Leta Honda'
            },
            'columbiahonda.com': {
                'class': 'COLUMBIAHONDA',
                'method': 'start_scraping_columbiahonda',
                'display_name': 'Columbia Honda'
            },
            'davesinclairlincolnstpeters.com': {
                'class': 'DAVESINCLAIRLINCOLNSTPETERS',
                'method': 'start_scraping_davesinclairlincolnstpeters',
                'display_name': 'Dave Sinclair Lincoln St. Peters'
            },
            'weberchev.com': {
                'class': 'WEBERCHEV',
                'method': 'start_scraping_weberchev',
                'display_name': 'Weber Chevrolet'
            },
            'suntrupbuickgmc.com': {
                'class': 'SUNTRUPBUICKGMC',
                'method': 'start_scraping_suntrupbuickgmc',
                'display_name': 'Suntrup Buick GMC'
            },
            'suntrupfordwest.com': {
                'class': 'SUNTRUPFORDWEST',
                'method': 'start_scraping_suntrupfordwest',
                'display_name': 'Suntrup Ford West'
            },
            'audiranchomirage.com': {
                'class': 'AUDIRANCHOMIRAGE',
                'method': 'start_scraping_audiranchomirage',
                'display_name': 'Audi Ranch Mirage'
            }
        }
        
        # Initialize processed sites tracking
        self.sites_processed_file = self.log_folder / 'sites_processed.json'
        self.sites_processed_data = self.load_processed_sites()
        
        self.logger.info(f"Enhanced Scraper Controller initialized with {len(self.scraper_mapping)} scrapers")
    
    def setup_logging(self):
        """Setup enhanced logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('enhanced_scraper_controller.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_directories(self):
        """Setup output directories like scraper 18"""
        self.data_folder = Path('./output_data')
        self.data_folder.mkdir(exist_ok=True)
        
        # Create dated folder like scraper 18
        date_folder = self.data_folder / str(datetime.datetime.now().date())
        date_folder.mkdir(exist_ok=True)
        self.data_folder = date_folder
        
        self.log_folder = self.data_folder / 'log'
        self.log_folder.mkdir(exist_ok=True)
        
        self.output_file = self.data_folder / 'complete_data.csv'
    
    def load_processed_sites(self):
        """Load processed sites data like scraper 18"""
        try:
            if self.sites_processed_file.exists():
                with open(self.sites_processed_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            self.logger.warning(f"Could not load processed sites: {e}")
            return []
    
    def save_processed_sites(self):
        """Save processed sites data"""
        try:
            with open(self.sites_processed_file, 'w') as f:
                json.dump(self.sites_processed_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save processed sites: {e}")
    
    def report_progress(self, message):
        """Report progress to callback if available"""
        if self.progress_callback:
            self.progress_callback(message)
        self.logger.info(message)
    
    def run_single_scraper(self, site_name: str, force_run: bool = False) -> Dict[str, Any]:
        """
        Run a single scraper with enhanced error handling and detailed progress reporting
        Preserves the exact logic from scraper 18 main.py with enhanced real-time updates
        """
        result = {
            'site_name': site_name,
            'success': False,
            'error': None,
            'start_time': datetime.datetime.now(),
            'end_time': None,
            'duration_seconds': 0,
            'vehicles_processed': 0
        }
        
        try:
            if site_name not in self.scraper_mapping:
                result['error'] = f"No scraper configuration found for {site_name}"
                return result
            
            scraper_config = self.scraper_mapping[site_name]
            display_name = scraper_config['display_name']
            
            # Check if already processed (like scraper 18)
            if not force_run and site_name in self.sites_processed_data:
                result['error'] = "Site already processed (use force_run=True to override)"
                self.logger.info(f"SKIP {display_name}: Already processed, skipping")
                return result
            
            # Report start like scraper 18
            index = len(self.sites_processed_data) + 1
            total = len(self.scraper_mapping)
            self.report_progress(f"{index} / {total} : {display_name} : starting")
            
            # Create a custom output file and folder for this scraper to capture CSV output
            scraper_output_folder = self.data_folder / display_name.replace(" ", "_").replace(".", "_")
            scraper_output_folder.mkdir(exist_ok=True)
            scraper_output_file = scraper_output_folder / f"{display_name.replace(' ', '_')}_output.csv"
            
            # Get the scraper class and method
            class_name = scraper_config['class']
            method_name = scraper_config['method']
            
            # Create progress callback for real-time updates
            def scraper_progress_callback(progress_data):
                progress_type = progress_data.get('type', 'info')
                message = progress_data.get('message', '')
                vehicles_processed = progress_data.get('vehicles_processed', 0)
                current_page = progress_data.get('current_page', 0) 
                total_pages = progress_data.get('total_pages', 0)
                errors = progress_data.get('errors', 0)
                
                # Update result with current progress
                result['vehicles_processed'] = vehicles_processed
                
                # Report different types of progress with enhanced detail
                if progress_type == 'url_processing':
                    status = f"[API] {message}"
                elif progress_type == 'page_info':
                    status = f"[PAGINATION] {message}"
                elif progress_type == 'vehicle_processed':
                    status = f"[VEHICLE] {message}"
                elif progress_type == 'save_success':
                    status = f"[SAVE] {message}"
                elif progress_type == 'save_failed':
                    status = f"[ERROR] {message}"
                elif progress_type == 'database_error':
                    status = f"[DB_ERROR] {message}"
                else:
                    status = f"[INFO] {message}"
                
                # Report to console
                self.report_progress(status)
                
                # If we have a progress reporter (from web GUI), provide detailed updates
                if hasattr(self, 'current_progress_reporter') and self.current_progress_reporter:
                    self.current_progress_reporter.update_scraper_progress(
                        display_name,
                        status,
                        details="",
                        vehicles_processed=vehicles_processed,
                        current_page=current_page,
                        total_pages=total_pages,
                        errors=errors
                    )
            
            # Define scraper function to wrap with monitor
            def execute_scraper():
                if site_name == 'joemachensnissan.com':
                    JOEMACHENSNISSAN(str(self.data_folder), str(self.output_file)).start_scraping_joemachensnissan()
                elif site_name == 'joemachenscdjr.com':
                    JOEMACHENSCDJR(str(self.data_folder), str(self.output_file)).start_scraping_joemachenscdjr()
                elif site_name == 'joemachenshyundai.com':
                    JOEMACHENSHYUNDAI(str(self.data_folder), str(self.output_file)).start_scraping_joemachenshyundai()
                elif site_name == 'kiaofcolumbia.com':
                    KIAOFCOLUMBIA(str(self.data_folder), str(self.output_file)).start_scraping_kiaofcolumbia()
                elif site_name == 'porschestlouis.com':
                    PORSCHESTLOUIS(str(self.data_folder), str(self.output_file)).start_scraping_porschestlouis()
                elif site_name == 'auffenberghyundai.com':
                    AUFFENBERGHYUNDAI(str(self.data_folder), str(self.output_file)).start_scraping_auffenberghyundai()
                elif site_name == 'hondafrontenac.com':
                    HONDAFRONTENAC(str(self.data_folder), str(self.output_file)).start_scraping_hondafrontenac()
                elif site_name == 'bommaritocadillac.com':
                    BOMMARITOCADILLAC(str(self.data_folder), str(self.output_file)).start_scraping_bommaritocadillac()
                elif site_name == 'pappastoyota.com':
                    PAPPASTOYOTA(str(self.data_folder), str(self.output_file)).start_scraping_pappastoyota()
                elif site_name == 'twincitytoyota.com':
                    TWINCITYTOYOTA(str(self.data_folder), str(self.output_file)).start_scraping_twincitytoyota()
                elif site_name == 'serrahondaofallon.com':
                    SERRAHONDAOFALLON(str(self.data_folder), str(self.output_file)).start_scraping_serrahondaofallon()
                elif site_name == 'southcountyautos.com':
                    SOUTHCOUNTYAUTOS(str(self.data_folder), str(self.output_file)).start_scraping_southcountyautos()
                elif site_name == 'glendalechryslerjeep.net':
                    GLENDALECHRYSLERJEEP(str(self.data_folder), str(self.output_file)).start_scraping_glendalechryslerjeep()
                elif site_name == 'davesinclairlincolnsouth.com':
                    DAVESINCLAIRLINCOLNSOUTH(str(self.data_folder), str(self.output_file)).start_scraping_davesinclairlincolnsouth()
                elif site_name == 'suntrupkiasouth.com':
                    SUNTRUPKIASOUTH(str(self.data_folder), str(self.output_file)).start_scraping_suntrupkiasouth()
                elif site_name == 'columbiabmw.com':
                    COLUMBIABMW(str(self.data_folder), str(self.output_file)).start_scraping_columbiabmw()
                elif site_name == 'rustydrewingcadillac.com':
                    RUSTYDREWINGCADILLAC(str(self.data_folder), str(self.output_file)).start_scraping_rustydrewingcadillac()
                elif site_name == 'rustydrewingchevroletbuickgmc.com':
                    RUSTYDREWINGCHEVROLETBUICKGMC(str(self.data_folder), str(self.output_file)).start_scraping_rustydrewingchevroletbuickgmc()
                elif site_name == 'pundmannford.com':
                    PUNDMANNFORD(str(self.data_folder), str(self.output_file)).start_scraping_pundmannford()
                elif site_name == 'stehouwerauto.com':
                    STEHOUWERAUTO(str(self.data_folder), str(self.output_file)).start_scraping_stehouwerauto()
                elif site_name == 'bmwofweststlouis.com':
                    BMWOFWESTSTLOUIS(str(self.data_folder), str(self.output_file)).start_scraping_bmwofweststlouis()
                elif site_name == 'bommaritowestcounty.com':
                    BOMMARITOWESTCOUNTY(str(self.data_folder), str(self.output_file)).start_scraping_bommaritowestcounty()
                elif site_name == 'hwkia.com':
                    HWKIA(str(self.data_folder), str(self.output_file)).start_scraping_hwkia()
                elif site_name == 'wcvolvocars.com':
                    WCVOLVOCARS(str(self.data_folder), str(self.output_file)).start_scraping_wcvolvocars()
                elif site_name == 'joemachenstoyota.com':
                    JOEMACHENSTOYOTA(str(self.data_folder), str(self.output_file)).start_scraping_joemachenstoyota()
                elif site_name == 'suntruphyundaisouth.com':
                    SUNTRUPHYUNDAISOUTH(str(self.data_folder), str(self.output_file)).start_scraping_suntruphyundaisouth()
                elif site_name == 'landroverranchomirage.com':
                    LANDROVERRANCHOMIRAGE(str(self.data_folder), str(self.output_file)).start_scraping_landroverranchomirage()
                elif site_name == 'jaguarranchomirage.com':
                    JAGUARRANCHOMIRAGE(str(self.data_folder), str(self.output_file)).start_scraping_jaguarranchomirage()
                elif site_name == 'indigoautogroup.com':
                    INDIGOAUTOGROUP(str(self.data_folder), str(self.output_file)).start_scraping_indigoautogroup()
                elif site_name == 'miniofstlouis.com':
                    MINIOFSTLOUIS(str(self.data_folder), str(self.output_file)).start_scraping_miniofstlouis()
                elif site_name == 'suntrupfordkirkwood.com':
                    SUNTRUPFORDKIRKWOOD(str(self.data_folder), str(self.output_file)).start_scraping_suntrupfordkirkwood()
                elif site_name == 'thoroughbredford.com':
                    THOROUGHBREDFORD(str(self.data_folder), str(self.output_file)).start_scraping_thoroughbredford()
                elif site_name == 'spiritlexus.com':
                    SPIRITLEXUS(str(self.data_folder), str(self.output_file)).start_scraping_spiritlexus()
                elif site_name == 'frankletahonda.com':
                    FRANKLETAHONDA(str(self.data_folder), str(self.output_file)).start_scraping_frankletahonda()
                elif site_name == 'columbiahonda.com':
                    COLUMBIAHONDA(str(self.data_folder), str(self.output_file)).start_scraping_columbiahonda()
                elif site_name == 'davesinclairlincolnstpeters.com':
                    DAVESINCLAIRLINCOLNSTPETERS(str(self.data_folder), str(self.output_file)).start_scraping_davesinclairlincolnstpeters()
                elif site_name == 'weberchev.com':
                    WEBERCHEV(str(self.data_folder), str(self.output_file)).start_scraping_weberchev()
                elif site_name == 'suntrupbuickgmc.com':
                    SUNTRUPBUICKGMC(str(self.data_folder), str(self.output_file)).start_scraping_suntrupbuickgmc()
                elif site_name == 'suntrupfordwest.com':
                    SUNTRUPFORDWEST(str(self.data_folder), str(self.output_file)).start_scraping_suntrupfordwest()
                elif site_name == 'audiranchomirage.com':
                    AUDIRANCHOMIRAGE(str(self.data_folder), str(self.output_file)).start_scraping_audiranchomirage()
                else:
                    raise ValueError(f"Scraper execution not implemented for {site_name}")
            
            # Execute scraper with monitoring
            monitor_result = monitor_scraper_execution(
                execute_scraper, 
                display_name, 
                scraper_progress_callback
            )
            
            # Check if monitoring detected any issues
            if not monitor_result['success']:
                result['error'] = monitor_result['error']
                return result
            
            # Update result with monitoring data
            monitoring_data = monitor_result.get('monitoring_data', {})
            result['vehicles_processed'] = monitoring_data.get('vehicles_processed', 0)
            
            # Report final statistics like scraper 18
            self.report_progress(f"[COMPLETE] Processed {result['vehicles_processed']} vehicles")
            
            # Mark as processed (like scraper 18)
            self.sites_processed_data.append(site_name)
            self.save_processed_sites()
            
            # Success!
            result['success'] = True
            result['end_time'] = datetime.datetime.now()
            result['duration_seconds'] = (result['end_time'] - result['start_time']).total_seconds()
            
            self.report_progress(f"SUCCESS {display_name}: Completed successfully in {result['duration_seconds']:.1f}s")
            
        except Exception as e:
            result['error'] = str(e)
            result['end_time'] = datetime.datetime.now()
            result['duration_seconds'] = (result['end_time'] - result['start_time']).total_seconds()
            
            self.logger.error(f"FAILED {display_name}: Failed after {result['duration_seconds']:.1f}s")
            self.logger.error(f"Error details: {traceback.format_exc()}")
            
            self.report_progress(f"FAILED {display_name}: Failed - {str(e)}")
        
        return result
    
    def run_multiple_scrapers(self, site_names: List[str], force_run: bool = False) -> Dict[str, Any]:
        """Run multiple scrapers with enhanced error handling"""
        
        session_result = {
            'start_time': datetime.datetime.now(),
            'end_time': None,
            'total_scrapers': len(site_names),
            'successful_scrapers': 0,
            'failed_scrapers': 0,
            'results': {},
            'errors': []
        }
        
        self.report_progress(f"BATCH: Starting batch scrape of {len(site_names)} scrapers")
        
        for index, site_name in enumerate(site_names):
            self.report_progress(f"PROGRESS: {index + 1}/{len(site_names)} - {site_name}")
            
            try:
                result = self.run_single_scraper(site_name, force_run)
                session_result['results'][site_name] = result
                
                if result['success']:
                    session_result['successful_scrapers'] += 1
                else:
                    session_result['failed_scrapers'] += 1
                    if result['error']:
                        session_result['errors'].append(f"{site_name}: {result['error']}")
                
            except Exception as e:
                # System-level error - log but continue with next scraper
                error_msg = f"System error running {site_name}: {str(e)}"
                session_result['errors'].append(error_msg)
                session_result['failed_scrapers'] += 1
                self.logger.error(f"SYSTEM ERROR: {error_msg}")
                self.logger.error(traceback.format_exc())
            
            # Brief pause between scrapers to prevent overwhelming servers
            time.sleep(1)
        
        session_result['end_time'] = datetime.datetime.now()
        session_result['total_duration'] = (session_result['end_time'] - session_result['start_time']).total_seconds()
        
        # Final report
        success_rate = (session_result['successful_scrapers'] / session_result['total_scrapers']) * 100
        self.report_progress(f"COMPLETE: Batch scrape completed:")
        self.report_progress(f"   SUCCESS: {session_result['successful_scrapers']}")
        self.report_progress(f"   FAILED: {session_result['failed_scrapers']}")
        self.report_progress(f"   SUCCESS RATE: {success_rate:.1f}%")
        self.report_progress(f"   TOTAL TIME: {session_result['total_duration']:.1f}s")
        
        return session_result
    
    def run_all_scrapers(self, force_run: bool = False) -> Dict[str, Any]:
        """Run all available scrapers"""
        all_sites = list(self.scraper_mapping.keys())
        return self.run_multiple_scrapers(all_sites, force_run)
    
    def get_available_scrapers(self) -> List[Dict[str, str]]:
        """Get list of available scrapers"""
        return [
            {
                'site_name': site_name,
                'display_name': config['display_name'],
                'processed': site_name in self.sites_processed_data
            }
            for site_name, config in self.scraper_mapping.items()
        ]
    
    def reset_processed_sites(self):
        """Reset processed sites list"""
        self.sites_processed_data = []
        self.save_processed_sites()
        self.logger.info("Processed sites list reset")

def test_controller():
    """Test the enhanced controller"""
    def progress_callback(message):
        print(f"[PROGRESS] {message}")
    
    controller = EnhancedScraperController(progress_callback)
    
    print(f"Available scrapers: {len(controller.get_available_scrapers())}")
    
    # Test with a single scraper
    test_result = controller.run_single_scraper('columbiahonda.com', force_run=True)
    print(f"Test result: {test_result}")

if __name__ == "__main__":
    test_controller()