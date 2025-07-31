"""
Real-time Scraper Management System
Captures and streams console output from scrapers in real-time
"""

import subprocess
import threading
import queue
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable
import psutil
import os
import signal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScraperProcess:
    """Manages a single scraper process with real-time output capture"""
    
    def __init__(self, scraper_name: str, scraper_path: str, dealership_name: str):
        self.scraper_name = scraper_name
        self.scraper_path = scraper_path
        self.dealership_name = dealership_name
        self.process = None
        self.output_queue = queue.Queue()
        self.status = "idle"  # idle, running, completed, failed
        self.start_time = None
        self.end_time = None
        self.vehicles_scraped = 0
        self.pages_processed = 0
        self.current_url = ""
        self.errors = []
        self.output_callbacks = []
        
    def add_output_callback(self, callback: Callable):
        """Add callback function for real-time output processing"""
        self.output_callbacks.append(callback)
        
    def start_scraping(self):
        """Start the scraper process with output capture"""
        try:
            self.status = "running"
            self.start_time = datetime.now()
            
            # Start the scraper process
            self.process = subprocess.Popen(
                ["python", self.scraper_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1,
                cwd=Path(self.scraper_path).parent
            )
            
            # Start output capture threads
            stdout_thread = threading.Thread(
                target=self._capture_output, 
                args=(self.process.stdout, "stdout")
            )
            stderr_thread = threading.Thread(
                target=self._capture_output, 
                args=(self.process.stderr, "stderr")
            )
            
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()
            
            logger.info(f"Started scraper process for {self.dealership_name}")
            
        except Exception as e:
            logger.error(f"Failed to start scraper for {self.dealership_name}: {e}")
            self.status = "failed"
            self.errors.append(str(e))
            
    def _capture_output(self, pipe, stream_type):
        """Capture output from stdout/stderr"""
        try:
            for line in iter(pipe.readline, ''):
                if line:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    
                    # Parse scraper output for metrics
                    self._parse_scraper_metrics(line.strip())
                    
                    # Create output message
                    output_msg = {
                        'timestamp': timestamp,
                        'stream': stream_type,
                        'message': line.strip(),
                        'scraper': self.scraper_name,
                        'dealership': self.dealership_name,
                        'vehicles_scraped': self.vehicles_scraped,
                        'pages_processed': self.pages_processed,
                        'current_url': self.current_url
                    }
                    
                    # Add to queue and notify callbacks
                    self.output_queue.put(output_msg)
                    for callback in self.output_callbacks:
                        try:
                            callback(output_msg)
                        except Exception as e:
                            logger.error(f"Callback error: {e}")
                            
        except Exception as e:
            logger.error(f"Error capturing {stream_type}: {e}")
            
    def _parse_scraper_metrics(self, line: str):
        """Parse scraper output to extract metrics"""
        try:
            # Parse different types of scraper output
            if "Processing URL:" in line:
                self.current_url = line.split("Processing URL:", 1)[1].strip()
                
            elif " : " in line and line.count(" : ") >= 3:
                # Parse format: "1 : 24 : 156 : 7" (page : vehicles_on_page : total_vehicles : total_pages)
                parts = [p.strip() for p in line.split(" : ")]
                if len(parts) >= 4 and parts[0].isdigit():
                    self.pages_processed = int(parts[0])
                    if parts[2].isdigit():
                        self.vehicles_scraped = int(parts[2])
                        
            elif "Vehicle Already Processed..." in line:
                # Don't increment for already processed vehicles  
                pass
                
            elif line.startswith("error") or "Error" in line:
                self.errors.append(line)
                
        except Exception as e:
            logger.debug(f"Error parsing metrics from line '{line}': {e}")
            
    def stop_scraping(self):
        """Stop the scraper process"""
        if self.process and self.process.poll() is None:
            try:
                # Try graceful termination first
                self.process.terminate()
                
                # Wait up to 5 seconds for graceful shutdown
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if still running
                    self.process.kill()
                    self.process.wait()
                    
                self.status = "stopped"
                self.end_time = datetime.now()
                logger.info(f"Stopped scraper for {self.dealership_name}")
                
            except Exception as e:
                logger.error(f"Error stopping scraper: {e}")
                
    def get_status(self) -> Dict:
        """Get current scraper status"""
        runtime = None
        if self.start_time:
            end = self.end_time or datetime.now()
            runtime = (end - self.start_time).total_seconds()
            
        return {
            'scraper_name': self.scraper_name,
            'dealership_name': self.dealership_name,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'runtime_seconds': runtime,
            'vehicles_scraped': self.vehicles_scraped,
            'pages_processed': self.pages_processed,
            'current_url': self.current_url,
            'errors': self.errors,
            'process_id': self.process.pid if self.process else None
        }
        
    def is_complete(self) -> bool:
        """Check if scraper process is complete"""
        if self.process:
            poll_result = self.process.poll()
            if poll_result is not None:
                self.status = "completed" if poll_result == 0 else "failed"
                self.end_time = datetime.now()
                return True
        return False


class ScraperManager:
    """Manages multiple scraper processes with real-time monitoring"""
    
    def __init__(self):
        self.scrapers: Dict[str, ScraperProcess] = {}
        self.output_callbacks = []
        self.scraper_base_path = Path("C:/Users/Workstation_1/Documents/Tools/ClaudeCode/projects/shared_resources/Project reference for scraper/vehicle_scraper 18")
        
        # Mapping of dealership names to scraper files
        self.scraper_mapping = {
            'Columbia Honda': 'scrapers/columbiahonda.py',
            'BMW of West St. Louis': 'scrapers/bmwofweststlouis.py', 
            'Dave Sinclair Lincoln South': 'scrapers/davesinclairlincolnsouth.py',
            'Suntrup Ford West': 'scrapers/suntrupfordwest.py',
            'Suntrup Ford Kirkwood': 'scrapers/suntrupfordkirkwood.py',
            'Joe Machens Hyundai': 'scrapers/joemachenshyundai.py',
            'Joe Machens Toyota': 'scrapers/joemachenstoyota.py',
            'Thoroughbred Ford': 'scrapers/thoroughbredford.py'
        }
        
    def add_output_callback(self, callback: Callable):
        """Add global output callback for all scrapers"""
        self.output_callbacks.append(callback)
        
    def start_scraper(self, dealership_name: str) -> bool:
        """Start scraping for a specific dealership"""
        try:
            if dealership_name in self.scrapers:
                logger.warning(f"Scraper for {dealership_name} is already running")
                return False
                
            if dealership_name not in self.scraper_mapping:
                logger.error(f"No scraper mapping found for {dealership_name}")
                return False
                
            scraper_file = self.scraper_mapping[dealership_name]
            scraper_path = self.scraper_base_path / scraper_file
            
            if not scraper_path.exists():
                logger.error(f"Scraper file not found: {scraper_path}")
                return False
                
            # Create scraper process
            scraper_name = scraper_file.split('/')[-1].replace('.py', '')
            scraper_process = ScraperProcess(scraper_name, str(scraper_path), dealership_name)
            
            # Add callbacks
            for callback in self.output_callbacks:
                scraper_process.add_output_callback(callback)
                
            # Start scraping
            scraper_process.start_scraping()
            self.scrapers[dealership_name] = scraper_process
            
            logger.info(f"Started scraper for {dealership_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start scraper for {dealership_name}: {e}")
            return False
            
    def stop_scraper(self, dealership_name: str) -> bool:
        """Stop scraping for a specific dealership"""
        try:
            if dealership_name not in self.scrapers:
                logger.warning(f"No active scraper found for {dealership_name}")
                return False
                
            scraper = self.scrapers[dealership_name]
            scraper.stop_scraping()
            del self.scrapers[dealership_name]
            
            logger.info(f"Stopped scraper for {dealership_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop scraper for {dealership_name}: {e}")
            return False
            
    def stop_all_scrapers(self):
        """Stop all active scrapers"""
        for dealership_name in list(self.scrapers.keys()):
            self.stop_scraper(dealership_name)
            
    def get_scraper_status(self, dealership_name: str) -> Optional[Dict]:
        """Get status of specific scraper"""
        if dealership_name in self.scrapers:
            return self.scrapers[dealership_name].get_status()
        return None
        
    def get_all_scrapers_status(self) -> Dict[str, Dict]:
        """Get status of all scrapers"""
        status = {}
        for dealership_name, scraper in self.scrapers.items():
            status[dealership_name] = scraper.get_status()
        return status
        
    def cleanup_completed_scrapers(self):
        """Remove completed scrapers from active list"""
        completed = []
        for dealership_name, scraper in self.scrapers.items():
            if scraper.is_complete():
                completed.append(dealership_name)
                
        for dealership_name in completed:
            logger.info(f"Cleaning up completed scraper: {dealership_name}")
            del self.scrapers[dealership_name]
            
    def get_recent_output(self, dealership_name: str, max_lines: int = 50) -> List[Dict]:
        """Get recent output from a specific scraper"""
        if dealership_name not in self.scrapers:
            return []
            
        scraper = self.scrapers[dealership_name]
        output_lines = []
        
        # Get output from queue (non-blocking)
        while not scraper.output_queue.empty() and len(output_lines) < max_lines:
            try:
                output_lines.append(scraper.output_queue.get_nowait())
            except queue.Empty:
                break
                
        return output_lines


# Global scraper manager instance
scraper_manager = ScraperManager()

if __name__ == "__main__":
    # Test the scraper manager
    def output_callback(output_msg):
        print(f"[{output_msg['timestamp']}] {output_msg['dealership']}: {output_msg['message']}")
        
    scraper_manager.add_output_callback(output_callback)
    
    # Start test scraper
    if scraper_manager.start_scraper("Columbia Honda"):
        print("Scraper started successfully")
        
        # Monitor for 30 seconds
        for i in range(30):
            time.sleep(1)
            status = scraper_manager.get_scraper_status("Columbia Honda")
            if status:
                print(f"Status: {status['status']}, Vehicles: {status['vehicles_scraped']}, Pages: {status['pages_processed']}")
                
        scraper_manager.stop_scraper("Columbia Honda")
    else:
        print("Failed to start scraper")