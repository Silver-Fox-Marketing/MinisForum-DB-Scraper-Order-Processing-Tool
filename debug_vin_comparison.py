"""
Debug script to check which expected VINs are in the Pappas Toyota VIN log
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'projects', 'minisforum_database_transfer', 'bulletproof_package', 'scripts'))

from database_connection import db_manager

# Expected 27 VINs from your list
expected_vins = [
    "JTNC4MBE8S3251508",
    "2T3G1RFV9SC555175", 
    "4T1DAACK0SU207612",
    "4T1DAACK1TU209709",
    "JTMRWRFV1SD331470",
    "4T1DBADK8TU542324",
    "4T1DAACK4TU652503",
    "2T3N1RFV6SW587930",
    "2T3N1RFV1SW585311",
    "JTDACACUXT3054506",
    "3TYLE5JN5ST089543",
    "3TMLB5JN4SM173065",
    "5TDAAAB52TS105320",
    "5TDAAAB5XSS103880",
    "5TFLA5DB7TX341748",
    "JTEVA5BR9S5044849",
    "JTEVA5BR8S5049217",
    "3TYLC5LN3ST041350",
    "5TFWA5DB7TX340743",
    "7SVAAABA1TX074364",
    "4T1G11BKXLU006834",
    "5YFB4MDEXSP341778",
    "JTMDWRFV9LD069614",
    "2T3A1RFV9MC208826",
    "3TMGZ5AN3PM594747",
    "5TFMA5EC2NX009361",
    "JTEBU5JR8A5008998"
]

print(f"=== CHECKING {len(expected_vins)} EXPECTED VINs ===")

# Check which expected VINs are in the VIN log
in_vinlog = []
not_in_vinlog = []

for vin in expected_vins:
    result = db_manager.execute_query(
        "SELECT COUNT(*) as count FROM pappas_toyota_vin_log WHERE vin = %s",
        (vin,)
    )
    count = result[0]['count']
    
    if count > 0:
        in_vinlog.append(vin)
        print(f"✓ {vin} - IN VIN LOG")
    else:
        not_in_vinlog.append(vin)
        print(f"✗ {vin} - NOT IN VIN LOG")

print(f"\n=== SUMMARY ===")
print(f"Expected VINs IN VIN log: {len(in_vinlog)}")
print(f"Expected VINs NOT IN VIN log: {len(not_in_vinlog)}")

if len(not_in_vinlog) == 27:
    print("\n[ISSUE FOUND] ALL 27 expected VINs are missing from VIN log!")
    print("This means the VIN log import didn't work correctly.")
elif len(not_in_vinlog) == 0:
    print("\n[ISSUE FOUND] ALL 27 expected VINs are already in VIN log!")
    print("This means CAO should return 0 vehicles, not 80.")
else:
    print(f"\n[MIXED RESULT] {len(not_in_vinlog)} expected VINs are missing from VIN log")
    print("The CAO should return these missing VINs only.")

# Now check how many total vehicles CAO query would find
print(f"\n=== CHECKING TOTAL CAO QUERY ===")
total_result = db_manager.execute_query("""
    SELECT COUNT(*) as count FROM normalized_vehicle_data nvd
    JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
    JOIN scraper_imports si ON rvd.import_id = si.import_id
    WHERE nvd.location = %s 
    AND nvd.on_lot_status IN ('onlot', 'on lot')
    AND si.status = 'active'
    AND nvd.vin NOT IN (SELECT vin FROM pappas_toyota_vin_log WHERE vin IS NOT NULL)
""", ('Pappas Toyota',))

total_cao_count = total_result[0]['count']
print(f"Total vehicles CAO query finds: {total_cao_count}")
print(f"Expected: 27")
print(f"Difference: {total_cao_count - 27}")

if total_cao_count == 80:
    print("\n[CONFIRMED] CAO query returns 80 vehicles - this matches your test result")
else:
    print(f"\n[MISMATCH] CAO query returns {total_cao_count} vehicles, but you got 80")