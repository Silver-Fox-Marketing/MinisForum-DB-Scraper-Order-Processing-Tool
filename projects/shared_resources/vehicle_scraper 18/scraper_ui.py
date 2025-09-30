#!/usr/bin/env python3
"""
Scraper UI - Web interface for selecting and running vehicle scrapers
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import glob
import subprocess
import threading
import time
import json
from datetime import datetime

app = Flask(__name__)

class ScraperManager:
    def __init__(self, scrapers_dir):
        self.scrapers_dir = scrapers_dir
        self.running_scrapers = {}
        self.scraper_logs = {}

    def get_available_scrapers(self):
        """Get list of all available scrapers"""
        scrapers = []
        pattern = os.path.join(self.scrapers_dir, "*.py")

        for file_path in glob.glob(pattern):
            filename = os.path.basename(file_path)

            # Skip utility files
            if filename in ['helper_class.py', 'interface_class.py', '__init__.py']:
                continue

            # Skip old versions
            if '_old.py' in filename:
                continue

            # Convert filename to readable name
            scraper_name = filename.replace('.py', '')
            display_name = self.format_display_name(scraper_name)

            scrapers.append({
                'name': scraper_name,
                'display_name': display_name,
                'filename': filename,
                'status': 'ready',
                'last_run': None
            })

        return sorted(scrapers, key=lambda x: x['display_name'])

    def format_display_name(self, scraper_name):
        """Convert snake_case scraper names to readable format"""
        # Handle special cases
        replacements = {
            'bmwofweststlouis': 'BMW of West St. Louis',
            'joemachensnissan': 'Joe Machens Nissan',
            'joemachenstoyota': 'Joe Machens Toyota',
            'joemachenshyundai': 'Joe Machens Hyundai',
            'joemachenscdjr': 'Joe Machens CDJR',
            'audiranchomirage': 'Audi Ranch Mirage',
            'landroverranchomirage': 'Land Rover Ranch Mirage',
            'jaguarranchomirage': 'Jaguar Ranch Mirage',
            'columbiabmw': 'Columbia BMW',
            'columbiahonda': 'Columbia Honda',
            'hwkia': 'HW Kia',
            'wcvolvocars': 'WC Volvo Cars',
        }

        if scraper_name in replacements:
            return replacements[scraper_name]

        # Generic formatting for others
        words = []
        current_word = ""

        for char in scraper_name:
            if char.isupper() and current_word:
                words.append(current_word)
                current_word = char
            else:
                current_word += char

        if current_word:
            words.append(current_word)

        return ' '.join(word.capitalize() for word in words)

    def run_scraper(self, scraper_name):
        """Run a specific scraper"""
        if scraper_name in self.running_scrapers:
            return False, "Scraper is already running"

        # Use the original date-based folder naming convention with absolute path
        today = datetime.now().strftime('%Y-%m-%d')
        working_dir = self.scrapers_dir.replace('/scrapers', '').replace('\\scrapers', '')
        output_dir = os.path.join(working_dir, 'output_data', today)
        os.makedirs(output_dir, exist_ok=True)

        # Create log folder
        log_dir = os.path.join(output_dir, 'log')
        os.makedirs(log_dir, exist_ok=True)

        # Create a Python script that imports and runs the specific scraper
        # This mimics what main.py does but for individual scrapers
        # Convert Windows paths to use forward slashes to avoid escape sequence issues
        safe_output_dir = output_dir.replace('\\', '/')

        runner_script = f"""
import sys
sys.path.append('.')
from scrapers.{scraper_name} import *
from scrapers.helper_class import Helper
import datetime
import os

try:
    # Initialize helper and set up paths (like main.py does)
    helper = Helper()
    data_folder = '{safe_output_dir}/'

    # Create the scraper class name (uppercase version)
    class_name = '{scraper_name.upper()}'

    # Get the class and instantiate it
    scraper_class = globals()[class_name]
    output_file = data_folder + '{scraper_name}_vehicles.csv'

    print(f'[START] Starting {{class_name}} scraper')
    print(f'[OUTPUT] Data will be saved to: {{output_file}}')

    # Instantiate and run the scraper
    scraper_instance = scraper_class(data_folder, output_file)
    scraper_instance.start_scraping_{scraper_name}()

    print('[SUCCESS] Scraper completed successfully')

except Exception as e:
    print(f'[ERROR] Scraper failed: {{str(e)}}')
    import traceback
    traceback.print_exc()
    raise
