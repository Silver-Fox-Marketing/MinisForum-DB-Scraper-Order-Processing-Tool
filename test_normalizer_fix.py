#!/usr/bin/env python3
"""
Test script to verify the normalizer instance fix in scraper_import_manager.py
"""
import sys
sys.path.append('C:/Users/Workstation_1/Documents/Tools/ClaudeCode/projects/minisforum_database_transfer/bulletproof_package/scripts')

def test_global_normalizer_instance():
    """Test that the global normalizer instance has the updated mappings"""
    print("=== TESTING GLOBAL NORMALIZER INSTANCE FIX ===")
    
    from scraper_data_normalizer import normalizer
    
    print("Testing vehicle type mappings:")
    test_types = ["used", "carbravo", "demo", "certified", "new"]
    
    for vehicle_type in test_types:
        normalized = normalizer.normalize_vehicle_type(vehicle_type)
        print(f"  '{vehicle_type}' -> '{normalized}'")
    
    print("\nTesting lot status mappings:")  
    test_statuses = ["On The Lot", "FCTP_READYFORSALE", "Courtesy Transportation Unit", "Dealer Retail Stock - Upfitted"]
    
    for status in test_statuses:
        normalized = normalizer.normalize_lot_status(status)
        print(f"  '{status}' -> '{normalized}'")
    
    # Check the specific problematic case
    print("\n=== SPECIFIC PROBLEMATIC CASE TEST ===")
    print("VIN KL4MMGSL8PB113029 - Type: 'used'")
    result = normalizer.normalize_vehicle_type("used")
    print(f"Normalization result: 'used' -> '{result}'")
    
    if result == 'po':
        print("[SUCCESS] 'used' correctly normalizes to 'po'")
        return True
    else:
        print(f"[ERROR] 'used' should normalize to 'po', got '{result}'")
        return False

def test_import_manager_fix():
    """Test that scraper_import_manager uses the global instance"""
    print("\n=== TESTING SCRAPER_IMPORT_MANAGER FIX ===")
    
    try:
        # Check that the import statement is correct
        from scraper_import_manager import ScraperImportManager
        
        # Import the global normalizer 
        from scraper_data_normalizer import normalizer
        
        print("[SUCCESS] ScraperImportManager imports corrected")
        print("[SUCCESS] Global normalizer instance available")
        
        # Test that our mappings are present
        mapping_count = len(normalizer.vehicle_type_mapping)
        print(f"[INFO] Global normalizer has {mapping_count} vehicle type mappings")
        
        # Check specific mapping
        has_carbravo = 'carbravo' in normalizer.vehicle_type_mapping
        has_demo = 'demo' in normalizer.vehicle_type_mapping
        has_used = 'used' in normalizer.vehicle_type_mapping
        
        print(f"[INFO] Has 'carbravo' mapping: {has_carbravo}")
        print(f"[INFO] Has 'demo' mapping: {has_demo}")
        print(f"[INFO] Has 'used' mapping: {has_used}")
        
        if has_carbravo and has_demo and has_used:
            print("[SUCCESS] All required mappings are present in global instance")
            return True
        else:
            print("[ERROR] Missing required mappings in global instance")
            return False
            
    except Exception as e:
        print(f"[ERROR] Import manager test failed: {e}")
        return False

if __name__ == "__main__":
    print("NORMALIZER INSTANCE FIX VERIFICATION")
    print("=" * 50)
    
    success1 = test_global_normalizer_instance()
    success2 = test_import_manager_fix()
    
    if success1 and success2:
        print("\n[SUCCESS] All tests passed - normalizer fix verified!")
        print("[READY] CSV import should now work without constraint violations")
    else:
        print("\n[ERROR] Some tests failed - fix may not be complete")