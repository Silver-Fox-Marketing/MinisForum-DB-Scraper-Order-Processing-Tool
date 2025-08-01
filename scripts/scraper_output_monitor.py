#!/usr/bin/env python3
"""
Scraper Output Monitor
=====================

Monitors scraper output in real-time to provide detailed progress updates
that match the scraper 18 console output style.

Author: Silver Fox Assistant
Created: 2025-08-01
"""

import io
import sys
import re
import threading
import time
import csv
from pathlib import Path
from typing import Callable, Dict, Any, List
from contextlib import redirect_stdout, redirect_stderr

class ScraperOutputMonitor:
    """Monitors scraper output and provides real-time progress updates"""
    
    def __init__(self, progress_callback: Callable = None):
        self.progress_callback = progress_callback
        self.captured_output = []
        self.vehicles_processed = 0
        self.current_page = 0
        self.total_pages = 0
        self.urls_processed = []
        self.errors = []
        self.dealership_name = ""
        
        # Pattern matching for scraper 18 style output
        self.patterns = {
            'processing_url': re.compile(r'Processing URL:\s+(.+)'),
            'page_info': re.compile(r'(\d+)\s+:\s+(\d+)\s+:\s+(\d+)\s+:\s+(\d+)'),  # page : per_page : total : total_pages
            'vehicle_info': re.compile(r'(\d+)\s+:\s+(\d+)\s+:\s+(.+?)\s+:\s+(.+)'),  # page : per_page : vehicle_name : url
            'directory_created': re.compile(r'Directory (.+) Created'),
            'database_error': re.compile(r'Database connection error: (.+)'),
            'save_status': re.compile(r'(SUCCESS|FAILED): (.+)')
        }
    
    def set_dealership_name(self, name: str):
        """Set the current dealership name"""
        self.dealership_name = name
    
    def report_progress(self, message: str, progress_type: str = 'info'):
        """Report progress to callback"""
        if self.progress_callback:
            self.progress_callback({
                'type': progress_type,
                'message': message,
                'dealership': self.dealership_name,
                'vehicles_processed': self.vehicles_processed,
                'current_page': self.current_page,
                'total_pages': self.total_pages,
                'errors': len(self.errors)
            })
    
    def process_output_line(self, line: str):
        """Process a single line of output from the scraper"""
        line = line.strip()
        if not line:
            return
        
        self.captured_output.append(line)
        
        # Check for processing URL
        url_match = self.patterns['processing_url'].match(line)
        if url_match:
            url = url_match.group(1)
            self.urls_processed.append(url)
            self.report_progress(f"Processing URL: {url}", 'url_processing')
            return
        
        # Check for page info (1 : 24 : 266 : 12)
        page_match = self.patterns['page_info'].match(line)
        if page_match:
            self.current_page = int(page_match.group(1))
            per_page = int(page_match.group(2))
            total_vehicles = int(page_match.group(3))
            self.total_pages = int(page_match.group(4))
            
            self.report_progress(
                f"Page {self.current_page}/{self.total_pages} - {per_page} vehicles per page - {total_vehicles} total",
                'page_info'
            )
            return
        
        # Check for vehicle processing (1 : 24 : 2025 Honda Civic : url)
        vehicle_match = self.patterns['vehicle_info'].match(line)
        if vehicle_match:
            page = int(vehicle_match.group(1))
            per_page = int(vehicle_match.group(2))
            vehicle_name = vehicle_match.group(3)
            vehicle_url = vehicle_match.group(4)
            
            self.vehicles_processed += 1
            
            self.report_progress(
                f"Vehicle {self.vehicles_processed}: {vehicle_name}",
                'vehicle_processed'
            )
            return
        
        # Check for directory creation
        dir_match = self.patterns['directory_created'].match(line)
        if dir_match:
            directory = dir_match.group(1)
            self.report_progress(f"Created directory: {directory}", 'directory_created')
            return
        
        # Check for database errors
        db_error_match = self.patterns['database_error'].match(line)
        if db_error_match:
            error = db_error_match.group(1)
            self.errors.append(error)
            self.report_progress(f"Database error: {error}", 'database_error')
            return
        
        # Check for save status
        save_match = self.patterns['save_status'].match(line)
        if save_match:
            status = save_match.group(1)
            details = save_match.group(2)
            progress_type = 'save_success' if status == 'SUCCESS' else 'save_failed'
            self.report_progress(f"{status}: {details}", progress_type)
            return
        
        # For any other output, just report it as general info
        if line.startswith('--'):
            return  # Skip separator lines
        
        self.report_progress(line, 'general')
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the monitoring session"""
        return {
            'vehicles_processed': self.vehicles_processed,
            'urls_processed': len(self.urls_processed),
            'pages_processed': self.current_page,
            'total_pages': self.total_pages,
            'errors': len(self.errors),
            'error_details': self.errors,
            'captured_output': self.captured_output
        }

class OutputCapture:
    """Captures stdout/stderr and processes it through the monitor"""
    
    def __init__(self, monitor: ScraperOutputMonitor):
        self.monitor = monitor
        self.buffer = io.StringIO()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.capturing = True
    
    def write(self, text):
        # Write to original stdout first
        self.original_stdout.write(text)
        self.original_stdout.flush()
        
        # Only process through monitor if we're actively capturing (avoid recursion)
        if self.capturing and text.strip():
            # Temporarily disable capturing to avoid recursion from callback
            self.capturing = False
            try:
                lines = text.split('\n')
                for line in lines:
                    if line.strip():
                        self.monitor.process_output_line(line)
            finally:
                self.capturing = True
    
    def flush(self):
        self.original_stdout.flush()

def monitor_scraper_execution(scraper_function: Callable, dealership_name: str, progress_callback: Callable = None) -> Dict[str, Any]:
    """
    Monitor a scraper execution and provide real-time progress updates
    
    Args:
        scraper_function: The scraper function to execute
        dealership_name: Name of the dealership being scraped
        progress_callback: Callback function for progress updates
    
    Returns:
        Dict containing execution results and monitoring data
    """
    monitor = ScraperOutputMonitor(progress_callback)
    monitor.set_dealership_name(dealership_name)
    
    # Capture stdout during scraper execution
    capture = OutputCapture(monitor)
    
    result = {
        'success': False,
        'error': None,
        'monitoring_data': None
    }
    
    try:
        # Redirect stdout to our capture system
        sys.stdout = capture
        
        # Execute the scraper function
        scraper_function()
        
        result['success'] = True
        
    except Exception as e:
        result['error'] = str(e)
        monitor.report_progress(f"ERROR: {str(e)}", 'error')
        
    finally:
        # Restore original stdout
        sys.stdout = capture.original_stdout
        
        # Get monitoring summary
        result['monitoring_data'] = monitor.get_summary()
    
    return result

# Test function
def test_monitor():
    """Test the output monitor"""
    def mock_scraper():
        print("Processing URL: https://example.com/vehicles")
        print("1 : 24 : 100 : 5")
        for i in range(1, 6):
            print(f"1 : 24 : 2025 Honda Civic {i} : https://example.com/vehicle/{i}")
            time.sleep(0.1)
        print("SUCCESS: Vehicle data saved")
    
    def progress_callback(data):
        # Write directly to stderr to avoid capture recursion
        sys.stderr.write(f"[MONITOR] {data['type']}: {data['message']}\n")
        sys.stderr.flush()
    
    result = monitor_scraper_execution(mock_scraper, "Test Dealership", progress_callback)
    sys.stderr.write(f"Result: {result}\n")

if __name__ == "__main__":
    test_monitor()