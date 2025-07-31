"""
BMW of West St. Louis Real Working Scraper
Imported from Scraper 18 system - July 30, 2025

Direct integration using exact working logic from scraper 18.
Uses Algolia search API to retrieve live vehicle inventory.
"""

import json
import requests
import time
from typing import List, Dict, Any
from datetime import datetime

class BMWOfWestStLouisRealScraper:
    """Real working scraper for BMW of West St. Louis using exact scraper 18 logic"""
    
    def __init__(self, progress_callback=None):
        self.dealer_name = "BMW of West St. Louis"
        self.progress_callback = progress_callback
        self.total_processed = 0
        
        # Algolia API configuration (exact from scraper 18)
        self.algolia_url = "https://sewjn80htn-dsn.algolia.net/1/indexes/*/queries"
        self.algolia_params = {
            'x-algolia-agent': 'Algolia%20for%20JavaScript%20(4.9.1)%3B%20Browser%20(lite)%3B%20JS%20Helper%20(3.22.4)',
            'x-algolia-api-key': '179608f32563367799314290254e3e44',
            'x-algolia-application-id': 'SEWJN80HTN'
        }
        
        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
        }
        
        # BMW location information
        self.location_info = {
            'street_addr': '14417 Manchester Rd.',
            'locality': 'Manchester',
            'postal_code': '63011',
            'region': 'MO',
            'country': 'US',
            'location': 'BMW of West St Louis'
        }
        
        self.log("BMW of West St. Louis scraper initialized")

    def log(self, message):
        """Send log message via progress callback"""
        if self.progress_callback:
            self.progress_callback(message)
        print(f"[BMW West StL] {message}")

    def get_vehicles_by_mode(self, page_num: int, mode: str) -> Dict[str, Any]:
        """Get vehicles from Algolia API by mode (new, used, certified)"""
        
        url = f"{self.algolia_url}?{self.algolia_params['x-algolia-agent']}&{self.algolia_params['x-algolia-api-key']}&{self.algolia_params['x-algolia-application-id']}"
        
        # Build payload based on mode (exact logic from scraper 18)
        if mode == 'used':
            payload = json.dumps({
                "requests": [{
                    "indexName": "bmwofweststlouis-sbm0125_production_inventory_specials_oem_price",
                    "params": f"facetFilters=%5B%5B%22Location%3ABMW%20of%20West%20St.%20Louis%3Cbr%3E%3Ca%20href%3D%5C%22https%3A%2F%2Fmaps.app.goo.gl%2FQyXQWdf6BV6jobY18%5C%22%20target%3D%5C%22_blank%5C%22%3E14417%20Manchester%20Road%3Cbr%3EManchester%2C%20MO%2063011%3C%2Fa%3E%3Cbr%3E%3Ca%20href%3D%5C%22tel%3A888-291-4102%5C%22%3E888-291-4102%3C%2Fa%3E%22%5D%2C%5B%22type%3ACertified%20Pre-Owned%22%2C%22type%3APre-Owned%22%5D%5D&facets=%5B%22make%22%2C%22model%22%2C%22type%22%2C%22year%22%2C%22price%22%5D&hitsPerPage=20&maxValuesPerFacet=250&page={page_num}"
                }]
            })
        elif mode == 'certified':
            payload = json.dumps({
                "requests": [{
                    "indexName": "bmwofweststlouis-sbm0125_production_inventory_specials_oem_price",
                    "params": f"facetFilters=%5B%5B%22Location%3ABMW%20of%20West%20St.%20Louis%3Cbr%3E%3Ca%20href%3D%5C%22https%3A%2F%2Fmaps.app.goo.gl%2FQyXQWdf6BV6jobY18%5C%22%20target%3D%5C%22_blank%5C%22%3E14417%20Manchester%20Road%3Cbr%3EManchester%2C%20MO%2063011%3C%2Fa%3E%3Cbr%3E%3Ca%20href%3D%5C%22tel%3A888-291-4102%5C%22%3E888-291-4102%3C%2Fa%3E%22%5D%2C%5B%22make%3ABMW%22%5D%2C%5B%22type%3ACertified%20Pre-Owned%22%5D%5D&facets=%5B%22make%22%2C%22model%22%2C%22type%22%2C%22year%22%2C%22price%22%5D&hitsPerPage=20&maxValuesPerFacet=250&page={page_num}"
                }]
            })
        else:  # new
            payload = json.dumps({
                "requests": [{
                    "indexName": "bmwofweststlouis-sbm0125_production_inventory_sort_image_type_price_lh",
                    "params": f"facetFilters=%5B%5B%22Location%3ABMW%20of%20West%20St.%20Louis%3Cbr%3E%3Ca%20href%3D%5C%22https%3A%2F%2Fmaps.app.goo.gl%2FQyXQWdf6BV6jobY18%5C%22%20target%3D%5C%22_blank%5C%22%3E14417%20Manchester%20Road%3Cbr%3EManchester%2C%20MO%2063011%3C%2Fa%3E%3Cbr%3E%3Ca%20href%3D%5C%22tel%3A888-291-4102%5C%22%3E888-291-4102%3C%2Fa%3E%22%5D%2C%5B%22type%3ANew%22%5D%5D&facets=%5B%22make%22%2C%22model%22%2C%22type%22%2C%22year%22%2C%22price%22%5D&hitsPerPage=20&maxValuesPerFacet=250&page={page_num}"
                }]
            })

        # Make API request with retry logic
        retry_count = 0
        while retry_count < 3:
            try:
                response = requests.post(self.algolia_url, headers=self.headers, data=payload, timeout=30)
                response.raise_for_status()
                return response.json()
            except Exception as error:
                self.log(f"Error getting vehicles (attempt {retry_count + 1}): {error}")
                retry_count += 1
                if retry_count < 3:
                    time.sleep(2)
        
        return {"results": [{"hits": [], "nbHits": 0, "nbPages": 0}]}

    def process_vehicle_data(self, vehicle_json: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual vehicle from API response - exact logic from scraper 18"""
        
        try:
            # Extract core vehicle data using exact scraper 18 logic
            vin = vehicle_json.get('objectID', '')
            stock = vehicle_json.get('stock', '')
            v_type = vehicle_json.get('type', '')

            # Handle certified pre-owned type conversion
            if 'Certified Pre-Owned' in v_type:
                v_type = 'Used'

            year = vehicle_json.get('year', '')
            make = vehicle_json.get('make', '')
            model = vehicle_json.get('model', '')
            trim = vehicle_json.get('trim', '')
            ext_color = vehicle_json.get('ext_color', '')
            status = ''
            price = vehicle_json.get('our_price', '')
            body = vehicle_json.get('body', '')
            fuel_type = vehicle_json.get('fueltype', '')
            msrp = vehicle_json.get('msrp', 0)

            # Handle price formatting
            if 'please call for price' in str(price).lower():
                price = 'Please call for price'

            # Handle MSRP
            if msrp:
                try:
                    msrp = int(msrp)
                except:
                    msrp = ''
            else:
                msrp = ''

            date_in_stock = vehicle_json.get('date_in_stock', '')
            vehicle_url = vehicle_json.get('link', '')

            # Create normalized vehicle record
            vehicle_data = {
                'vin': vin,
                'stock': stock,
                'dealer_name': self.dealer_name,
                'location': self.location_info['location'],
                'year': year,
                'make': make,
                'model': model,
                'trim': trim,
                'body_style': body,
                'exterior_color': ext_color,
                'interior_color': '',  # Not provided in API
                'engine': '',  # Not detailed in API response
                'transmission': '',  # Not detailed in API response
                'drivetrain': '',  # Not provided in API
                'mileage': 0,  # New cars typically 0, used cars not provided in list
                'price': price,
                'vehicle_type': v_type.lower() if v_type else '',
                'condition': 'new' if v_type == 'New' else 'used',
                'description': vehicle_json.get('title_vrp', ''),
                'features': fuel_type,  # Store fuel type in features
                'images': [],  # Would need additional API call for images
                'dealer_website': 'https://www.bmwofweststlouis.com',
                'vehicle_url': vehicle_url,
                'last_seen_date': datetime.now().isoformat(),
                'source': 'bmw_west_stl_algolia_api',
                'raw_data': vehicle_json,
                'msrp': msrp,
                'date_in_stock': date_in_stock,
                'street_addr': self.location_info['street_addr'],
                'locality': self.location_info['locality'],
                'postal_code': self.location_info['postal_code'],
                'region': self.location_info['region'],
                'country': self.location_info['country']
            }

            return vehicle_data

        except Exception as e:
            self.log(f"Error processing vehicle data: {e}")
            return None

    def get_all_vehicles(self) -> List[Dict[str, Any]]:
        """Main scraping method - exact logic from scraper 18"""
        all_vehicles = []
        
        self.log("Starting BMW of West St. Louis vehicle scraping...")
        
        # Process each vehicle type: used, new, certified (exact order from scraper 18)
        for mode in ['used', 'new', 'certified']:
            self.log(f"Scraping {mode} vehicles...")
            
            page_num = 0
            mode_vehicle_count = 0
            
            while True:
                self.log(f"Processing {mode} vehicles page {page_num}...")
                
                # Get vehicles from API
                api_response = self.get_vehicles_by_mode(page_num, mode)
                
                try:
                    json_data = api_response['results'][0]
                    total_vehicles = json_data.get('nbHits', 0)
                    total_pages = json_data.get('nbPages', 0)
                    vehicles_on_page = json_data.get('hits', [])
                    
                    self.log(f"Page {page_num}: {len(vehicles_on_page)} vehicles (Total: {total_vehicles}, Pages: {total_pages})")
                    
                    # Process each vehicle on this page
                    for vehicle_json in vehicles_on_page:
                        vehicle_data = self.process_vehicle_data(vehicle_json)
                        if vehicle_data:
                            all_vehicles.append(vehicle_data)
                            mode_vehicle_count += 1
                            self.total_processed += 1
                            
                            # Log progress every 10 vehicles
                            if self.total_processed % 10 == 0:
                                self.log(f"Processed {self.total_processed} vehicles total")
                    
                    # Check if we've reached the last page
                    if page_num >= total_pages - 1:  # API pages are 0-indexed
                        break
                        
                    page_num += 1
                    
                except (KeyError, IndexError) as e:
                    self.log(f"Error parsing API response for {mode} page {page_num}: {e}")
                    break
                    
                # Small delay between pages to be respectful
                time.sleep(0.5)
            
            self.log(f"Completed {mode} vehicles: {mode_vehicle_count} vehicles")
        
        self.log(f"BMW of West St. Louis scraping completed! Total vehicles: {len(all_vehicles)}")
        return all_vehicles


# Test function for individual testing
if __name__ == "__main__":
    def test_progress_callback(message):
        print(f"[PROGRESS] {message}")
    
    scraper = BMWOfWestStLouisRealScraper(progress_callback=test_progress_callback)
    vehicles = scraper.get_all_vehicles()
    
    print(f"\n[TEST RESULTS]")
    print(f"Total vehicles scraped: {len(vehicles)}")
    
    if vehicles:
        print(f"Sample vehicle data:")
        sample = vehicles[0]
        for key, value in sample.items():
            if key != 'raw_data':  # Skip raw data for readability
                print(f"  {key}: {value}")