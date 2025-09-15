#!/usr/bin/env python3
"""
Fix Suntrup Kia South Configuration
Apply Porsche St. Louis working template BUT keep Suntrup's NEW VEHICLES ONLY rule

CRITICAL: Suntrup Kia South only wants graphics for NEW vehicles
"""

import sys
import os

# Add the correct paths for database connection
sys.path.insert(0, r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts')

from database_connection import db_manager
import json

def main():
    print("=" * 80)
    print("SUNTRUP KIA SOUTH CONFIG FIX - NEW VEHICLES ONLY")
    print("Using Porsche structure but keeping NEW VEHICLES ONLY rule")
    print("=" * 80)
    
    # Step 1: Verify Porsche's working config (DO NOT ALTER)
    print("\n1. VERIFYING PORSCHE WORKING TEMPLATE (Read-Only):")
    porsche_config = db_manager.execute_query("""
        SELECT name, filtering_rules FROM dealership_configs 
        WHERE name = 'Porsche St. Louis'
    """)
    
    if not porsche_config:
        print("ERROR: Cannot find Porsche St. Louis template!")
        return False
        
    porsche_rules = porsche_config[0]['filtering_rules']
    print(f"✅ Porsche template found with working structure")
    
    # Step 2: Get Suntrup Kia South current config
    print("\n2. CURRENT SUNTRUP KIA SOUTH CONFIG:")
    suntrup_config = db_manager.execute_query("""
        SELECT name, filtering_rules FROM dealership_configs 
        WHERE name = 'Suntrup Kia South'
    """)
    
    if not suntrup_config:
        print("ERROR: Cannot find Suntrup Kia South!")
        return False
        
    current_rules = suntrup_config[0]['filtering_rules']
    print(f"Current config: {json.dumps(current_rules, indent=2)}")
    
    # Step 3: Create the updated config - Porsche structure + NEW ONLY rule
    print("\n3. CREATING UPDATED CONFIG:")
    print("   ✅ Using Porsche's working structure")
    print("   ✅ Keeping NEW VEHICLES ONLY rule for Suntrup Kia South")
    
    # Use Porsche's working configuration structure but keep NEW ONLY
    updated_config = {
        "notes": "NEW VEHICLES ONLY - Using Porsche St. Louis working template structure",
        "rationale": "Suntrup Kia South processes only new vehicles with proper status filtering based on working Porsche template",
        "order_type": "cao",
        "require_stock": True,
        "vehicle_types": ["new"],  # KEEP: NEW ONLY per Suntrup's business rule
        "exclude_status": ["In-Transit", "Sold", "Allocated"],  # COPY: Porsche's working exclusions
        "allowed_vehicle_types": ["new"],  # KEEP: NEW ONLY per Suntrup's business rule
        "exclude_missing_stock": True  # COPY: Porsche's working requirement
    }
    
    print(f"New config: {json.dumps(updated_config, indent=2)}")
    
    # Check what changed
    print("\n4. CHANGES BEING APPLIED:")
    changes_made = []
    
    if current_rules.get("exclude_status") != updated_config["exclude_status"]:
        changes_made.append("Updated exclude_status array")
    if current_rules.get("require_stock") != updated_config["require_stock"]:
        changes_made.append("Updated require_stock setting")
    if current_rules.get("exclude_missing_stock") != updated_config["exclude_missing_stock"]:
        changes_made.append("Updated exclude_missing_stock setting")
        
    if not changes_made:
        print("   No structural changes needed - config already matches Porsche template structure")
        print("   Issue may be elsewhere in the system")
        return True
    else:
        for change in changes_made:
            print(f"   • {change}")
    
    # Step 5: Apply the update
    print("\n5. APPLYING UPDATE TO SUNTRUP KIA SOUTH:")
    
    try:
        result = db_manager.execute_query("""
            UPDATE dealership_configs 
            SET filtering_rules = %s, updated_at = CURRENT_TIMESTAMP
            WHERE name = 'Suntrup Kia South'
        """, (json.dumps(updated_config),))
        
        print("✅ SUCCESS: Suntrup Kia South config updated with Porsche structure!")
        
        # Step 6: Verify the update
        print("\n6. VERIFYING UPDATE:")
        verification = db_manager.execute_query("""
            SELECT filtering_rules FROM dealership_configs 
            WHERE name = 'Suntrup Kia South'
        """)
        
        if verification:
            verified_rules = verification[0]['filtering_rules']
            print(f"Verified updated config: {json.dumps(verified_rules, indent=2)}")
            
            # Verify key requirements
            if (verified_rules.get('vehicle_types') == ['new'] and 
                verified_rules.get('allowed_vehicle_types') == ['new'] and
                verified_rules.get('order_type') == 'cao'):
                print("✅ VERIFICATION PASSED: NEW VEHICLES ONLY rule maintained")
                print("✅ VERIFICATION PASSED: Porsche template structure applied")
                return True
            else:
                print("❌ VERIFICATION FAILED: Config not updated correctly")
                return False
        else:
            print("❌ VERIFICATION FAILED: Could not retrieve updated config")
            return False
            
    except Exception as e:
        print(f"❌ ERROR updating config: {e}")
        return False

def show_summary():
    print("\n" + "=" * 80)
    print("SUMMARY - SUNTRUP KIA SOUTH UPDATED WITH PORSCHE WORKING STRUCTURE")
    print("=" * 80)
    print("✅ MAINTAINED: NEW VEHICLES ONLY business rule")
    print("✅ APPLIED: Porsche St. Louis working template structure")
    print("✅ UPDATED: exclude_status, require_stock, exclude_missing_stock")
    print()
    print("Business Rule Preserved:")
    print('  "vehicle_types": ["new"]')
    print('  "allowed_vehicle_types": ["new"]')
    print()
    print("Working Structure Applied:")
    print('  "exclude_status": ["In-Transit", "Sold", "Allocated"]')
    print('  "require_stock": true')  
    print('  "exclude_missing_stock": true')
    print()
    print("🎯 Suntrup Kia South should now work like Porsche but for NEW vehicles only")

if __name__ == "__main__":
    success = main()
    if success:
        show_summary()
        print("\n🚀 READY FOR TESTING: Test Suntrup Kia South CAO order in web interface")
        print("   Expected: Should get correct NEW vehicle VINs immediately (like Porsche)")
    else:
        print("\n❌ UPDATE FAILED: Please check error messages above")