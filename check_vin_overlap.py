"""
Check if the 27 expected VINs are in the 80 VINs generated
"""
import csv

def check_vin_overlap():
    """Check if expected VINs are in the generated result"""
    
    # Expected 27 VINs
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
    
    # Read VINs from the generated CSV
    csv_path = r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\orders\Pappas_Toyota\20250910_163856\PAPPASTOYOTA_09-10 - BILLING.csv"
    
    generated_vins = []
    with open(csv_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            if len(row) > 0 and row[0] and ' - ' in row[0]:
                # Extract VIN from format like "2026 Toyota Sequoia - T41905 - 7SVAAABA1TX074364"
                parts = row[0].split(' - ')
                if len(parts) >= 3:
                    vin = parts[2].strip()
                    generated_vins.append(vin)
    
    print(f"Expected VINs: {len(expected_vins)}")
    print(f"Generated VINs: {len(generated_vins)}")
    
    # Check which expected VINs are found
    found_vins = []
    missing_vins = []
    
    for vin in expected_vins:
        if vin in generated_vins:
            found_vins.append(vin)
        else:
            missing_vins.append(vin)
    
    print(f"\n=== VIN OVERLAP RESULTS ===")
    print(f"Expected VINs found in result: {len(found_vins)}/{len(expected_vins)}")
    print(f"Missing VINs: {len(missing_vins)}")
    
    if missing_vins:
        print("\nMissing VINs:")
        for vin in missing_vins:
            print(f"  - {vin}")
    
    # Check for extra VINs (not in expected list)
    extra_vins = []
    for vin in generated_vins:
        if vin not in expected_vins:
            extra_vins.append(vin)
    
    print(f"\nExtra VINs (not expected): {len(extra_vins)}")
    if extra_vins:
        print("Extra VINs:")
        for vin in extra_vins[:10]:  # Show first 10
            print(f"  - {vin}")
        if len(extra_vins) > 10:
            print(f"  ... and {len(extra_vins) - 10} more")
    
    # Print the counts for analysis
    print(f"\n=== ANALYSIS ===")
    print(f"Expected: 27 VINs")
    print(f"Generated: {len(generated_vins)} VINs")
    print(f"Found in result: {len(found_vins)} VINs")
    print(f"Missing from result: {len(missing_vins)} VINs")
    print(f"Extra in result: {len(extra_vins)} VINs")
    
    if len(found_vins) == len(expected_vins):
        print("\n✅ ALL expected VINs are present in the result!")
        print("The issue is the extra VINs being included.")
    else:
        print("\n❌ Some expected VINs are missing from the result!")

if __name__ == "__main__":
    check_vin_overlap()