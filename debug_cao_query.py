"""
Debug the exact CAO query to see why we get 80 instead of 27 vehicles
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'projects', 'minisforum_database_transfer', 'bulletproof_package', 'scripts'))

from database_connection import db_manager

# Expected 27 VINs that should be the ONLY ones returned
expected_vins = [
    "JTNC4MBE8S3251508", "2T3G1RFV9SC555175", "4T1DAACK0SU207612",
    "4T1DAACK1TU209709", "JTMRWRFV1SD331470", "4T1DBADK8TU542324",
    "4T1DAACK4TU652503", "2T3N1RFV6SW587930", "2T3N1RFV1SW585311",
    "JTDACACUXT3054506", "3TYLE5JN5ST089543", "3TMLB5JN4SM173065",
    "5TDAAAB52TS105320", "5TDAAAB5XSS103880", "5TFLA5DB7TX341748",
    "JTEVA5BR9S5044849", "JTEVA5BR8S5049217", "3TYLC5LN3ST041350",
    "5TFWA5DB7TX340743", "7SVAAABA1TX074364", "4T1G11BKXLU006834",
    "5YFB4MDEXSP341778", "JTMDWRFV9LD069614", "2T3A1RFV9MC208826",
    "3TMGZ5AN3PM594747", "5TFMA5EC2NX009361", "JTEBU5JR8A5008998"
]

print("=== DEBUGGING CAO QUERY ===")

# Test the exact query from the logs  
query = """
    SELECT nvd.vin, nvd.vehicle_condition, rvd.status as raw_status,
           nvd.on_lot_status
    FROM normalized_vehicle_data nvd
    JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
    JOIN scraper_imports si ON rvd.import_id = si.import_id
    WHERE nvd.location = %s 
    AND nvd.on_lot_status IN ('onlot', 'on lot')
    AND si.status = 'active'
    AND nvd.vin NOT IN (SELECT vin FROM pappas_toyota_vin_log WHERE vin IS NOT NULL)
    ORDER BY nvd.updated_at DESC
"""

# Execute the query
params = ('Pappas Toyota',)
result = db_manager.execute_query(query, params)

print(f"Total vehicles found by CAO query: {len(result)}")

# Categorize the results
expected_found = []
unexpected_found = []

for vehicle in result:
    vin = vehicle['vin']
    if vin in expected_vins:
        expected_found.append(vehicle)
    else:
        unexpected_found.append(vehicle)

print(f"Expected VINs found: {len(expected_found)}/27")
print(f"Unexpected VINs found: {len(unexpected_found)}")

if len(expected_found) < 27:
    missing_expected = [vin for vin in expected_vins if vin not in [v['vin'] for v in expected_found]]
    print(f"Missing expected VINs: {missing_expected[:5]}...")

if len(unexpected_found) > 0:
    print(f"\n=== FIRST 10 UNEXPECTED VINs ===")
    for i, vehicle in enumerate(unexpected_found[:10]):
        print(f"{i+1}. {vehicle['vin']} - {vehicle['vehicle_condition']} - {vehicle['raw_status']}")
    
    # Check if these unexpected vehicles have issues
    print(f"\n=== ANALYZING UNEXPECTED VEHICLES ===")
    
    # Check status issues
    status_issues = [v for v in unexpected_found if v['raw_status'] and ('In-Transit' in str(v['raw_status']) or 'Sold' in str(v['raw_status']) or 'Allocated' in str(v['raw_status']))]
    print(f"Vehicles with problematic status: {len(status_issues)}")
    
    # Check vehicle condition issues
    condition_issues = [v for v in unexpected_found if v['vehicle_condition'] not in ['new', 'po', 'cpo']]
    print(f"Vehicles with problematic conditions: {len(condition_issues)}")

print(f"\n=== RESULT ===")
if len(result) == 27 and len(unexpected_found) == 0:
    print("SUCCESS: Query returns exactly 27 expected VINs")
elif len(result) == 80:
    print(f"CONFIRMED: Query returns 80 vehicles (matches your test)")
    print(f"ISSUE: 53 extra vehicles are being included that should be filtered out")
else:
    print(f"Query returns {len(result)} vehicles - different from your 80 test result")