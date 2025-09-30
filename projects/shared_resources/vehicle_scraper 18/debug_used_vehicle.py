#!/usr/bin/env python3

import sys
import re
import json
from bs4 import BeautifulSoup
sys.path.append('.')
from scrapers.joemachensnissan import JOEMACHENSNISSAN

# Test URL for a Used vehicle from the CSV
test_url = "https://www.joemachensnissan.com/inventory/used-2023-nissan-pathfinder-s-4wd-4d-sport-utility-5n1dr3ac2pc265749/"

print(f"[DEBUG] Testing Used vehicle page: {test_url}")

try:
    # Create scraper instance
    scraper = JOEMACHENSNISSAN("output_data/2025-09-26/", "test_output.csv")

    # Get the page
    soup = scraper.interface.get_selenium_response(test_url)
    page_soup = scraper.interface.make_soup()

    print("\n[DEBUG] Page title:", page_soup.find('title').text if page_soup.find('title') else "No title found")

    # Look for all script tags
    script_tags = page_soup.find_all('script')
    print(f"\n[DEBUG] Found {len(script_tags)} script tags")

    found_patterns = []

    for i, script in enumerate(script_tags):
        if script.string:
            script_content = script.string.strip()

            # Check for the patterns we know about
            if 'DITagLocalization' in script_content and 'vehicleInfo' in script_content:
                found_patterns.append(f"SCRIPT {i}: DITagLocalization with vehicleInfo")
                # Extract sample data
                vehicle_info_match = re.search(r'"vehicleInfo":\s*(\{[^}]+\})', script_content)
                if vehicle_info_match:
                    print(f"\n[FOUND] DITagLocalization vehicleInfo: {vehicle_info_match.group(1)}")

            elif 'inventory_localization' in script_content and '"vehicle"' in script_content:
                found_patterns.append(f"SCRIPT {i}: inventory_localization with vehicle data")
                # Show sample
                print(f"\n[FOUND] inventory_localization script (first 500 chars): {script_content[:500]}")

            elif 'accutradeObj' in script_content and '"vehicle"' in script_content:
                found_patterns.append(f"SCRIPT {i}: accutradeObj with vehicle data")
                vehicle_match = re.search(r'"vehicle":\s*(\{[^}]+\})', script_content)
                if vehicle_match:
                    print(f"\n[FOUND] accutradeObj vehicle: {vehicle_match.group(1)}")

            # Look for any VIN patterns
            elif re.search(r'["\']vin["\']\s*:\s*["\'][A-HJ-NPR-Z0-9]{17}["\']', script_content):
                found_patterns.append(f"SCRIPT {i}: Contains VIN pattern")
                vin_matches = re.findall(r'["\']vin["\']\s*:\s*["\']([A-HJ-NPR-Z0-9]{17})["\']', script_content)
                print(f"\n[FOUND] VIN patterns in script {i}: {vin_matches}")

    print(f"\n[SUMMARY] Found patterns: {found_patterns}")

    # Test current extraction
    print(f"\n[TEST] Testing current extraction method:")
    result = scraper.process_vehicle_detail_page(test_url)
    print(f"Result: {result}")

    # Close driver
    scraper.interface.close_driver()

    print("\n[SUCCESS] Debug completed")

except Exception as e:
    print(f"[ERROR] Debug failed: {e}")
    import traceback
    traceback.print_exc()