"""
Working Joe Machens Nissan scraper using Chrome driver approach
This replaces the API approach that was getting stuck
"""

def start_scraping_joemachensnissan(self):
    """
    Main scraping method using Chrome driver + Cloudflare bypass
    This replaces the broken API approach
    """
    processed_json_file = self.log_folder + 'vehicles_processed.json'
    processed_json_data = self.helper.json_exist_data(processed_json_file)

    print("[INIT] Starting Joe Machens Nissan scraper with Chrome driver approach...")

    # Initialize driver
    if not self.interface.driver_initialized:
        self.interface.get_driver()

    # Scrape different inventory types (focus on new first since that has 247 VINs)
    for inventory_type in ['new', 'used', 'certified']:
        print(f"[SCRAPE] Processing {inventory_type} vehicles...")

        page_num = 1
        while page_num <= 20:  # Up to 20 pages to capture all 247 VINs
            print(f"[PAGE] Getting {inventory_type} vehicles page {page_num}")

            try:
                # Get vehicle URLs from listing page using working Chrome driver method
                vehicle_urls = self.get_vehicle_listing_urls(inventory_type, page_num)

                if not vehicle_urls:
                    print(f"[DONE] No more vehicles found on page {page_num} for {inventory_type}")
                    break

                print(f"[FOUND] {len(vehicle_urls)} vehicles on page {page_num}")

                # Process each vehicle
                for i, vehicle_url in enumerate(vehicle_urls):
                    print(f"[VEHICLE] Processing {i+1}/{len(vehicle_urls)}: {vehicle_url}")

                    # Skip if already processed
                    if vehicle_url in processed_json_data:
                        print(f"[SKIP] Vehicle already processed")
                        continue

                    # Skip navigation/category URLs (only process inventory URLs)
                    if '/inventory/' not in vehicle_url:
                        print(f"[SKIP] Skipping non-inventory URL: {vehicle_url}")
                        continue

                    # Process individual vehicle detail page
                    vehicle_data = self.process_vehicle_detail_page(vehicle_url)

                    if vehicle_data:
                        # Convert to Toyota scraper format and save
                        self.processing_each_vehicle(vehicle_data)
                        processed_json_data.append(vehicle_url)
                        self.helper.write_json_file(processed_json_data, processed_json_file)
                        print(f"[SUCCESS] Saved: {vehicle_data.get('year', '')} {vehicle_data.get('make', '')} {vehicle_data.get('model', '')} - VIN: {vehicle_data.get('vin', '')}")
                    else:
                        print(f"[ERROR] Failed to extract data for {vehicle_url}")

                    # Small delay between vehicles
                    time.sleep(1)

                page_num += 1

            except Exception as e:
                print(f"[ERROR] Failed to process page {page_num} for {inventory_type}: {e}")
                break

        print(f"[COMPLETE] Finished processing {inventory_type} vehicles")

    # Close driver
    self.interface.close_driver()
    print("[COMPLETE] All vehicle types processed")


def processing_each_vehicle(self, vehicle_data):
    """
    Convert vehicle data to Toyota scraper format and save to CSV
    """
    if not vehicle_data:
        return

    # Map fields to Toyota scraper format
    csv_row = [
        vehicle_data.get('vin', ''),
        vehicle_data.get('stock', ''),
        vehicle_data.get('type', 'New'),
        vehicle_data.get('year', ''),
        vehicle_data.get('make', ''),
        vehicle_data.get('model', ''),
        vehicle_data.get('trim', ''),
        vehicle_data.get('exteriorColor', ''),
        'In-Stock',  # Status
        vehicle_data.get('price', ''),
        vehicle_data.get('bodyStyle', ''),
        vehicle_data.get('fuelType', ''),
        vehicle_data.get('msrp', ''),
        vehicle_data.get('dateInStock', ''),
        '1180 Vandiver Dr',  # Street address
        'Columbia',  # Locality
        '65202',  # Postal code
        'MO',  # Region
        'US',  # Country
        'Joe Machens Nissan',  # Location
        vehicle_data.get('url', '')
    ]

    # Write to output file
    self.helper.writing_output_file(csv_row, self.output_file)