#!/usr/bin/env python3
"""Test script to verify manual VIN import endpoint exists"""

# Add the scripts directory to Python path for imports
import sys
from pathlib import Path

scripts_dir = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

# Import the Flask app
import app

print("=== TESTING MANUAL VIN IMPORT ENDPOINT ===")
print(f"Flask app: {app.app}")

# Check all routes
print("\nAll available routes:")
for rule in app.app.url_map.iter_rules():
    if 'manual' in rule.rule.lower() or 'vin' in rule.rule.lower():
        print(f"  {rule.rule} -> {rule.methods} -> {rule.endpoint}")

# Test if manual_vin_import function exists
if hasattr(app, 'manual_vin_import'):
    print(f"\n✅ manual_vin_import function exists: {app.manual_vin_import}")
else:
    print("\n❌ manual_vin_import function does NOT exist")

# Try to call the function manually
try:
    with app.app.app_context():
        from flask import request
        # Test data
        test_data = {
            'dealership_name': 'Test Dealership',
            'vins': [{'vin': '1HGCM82633A123456', 'order_number': '12345'}],
            'import_date': '2025-08-27T17:10:00.000Z',
            'source': 'manual_entry'
        }
        
        # Create mock request
        with app.app.test_request_context('/api/manual-vin-import', 
                                        method='POST', 
                                        json=test_data):
            result = app.manual_vin_import()
            print(f"\n✅ Function call succeeded: {result}")
except Exception as e:
    print(f"\n❌ Function call failed: {e}")
    import traceback
    traceback.print_exc()