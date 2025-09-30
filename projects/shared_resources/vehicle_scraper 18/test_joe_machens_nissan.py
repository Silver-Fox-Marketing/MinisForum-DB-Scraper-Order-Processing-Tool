"""
Test script for Joe Machens Nissan scraper
Tests the updated scraper to ensure it properly extracts vehicle data
"""

import sys
import os

# Add the current directory to path so we can import scrapers
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.joemachensnissan import JOEMACHENSNISSAN

def test_single_page():
    """Test scraping a single vehicle detail page"""
    print("[TEST] Testing Joe Machens Nissan scraper with single vehicle page")
    print("-" * 70)

    # Initialize scraper
    scraper = JOEMACHENSNISSAN(
        data_folder="test_output/",
        output_file="test_joe_machens_nissan.csv"
    )

    # Test URL extraction for a single page
    print("[TEST] Testing vehicle listing URL extraction...")
    vehicle_urls = scraper.get_vehicle_listing_urls('new', 1)

    if vehicle_urls:
        print(f"[SUCCESS] Found {len(vehicle_urls)} vehicle URLs")

        # Test processing the first vehicle
        if len(vehicle_urls) > 0:
            test_url = vehicle_urls[0]
            print(f"[TEST] Testing vehicle detail extraction for: {test_url}")

            vehicle_data = scraper.process_vehicle_detail_page(test_url)

            if vehicle_data:
                print("[SUCCESS] Successfully extracted vehicle data:")
                print(f"  - VIN: {vehicle_data.get('vin', 'N/A')}")
                print(f"  - Stock: {vehicle_data.get('stock', 'N/A')}")
                print(f"  - Year: {vehicle_data.get('year', 'N/A')}")
                print(f"  - Make: {vehicle_data.get('make', 'N/A')}")
                print(f"  - Model: {vehicle_data.get('model', 'N/A')}")
                print(f"  - Type: {vehicle_data.get('type', 'N/A')}")
                print(f"  - Price: {vehicle_data.get('price', 'N/A')}")

                # Test the processing method
                print("[TEST] Testing data output formatting...")
                vehicle_data['url'] = test_url
                scraper.processing_each_vehicle(vehicle_data)
                print("[SUCCESS] Vehicle data formatted and saved")
            else:
                print("[ERROR] Failed to extract vehicle data")
    else:
        print("[WARNING] No vehicle URLs found - site may be blocking or structure changed")

    # Clean up
    if scraper.interface.driver_initialized:
        scraper.interface.close_driver()

    print("-" * 70)
    print("[TEST] Test complete")

if __name__ == "__main__":
    test_single_page()