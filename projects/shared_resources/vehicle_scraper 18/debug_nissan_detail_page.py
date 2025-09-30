"""
Debug script to examine Joe Machens Nissan vehicle detail page structure
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.interface_class import INTERFACING
import time

def debug_vehicle_page():
    """Debug a single vehicle detail page to understand the structure"""

    interface = INTERFACING()
    interface.get_driver()

    # Test URL from our successful listing
    test_url = "https://www.joemachensnissan.com/inventory/new-2025-nissan-kicks-sr-awd-crossover-3n8ap6db9sl365043/"

    print(f"[DEBUG] Loading vehicle detail page: {test_url}")
    interface.driver.get(test_url)
    time.sleep(10)  # Wait for page to load

    # Get page source
    page_source = interface.driver.page_source

    print(f"[DEBUG] Page title: {interface.driver.title}")
    print(f"[DEBUG] Page source length: {len(page_source)}")

    # Check for various script patterns
    soup = interface.make_soup()

    # Look for script tags
    scripts = soup.find_all('script')
    print(f"[DEBUG] Found {len(scripts)} script tags")

    # Check for specific patterns
    patterns_to_check = [
        'shift_digital_session_id',
        'vehicle_vin',
        'vehicle_stock',
        'dataLayer',
        'gtag',
        'vehicle',
        'inventory'
    ]

    found_patterns = {}
    for pattern in patterns_to_check:
        found_patterns[pattern] = []

    for i, script in enumerate(scripts):
        script_text = script.get_text()
        if script_text:
            for pattern in patterns_to_check:
                if pattern in script_text:
                    found_patterns[pattern].append(i)

    print("\n[DEBUG] Pattern analysis:")
    for pattern, script_indices in found_patterns.items():
        if script_indices:
            print(f"  - {pattern}: Found in scripts {script_indices}")
        else:
            print(f"  - {pattern}: Not found")

    # Show content of scripts that might contain vehicle data
    for pattern in ['vehicle_vin', 'vehicle_stock', 'vehicle', 'dataLayer']:
        if found_patterns[pattern]:
            script_idx = found_patterns[pattern][0]
            script_content = scripts[script_idx].get_text()
            print(f"\n[DEBUG] Script {script_idx} content (first 500 chars):")
            print(script_content[:500])
            print("..." if len(script_content) > 500 else "")

    # Look for JSON-LD structured data
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    print(f"\n[DEBUG] Found {len(json_ld_scripts)} JSON-LD scripts")

    for i, script in enumerate(json_ld_scripts):
        print(f"[DEBUG] JSON-LD script {i} content (first 300 chars):")
        print(script.get_text()[:300])
        print("..." if len(script.get_text()) > 300 else "")

    # Look for meta tags with vehicle info
    meta_tags = soup.find_all('meta')
    vehicle_meta = []
    for meta in meta_tags:
        if meta.get('name') or meta.get('property'):
            name_or_prop = meta.get('name') or meta.get('property')
            if any(keyword in name_or_prop.lower() for keyword in ['vehicle', 'car', 'auto', 'vin']):
                vehicle_meta.append(meta)

    print(f"\n[DEBUG] Found {len(vehicle_meta)} vehicle-related meta tags:")
    for meta in vehicle_meta[:5]:  # Show first 5
        print(f"  - {meta}")

    interface.close_driver()

if __name__ == "__main__":
    debug_vehicle_page()