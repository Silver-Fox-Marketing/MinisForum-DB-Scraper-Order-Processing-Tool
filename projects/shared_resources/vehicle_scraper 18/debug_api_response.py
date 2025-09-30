import json
import requests

def test_joe_machens_nissan_api():
    """Test the actual API response to see the structure"""

    url = "https://2591j46p8g-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.9.1)%3B%20Browser%20(lite)%3B%20JS%20Helper%20(3.4.4)&x-algolia-api-key=78311e75e16dd6273d6b00cd6c21db3c&x-algolia-application-id=2591J46P8G"

    # Test with 'used' mode payload
    payload = json.dumps({"requests": [{
        "indexName": "joemachensnissan-winback1023_production_inventory_days_in_stock_high_to_low",
        "params": "maxValuesPerFacet=250&hitsPerPage=20&page=0&facets=%5B%22features%22%2C%22our_price%22%2C%22lightning.lease_monthly_payment%22%2C%22lightning.finance_monthly_payment%22%2C%22type%22%2C%22api_id%22%2C%22year%22%2C%22make%22%2C%22model%22%2C%22model_number%22%2C%22trim%22%2C%22body%22%2C%22doors%22%2C%22miles%22%2C%22ext_color_generic%22%2C%22features%22%2C%22lightning.isSpecial%22%2C%22lightning.locations%22%2C%22Location%22%2C%22in_transit_filter%22%2C%22lightning.status%22%2C%22lightning.class%22%2C%22fueltype%22%2C%22bedtype%22%2C%22engine_description%22%2C%22transmission_description%22%2C%22metal_flags%22%2C%22city_mpg%22%2C%22hw_mpg%22%2C%22days_in_stock%22%2C%22date_in_stock%22%2C%22ford_SpecialVehicle%22%2C%22lightning.locations.meta_location%22%2C%22intransit_filter%22%2C%22location%22%2C%22special_field_1%22%2C%22title_vrp%22%2C%22ext_color%22%2C%22int_color%22%2C%22certified%22%2C%22lightning%22%2C%22drivetrain%22%2C%22int_options%22%2C%22ext_options%22%2C%22cylinders%22%2C%22vin%22%2C%22stock%22%2C%22msrp%22%2C%22our_price_label%22%2C%22finance_details%22%2C%22lease_details%22%2C%22thumbnail%22%2C%22link%22%2C%22objectID%22%2C%22algolia_sort_order%22%2C%22date_modified%22%2C%22hash%22%2C%22monroneyLabel%22%5D&tagFilters=&facetFilters=%5B%5B%22location%3AJoe%20Machens%20Nissan%22%5D%2C%5B%22type%3ANew%22%2C%22type%3ACertified%20Used%22%2C%22type%3AUsed%22%5D%5D"
    }, {
        "indexName": "joemachensnissan-winback1023_production_inventory_days_in_stock_high_to_low",
        "params": "maxValuesPerFacet=250&hitsPerPage=1&page=0&attributesToRetrieve=%5B%5D&attributesToHighlight=%5B%5D&attributesToSnippet=%5B%5D&tagFilters=&analytics=false&clickAnalytics=false&facets=location&facetFilters=%5B%5B%22type%3ANew%22%2C%22type%3ACertified%20Used%22%2C%22type%3AUsed%22%5D%5D"
    }, {
        "indexName": "joemachensnissan-winback1023_production_inventory_days_in_stock_high_to_low",
        "params": "maxValuesPerFacet=250&hitsPerPage=1&page=0&attributesToRetrieve=%5B%5D&attributesToHighlight=%5B%5D&attributesToSnippet=%5B%5D&tagFilters=&analytics=false&clickAnalytics=false&facets=type&facetFilters=%5B%5B%22location%3AJoe%20Machens%20Nissan%22%5D%5D"
    }]})

    headers = {
        'Content-Type': 'application/json'
    }

    try:
        print("[DEBUG] Making API request...")
        response = requests.post(url, headers=headers, data=payload)

        print(f"[DEBUG] Status code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"[DEBUG] Response keys: {list(data.keys())}")

            # Print the structure
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, list):
                        print(f"[DEBUG] {key}: list with {len(value)} items")
                        if len(value) > 0:
                            print(f"[DEBUG] {key}[0] keys: {list(value[0].keys()) if isinstance(value[0], dict) else type(value[0])}")
                    else:
                        print(f"[DEBUG] {key}: {type(value)}")

            # Save full response for inspection
            with open('api_response_debug.json', 'w') as f:
                json.dump(data, f, indent=2)
            print("[DEBUG] Full response saved to api_response_debug.json")

        else:
            print(f"[ERROR] Request failed: {response.status_code}")
            print(f"[ERROR] Response: {response.text}")

    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")

if __name__ == "__main__":
    test_joe_machens_nissan_api()