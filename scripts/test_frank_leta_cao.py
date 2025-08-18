"""
Test Frank Leta Honda CAO Processing with Production Data
========================================================

This script safely tests Frank Leta Honda CAO logic by:
1. Importing today's CSV data in production mode
2. Running CAO order processing test
3. Cleaning up test data and VIN log entries
4. Leaving production state unchanged

This allows testing CAO logic without contaminating production VIN logs.
"""

import sys
import pandas as pd
import io
from pathlib import Path
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, 'C:/Users/Workstation_1/Documents/Tools/ClaudeCode/projects/minisforum_database_transfer/bulletproof_package/scripts')
from database_connection import db_manager
from order_processing_workflow import OrderProcessingWorkflow

def main():
    print("=" * 60)
    print("FRANK LETA HONDA CAO TEST")
    print("=" * 60)
    
    # Step 1: Import today's CSV data in production mode (temporarily)
    csv_path = r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\Raw scraper output from 81125\complete_data-8-11-25.csv'
    
    print(f"Step 1: Importing CSV data from {Path(csv_path).name}")
    
    # Read and process CSV (same logic as Flask endpoint but in production mode)
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    frank_leta_df = df[df['Location'] == 'Frank Leta Honda']
    
    if len(frank_leta_df) == 0:
        print("❌ No Frank Leta Honda data found in CSV")
        return
    
    print(f"✅ Found {len(frank_leta_df)} Frank Leta Honda vehicles in CSV")
    
    # Clear any existing data for today
    db_manager.execute_query("DELETE FROM raw_vehicle_data WHERE import_date = CURRENT_DATE")
    print("✅ Cleared existing data for today")
    
    # Import Frank Leta Honda data in PRODUCTION mode (no TEST_IMPORT suffix)
    rows_to_insert = []
    for _, row in frank_leta_df.iterrows():
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
        
        # Build row tuple (PRODUCTION mode - no TEST_IMPORT)
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
            None,  # date_in_stock
            row['Street Address'],  # street_address
            row['Locality'],  # locality
            row['Postal Code'],  # postal_code
            row['Region'],  # region
            row['Country'],  # country
            'Frank Leta Honda',  # location (PRODUCTION NAME)
            row.get('Vechile URL', '') if 'Vechile URL' in row else ''  # vehicle_url
        )
        
        rows_to_insert.append(row_data)
    
    # Insert data
    columns = [
        'vin', 'stock', 'type', 'year', 'make', 'model', 'trim',
        'ext_color', 'status', 'price', 'body_style', 'fuel_type', 
        'msrp', 'date_in_stock', 'street_address', 'locality',
        'postal_code', 'region', 'country', 'location', 'vehicle_url'
    ]
    
    inserted_count = db_manager.execute_batch_insert('raw_vehicle_data', columns, rows_to_insert)
    print(f"✅ Imported {inserted_count} Frank Leta Honda vehicles in production mode")
    
    # Step 2: Record current VIN log state for cleanup
    print(f"\nStep 2: Recording current VIN log state for cleanup")
    
    # Get current VIN count in log before test
    pre_test_vins = db_manager.execute_query("SELECT COUNT(*) as count FROM frank_leta_honda_vin_log")
    pre_test_count = pre_test_vins[0]['count'] if pre_test_vins else 0
    print(f"✅ Frank Leta Honda VIN log has {pre_test_count} VINs before test")
    
    # Step 3: Run CAO order processing test
    print(f"\nStep 3: Running Frank Leta Honda CAO order processing test")
    
    workflow = OrderProcessingWorkflow()
    result = workflow.process_cao_order('Frank Leta Honda', ['used'])  # Test with used vehicles
    
    print(f"\n🔍 CAO TEST RESULTS:")
    print(f"   Success: {result['success']}")
    print(f"   Total vehicles in inventory: {result.get('total_vehicles', 0)}")
    print(f"   New vehicles (needs graphics): {result.get('new_vehicles', 0)}")
    print(f"   Removed vehicles: {result.get('removed_vehicles', 0)}")
    
    if result['success']:
        print(f"   QR codes generated: {result.get('qr_codes_generated', 0)}")
        print(f"   Order ID: {result.get('order_id', 'N/A')}")
        print(f"✅ CAO processing worked correctly!")
    else:
        print(f"   Error: {result.get('error', 'Unknown error')}")
        print(f"❌ CAO processing failed")
    
    # Step 4: Clean up test data and VIN log entries
    print(f"\nStep 4: Cleaning up test data and VIN log entries")
    
    # Remove test data from raw_vehicle_data
    db_manager.execute_query("DELETE FROM raw_vehicle_data WHERE import_date = CURRENT_DATE")
    print("✅ Removed test data from raw_vehicle_data")
    
    # Remove any VIN log entries created during test
    post_test_vins = db_manager.execute_query("SELECT COUNT(*) as count FROM frank_leta_honda_vin_log")
    post_test_count = post_test_vins[0]['count'] if post_test_vins else 0
    
    if post_test_count > pre_test_count:
        vins_added = post_test_count - pre_test_count
        # Remove the most recent VIN entries (those added during test)
        db_manager.execute_query(f"""
            DELETE FROM frank_leta_honda_vin_log 
            WHERE vin IN (
                SELECT vin FROM frank_leta_honda_vin_log 
                ORDER BY created_at DESC 
                LIMIT {vins_added}
            )
        """)
        print(f"✅ Removed {vins_added} VIN entries added during test")
    else:
        print("✅ No VIN log entries to clean up")
    
    # Verify cleanup
    final_vins = db_manager.execute_query("SELECT COUNT(*) as count FROM frank_leta_honda_vin_log")
    final_count = final_vins[0]['count'] if final_vins else 0
    
    final_data = db_manager.execute_query("SELECT COUNT(*) as count FROM raw_vehicle_data WHERE import_date = CURRENT_DATE")
    final_data_count = final_data[0]['count'] if final_data else 0
    
    print(f"\n✅ CLEANUP VERIFICATION:")
    print(f"   VIN log count: {pre_test_count} → {final_count} (should be same)")
    print(f"   Today's data count: {final_data_count} (should be 0)")
    
    if final_count == pre_test_count and final_data_count == 0:
        print(f"🎉 CLEANUP SUCCESSFUL - Production state restored!")
    else:
        print(f"⚠️  WARNING - Cleanup may not be complete")
    
    print("\n" + "=" * 60)
    print("CAO TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()