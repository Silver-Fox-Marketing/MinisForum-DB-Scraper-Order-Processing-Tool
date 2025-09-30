import requests
import time
import json

def test_algolia_list_indices():
    """Try to list all indices to find the correct one"""

    app_id = "2591J46P8G"
    api_key = "78311e75e16dd6273d6b00cd6c21db3c"

    url = f"https://{app_id.lower()}-dsn.algolia.net/1/indexes"

    headers = {
        'X-Algolia-Application-Id': app_id,
        'X-Algolia-API-Key': api_key
    }

    try:
        print(f"[DEBUG] Trying to list all indices...")
        response = requests.get(url, headers=headers)

        print(f"[DEBUG] Status code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"[DEBUG] Response keys: {list(data.keys())}")

            if 'items' in data:
                indices = data['items']
                print(f"[SUCCESS] Found {len(indices)} indices")

                joe_machens_indices = []
                for index in indices:
                    index_name = index.get('name', '')
                    if 'joemachens' in index_name.lower():
                        joe_machens_indices.append(index_name)
                        print(f"[MATCH] Joe Machens index: {index_name}")

                return joe_machens_indices

            else:
                print(f"[DEBUG] Full response: {data}")

        else:
            print(f"[ERROR] Request failed: {response.status_code}")
            print(f"[ERROR] Response: {response.text}")

    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")

    return []

def test_common_index_patterns():
    """Test common index naming patterns"""

    app_id = "2591J46P8G"
    api_key = "78311e75e16dd6273d6b00cd6c21db3c"

    # Common patterns for automotive dealership Algolia indices
    patterns = [
        "joemachensnissan_production_inventory",
        "joemachensnissan-production-inventory",
        "joemachensnissan_inventory",
        "joemachensnissan-inventory",
        "joemachensnissan_prod_inventory",
        "joemachensnissan-prod-inventory",
        "joemachensnissan_2024_production_inventory",
        "joemachensnissan-2024-production-inventory",
        "joemachensnissan_2025_production_inventory",
        "joemachensnissan-2025-production-inventory",
        "joemachensnissan_production_inventory_days_in_stock_high_to_low",
        "joemachensnissan-production-inventory-days-in-stock-high-to-low",
        "joemachensnissan_winback2024_production_inventory",
        "joemachensnissan-winback2024-production-inventory",
        "joemachensnissan_winback2024_production_inventory_days_in_stock_high_to_low",
        "joemachensnissan-winback2024-production-inventory-days-in-stock-high-to-low",
        "joemachensnissan_winback_production_inventory",
        "joemachensnissan-winback-production-inventory"
    ]

    base_url = f"https://{app_id.lower()}-dsn.algolia.net/1/indexes"

    headers = {
        'X-Algolia-Application-Id': app_id,
        'X-Algolia-API-Key': api_key
    }

    working_indices = []

    for pattern in patterns:
        try:
            test_url = f"{base_url}/{pattern}/settings"
            print(f"[DEBUG] Testing: {pattern}")

            response = requests.get(test_url, headers=headers)

            if response.status_code == 200:
                print(f"[SUCCESS] Found valid index: {pattern}")
                working_indices.append(pattern)

                # Test a query to make sure it has data
                query_url = f"{base_url}/{pattern}/query"
                query_payload = {
                    "query": "",
                    "hitsPerPage": 1,
                    "page": 0
                }

                query_response = requests.post(query_url, headers=headers, json=query_payload)
                if query_response.status_code == 200:
                    query_data = query_response.json()
                    hit_count = query_data.get('nbHits', 0)
                    print(f"[INFO] Index {pattern} has {hit_count} vehicles")

            elif response.status_code == 404:
                print(f"[INFO] Not found: {pattern}")
            else:
                print(f"[INFO] Status {response.status_code}: {pattern}")

            time.sleep(0.1)  # Be polite to the API

        except Exception as e:
            print(f"[ERROR] Error testing {pattern}: {e}")

    return working_indices

if __name__ == "__main__":
    print("=== Advanced Joe Machens Nissan Algolia Index Search ===")

    # First try to list all indices
    print("\n--- Trying to list all indices ---")
    found_indices = test_algolia_list_indices()

    if found_indices:
        print(f"\n[SUCCESS] Found Joe Machens indices: {found_indices}")
    else:
        print("\n--- Testing common patterns ---")
        working_indices = test_common_index_patterns()

        if working_indices:
            print(f"\n[SUCCESS] Found working indices: {working_indices}")
        else:
            print("\n[ERROR] No working indices found")