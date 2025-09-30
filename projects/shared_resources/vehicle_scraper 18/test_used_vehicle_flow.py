#!/usr/bin/env python3

import sys
import json
sys.path.append('.')
from scrapers.joemachensnissan import JOEMACHENSNISSAN

# Test with a Used vehicle URL from the CSV
test_url = "https://www.joemachensnissan.com/inventory/used-2023-nissan-pathfinder-s-4wd-4d-sport-utility-5n1dr3ac2pc265749/"

print(f"[TEST] Testing complete scraper flow for Used vehicle: {test_url}")

try:
    # Create scraper instance exactly like the main scraper
    scraper = JOEMACHENSNISSAN("output_data/2025-09-26/", "test_used_output.csv")

    print("\n[STEP 1] Testing process_vehicle_detail_page...")
    vehicle_data = scraper.process_vehicle_detail_page(test_url)
    print(f"Extracted vehicle_data: {vehicle_data}")

    if vehicle_data and vehicle_data.get('vin'):
        print(f"\n[STEP 2] Adding URL to vehicle_data...")
        vehicle_data['url'] = test_url
        print(f"Vehicle data with URL: {vehicle_data}")

        print(f"\n[STEP 3] Testing processing_each_vehicle...")
        print(f"About to call processing_each_vehicle with: {vehicle_data}")

        # Call processing_each_vehicle exactly like the main scraper does
        scraper.processing_each_vehicle(vehicle_data)
        print("[SUCCESS] processing_each_vehicle completed")

        print(f"\n[STEP 4] Checking output file...")
        # Read the output file to see what was written
        try:
            with open("output_data/2025-09-26/test_used_output.csv", 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
                print(f"Output file has {len(lines)} lines")
                for i, line in enumerate(lines):
                    print(f"Line {i}: {line.strip()}")
        except Exception as e:
            print(f"Error reading output file: {e}")

    else:
        print("[ERROR] No vehicle data extracted")

    # Close driver
    scraper.interface.close_driver()

    print("\n[COMPLETE] Test finished")

except Exception as e:
    print(f"[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()