import requests
from bs4 import BeautifulSoup
import re

def find_joe_machens_nissan_index():
    """Find the current Algolia index name for Joe Machens Nissan"""

    # Try to visit the Joe Machens Nissan inventory page
    inventory_url = "https://www.joemachensnissan.com/new-inventory/index.htm"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        print(f"[DEBUG] Visiting: {inventory_url}")
        response = requests.get(inventory_url, headers=headers, timeout=30)

        if response.status_code == 200:
            html_content = response.text

            # Look for Algolia configuration in the JavaScript
            algolia_patterns = [
                r'indexName["\']?\s*:\s*["\']([^"\']+)["\']',
                r'algolia.*indexName.*["\']([^"\']+)["\']',
                r'["\']indexName["\']\s*:\s*["\']([^"\']+)["\']',
                r'joemachensnissan[^"\']*',
                r'production_inventory[^"\']*'
            ]

            found_indices = set()
            for pattern in algolia_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                found_indices.update(matches)

            print(f"[DEBUG] Found potential index names: {list(found_indices)}")

            # Also look for the Algolia application ID and API key
            algolia_app_id = re.search(r'x-algolia-application-id["\']?\s*[:=]\s*["\']([^"\']+)["\']', html_content, re.IGNORECASE)
            algolia_api_key = re.search(r'x-algolia-api-key["\']?\s*[:=]\s*["\']([^"\']+)["\']', html_content, re.IGNORECASE)

            if algolia_app_id:
                print(f"[DEBUG] Found Algolia App ID: {algolia_app_id.group(1)}")
            if algolia_api_key:
                print(f"[DEBUG] Found Algolia API Key: {algolia_api_key.group(1)}")

            # Save the HTML content for manual inspection
            with open('joemachens_page_source.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("[DEBUG] Page source saved to joemachens_page_source.html")

            return found_indices

        else:
            print(f"[ERROR] Failed to load page: {response.status_code}")

    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")

    return set()

def test_algolia_indices(indices, app_id="2591J46P8G", api_key="78311e75e16dd6273d6b00cd6c21db3c"):
    """Test potential Algolia indices to see which ones exist"""

    base_url = f"https://{app_id.lower()}-dsn.algolia.net/1/indexes"

    headers = {
        'X-Algolia-Application-Id': app_id,
        'X-Algolia-API-Key': api_key
    }

    for index_name in indices:
        if not index_name or len(index_name) < 5:  # Skip very short matches
            continue

        try:
            test_url = f"{base_url}/{index_name}/settings"
            print(f"[DEBUG] Testing index: {index_name}")

            response = requests.get(test_url, headers=headers)
            print(f"[DEBUG] {index_name}: Status {response.status_code}")

            if response.status_code == 200:
                print(f"[SUCCESS] Found valid index: {index_name}")
            elif response.status_code == 404:
                print(f"[INFO] Index not found: {index_name}")
            else:
                print(f"[INFO] Other response for {index_name}: {response.status_code}")

        except Exception as e:
            print(f"[ERROR] Error testing {index_name}: {e}")

if __name__ == "__main__":
    print("=== Finding Joe Machens Nissan Algolia Index ===")
    indices = find_joe_machens_nissan_index()

    if indices:
        print("\n=== Testing Found Indices ===")
        test_algolia_indices(indices)
    else:
        print("[INFO] No indices found in page source")