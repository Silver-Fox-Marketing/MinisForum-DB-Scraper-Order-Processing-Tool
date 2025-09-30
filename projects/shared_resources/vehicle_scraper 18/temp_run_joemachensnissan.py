
import sys
sys.path.append('.')
from scrapers.joemachensnissan import *
from scrapers.helper_class import Helper
import datetime
import os

try:
    # Initialize helper and set up paths (like main.py does)
    helper = Helper()
    data_folder = 'C:/Users/Workstation_1/Documents/Tools/ClaudeCode/projects/shared_resources/vehicle_scraper 18/output_data/2025-09-26/'

    # Create the scraper class name (uppercase version)
    class_name = 'JOEMACHENSNISSAN'

    # Get the class and instantiate it
    scraper_class = globals()[class_name]
    output_file = data_folder + 'joemachensnissan_vehicles.csv'

    print(f'[START] Starting {class_name} scraper')
    print(f'[OUTPUT] Data will be saved to: {output_file}')

    # Instantiate and run the scraper
    scraper_instance = scraper_class(data_folder, output_file)
    scraper_instance.start_scraping_joemachensnissan()

    print('[SUCCESS] Scraper completed successfully')

except Exception as e:
    print(f'[ERROR] Scraper failed: {str(e)}')
    import traceback
    traceback.print_exc()
    raise
