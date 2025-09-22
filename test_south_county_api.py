#!/usr/bin/env python3
"""
Test South County DCJR API response to see the exact structure
"""

import sys
import json
from pathlib import Path

# Add the scripts directory to Python path
scripts_dir = Path(__file__).parent / 'projects/minisforum_database_transfer/bulletproof_package/scripts'
sys.path.insert(0, str(scripts_dir))

from correct_order_processing import CorrectOrderProcessor

def test_api_response():
    """Test the exact API response structure for South County DCJR"""
    processor = CorrectOrderProcessor()

    print("TESTING SOUTH COUNTY DCJR API RESPONSE")
    print("=" * 50)

    try:
        # Test with skip_vin_logging=True to avoid affecting production
        result = processor.process_cao_order('South County DCJR', skip_vin_logging=True)

        print("SUCCESS! Raw result structure:")
        print(json.dumps(result, indent=2, default=str))

        print("\n" + "=" * 50)
        print("KEY ANALYSIS:")
        print(f"- success: {result.get('success')}")
        print(f"- csv_file type: {type(result.get('csv_file'))}")
        print(f"- csv_file value: {result.get('csv_file')}")
        print(f"- new_vehicles: {result.get('new_vehicles')}")
        print(f"- vehicle_count: {result.get('vehicle_count')}")

        # Check if csv_file is a dict (mixed template)
        if isinstance(result.get('csv_file'), dict):
            print("\nMIXED TEMPLATE DETECTED:")
            csv_files = result['csv_file']
            for key, value in csv_files.items():
                print(f"  - {key}: {value}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_api_response()