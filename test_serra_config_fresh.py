#!/usr/bin/env python3
"""
CACHE BUSTING TEST: Serra Honda O'Fallon Configuration Verification
Tests if the updated configuration is being loaded correctly from fresh database query
"""
import sys
import json
sys.path.append('C:/Users/Workstation_1/Documents/Tools/ClaudeCode/projects/minisforum_database_transfer/bulletproof_package/scripts')

from database_connection import db_manager
from datetime import datetime

def test_fresh_config():
    """Test fresh configuration loading with cache busting"""
    print("=== CACHE BUSTING TEST: Serra Honda O'Fallon Configuration ===")
    
    # CACHE BUSTING: Force fresh query with timestamp ordering
    config = db_manager.execute_query("""
        SELECT filtering_rules, updated_at FROM dealership_configs 
        WHERE name = %s AND is_active = true
        ORDER BY updated_at DESC NULLS LAST
    """, ("Serra Honda O'Fallon",))
    
    if not config:
        print("[ERROR] No active configuration found for Serra Honda O'Fallon")
        return False
        
    filtering_rules = config[0]['filtering_rules']
    updated_at = config[0]['updated_at']
    
    print(f"[SUCCESS] Fresh config loaded - Updated: {updated_at}")
    print(f"[CONFIG] Raw filtering_rules: {json.dumps(filtering_rules, indent=2)}")
    
    # Check for seasoning filter
    seasoning_days = filtering_rules.get('seasoning_days', 0)
    print(f"[SEASONING] seasoning_days: {seasoning_days}")
    
    if seasoning_days == 7:
        print("[SUCCESS] 7-day seasoning filter found in configuration!")
        return True
    else:
        print(f"[ERROR] Expected 7-day seasoning filter, found: {seasoning_days}")
        return False

def test_vehicle_dates():
    """Test if vehicles have date_in_stock data for seasoning filter"""
    print("\n=== TESTING VEHICLE DATE DATA ===")
    
    vehicles = db_manager.execute_query("""
        SELECT vin, date_in_stock, price
        FROM normalized_vehicle_data 
        WHERE location = %s
        AND date_in_stock IS NOT NULL
        LIMIT 5
    """, ("Serra Honda O'Fallon",))
    
    if vehicles:
        print(f"[SUCCESS] Found {len(vehicles)} vehicles with date_in_stock data")
        for v in vehicles:
            if v['date_in_stock']:
                days_old = (datetime.now().date() - v['date_in_stock']).days
                print(f"  VIN: {v['vin']} - Stock Date: {v['date_in_stock']} - Days: {days_old}")
    else:
        print("[WARNING] No vehicles found with date_in_stock data")
        
    # Count total vehicles
    total = db_manager.execute_query("""
        SELECT COUNT(*) as count FROM normalized_vehicle_data 
        WHERE location = %s
    """, ("Serra Honda O'Fallon",))
    
    print(f"[INFO] Total Serra Honda O'Fallon vehicles: {total[0]['count'] if total else 0}")

if __name__ == "__main__":
    config_ok = test_fresh_config()
    test_vehicle_dates()
    
    if config_ok:
        print("\n[SUCCESS] Configuration cache busting test PASSED - 7-day filter loaded")
    else:
        print("\n[ERROR] Configuration cache busting test FAILED - Old config still cached")