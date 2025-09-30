#!/usr/bin/env python3

import sys
sys.path.append('.')
from scrapers.joemachensnissan import JOEMACHENSNISSAN

# Test the current extraction logic
test_url = "https://www.joemachensnissan.com/inventory/new-2025-nissan-murano-sl-awd-crossover-5n1az3cs4sc110149/"

print(f"[TEST] Testing current extraction logic for: {test_url}")

try:
    # Create scraper instance
    scraper = JOEMACHENSNISSAN("output_data/2025-09-26/", "test_output.csv")

    # Use the current process_vehicle_detail_page method
    result = scraper.process_vehicle_detail_page(test_url)

    print(f"\n[RESULT] Extracted data: {result}")

    if result:
        print("\n[ANALYSIS] Fields extracted:")
        for key, value in result.items():
            print(f"  {key}: '{value}'")
    else:
        print("\n[ANALYSIS] No data extracted")

    # Close driver
    scraper.interface.close_driver()

except Exception as e:
    print(f"[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()