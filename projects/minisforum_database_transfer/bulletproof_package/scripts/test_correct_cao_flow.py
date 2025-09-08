"""
Test the correct CAO workflow:
1. Fresh scraper data 
2. Pre-filter (remove in-transit, no stock)
3. Compare against ALL VINs in dealership VIN log
4. Result = VINs needing graphics
"""
import pandas as pd
import sys
sys.path.insert(0, 'scripts')
from database_connection import db_manager

def main():
    print("=== TESTING CORRECT CAO WORKFLOW ===")

    # Step 1: Load fresh scraper data
    csv_path = r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\Raw scraper output from 81125\complete_data-8-11-25.csv'
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    
    porsche_df = df[df['Location'] == 'Porsche St. Louis']
    print(f"Step 1: Fresh Porsche inventory: {len(porsche_df)} vehicles")

    # Step 2: Pre-filter
    filtered_df = porsche_df[
        (porsche_df['Stock'] != '') & 
        (porsche_df['Stock'].str.lower() != 'nan') &
        (porsche_df['Stock'].notna()) &
        (~porsche_df['Status'].str.lower().str.contains('transit', na=False))
    ]
    
    print(f"Step 2: After pre-filtering: {len(filtered_df)} vehicles")
    
    # Step 3: Get ALL VINs in Porsche VIN log
    vin_log_query = "SELECT vin FROM porsche_st_louis_vin_log;"
    vin_log_results = db_manager.execute_query(vin_log_query)
    vin_log_set = {row['vin'] for row in vin_log_results}
    
    print(f"Step 3: VINs in Porsche log: {len(vin_log_set)}")
    
    # Step 4: Find NEW VINs (in filtered data but NOT in VIN log)
    filtered_vins = set(filtered_df['Vin'])
    new_vins = filtered_vins - vin_log_set
    
    print(f"Step 4: NEW VINs needing graphics: {len(new_vins)}")
    
    # Check against Nick's expected result
    nicks_vins = {
        'WP1AE2AY2SDA17074', 'WP1BA2AY2SDA32139', 'WP0AA2YA6SL010964', 'WP0AA2YAXSL010949',
        'WP0AD2Y10SSA50361', 'WP1AB2XA9SL153644', 'WP1AN2AY2SDA22713', 'WP1AG2AY1SDA26116',
        'WP0CA2A82SK212948', 'WP0AB2A83SK261659', 'WP1AA2A55SLB15197', 'WP1AC2XA8SL176362',
        'WP1AG2A51SLB43769', 'WP1AA2A52SLB15299', 'WP1AA2A55SLB15300', 'WP1AA2A5XSLB15292',
        'WP1AA2XAXSL003397', 'WP0BB2A96PS233990', 'WP1BA2AY5SDA30921', 'WP0AA2A9XSS206203',
        'WP0BB2A9XMS235253', 'WDDZF8KB8JA374280'
    }
    
    print(f"\\n=== COMPARISON WITH NICK'S EXPECTED RESULT ===")
    print(f"Nick expects: 22 vehicles")
    print(f"We calculated: {len(new_vins)} vehicles")
    
    # Check overlap
    matching_vins = new_vins.intersection(nicks_vins)
    extra_vins = new_vins - nicks_vins
    missing_vins = nicks_vins - new_vins
    
    print(f"\\nMatching Nick's list: {len(matching_vins)}")
    print(f"Extra VINs we have: {len(extra_vins)}")  
    print(f"Missing from our result: {len(missing_vins)}")
    
    if len(missing_vins) > 0:
        print(f"\\nMissing VINs (Nick has but we don't):")
        for vin in sorted(missing_vins):
            # Check if this VIN is in our filtered data
            in_filtered = vin in filtered_vins
            in_vin_log = vin in vin_log_set
            print(f"  {vin} - In filtered: {in_filtered}, In VIN log: {in_vin_log}")
    
    if len(extra_vins) > 0:
        print(f"\\nExtra VINs (we have but Nick doesn't) - first 5:")
        for vin in sorted(extra_vins)[:5]:
            print(f"  {vin}")
    
    print(f"\\n=== DIAGNOSIS ===")
    if len(new_vins) == 22 and len(matching_vins) == 22:
        print("PERFECT! The workflow is working correctly")
    elif len(missing_vins) > 0:
        print("Issue: Nick's VINs are in our VIN log (marked as already processed)")
        print("Solution: Those VINs should NOT be in the VIN log yet")
    elif len(extra_vins) > 0:
        print("Issue: We have more new VINs than expected")
        print("Solution: Some of our 'new' VINs should be in the VIN log")

if __name__ == "__main__":
    main()