"""
Import fresh August 11 scraper data directly into raw_vehicle_data
"""
import pandas as pd
import sys
sys.path.insert(0, 'scripts')
from database_connection import db_manager
from datetime import datetime

def main():
    print("=== IMPORTING FRESH AUGUST 11 SCRAPER DATA ===")
    
    csv_path = r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\Raw scraper output from 81125\complete_data-8-11-25.csv'
    
    # Read CSV data
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    print(f"Total records in CSV: {len(df)}")
    
    # Map CSV columns to database columns
    column_mapping = {
        'Vin': 'vin',
        'Stock': 'stock', 
        'Type': 'type',
        'Year': 'year',
        'Make': 'make',
        'Model': 'model',
        'Trim': 'trim',
        'Ext Color': 'ext_color',
        'Status': 'status',
        'Price': 'price',
        'Body Style': 'body_style',
        'Fuel Type': 'fuel_type',
        'MSRP': 'msrp',
        'Date In Stock': 'date_in_stock',
        'Street Address': 'street_address',
        'Locality': 'locality', 
        'Postal Code': 'postal_code',
        'Region': 'region',
        'Country': 'country',
        'Location': 'location',
        'Vechile URL': 'vehicle_url'  # Note: typo in CSV header
    }
    
    # First, clear today's data to avoid duplicates
    print("Clearing today's raw_vehicle_data...")
    db_manager.execute_query("DELETE FROM raw_vehicle_data WHERE import_date = CURRENT_DATE")
    
    # Process in batches by dealership
    dealership_groups = df.groupby('Location')
    total_imported = 0
    
    for dealership_name, group_df in dealership_groups:
        print(f"\nProcessing {dealership_name}: {len(group_df)} vehicles")
        
        # Prepare data for bulk insert
        rows_to_insert = []
        
        for _, row in group_df.iterrows():
            # Convert year to int if possible
            try:
                year_val = int(row['Year']) if row['Year'] and row['Year'].isdigit() else None
            except:
                year_val = None
            
            # Convert price to float if possible
            try:
                price_str = str(row['Price']).replace('$', '').replace(',', '')
                price_val = float(price_str) if price_str and price_str != '' else None
            except:
                price_val = None
                
            # Convert MSRP to float if possible  
            try:
                msrp_str = str(row['MSRP']).replace('$', '').replace(',', '')
                msrp_val = float(msrp_str) if msrp_str and msrp_str != '' else None
            except:
                msrp_val = None
            
            # Build row tuple
            row_data = (
                row['Vin'].strip().upper(),  # vin
                row['Stock'] if row['Stock'] != '' else None,  # stock
                row['Type'],  # type  
                year_val,  # year
                row['Make'],  # make
                row['Model'],  # model
                row['Trim'],  # trim
                row['Ext Color'],  # ext_color
                row['Status'],  # status
                price_val,  # price
                row['Body Style'],  # body_style
                row['Fuel Type'],  # fuel_type
                msrp_val,  # msrp
                None,  # date_in_stock (convert later if needed)
                row['Street Address'],  # street_address
                row['Locality'],  # locality
                row['Postal Code'],  # postal_code
                row['Region'],  # region
                row['Country'],  # country
                dealership_name,  # location
                row['Vechile URL'] if 'Vechile URL' in row and row['Vechile URL'] else ''  # vehicle_url
            )
            
            rows_to_insert.append(row_data)
        
        # Bulk insert this dealership's data
        if rows_to_insert:
            columns = [
                'vin', 'stock', 'type', 'year', 'make', 'model', 'trim',
                'ext_color', 'status', 'price', 'body_style', 'fuel_type', 
                'msrp', 'date_in_stock', 'street_address', 'locality',
                'postal_code', 'region', 'country', 'location', 'vehicle_url'
            ]
            
            try:
                inserted_count = db_manager.execute_batch_insert(
                    'raw_vehicle_data',
                    columns, 
                    rows_to_insert
                )
                print(f"  Imported {inserted_count} vehicles for {dealership_name}")
                total_imported += inserted_count
                
            except Exception as e:
                print(f"  ERROR importing {dealership_name}: {e}")
    
    print(f"\n=== IMPORT COMPLETE ===")
    print(f"Total vehicles imported: {total_imported}")
    
    # Verify key dealerships
    key_dealerships = ['Porsche St. Louis', 'BMW of West St. Louis', 'Bommarito West County']
    
    print(f"\nVerification - vehicles imported today:")
    for dealership in key_dealerships:
        try:
            result = db_manager.execute_query(
                "SELECT COUNT(*) as count FROM raw_vehicle_data WHERE location = %s AND import_date = CURRENT_DATE",
                (dealership,)
            )
            count = result[0]['count'] if result else 0
            print(f"  {dealership}: {count} vehicles")
        except Exception as e:
            print(f"  {dealership}: ERROR - {e}")

if __name__ == "__main__":
    main()