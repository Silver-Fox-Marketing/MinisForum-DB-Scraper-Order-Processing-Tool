#!/usr/bin/env python3
"""
Test South County DCJR API call directly via HTTP
"""

import requests
import json

def test_api_call():
    """Test the exact API call that the frontend makes"""
    url = "http://127.0.0.1:5000/api/orders/process-cao"

    payload = {
        "dealerships": ["South County DCJR"],
        "vehicle_types": None,
        "skip_vin_logging": True
    }

    headers = {
        "Content-Type": "application/json"
    }

    print("TESTING SOUTH COUNTY DCJR API CALL")
    print("=" * 50)
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print()

        if response.status_code == 200:
            result = response.json()
            print("SUCCESS! API Response:")
            print(json.dumps(result, indent=2))
        else:
            print(f"ERROR! Status: {response.status_code}")
            print(f"Response Text: {response.text}")

    except Exception as e:
        print(f"REQUEST ERROR: {e}")

if __name__ == '__main__':
    test_api_call()