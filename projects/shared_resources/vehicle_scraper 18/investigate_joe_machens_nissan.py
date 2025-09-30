import requests
from bs4 import BeautifulSoup
import re
import json
import time

def analyze_joe_machens_nissan_website():
    """Analyze Joe Machens Nissan website to find their new data source"""

    urls_to_check = [
        "https://www.joemachensnissan.com/",
        "https://www.joemachensnissan.com/new-vehicles/",
        "https://www.joemachensnissan.com/used-vehicles/",
        "https://www.joemachensnissan.com/inventory/",
        "https://www.joemachensnissan.com/new-inventory/",
        "https://www.joemachensnissan.com/used-inventory/"
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    for url in urls_to_check:
        try:
            print(f"\n[DEBUG] Checking: {url}")
            response = requests.get(url, headers=headers, timeout=30)

            print(f"[DEBUG] Status: {response.status_code}")

            if response.status_code == 200:
                html_content = response.text

                # Look for common inventory system patterns
                patterns_to_find = {
                    'Algolia': [r'algolia', r'x-algolia', r'indexName'],
                    'DealerSocket': [r'dealersocket', r'dealer-socket', r'inventory-api'],
                    'CDK': [r'cdkdigital', r'cdk-api', r'fortellis'],
                    'AutoTrader': [r'autotrader', r'inventory\.autotrader'],
                    'Cars.com': [r'cars\.com', r'cars-api'],
                    'DealerInspire': [r'dealerinspire', r'di-api'],
                    'WordPress': [r'wp-content', r'wp-json'],
                    'Custom API': [r'\/api\/', r'inventory\/api', r'vehicles\/api'],
                    'GraphQL': [r'graphql', r'__typename'],
                    'REST API': [r'\/rest\/', r'application\/json']
                }

                found_patterns = {}
                for system, patterns in patterns_to_find.items():
                    matches = []
                    for pattern in patterns:
                        found = re.findall(pattern, html_content, re.IGNORECASE)
                        if found:
                            matches.extend(found[:3])  # Limit matches
                    if matches:
                        found_patterns[system] = matches

                if found_patterns:
                    print(f"[FOUND] Potential systems in {url}:")
                    for system, matches in found_patterns.items():
                        print(f"  - {system}: {matches}")

                # Look for inventory-related JavaScript or API calls
                api_patterns = [
                    r'fetch\(["\']([^"\']*(?:inventory|vehicle|api)[^"\']*)["\']',
                    r'axios\.get\(["\']([^"\']*(?:inventory|vehicle|api)[^"\']*)["\']',
                    r'\.ajax\({[^}]*url[^}]*["\']([^"\']*(?:inventory|vehicle|api)[^"\']*)["\']',
                    r'["\']([^"\']*\/api\/[^"\']*)["\']',
                    r'endpoint["\']?\s*:\s*["\']([^"\']*)["\']'
                ]

                api_urls = set()
                for pattern in api_patterns:
                    matches = re.findall(pattern, html_content, re.IGNORECASE)
                    api_urls.update(matches)

                if api_urls:
                    print(f"[API URLS] Found potential API endpoints:")
                    for api_url in list(api_urls)[:5]:  # Show first 5
                        print(f"  - {api_url}")

                # Save the page source for manual inspection
                filename = url.replace('https://', '').replace('/', '_') + '.html'
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"[SAVED] Page source saved to: {filename}")

            else:
                print(f"[ERROR] Failed to load: {response.status_code}")

            time.sleep(1)  # Be polite

        except Exception as e:
            print(f"[ERROR] Exception for {url}: {e}")

def check_common_api_endpoints():
    """Check common API endpoint patterns for Joe Machens Nissan"""

    base_url = "https://www.joemachensnissan.com"

    api_endpoints = [
        "/api/inventory",
        "/api/vehicles",
        "/api/inventory/search",
        "/wp-json/wp/v2/inventory",
        "/inventory/api/search",
        "/vehicles/search",
        "/inventory.json",
        "/vehicles.json",
        "/api/inventory.json",
        "/rest/inventory"
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*'
    }

    working_endpoints = []

    print(f"\n[DEBUG] Testing API endpoints...")
    for endpoint in api_endpoints:
        try:
            url = base_url + endpoint
            print(f"[TEST] {url}")

            response = requests.get(url, headers=headers, timeout=10)
            print(f"  Status: {response.status_code}")

            if response.status_code == 200:
                try:
                    # Try to parse as JSON
                    data = response.json()
                    print(f"  [JSON] Success - Keys: {list(data.keys()) if isinstance(data, dict) else 'Array/Other'}")
                    working_endpoints.append({
                        'url': url,
                        'type': 'JSON',
                        'sample': str(data)[:200] + '...' if len(str(data)) > 200 else str(data)
                    })
                except:
                    # Not JSON, but might still be useful
                    content = response.text[:200] + '...' if len(response.text) > 200 else response.text
                    print(f"  [TEXT] Success - Content: {content}")
                    working_endpoints.append({
                        'url': url,
                        'type': 'TEXT',
                        'sample': content
                    })

        except Exception as e:
            print(f"  [ERROR] {e}")

        time.sleep(0.5)

    return working_endpoints

if __name__ == "__main__":
    print("=== Joe Machens Nissan Website Analysis ===")

    analyze_joe_machens_nissan_website()

    working_endpoints = check_common_api_endpoints()

    if working_endpoints:
        print(f"\n[SUCCESS] Found {len(working_endpoints)} working endpoints:")
        for endpoint in working_endpoints:
            print(f"  - {endpoint['url']} ({endpoint['type']})")

    print("\n[INFO] Analysis complete. Check saved HTML files for manual inspection.")