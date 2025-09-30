#!/usr/bin/env python3

import sys
import re
import json
from bs4 import BeautifulSoup
sys.path.append('.')
from scrapers.joemachensnissan import JOEMACHENSNISSAN

# Test URL from the output data
test_url = "https://www.joemachensnissan.com/inventory/new-2025-nissan-murano-sl-awd-crossover-5n1az3cs4sc110149/"

print(f"[DEBUG] Testing Joe Machens Nissan page: {test_url}")

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

    for i, script in enumerate(script_tags):
        if script.string:
            script_content = script.string.strip()

            # Check for common vehicle data patterns
            if any(pattern in script_content for pattern in ['vin', 'VIN', 'vehicle', 'Vehicle', 'year', 'make', 'model']):
                print(f"\n[SCRIPT {i}] Contains vehicle data patterns:")

                # Show first 500 chars to see structure
                print("First 500 chars:", script_content[:500])
                print("...")
                print("Last 500 chars:", script_content[-500:])

                # Look for specific patterns
                vin_matches = re.findall(r'["\']?[A-HJ-NPR-Z0-9]{17}["\']?', script_content)
                if vin_matches:
                    print(f"VIN matches found: {vin_matches}")

                year_matches = re.findall(r'["\']?year["\']?\s*:\s*["\']?(\d{4})["\']?', script_content, re.IGNORECASE)
                if year_matches:
                    print(f"Year matches found: {year_matches}")

                make_matches = re.findall(r'["\']?make["\']?\s*:\s*["\']([^"\']+)["\']', script_content, re.IGNORECASE)
                if make_matches:
                    print(f"Make matches found: {make_matches}")

                model_matches = re.findall(r'["\']?model["\']?\s*:\s*["\']([^"\']+)["\']', script_content, re.IGNORECASE)
                if model_matches:
                    print(f"Model matches found: {model_matches}")

                print("-" * 50)

    print("\n[DEBUG] Examining page title for vehicle info:")
    title_element = page_soup.find('title')
    if title_element:
        title_text = title_element.text
        print(f"Title: {title_text}")

        # Parse title
        if '|' in title_text:
            vehicle_info = title_text.split('|')[0].strip()
            parts = vehicle_info.split()
            print(f"Vehicle info parts: {parts}")
            if len(parts) >= 3 and parts[0].isdigit():
                print(f"Parsed - Year: {parts[0]}, Make: {parts[1]}, Model: {' '.join(parts[2:])}")

    print("\n[DEBUG] Looking for meta tags with vehicle data:")
    meta_tags = page_soup.find_all('meta')
    for meta in meta_tags:
        content = meta.get('content', '')
        name = meta.get('name', '')
        prop = meta.get('property', '')

        if any(keyword in content.lower() for keyword in ['vin', 'year', 'make', 'model', 'nissan']):
            print(f"Meta tag - Name: {name}, Property: {prop}, Content: {content}")

    print("\n[DEBUG] Looking for data attributes and structured data:")
    # Look for elements with data-* attributes
    elements_with_data = page_soup.find_all(attrs={"data-vin": True})
    if elements_with_data:
        print("Found elements with data-vin:")
        for elem in elements_with_data:
            print(f"  {elem.name}: {elem.get('data-vin')}")

    # Look for JSON-LD structured data
    json_ld_scripts = page_soup.find_all('script', type='application/ld+json')
    if json_ld_scripts:
        print("\n[DEBUG] Found JSON-LD scripts:")
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                print("JSON-LD data:", json.dumps(data, indent=2)[:1000])
            except:
                print("Could not parse JSON-LD")

    # Close driver
    scraper.interface.close_driver()

    print("\n[SUCCESS] Debug completed")

except Exception as e:
    print(f"[ERROR] Debug failed: {e}")
    import traceback
    traceback.print_exc()