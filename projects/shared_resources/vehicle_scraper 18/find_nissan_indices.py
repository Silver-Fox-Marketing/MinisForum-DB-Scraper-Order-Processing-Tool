import requests
import json

def find_nissan_indices():
    """Search for any Nissan-related indices"""

    app_id = "2591J46P8G"
    api_key = "78311e75e16dd6273d6b00cd6c21db3c"

    url = f"https://{app_id.lower()}-dsn.algolia.net/1/indexes"

    headers = {
        'X-Algolia-Application-Id': app_id,
        'X-Algolia-API-Key': api_key
    }

    try:
        print(f"[DEBUG] Searching for Nissan-related indices...")
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            indices = data['items']

            # Look for any index containing 'nissan'
            nissan_indices = []
            for index in indices:
                index_name = index.get('name', '')
                if 'nissan' in index_name.lower():
                    nissan_indices.append(index_name)

            print(f"[INFO] Found {len(nissan_indices)} Nissan-related indices:")
            for idx in nissan_indices:
                print(f"  - {idx}")

            # Also look for indices that might be Joe Machens related with different naming
            joe_related = []
            for index in indices:
                index_name = index.get('name', '')
                if any(pattern in index_name.lower() for pattern in ['joe', 'machens', 'columbia']):
                    joe_related.append(index_name)

            print(f"\n[INFO] Found {len(joe_related)} Joe/Machens/Columbia-related indices (first 20):")
            for idx in joe_related[:20]:
                print(f"  - {idx}")

            return nissan_indices, joe_related

        else:
            print(f"[ERROR] Request failed: {response.status_code}")

    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")

    return [], []

def test_nissan_indices(nissan_indices):
    """Test Nissan indices to see which ones have vehicle data"""

    app_id = "2591J46P8G"
    api_key = "78311e75e16dd6273d6b00cd6c21db3c"

    base_url = f"https://{app_id.lower()}-dsn.algolia.net/1/indexes"
    headers = {
        'X-Algolia-Application-Id': app_id,
        'X-Algolia-API-Key': api_key
    }

    for index_name in nissan_indices:
        try:
            print(f"\n[DEBUG] Testing index: {index_name}")

            query_url = f"{base_url}/{index_name}/query"
            query_payload = {
                "query": "",
                "hitsPerPage": 1,
                "page": 0
            }

            response = requests.post(query_url, headers=headers, json=query_payload)

            if response.status_code == 200:
                data = response.json()
                hit_count = data.get('nbHits', 0)
                hits = data.get('hits', [])

                print(f"[INFO] {index_name}: {hit_count} total items")

                if hits:
                    sample = hits[0]
                    # Look for vehicle-related fields
                    vehicle_fields = ['vin', 'make', 'model', 'year', 'stock', 'price']
                    found_fields = [field for field in vehicle_fields if field in sample]

                    if found_fields:
                        print(f"[VEHICLE DATA] Found vehicle fields: {found_fields}")
                        if 'make' in sample:
                            print(f"[MAKE] Sample make: {sample.get('make')}")
                        if 'model' in sample:
                            print(f"[MODEL] Sample model: {sample.get('model')}")
                    else:
                        print(f"[INFO] No obvious vehicle data fields found")

            else:
                print(f"[ERROR] Query failed: {response.status_code}")

        except Exception as e:
            print(f"[ERROR] Error testing {index_name}: {e}")

if __name__ == "__main__":
    print("=== Searching for Nissan Indices ===")

    nissan_indices, joe_related = find_nissan_indices()

    if nissan_indices:
        print(f"\n=== Testing {len(nissan_indices)} Nissan Indices ===")
        test_nissan_indices(nissan_indices)
    else:
        print("\n[INFO] No Nissan indices found")

    # Save the results
    with open('nissan_indices_search.json', 'w') as f:
        json.dump({
            'nissan_indices': nissan_indices,
            'joe_related_indices': joe_related
        }, f, indent=2)
    print("\n[INFO] Results saved to nissan_indices_search.json")