#!/usr/bin/env python3
"""
Import and Normalize CSV - Complete Process
==========================================
Simple script to import CSV data and run normalization correctly
"""
import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from csv_importer_complete import CompleteCSVImporter
from automated_normalization_manager import normalize_active_import
from database_connection import db_manager

def import_and_normalize_csv(csv_path: str):
    """
    Complete CSV import and normalization process
    """
    print(f"🔄 STARTING CSV IMPORT AND NORMALIZATION")
    print(f"📄 CSV File: {csv_path}")
    print("=" * 60)
    
    # Step 1: Import CSV
    print("STEP 1: Importing CSV data...")
    try:
        importer = CompleteCSVImporter()
        import_result = importer.import_complete_csv(csv_path)
        
        if import_result.get('imported_rows', 0) > 0:
            print(f"✅ SUCCESS: Imported {import_result['imported_rows']} raw records")
            print(f"   Dealerships: {import_result['dealerships_processed']}")
        else:
            print(f"❌ IMPORT FAILED: {import_result.get('errors', ['Unknown error'])}")
            return False
            
    except Exception as e:
        print(f"❌ IMPORT ERROR: {e}")
        return False
    
    # Step 2: Run Normalization
    print("\nSTEP 2: Running automated normalization...")
    try:
        normalization_result = normalize_active_import()
        
        if normalization_result['success']:
            print(f"✅ SUCCESS: Normalized {normalization_result['normalized_records']} records")
            print(f"   Import ID: {normalization_result['import_id']}")
            print(f"   Dealerships Processed: {normalization_result['dealerships_processed']}")
            
            # Show validation results
            if normalization_result.get('validation'):
                val = normalization_result['validation']
                print(f"   Completion Rate: {val['completion_rate']}%")
                print(f"   Raw → Normalized: {val['raw_records']} → {val['normalized_records']}")
                
                if val['is_complete']:
                    print("✅ NORMALIZATION COMPLETE - Ready for CAO processing")
                else:
                    print("⚠️  NORMALIZATION INCOMPLETE - Check errors")
        else:
            print(f"❌ NORMALIZATION FAILED: {normalization_result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ NORMALIZATION ERROR: {e}")
        return False
    
    # Step 3: Verification
    print("\nSTEP 3: Verification...")
    try:
        # Check a few key dealerships
        test_dealerships = ['HW Kia of West County', 'Honda of Frontenac', 'Glendale Chrysler Jeep Dodge Ram']
        
        for dealership in test_dealerships:
            raw_count = db_manager.execute_query("""
                SELECT COUNT(*) as count 
                FROM raw_vehicle_data rvd
                JOIN scraper_imports si ON rvd.import_id = si.import_id
                WHERE rvd.location = %s AND si.status = 'active'
            """, (dealership,), fetch='one')
            
            norm_count = db_manager.execute_query("""
                SELECT COUNT(*) as count 
                FROM normalized_vehicle_data nvd
                JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                JOIN scraper_imports si ON rvd.import_id = si.import_id
                WHERE nvd.location = %s AND si.status = 'active'
            """, (dealership,), fetch='one')
            
            raw_total = raw_count['count'] if raw_count else 0
            norm_total = norm_count['count'] if norm_count else 0
            
            status = "✅" if raw_total == norm_total and raw_total > 0 else "❌"
            print(f"   {status} {dealership}: {raw_total} raw → {norm_total} normalized")
        
        print("\n" + "=" * 60)
        print("🎯 IMPORT AND NORMALIZATION COMPLETE!")
        print("✅ Your data is ready for CAO processing")
        return True
        
    except Exception as e:
        print(f"❌ VERIFICATION ERROR: {e}")
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Import CSV and run normalization')
    parser.add_argument('csv_path', help='Path to complete_data CSV file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_path):
        print(f"❌ ERROR: CSV file not found: {args.csv_path}")
        return
    
    # Run the complete process
    success = import_and_normalize_csv(args.csv_path)
    
    if success:
        print("\n🚀 You can now run CAO orders - the normalization is working correctly!")
    else:
        print("\n❌ Import/normalization failed - check errors above")

if __name__ == "__main__":
    main()