"""

        # Write the runner script to a temporary file in the correct working directory
        working_dir = self.scrapers_dir.replace('/scrapers', '').replace('\\scrapers', '')
        temp_script = f"temp_run_{scraper_name}.py"
        temp_script_path = os.path.join(working_dir, temp_script)

        with open(temp_script_path, 'w') as f:
            f.write(runner_script)

        # Create the command to run the temporary script with full Python path
        cmd = ["C:\\Users\\Workstation_1\\AppData\\Local\\Programs\\Python\\Python311\\python.exe", temp_script]

        try:
            # Start the scraper process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=working_dir
            )

            self.running_scrapers[scraper_name] = {
                'process': process,
                'start_time': datetime.now(),
                'output_dir': output_dir,
                'status': 'running',
                'temp_script': temp_script_path
            }

            # Start thread to monitor the process
            monitor_thread = threading.Thread(
                target=self._monitor_scraper,
                args=(scraper_name, process)
            )
            monitor_thread.daemon = True
            monitor_thread.start()

            return True, f"Scraper started. Output will be saved to {output_dir}"

        except Exception as e:
            return False, f"Failed to start scraper: {str(e)}"

    def _monitor_scraper(self, scraper_name, process):
        """Monitor a running scraper process"""
        logs = []

        try:
            logs.append({
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'message': f'[START] Starting {scraper_name} scraper...'
            })
            self.scraper_logs[scraper_name] = logs

            # Wait for process to complete
            stdout, stderr = process.communicate()

            # Process stdout
            if stdout:
                for line in stdout.split('\n'):
                    line = line.strip()
                    if line:
                        logs.append({
                            'timestamp': datetime.now().strftime('%H:%M:%S'),
                            'message': line
                        })

            # Process stderr
            if stderr:
                for line in stderr.split('\n'):
                    line = line.strip()
                    if line:
                        logs.append({
                            'timestamp': datetime.now().strftime('%H:%M:%S'),
                            'message': f'[ERROR] {line}'
                        })

            # Keep only last 100 log lines
            if len(logs) > 100:
                logs = logs[-100:]

            self.scraper_logs[scraper_name] = logs

            # Update status
            if scraper_name in self.running_scrapers:
                self.running_scrapers[scraper_name]['status'] = 'completed' if process.returncode == 0 else 'failed'

                # Add final status message
                final_message = '[SUCCESS] Scraper completed successfully' if process.returncode == 0 else f'[ERROR] Scraper failed with code {process.returncode}'
                logs.append({
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'message': final_message
                })
                self.scraper_logs[scraper_name] = logs

                # Clean up temporary script
                temp_script = self.running_scrapers[scraper_name].get('temp_script')
                if temp_script and os.path.exists(temp_script):
                    try:
                        os.remove(temp_script)
                    except:
                        pass  # Don't fail if cleanup fails

        except Exception as e:
            if scraper_name in self.running_scrapers:
                self.running_scrapers[scraper_name]['status'] = 'failed'

                # Clean up temporary script on error too
                temp_script = self.running_scrapers[scraper_name].get('temp_script')
                if temp_script and os.path.exists(temp_script):
                    try:
                        os.remove(temp_script)
                    except:
                        pass

            logs.append({
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'message': f'[ERROR] Monitor exception: {str(e)}'
            })
            self.scraper_logs[scraper_name] = logs

    def get_scraper_status(self, scraper_name):
        """Get current status of a scraper"""
        if scraper_name in self.running_scrapers:
            return self.running_scrapers[scraper_name]['status']
        return 'ready'

    def get_scraper_logs(self, scraper_name):
        """Get logs for a specific scraper"""
        return self.scraper_logs.get(scraper_name, [])

    def stop_scraper(self, scraper_name):
        """Stop a running scraper"""
        if scraper_name in self.running_scrapers:
            process = self.running_scrapers[scraper_name]['process']
            try:
                process.terminate()
                del self.running_scrapers[scraper_name]
                return True, "Scraper stopped"
            except Exception as e:
                return False, f"Failed to stop scraper: {str(e)}"
        return False, "Scraper is not running"

# Initialize scraper manager
scrapers_dir = os.path.join(os.path.dirname(__file__), 'scrapers')
scraper_manager = ScraperManager(scrapers_dir)

@app.route('/')
def index():
    """Main page with scraper selection"""
    scrapers = scraper_manager.get_available_scrapers()
    return render_template('index.html', scrapers=scrapers)

@app.route('/run_scrapers', methods=['POST'])
def run_scrapers():
    """Run selected scrapers"""
    selected_scrapers = request.form.getlist('scrapers')

    if not selected_scrapers:
        return redirect(url_for('index', error='Please select at least one scraper'))

    results = []
    for scraper_name in selected_scrapers:
        success, message = scraper_manager.run_scraper(scraper_name)
        results.append({
            'scraper': scraper_name,
            'success': success,
            'message': message
        })

    return render_template('results.html', results=results)

@app.route('/status/<scraper_name>')
def get_status(scraper_name):
    """Get status of a specific scraper (AJAX endpoint)"""
    status = scraper_manager.get_scraper_status(scraper_name)
    logs = scraper_manager.get_scraper_logs(scraper_name)

    return jsonify({
        'status': status,
        'logs': logs[-10:] if logs else []  # Last 10 log entries
    })

@app.route('/stop/<scraper_name>', methods=['POST'])
def stop_scraper(scraper_name):
    """Stop a running scraper"""
    success, message = scraper_manager.stop_scraper(scraper_name)
    return jsonify({
        'success': success,
        'message': message
    })

@app.route('/logs/<scraper_name>')
def view_logs(scraper_name):
    """View detailed logs for a scraper"""
    logs = scraper_manager.get_scraper_logs(scraper_name)
    status = scraper_manager.get_scraper_status(scraper_name)

    return render_template('logs.html',
                         scraper_name=scraper_name,
                         logs=logs,
                         status=status)

if __name__ == '__main__':
    # Create output directory if it doesn't exist
    os.makedirs('output_data', exist_ok=True)

    print("Starting Scraper UI...")
    print("Access the interface at: http://localhost:5000")

    app.run(debug=True, host='0.0.0.0', port=5000)