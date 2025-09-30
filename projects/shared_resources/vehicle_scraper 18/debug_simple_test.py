"""
Simple debug test to see what's happening with Joe Machens Nissan
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.joemachensnissan import JOEMACHENSNISSAN

def simple_test():
    print("[DEBUG] Starting simple Joe Machens Nissan test...")

    scraper = JOEMACHENSNISSAN('test_output/', 'test.csv')

    print("[DEBUG] Testing new vehicles page 1...")
    vehicle_urls = scraper.get_vehicle_listing_urls('new', 1)

    print(f"[DEBUG] Found {len(vehicle_urls) if vehicle_urls else 0} vehicle URLs")

    if vehicle_urls:
        print("[DEBUG] Sample URLs found:")
        for i, url in enumerate(vehicle_urls[:5]):  # Show first 5
            print(f"  {i+1}. {url}")
    else:
        print("[DEBUG] No vehicle URLs found - this is the problem!")

    # Close driver
    if scraper.interface.driver_initialized:
        scraper.interface.close_driver()

if __name__ == "__main__":
    simple_test()