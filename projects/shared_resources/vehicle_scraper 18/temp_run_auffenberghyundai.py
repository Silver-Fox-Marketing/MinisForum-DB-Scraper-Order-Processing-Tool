
import sys
import os

# Set up the environment for the scrapers package
original_cwd = os.getcwd()
scraper_root = os.getcwd()  # Should be the vehicle_scraper 18 directory

# Add the parent directory to Python path to allow 'scrapers' package import
sys.path.insert(0, scraper_root)

try:
    # Import the scrapers package and specific scraper
    from scrapers import auffenberghyundai

    # Initialize data
    data_folder = 'C:/Users/Workstation_1/Documents/Tools/ClaudeCode/projects/shared_resources/vehicle_scraper 18/output_data/2025-09-27/'
    output_file = 'C:/Users/Workstation_1/Documents/Tools/ClaudeCode/projects/shared_resources/vehicle_scraper 18/output_data/2025-09-27/auffenberghyundai_vehicles.csv'

    # Create the scraper class name (uppercase version)
    class_name = 'AUFFENBERGHYUNDAI'

    # Get the class from the module
    scraper_class = getattr(auffenberghyundai, class_name)

    print(f'[START] Starting {class_name} scraper')
    print(f'[OUTPUT] Data will be saved to: {output_file}')

    # Instantiate and run the scraper
    scraper_instance = scraper_class(data_folder, output_file)

    # Run the scraper method
    scraper_method = getattr(scraper_instance, f'start_scraping_auffenberghyundai')
    scraper_method()

    print('[SUCCESS] Scraper completed successfully')

except Exception as e:
    print(f'[ERROR] Scraper failed: {str(e)}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    # Restore original working directory
    if original_cwd != os.getcwd():
        os.chdir(original_cwd)
