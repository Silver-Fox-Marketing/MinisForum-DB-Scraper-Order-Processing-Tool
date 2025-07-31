#!/usr/bin/env python3
"""
Test Missing APIs
================

Test the additional APIs needed for the search interface.

Author: Silver Fox Assistant  
Created: 2025-07-29
"""

import requests
import json

def test_apis():
    """Test the additional APIs"""
    
    base_url = "http://127.0.0.1:5000"
    
    tests = [
        f"{base_url}/api/data/dealers",
        f"{base_url}/api/data/date-range"
    ]
    
    print("\n" + "="*60)
    print(">> TESTING ADDITIONAL APIs")
    print("="*60)
    
    for url in tests:
        print(f"\n[TEST] {url}")
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"[OK] Status: {response.status_code}")
                print(f"Data: {json.dumps(data, indent=2)[:200]}...")
            else:
                print(f"[ERROR] Status: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"[ERROR] Request failed: {e}")
    
    print("\n" + "="*60)
    print(">> API TESTING COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_apis()