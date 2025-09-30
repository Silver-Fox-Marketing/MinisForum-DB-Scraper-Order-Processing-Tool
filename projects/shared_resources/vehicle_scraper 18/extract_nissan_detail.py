"""
Standalone script to extract vehicle details from Joe Machens Nissan detail page
Using JSON-LD structured data approach
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.interface_class import INTERFACING
import json
import time

def extract_vehicle_data():
    """Extract vehicle data from JSON-LD structured data"""

    interface = INTERFACING()
    interface.get_driver()

    # Test URL from our successful listing
    test_url = "https://www.joemachensnissan.com/inventory/new-2025-nissan-kicks-sr-awd-crossover-3n8ap6db9sl365043/"

    print(f"[EXTRACT] Loading vehicle detail page: {test_url}")
    interface.driver.get(test_url)
    time.sleep(10)  # Wait for page to load

    soup = interface.make_soup()

    # Find JSON-LD scripts
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    print(f"[EXTRACT] Found {len(json_ld_scripts)} JSON-LD scripts")

    vehicle_data = None
    for i, script in enumerate(json_ld_scripts):
        try:
            json_data = json.loads(script.get_text())
            print(f"[EXTRACT] JSON-LD script {i} type: {json_data.get('@type', 'unknown')}")

            # Look for Car/Product type with vehicle information
            if isinstance(json_data, dict) and json_data.get('@type'):
                types = json_data.get('@type', [])
                if isinstance(types, str):
                    types = [types]
                if 'Car' in types or 'Product' in types:
                    vehicle_data = json_data
                    print(f"[SUCCESS] Found vehicle data in JSON-LD script {i}")
                    break
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse JSON-LD script {i}: {e}")
            continue

    if vehicle_data:
        print("\n[VEHICLE DATA] Extracted vehicle information:")

        # Extract key vehicle information
        fields_to_extract = {
            'name': 'name',
            'vin': 'vehicleIdentificationNumber',
            'model': 'model',
            'brand': 'brand',
            'year': 'vehicleModelDate',
            'price': 'price',
            'stock': '@id',
            'mileage': 'mileageFromOdometer',
            'bodyType': 'bodyType',
            'fuelType': 'fuelType',
            'offers': 'offers'
        }

        extracted_data = {}
        for field, json_key in fields_to_extract.items():
            if json_key in vehicle_data:
                value = vehicle_data[json_key]
                if isinstance(value, dict) and 'name' in value:
                    # Brand/model objects often have name property
                    value = value['name']
                elif isinstance(value, list) and len(value) > 0:
                    # Some fields are arrays, take first item
                    value = value[0]
                    if isinstance(value, dict) and 'name' in value:
                        value = value['name']
                extracted_data[field] = value
                print(f"  - {field}: {value}")

        # Show the full JSON structure for reference
        print(f"\n[FULL JSON] Complete vehicle data structure:")
        print(json.dumps(vehicle_data, indent=2))

    else:
        print("[ERROR] Could not find vehicle data in any JSON-LD script")

    interface.close_driver()
    return extracted_data if vehicle_data else None

if __name__ == "__main__":
    extract_vehicle_data()