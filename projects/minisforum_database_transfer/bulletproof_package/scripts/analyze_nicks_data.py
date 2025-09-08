"""
Analyze Nick's exact scraper data to understand the filtering discrepancy
"""
import pandas as pd

def main():
    # Read today's scraper data that Nick used
    csv_path = r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\Raw scraper output from 81125\complete_data-8-11-25.csv'
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)

    print("=== NICK'S SCRAPER DATA ANALYSIS ===")
    print(f"Total records: {len(df)}")
    print(f"Columns: {list(df.columns)}")

    # Find Porsche entries
    porsche_df = df[df['Location'] == 'Porsche St. Louis']
    print(f"\nPorsche St. Louis records: {len(porsche_df)}")

    if len(porsche_df) > 0:
        print("\nFirst 5 Porsche vehicles with stock info:")
        for _, row in porsche_df.head().iterrows():
            vin = row['Vin']
            stock = row['Stock']
            status = row['Status']  
            year = row['Year']
            make = row['Make']
            model = row['Model']
            print(f"  {vin} - Stock: {repr(stock)} - Status: {repr(status)} - {year} {make} {model}")
        
        # Check Nick's VINs specifically
        nicks_vins = [
            'WP1AE2AY2SDA17074', 'WP1BA2AY2SDA32139', 'WP0AA2YA6SL010964', 'WP0AA2YAXSL010949',
            'WP0AD2Y10SSA50361', 'WP1AB2XA9SL153644', 'WP1AN2AY2SDA22713', 'WP1AG2AY1SDA26116',
            'WP0CA2A82SK212948', 'WP0AB2A83SK261659', 'WP1AA2A55SLB15197', 'WP1AC2XA8SL176362',
            'WP1AG2A51SLB43769', 'WP1AA2A52SLB15299', 'WP1AA2A55SLB15300', 'WP1AA2A5XSLB15292',
            'WP1AA2XAXSL003397', 'WP0BB2A96PS233990', 'WP1BA2AY5SDA30921', 'WP0AA2A9XSS206203',
            'WP0BB2A9XMS235253', 'WDDZF8KB8JA374280'
        ]
        
        print(f"\n=== NICK'S 22 VINS IN THE SCRAPER DATA ===")
        found_nicks = porsche_df[porsche_df['Vin'].isin(nicks_vins)]
        print(f"Found {len(found_nicks)} of Nick's 22 VINs in the scraper data")
        
        valid_stock_count = 0
        empty_stock_count = 0
        
        for _, row in found_nicks.iterrows():
            vin = row['Vin']
            stock = row['Stock']
            status = row['Status']
            has_stock = stock and str(stock).strip() != '' and str(stock).strip().lower() != 'nan'
            if has_stock:
                valid_stock_count += 1
            else:
                empty_stock_count += 1
            print(f"  {vin} - Stock: {repr(stock)} ({'VALID' if has_stock else 'EMPTY/NaN'}) - Status: {repr(status)}")
        
        print(f"\nNick's VINs with valid stock numbers: {valid_stock_count}/{len(found_nicks)}")
        print(f"Nick's VINs with empty/NaN stock: {empty_stock_count}/{len(found_nicks)}")
            
        # Check stock field patterns in all Porsche data
        print(f"\n=== STOCK FIELD ANALYSIS IN RAW CSV ===")
        
        # Count different types of stock values
        empty_stock = 0
        valid_stock = 0
        nan_stock = 0
        
        for _, row in porsche_df.iterrows():
            stock = row['Stock']
            if not stock or str(stock).strip() == '':
                empty_stock += 1
            elif str(stock).strip().lower() == 'nan':
                nan_stock += 1 
            else:
                valid_stock += 1
        
        print(f"  Empty/NULL stock: {empty_stock}")
        print(f"  Valid stock numbers: {valid_stock}")  
        print(f"  'NaN' string stock: {nan_stock}")
        print(f"  Total Porsche vehicles: {len(porsche_df)}")
        
        # Show vehicles WITH stock numbers (these should get graphics)
        print(f"\n=== PORSCHE VEHICLES WITH VALID STOCK (SHOULD GET GRAPHICS) ===")
        valid_stock_df = porsche_df[
            (porsche_df['Stock'] != '') & 
            (porsche_df['Stock'].str.lower() != 'nan') &
            (porsche_df['Stock'].notna())
        ]
        
        print(f"Porsche vehicles with valid stock: {len(valid_stock_df)}")
        print("\nFirst 10 with valid stock:")
        for _, row in valid_stock_df.head(10).iterrows():
            vin = row['Vin']
            stock = row['Stock']
            in_nicks = vin in nicks_vins
            marker = "★" if in_nicks else " "
            print(f"  {marker} {vin} - Stock: {stock}")
        
        # Count how many of these match Nick's list
        valid_from_nicks = valid_stock_df[valid_stock_df['Vin'].isin(nicks_vins)]
        print(f"\nOf the {len(valid_stock_df)} vehicles with valid stock:")
        print(f"  {len(valid_from_nicks)} are in Nick's list of 22")
        print(f"  {len(valid_stock_df) - len(valid_from_nicks)} are NOT in Nick's list")
        
        print(f"\n=== THE DISCREPANCY EXPLAINED ===")
        print(f"Nick expects: 22 vehicles")
        print(f"We would filter to: {len(valid_stock_df)} vehicles (with valid stock)")
        print(f"Difference: {22 - len(valid_stock_df)} vehicles")
        print(f"\nThis suggests Nick is NOT filtering out vehicles with missing stock numbers!")
        
    else:
        print("No Porsche St. Louis records found in the scraper data!")

if __name__ == "__main__":
    main()