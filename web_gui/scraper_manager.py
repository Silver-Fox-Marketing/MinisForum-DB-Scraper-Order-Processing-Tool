#!/usr/bin/env python3
"""
Scraper Manager
===============

Web GUI interface for managing scraper execution using the real scraper integration system.
This bridges the web interface with our bulletproof scraper system.

Author: Silver Fox Assistant
Created: 2025-08-01
"""

import os
import sys
import logging
import threading
import time
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime

# Add scripts directory to path
current_dir = Path(__file__).parent
scripts_dir = current_dir.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

try:
    from real_scraper_integration import RealScraperIntegration
    from database_connection import db_manager
    print("OK ScraperManager dependencies imported successfully")
except ImportError as e:
    print(f"ERROR: Failed to import scraper dependencies: {e}")
    raise

class ScraperManager:
    """
    Manager for coordinating scraper execution through the web interface
    """
    
    def __init__(self, socketio=None):
        """Initialize the scraper manager"""
        self.socketio = socketio
        self.logger = logging.getLogger(__name__)
        
        # Active scrapers tracking
        self.active_scrapers = {}  # dealership_name -> thread
        self.scraper_status = {}   # dealership_name -> status info
        
        # Output callbacks
        self.output_callbacks = []
        
        # Initialize real scraper integration
        self.real_scraper_integration = RealScraperIntegration(socketio)
        
        # Store reference for later updates
        self._socketio_ref = socketio
        
        self.logger.info("ScraperManager initialized")
    
    def add_output_callback(self, callback: Callable):
        """Add a callback for scraper output"""
        self.output_callbacks.append(callback)
    
    def update_socketio(self, socketio):
        """Update the socketio instance after Flask app initialization"""
        self.socketio = socketio
        self._socketio_ref = socketio
        # Also update the real scraper integration
        if hasattr(self.real_scraper_integration, 'socketio'):
            self.real_scraper_integration.socketio = socketio
        self.logger.info("ScraperManager socketio updated")
    
    def start_scraper(self, dealership_name: str) -> bool:
        """Start scraping for a specific dealership"""
        try:
            # Check if already running
            if dealership_name in self.active_scrapers:
                existing_thread = self.active_scrapers[dealership_name]
                if existing_thread.is_alive():
                    self.logger.warning(f"Scraper for {dealership_name} is already running")
                    return False
                else:
                    # Clean up dead thread
                    del self.active_scrapers[dealership_name]
            
            # Update status
            self.scraper_status[dealership_name] = {
                'status': 'starting',
                'start_time': datetime.now(),
                'progress': 0,
                'vehicles_processed': 0,
                'errors': 0,
                'current_activity': 'Initializing scraper...'
            }
            
            # Emit initial status - use events that frontend expects
            if self.socketio:
                # Emit scraper session start
                self.socketio.emit('scraper_session_start', {
                    'total_scrapers': 1,
                    'scrapers': [dealership_name]
                })
                
                # Emit individual scraper start
                self.socketio.emit('scraper_start', {
                    'scraper_name': dealership_name,
                    'progress': 1,
                    'total': 1,
                    'expected_vehicles': self.real_scraper_integration.expected_vehicle_counts.get(dealership_name, 30)
                })
            
            # Start scraper in background thread
            def run_scraper_thread():
                try:
                    self.logger.info(f"Starting real scraper for {dealership_name}")
                    
                    # Update status to running
                    self.scraper_status[dealership_name]['status'] = 'running'
                    self.scraper_status[dealership_name]['current_activity'] = 'Running enhanced scraper...'
                    
                    # Emit basic progress update to show scraper is starting execution
                    if self.socketio:
                        self.socketio.emit('scraper_progress', {
                            'scraper_name': dealership_name,
                            'status': 'Initializing enhanced scraper controller...',
                            'details': 'Loading scraper modules and preparing execution',
                            'vehicles_processed': 0,
                            'current_page': 0,
                            'total_pages': 0,
                            'errors': 0,
                            'overall_progress': 0,
                            'timestamp': time.strftime('%H:%M:%S')
                        })
                    
                    # Execute real scraper with periodic progress updates
                    if self.socketio:
                        self.socketio.emit('scraper_progress', {
                            'scraper_name': dealership_name,
                            'status': 'Executing enhanced scraper controller...',
                            'details': 'Running real scraper with bulletproof error handling',
                            'vehicles_processed': 0,
                            'current_page': 0,
                            'total_pages': 0,
                            'errors': 0,
                            'overall_progress': 10,
                            'timestamp': time.strftime('%H:%M:%S')
                        })
                    
                    result = self.real_scraper_integration.run_real_scraper(dealership_name)
                    
                    # Emit progress during execution
                    if self.socketio:
                        self.socketio.emit('scraper_progress', {
                            'scraper_name': dealership_name,
                            'status': 'Processing scraper results...',
                            'details': 'Analyzing scraped data and preparing output',
                            'vehicles_processed': result.get('vehicle_count', 0) if result else 0,
                            'current_page': 0,
                            'total_pages': 0,
                            'errors': 0,
                            'overall_progress': 90,
                            'timestamp': time.strftime('%H:%M:%S')
                        })
                    
                    # Update final status
                    if result['success']:
                        self.scraper_status[dealership_name]['status'] = 'completed'
                        self.scraper_status[dealership_name]['current_activity'] = 'Completed successfully'
                        self.scraper_status[dealership_name]['vehicles_processed'] = result.get('vehicle_count', 0)
                        
                        if self.socketio:
                            # Emit scraper completion
                            self.socketio.emit('scraper_complete', {
                                'scraper_name': dealership_name,
                                'success': True,
                                'vehicles_processed': result.get('vehicle_count', 0),
                                'duration': result.get('duration_seconds', 0),
                                'message': f'Completed successfully - {result.get("vehicle_count", 0)} vehicles processed'
                            })
                            
                            # Emit session completion (since we're running single scrapers)
                            self.socketio.emit('scraper_session_complete', {
                                'total_scrapers': 1,
                                'successful_scrapers': 1,
                                'failed_scrapers': 0,
                                'total_vehicles': result.get('vehicle_count', 0),
                                'success_rate': 100.0,
                                'duration': result.get('duration_seconds', 0)
                            })
                        
                        self.logger.info(f"Scraper for {dealership_name} completed successfully")
                    else:
                        self.scraper_status[dealership_name]['status'] = 'failed'
                        self.scraper_status[dealership_name]['current_activity'] = f'Failed: {result.get("error", "Unknown error")}'
                        self.scraper_status[dealership_name]['errors'] += 1
                        
                        if self.socketio:
                            # Emit scraper failure
                            self.socketio.emit('scraper_complete', {
                                'scraper_name': dealership_name,
                                'success': False,
                                'error': result.get('error', 'Unknown error'),
                                'vehicles_processed': 0,
                                'duration': 0,
                                'message': f'Failed: {result.get("error", "Unknown error")}'
                            })
                            
                            # Emit session completion with failure
                            self.socketio.emit('scraper_session_complete', {
                                'total_scrapers': 1,
                                'successful_scrapers': 0,
                                'failed_scrapers': 1,
                                'total_vehicles': 0,
                                'success_rate': 0.0,
                                'duration': 0
                            })
                        
                        self.logger.error(f"Scraper for {dealership_name} failed: {result.get('error')}")
                    
                    # Call output callbacks
                    for callback in self.output_callbacks:
                        try:
                            callback(dealership_name, result)
                        except Exception as e:
                            self.logger.error(f"Output callback error: {e}")
                    
                except Exception as e:
                    self.logger.error(f"Error in scraper thread for {dealership_name}: {e}")
                    
                    # Update error status
                    self.scraper_status[dealership_name]['status'] = 'failed'
                    self.scraper_status[dealership_name]['current_activity'] = f'Error: {str(e)}'
                    self.scraper_status[dealership_name]['errors'] += 1
                    
                    if self.socketio:
                        # Emit scraper failure due to exception
                        self.socketio.emit('scraper_complete', {
                            'scraper_name': dealership_name,
                            'success': False,
                            'error': str(e),
                            'vehicles_processed': 0,
                            'duration': 0,
                            'message': f'Error: {str(e)}'
                        })
                        
                        # Emit session completion with failure
                        self.socketio.emit('scraper_session_complete', {
                            'total_scrapers': 1,
                            'successful_scrapers': 0,
                            'failed_scrapers': 1,
                            'total_vehicles': 0,
                            'success_rate': 0.0,
                            'duration': 0
                        })
                
                finally:
                    # Clean up thread reference
                    if dealership_name in self.active_scrapers:
                        del self.active_scrapers[dealership_name]
            
            # Start the thread
            thread = threading.Thread(target=run_scraper_thread, name=f"Scraper-{dealership_name}")
            thread.daemon = True
            thread.start()
            
            # Track the thread
            self.active_scrapers[dealership_name] = thread
            
            self.logger.info(f"Started scraper thread for {dealership_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start scraper for {dealership_name}: {e}")
            
            # Update error status
            self.scraper_status[dealership_name] = {
                'status': 'failed',
                'start_time': datetime.now(),
                'progress': 0,
                'vehicles_processed': 0,
                'errors': 1,
                'current_activity': f'Failed to start: {str(e)}'
            }
            
            if self.socketio:
                # Emit scraper failure to start
                self.socketio.emit('scraper_complete', {
                    'scraper_name': dealership_name,
                    'success': False,
                    'error': f'Failed to start: {str(e)}',
                    'vehicles_processed': 0,
                    'duration': 0,
                    'message': f'Failed to start: {str(e)}'
                })
                
                # Emit session completion with failure
                self.socketio.emit('scraper_session_complete', {
                    'total_scrapers': 1,
                    'successful_scrapers': 0,
                    'failed_scrapers': 1,
                    'total_vehicles': 0,
                    'success_rate': 0.0,
                    'duration': 0
                })
            
            return False
    
    def stop_scraper(self, dealership_name: str) -> bool:
        """Stop scraping for a specific dealership"""
        try:
            if dealership_name not in self.active_scrapers:
                self.logger.warning(f"No active scraper found for {dealership_name}")
                return False
            
            thread = self.active_scrapers[dealership_name]
            if not thread.is_alive():
                # Thread already finished
                del self.active_scrapers[dealership_name]
                return True
            
            # Note: Python threads cannot be forcibly stopped safely
            # We can only mark the scraper as stopped and hope the thread completes
            self.logger.warning(f"Cannot forcibly stop scraper thread for {dealership_name}")
            
            # Update status
            if dealership_name in self.scraper_status:
                self.scraper_status[dealership_name]['status'] = 'stopping'
                self.scraper_status[dealership_name]['current_activity'] = 'Stopping scraper...'
            
            if self.socketio:
                # Emit scraper stopping (but not completion yet since threads can't be forcibly stopped)
                self.socketio.emit('scraper_progress', {
                    'scraper_name': dealership_name,
                    'status': 'Stopping scraper...',
                    'details': 'Waiting for current operation to complete',
                    'timestamp': time.strftime('%H:%M:%S')
                })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop scraper for {dealership_name}: {e}")
            return False
    
    def get_scraper_status(self, dealership_name: str) -> Dict[str, Any]:
        """Get current status of a scraper"""
        return self.scraper_status.get(dealership_name, {
            'status': 'idle',
            'progress': 0,
            'vehicles_processed': 0,
            'errors': 0,
            'current_activity': 'Not running'
        })
    
    def get_all_scraper_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all scrapers"""
        return self.scraper_status.copy()
    
    def is_scraper_running(self, dealership_name: str) -> bool:
        """Check if a scraper is currently running"""
        if dealership_name not in self.active_scrapers:
            return False
        
        thread = self.active_scrapers[dealership_name]
        return thread.is_alive()
    
    def start_multiple_scrapers(self, dealership_names: List[str]) -> Dict[str, bool]:
        """Start multiple scrapers"""
        results = {}
        
        for dealership_name in dealership_names:
            results[dealership_name] = self.start_scraper(dealership_name)
            
            # Brief delay between starts to prevent overwhelming the system
            time.sleep(1)
        
        return results
    
    def stop_all_scrapers(self) -> Dict[str, bool]:
        """Stop all active scrapers"""
        results = {}
        
        for dealership_name in list(self.active_scrapers.keys()):
            results[dealership_name] = self.stop_scraper(dealership_name)
        
        return results
    
    def get_available_dealerships(self) -> List[str]:
        """Get list of available dealerships for scraping"""
        try:
            # Get from real scraper integration mapping
            return list(self.real_scraper_integration.real_scraper_mapping.keys())
        except Exception as e:
            self.logger.error(f"Error getting available dealerships: {e}")
            return []

# Create global instance
scraper_manager = ScraperManager()

# Test function
def test_scraper_manager():
    """Test the scraper manager"""
    print("Testing ScraperManager...")
    
    available = scraper_manager.get_available_dealerships()
    print(f"Available dealerships: {len(available)}")
    print(f"First 5: {available[:5]}")
    
    # Test status
    status = scraper_manager.get_scraper_status('Columbia Honda')
    print(f"Columbia Honda status: {status}")

if __name__ == "__main__":
    test_scraper_manager()