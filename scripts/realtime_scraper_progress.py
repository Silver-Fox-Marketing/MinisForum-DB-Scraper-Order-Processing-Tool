#!/usr/bin/env python3
"""
Real-time Scraper Progress System
=================================

Provides real-time progress updates for scrapers with terminal output
and WebSocket communication to the web GUI.

Author: Silver Fox Assistant
Created: 2025-07-28
"""

import sys
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path

class ScraperProgressReporter:
    """Real-time progress reporting for scrapers"""
    
    def __init__(self, socketio=None):
        self.socketio = socketio
        self.logger = logging.getLogger(__name__)
        self.start_time = None
        self.total_scrapers = 0
        self.completed_scrapers = 0
        self.failed_scrapers = 0
        self.current_scraper = None
        self.progress_callback = None
        
    def set_progress_callback(self, callback: Callable):
        """Set callback function for progress updates"""
        self.progress_callback = callback
    
    def start_scraping_session(self, total_scrapers: int, scraper_names: List[str]):
        """Start a new scraping session"""
        self.start_time = datetime.now()
        self.total_scrapers = total_scrapers
        self.completed_scrapers = 0
        self.failed_scrapers = 0
        self.current_scraper = None
        
        # Terminal output
        print("=" * 80)
        print("[SCRAPER] SILVER FOX SCRAPER SYSTEM - STARTING REAL-TIME SCRAPING")
        print("=" * 80)
        print(f"[INFO] Total scrapers to run: {total_scrapers}")
        print(f"[INFO] Target dealerships: {', '.join(scraper_names)}")
        print(f"[INFO] Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()
        
        # WebSocket update
        if self.socketio:
            self.socketio.emit('scraper_session_start', {
                'total_scrapers': total_scrapers,
                'scraper_names': scraper_names,
                'start_time': self.start_time.isoformat(),
                'status': 'started'
            })
        
        # Progress callback
        if self.progress_callback:
            self.progress_callback({
                'type': 'session_start',
                'total_scrapers': total_scrapers,
                'progress_percent': 0
            })
    
    def start_scraper(self, scraper_name: str, expected_vehicles: int = None):
        """Start an individual scraper"""
        self.current_scraper = scraper_name
        
        # Terminal output
        print(f"[START] Starting scraper: {scraper_name}")
        if expected_vehicles:
            print(f"   Expected vehicles: ~{expected_vehicles}")
        print(f"   Progress: {self.completed_scrapers + self.failed_scrapers + 1}/{self.total_scrapers}")
        
        # WebSocket update
        if self.socketio:
            self.socketio.emit('scraper_start', {
                'scraper_name': scraper_name,
                'expected_vehicles': expected_vehicles,
                'progress': self.completed_scrapers + self.failed_scrapers + 1,
                'total': self.total_scrapers
            })
        
        # Progress callback
        if self.progress_callback:
            progress_percent_start = ((self.completed_scrapers + self.failed_scrapers) / self.total_scrapers) * 100 if self.total_scrapers > 0 else 0
            self.progress_callback({
                'type': 'scraper_start',
                'scraper_name': scraper_name,
                'progress_percent': progress_percent_start
            })
    
    def update_scraper_progress(self, scraper_name: str, status: str, details: str = "", 
                               vehicles_processed: int = 0, current_page: int = 0, total_pages: int = 0, 
                               errors: int = 0):
        """Update progress during scraping with detailed metrics"""
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # Terminal output (matching scraper 18 style)
        print(f"   [{current_time}] {status}")
        if details:
            print(f"   └── {details}")
        
        # Calculate real-time progress within current scraper
        scraper_progress = 0
        if total_pages > 0:
            scraper_progress = (current_page / total_pages) * 100
        
        # Calculate overall session progress
        overall_progress = 0
        if self.total_scrapers > 0:
            # Progress from completed scrapers
            completed_progress = (self.completed_scrapers + self.failed_scrapers) / self.total_scrapers
            # Progress from current scraper (partial)
            current_scraper_progress = (scraper_progress / 100) / self.total_scrapers
            overall_progress = (completed_progress + current_scraper_progress) * 100
        
        # WebSocket update with detailed progress data
        if self.socketio:
            self.socketio.emit('scraper_progress', {
                'scraper_name': scraper_name,
                'status': status,
                'details': details,
                'timestamp': current_time,
                'vehicles_processed': vehicles_processed,
                'current_page': current_page,
                'total_pages': total_pages,
                'scraper_progress': scraper_progress,
                'overall_progress': overall_progress,
                'completed_scrapers': self.completed_scrapers,
                'failed_scrapers': self.failed_scrapers,
                'total_scrapers': self.total_scrapers,
                'errors': errors
            })
        
        # Progress callback with real-time data
        if self.progress_callback:
            self.progress_callback({
                'type': 'scraper_progress_update',
                'scraper_name': scraper_name,
                'vehicles_processed': vehicles_processed,
                'progress_percent': overall_progress,
                'current_page': current_page,
                'total_pages': total_pages,
                'errors': errors
            })
    
    def complete_scraper(self, scraper_name: str, result: Dict[str, Any]):
        """Complete an individual scraper"""
        self.completed_scrapers += 1
        duration = time.time() - self.start_time.timestamp() if self.start_time else 0
        
        success = result.get('success', False)
        vehicle_count = result.get('vehicle_count', 0)
        data_source = result.get('data_source', 'unknown')
        is_real_data = result.get('is_real_data', False)
        
        # Terminal output
        if success:
            status_prefix = "[SUCCESS]" if is_real_data else "[FALLBACK]"
            data_type = "REAL DATA" if is_real_data else "FALLBACK"
            print(f"{status_prefix} COMPLETED: {scraper_name}")
            print(f"   [DATA] Vehicles found: {vehicle_count}")
            print(f"   [SOURCE] Data source: {data_source}")
            print(f"   [TYPE] Data type: {data_type}")
            if result.get('duration_seconds'):
                print(f"   [TIME] Duration: {result['duration_seconds']:.1f}s")
        else:
            print(f"[FAILED] FAILED: {scraper_name}")
            print(f"   [ERROR] Error: {result.get('error', 'Unknown error')}")
            self.failed_scrapers += 1
            self.completed_scrapers -= 1  # Adjust count
        
        if self.total_scrapers > 0:
            progress_percent = ((self.completed_scrapers + self.failed_scrapers) / self.total_scrapers) * 100
            print(f"   [PROGRESS] Overall progress: {progress_percent:.1f}% ({self.completed_scrapers + self.failed_scrapers}/{self.total_scrapers})")
        else:
            print(f"   [PROGRESS] Individual scraper completed (session not tracked)")
        print()
        
        # WebSocket update
        if self.socketio:
            progress_percent_ws = progress_percent if self.total_scrapers > 0 else 100
            self.socketio.emit('scraper_complete', {
                'scraper_name': scraper_name,
                'success': success,
                'vehicle_count': vehicle_count,
                'data_source': data_source,
                'is_real_data': is_real_data,
                'duration': result.get('duration_seconds', 0),
                'error': result.get('error'),
                'progress_percent': progress_percent_ws,
                'completed': self.completed_scrapers,
                'failed': self.failed_scrapers,
                'total': self.total_scrapers
            })
        
        # Progress callback
        if self.progress_callback:
            progress_percent_callback = progress_percent if self.total_scrapers > 0 else 100
            self.progress_callback({
                'type': 'scraper_complete',
                'scraper_name': scraper_name,
                'success': success,
                'progress_percent': progress_percent_callback
            })
    
    def complete_session(self, session_results: Dict[str, Any]):
        """Complete the entire scraping session"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds() if self.start_time else 0
        
        total_vehicles = session_results.get('total_vehicles', 0)
        total_real_data = session_results.get('total_real_data', 0)
        total_fallback_data = session_results.get('total_fallback_data', 0)
        errors = session_results.get('errors', [])
        
        # Terminal output
        print("=" * 80)
        print("[COMPLETE] SCRAPING SESSION COMPLETED")
        print("=" * 80)
        print(f"[TIME] Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[DURATION] Total duration: {total_duration:.1f} seconds")
        print(f"[STATS] Scrapers run: {self.total_scrapers}")
        print(f"[SUCCESS] Successful: {self.completed_scrapers}")
        print(f"[FAILED] Failed: {self.failed_scrapers}")
        print(f"[RATE] Success rate: {(self.completed_scrapers / self.total_scrapers * 100):.1f}%")
        print()
        print(f"[VEHICLES] Total vehicles: {total_vehicles}")
        print(f"[REAL] Real data: {total_real_data}")
        print(f"[FALLBACK] Fallback data: {total_fallback_data}")
        
        if total_real_data > 0:
            real_data_percent = (total_real_data / total_vehicles * 100) if total_vehicles > 0 else 0
            print(f"[REAL_RATE] Real data rate: {real_data_percent:.1f}%")
        
        if errors:
            print(f"[ERRORS] Errors encountered: {len(errors)}")
            for error in errors[:3]:  # Show first 3 errors
                print(f"   - {error}")
            if len(errors) > 3:
                print(f"   ... and {len(errors) - 3} more")
        
        print("=" * 80)
        
        if total_real_data > 0:
            print("[SUCCESS] Real data extracted from live APIs!")
        else:
            print("[WARNING] No real data extracted - check API connectivity")
        
        print("=" * 80)
        print()
        
        # WebSocket update
        if self.socketio:
            self.socketio.emit('scraper_session_complete', {
                'end_time': end_time.isoformat(),
                'total_duration': total_duration,
                'total_scrapers': self.total_scrapers,
                'completed': self.completed_scrapers,
                'failed': self.failed_scrapers,
                'success_rate': (self.completed_scrapers / self.total_scrapers * 100),
                'total_vehicles': total_vehicles,
                'total_real_data': total_real_data,
                'total_fallback_data': total_fallback_data,
                'real_data_rate': (total_real_data / total_vehicles * 100) if total_vehicles > 0 else 0,
                'errors': errors
            })
        
        # Progress callback
        if self.progress_callback:
            self.progress_callback({
                'type': 'session_complete',
                'progress_percent': 100,
                'success_rate': (self.completed_scrapers / self.total_scrapers * 100),
                'total_vehicles': total_vehicles
            })

class ProgressBar:
    """ASCII progress bar for terminal"""
    
    def __init__(self, total: int, width: int = 50, prefix: str = "Progress"):
        self.total = total
        self.width = width
        self.prefix = prefix
        self.current = 0
    
    def update(self, current: int, suffix: str = ""):
        """Update progress bar"""
        self.current = current
        percent = (current / self.total) * 100
        filled = int(self.width * current // self.total)
        bar = '█' * filled + '░' * (self.width - filled)
        
        print(f'\r{self.prefix}: |{bar}| {percent:.1f}% {suffix}', end='', flush=True)
    
    def complete(self, suffix: str = "Complete!"):
        """Complete the progress bar"""
        self.update(self.total, suffix)
        print()  # New line

def test_progress_reporter():
    """Test the progress reporter"""
    reporter = ScraperProgressReporter()
    
    # Test session
    scrapers = ['Test Dealer 1', 'Test Dealer 2', 'Test Dealer 3']
    reporter.start_scraping_session(len(scrapers), scrapers)
    
    for i, scraper in enumerate(scrapers):
        reporter.start_scraper(scraper, expected_vehicles=random.randint(20, 50))
        
        # Simulate scraping progress
        reporter.update_scraper_progress(scraper, "Connecting to API...")
        time.sleep(0.5)
        reporter.update_scraper_progress(scraper, "Fetching vehicle data...")
        time.sleep(0.5)
        reporter.update_scraper_progress(scraper, "Processing vehicles...")
        
        # Complete scraper
        result = {
            'success': True,
            'vehicle_count': random.randint(15, 45),
            'data_source': 'real_api' if random.random() > 0.3 else 'fallback',
            'is_real_data': random.random() > 0.3,
            'duration_seconds': random.uniform(2.0, 8.0)
        }
        reporter.complete_scraper(scraper, result)
    
    # Complete session
    session_results = {
        'total_vehicles': 120,
        'total_real_data': 80,
        'total_fallback_data': 40,
        'errors': []
    }
    reporter.complete_session(session_results)

if __name__ == "__main__":
    import random
    test_progress_reporter()