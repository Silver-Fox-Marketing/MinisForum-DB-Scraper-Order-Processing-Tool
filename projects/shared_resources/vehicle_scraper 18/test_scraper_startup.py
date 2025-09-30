#!/usr/bin/env python3

import sys
sys.path.append('.')
from scrapers.joemachensnissan import JOEMACHENSNISSAN

print("[TEST] Testing scraper startup and initialization...")

try:
    # Create scraper instance exactly like the main scraper
    scraper = JOEMACHENSNISSAN("output_data/2025-09-26/", "test_startup.csv")
    print("[SUCCESS] Scraper instance created")

    # Test just the header initialization part
    print("[TEST] Testing CSV header initialization...")
    scraper.helper.writing_output_file_header([
        'Vin',
        'Stock',
        'Type',
        'Year',
        'Make',
        'Model',
        'Trim',
        'Ext Color',
        'Status',
        'Price',
        'Body Style',
        'Fuel Type',
        'MSRP',
        'Date In Stock',
        'Street Address',
        'Locality',
        'Postal Code',
        'Region',
        'Country',
        'Location',
        'Vechile URL'
    ], "output_data/2025-09-26/test_startup.csv")
    print("[SUCCESS] CSV headers written")

    # Check if file was created
    import os
    if os.path.exists("output_data/2025-09-26/test_startup.csv"):
        print("[SUCCESS] CSV file created")
        with open("output_data/2025-09-26/test_startup.csv", 'r') as f:
            content = f.read()
            print(f"File content: {content}")
    else:
        print("[ERROR] CSV file not created")

    print("[TEST] Testing scraper startup method (without running full scrape)...")

    # Don't actually run the scraper, just see if we can get to the setup part
    print("[INFO] Would start scraping here...")

except Exception as e:
    print(f"[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()