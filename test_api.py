#!/usr/bin/env python3
import requests
import json

try:
    response = requests.get('http://localhost:5000/api/dealership-settings')
    data = response.json()

    if data.get('success'):
        dealerships = data.get('dealerships', [])
        for dealership in dealerships:
            if 'Pappas Toyota' in dealership.get('name', ''):
                print(f"=== PAPPAS TOYOTA SETTINGS ===")
                print(f"Name: {dealership.get('name')}")
                filtering_rules = dealership.get('filtering_rules', {})
                print(f"Filtering Rules:")
                print(json.dumps(filtering_rules, indent=2))
                required_brands = filtering_rules.get('required_brands', [])
                print(f"Required Brands: {required_brands}")
                break
        else:
            print("Pappas Toyota not found in API response")
    else:
        print(f"API Error: {data}")

except Exception as e:
    print(f"Error: {e}")