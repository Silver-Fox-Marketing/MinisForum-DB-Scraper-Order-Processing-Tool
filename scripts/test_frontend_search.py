#!/usr/bin/env python3
"""
Test Frontend Search
===================

Test the frontend search by making the exact same calls the frontend would make.

Author: Silver Fox Assistant  
Created: 2025-07-29
"""

import requests
import json

def test_frontend_flow():
    """Test the complete frontend initialization flow"""
    
    base_url = "http://127.0.0.1:5000"
    
    print("\n" + "="*60)
    print(">> TESTING FRONTEND SEARCH FLOW")
    print("="*60)
    
    # Test 1: Initial data load (what happens when Data tab opens)
    print("\n[TEST 1] Initial data load (no query)")
    try:
        params = {
            'query': '',
            'limit': 50,
            'offset': 0,
            'filter_by': 'all',
            'data_type': 'both',
            'sort_by': 'import_timestamp',
            'sort_order': 'desc'
        }
        
        response = requests.get(f"{base_url}/api/data/search", params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"[OK] Found {data['total_count']} vehicles")
                print(f"[OK] Returned {len(data['data'])} vehicles in this page")
                if data['data']:
                    print("Sample vehicles:")
                    for i, vehicle in enumerate(data['data'][:3]):
                        print(f"  {i+1}. {vehicle.get('year', 'N/A')} {vehicle.get('make', 'N/A')} {vehicle.get('model', 'N/A')} - {vehicle.get('location', 'N/A')}")
                else:
                    print("[ERROR] No vehicles in data array!")
            else:
                print(f"[ERROR] API returned success=false: {data.get('error', 'Unknown error')}")
        else:
            print(f"[ERROR] HTTP {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
    
    # Test 2: Search with query
    print("\n[TEST 2] Search for 'Lincoln'")
    try:
        params = {
            'query': 'Lincoln',
            'limit': 5,
            'offset': 0,
            'filter_by': 'all',
            'data_type': 'both',
            'sort_by': 'import_timestamp',
            'sort_order': 'desc'
        }
        
        response = requests.get(f"{base_url}/api/data/search", params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"[OK] Found {data['total_count']} Lincoln vehicles")
                if data['data']:
                    print("Lincoln vehicles:")
                    for i, vehicle in enumerate(data['data']):
                        print(f"  {i+1}. {vehicle.get('year', 'N/A')} {vehicle.get('make', 'N/A')} {vehicle.get('model', 'N/A')} - ${vehicle.get('price', 'N/A')}")
            else:
                print(f"[ERROR] API returned success=false: {data.get('error', 'Unknown error')}")
        else:
            print(f"[ERROR] HTTP {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
    
    # Test 3: Load dealers list
    print("\n[TEST 3] Load dealers list")
    try:
        response = requests.get(f"{base_url}/api/data/dealers", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"[OK] Found {len(data['dealers'])} dealers")
                print("Sample dealers:", data['dealers'][:5])
            else:
                print(f"[ERROR] API returned success=false: {data.get('error', 'Unknown error')}")
        else:
            print(f"[ERROR] HTTP {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
    
    print("\n" + "="*60)
    print(">> FRONTEND FLOW TESTING COMPLETE")
    print("="*60)
    print("\nIf all tests show [OK], the search should work in the browser!")
    print("Try refreshing the page and clicking on the Data tab.")
    print("="*60)

if __name__ == "__main__":
    test_frontend_flow()