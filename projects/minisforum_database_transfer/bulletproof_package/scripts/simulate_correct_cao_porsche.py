"""
Simulate the correct CAO workflow for Porsche:
1. Fresh scraper data (from today's CSV)
2. Pre-filter: Remove vehicles without stock numbers and in-transit
3. Compare against a PROPERLY SIZED VIN log (not 1329 old VINs)
"""
import pandas as pd
import sys
sys.path.insert(0, 'scripts')
from database_connection import db_manager

def main():
    print("=== SIMULATING CORRECT PORSCHE CAO WORKFLOW ===")

    # Step 1: Load fresh scraper data
    csv_path = r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\Raw scraper output from 81125\complete_data-8-11-25.csv'
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    
    # Get Porsche data
    porsche_df = df[df['Location'] == 'Porsche St. Louis']
    print(f"Step 1: Fresh Porsche inventory: {len(porsche_df)} vehicles")

    # Step 2: Pre-filter - Remove vehicles without stock numbers and in-transit
    # Filter criteria:
    # - Must have valid stock number
    # - Must not be in-transit
    filtered_df = porsche_df[
        (porsche_df['Stock'] != '') & 
        (porsche_df['Stock'].str.lower() != 'nan') &
        (porsche_df['Stock'].notna()) &
        (~porsche_df['Status'].str.lower().str.contains('transit', na=False))
    ]
    
    print(f"Step 2: After pre-filtering (stock + not in-transit): {len(filtered_df)} vehicles")
    
    # Show status breakdown
    status_counts = porsche_df['Status'].value_counts()
    print(f"\nStatus breakdown:")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    
    # Step 3: Get Nick's expected VINs
    nicks_vins = {
        'WP1AE2AY2SDA17074', 'WP1BA2AY2SDA32139', 'WP0AA2YA6SL010964', 'WP0AA2YAXSL010949',
        'WP0AD2Y10SSA50361', 'WP1AB2XA9SL153644', 'WP1AN2AY2SDA22713', 'WP1AG2AY1SDA26116',
        'WP0CA2A82SK212948', 'WP0AB2A83SK261659', 'WP1AA2A55SLB15197', 'WP1AC2XA8SL176362',
        'WP1AG2A51SLB43769', 'WP1AA2A52SLB15299', 'WP1AA2A55SLB15300', 'WP1AA2A5XSLB15292',
        'WP1AA2XAXSL003397', 'WP0BB2A96PS233990', 'WP1BA2AY5SDA30921', 'WP0AA2A9XSS206203',
        'WP0BB2A9XMS235253', 'WDDZF8KB8JA374280'
    }
    
    # Step 4: If we had the RIGHT VIN log (from a few days ago), 
    # then Nick's 22 VINs should be the NEW ones not in that log
    
    print(f"\nStep 3: Nick expects 22 VINs to get graphics")
    print(f"This means the VIN log should contain: {len(filtered_df)} - 22 = {len(filtered_df) - 22} VINs")
    
    # Verify all of Nick's VINs are in our filtered list
    nicks_in_filtered = filtered_df[filtered_df['Vin'].isin(nicks_vins)]
    print(f"\nVerification:")
    print(f"  Nick's VINs in filtered data: {len(nicks_in_filtered)}/22")
    print(f"  Nick's VINs with valid stock: {len(nicks_in_filtered)}/22")
    
    if len(nicks_in_filtered) == 22:
        print(f"  ✅ All of Nick's VINs pass the pre-filtering!")
    else:
        print(f"  ❌ {22 - len(nicks_in_filtered)} of Nick's VINs are missing from filtered data")
        
        missing_vins = set(nicks_vins) - set(nicks_in_filtered['Vin'])
        print(f"  Missing VINs: {missing_vins}")

    # Step 5: What should the VIN log contain?
    print(f"\n=== WHAT THE VIN LOG SHOULD CONTAIN ===")
    print(f"If Nick gets 22 vehicles, the VIN log should have:")
    print(f"  {len(filtered_df) - 22} VINs from recent orders (not {1329})")
    print(f"  This suggests the current VIN log has too many old VINs")
    
    # Show which VINs would NOT be in Nick's result (these should be in VIN log)
    not_nicks = filtered_df[~filtered_df['Vin'].isin(nicks_vins)]
    print(f"\nVINs that should be in VIN log (already processed): {len(not_nicks)}")
    print(f"Sample VINs that should be in log:")
    for _, row in not_nicks.head(5).iterrows():
        print(f"  {row['Vin']} - Stock: {row['Stock']}")
    
    print(f"\n=== SOLUTION ===")
    print(f"1. Clear the Porsche VIN log")
    print(f"2. Add only the {len(not_nicks)} VINs that should be 'already processed'")
    print(f"3. Run CAO - should get exactly {len(nicks_in_filtered)} vehicles")

if __name__ == "__main__":
    main()