#!/usr/bin/env python3
"""
Test Search API
===============

Test the vehicle data search API to verify it's working correctly.

Author: Silver Fox Assistant  
Created: 2025-07-29
"""

import requests
import json

def test_search_api():
    """Test the search API with various queries"""
    
    base_url = "http://127.0.0.1:5000/api/data/search"
    
    test_cases = [
        {
            "name": "Test 1: Search for Lincoln",
            "params": {"query": "Lincoln", "limit": 5}
        },
        {
            "name": "Test 2: Search for BMW", 
            "params": {"query": "BMW", "limit": 5}
        },
        {
            "name": "Test 3: Search all data (no query)",
            "params": {"limit": 10}
        },
        {
            "name": "Test 4: Search with raw data only",
            "params": {"query": "Ford", "data_type": "raw", "limit": 3}
        }
    ]
    
    print("\n" + "="*60)
    print(">> TESTING VEHICLE DATA SEARCH API")
    print("="*60)
    
    for test in test_cases:
        print(f"\n[TEST] {test['name']}")
        print(f"Params: {test['params']}")
        
        try:
            response = requests.get(base_url, params=test['params'], timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"[OK] SUCCESS: Found {data['total_count']} vehicles")
                    if data['data']:
                        print("Sample results:")
                        for i, vehicle in enumerate(data['data'][:3]):
                            print(f"  {i+1}. {vehicle.get('year', 'N/A')} {vehicle.get('make', 'N/A')} {vehicle.get('model', 'N/A')} - {vehicle.get('location', 'N/A')}")
                    else:
                        print("  No vehicles returned")
                else:
                    print(f"[ERROR] API Error: {data.get('error', 'Unknown error')}")
            else:
                print(f"[ERROR] HTTP Error: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"[ERROR] Request failed: {e}")
    
    print("\n" + "="*60)
    print(">> API TESTING COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_search_api()