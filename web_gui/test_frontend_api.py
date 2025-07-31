#!/usr/bin/env python3
"""
Test Frontend API Endpoints
===========================

Simple script to test the API endpoints that the frontend uses
to ensure they're working correctly.

Author: Silver Fox Assistant
Created: 2025-07-29
"""

import requests
import json

def test_dealerships_api():
    """Test the dealerships API endpoint"""
    try:
        print("Testing /api/dealerships endpoint...")
        response = requests.get('http://127.0.0.1:5000/api/dealerships')
        
        if response.status_code == 200:
            dealerships = response.json()
            print(f"✅ SUCCESS: API returned {len(dealerships)} dealerships")
            
            # Check for active dealerships
            active_dealerships = [d for d in dealerships if d.get('is_active', False)]
            print(f"📊 ACTIVE: {len(active_dealerships)} active dealerships")
            
            # List active dealerships
            print("\n🎯 ACTIVE DEALERSHIPS:")
            for dealership in active_dealerships:
                name = dealership.get('name', 'Unknown')
                print(f"   - {name}")
            
            # Check if Dave Sinclair Lincoln South is in the list
            dave_sinclair = None
            for d in dealerships:
                if 'Dave Sinclair Lincoln South' in d.get('name', ''):
                    dave_sinclair = d
                    break
            
            if dave_sinclair:
                print(f"\n✅ FOUND: Dave Sinclair Lincoln South")
                print(f"   Status: {'ACTIVE' if dave_sinclair.get('is_active') else 'INACTIVE'}")
                print(f"   Name: {dave_sinclair.get('name')}")
            else:
                print(f"\n❌ NOT FOUND: Dave Sinclair Lincoln South")
                
            return True
        else:
            print(f"❌ ERROR: API returned status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Failed to test API: {e}")
        return False

def test_page_load():
    """Test if the main page loads correctly"""
    try:
        print("\nTesting main page load...")
        response = requests.get('http://127.0.0.1:5000/')
        
        if response.status_code == 200:
            print("✅ SUCCESS: Main page loads correctly")
            
            # Check if key elements are present in HTML
            html = response.text
            key_elements = [
                'dealershipCheckboxGrid',
                'selectDealershipsBtn', 
                'MinisFornumApp',
                'loadDealerships'
            ]
            
            missing_elements = []
            for element in key_elements:
                if element not in html:
                    missing_elements.append(element)
            
            if missing_elements:
                print(f"⚠️  WARNING: Missing elements: {missing_elements}")
            else:
                print("✅ SUCCESS: All key elements found in HTML")
                
            return True
        else:
            print(f"❌ ERROR: Page returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Failed to test page load: {e}")
        return False

if __name__ == "__main__":
    print("Frontend API Test Suite")
    print("=" * 40)
    
    # Test API endpoints
    api_success = test_dealerships_api()
    
    # Test page load
    page_success = test_page_load()
    
    print("\n" + "=" * 40)
    if api_success and page_success:
        print("🎉 ALL TESTS PASSED")
        print("\nThe frontend should be able to load dealerships.")
        print("If dropdown is still not showing, check browser console for JS errors.")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nCheck the server logs for more details.")