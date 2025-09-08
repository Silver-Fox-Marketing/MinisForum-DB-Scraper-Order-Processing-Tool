#!/usr/bin/env python3
"""
Analyze Rusty Drewing raw data to identify why extra VINs weren't filtered out
Check for in-transit status, blank stock numbers, and other filtering issues
"""

import sys
import csv
from pathlib import Path
from datetime import datetime

current_file = Path(__file__).resolve()
sys.path.insert(0, str(current_file.parent / 'scripts'))

from database_connection import db_manager

# Expected VINs (correct ones we should have gotten)
EXPECTED_VINS = [
    '3GKALZEG6TL100587', '3GTPUCEK5SG349734', '1GT4UPEY0SF334364', '3GNAXPEG4TL203843',
    '2GCUKGED9T1100803', '1GT4UNEY7SF365518', 'KL47LBEP3SB237171', 'KL47LBEP0SB237192',
    'KL77LKEP1SC328663', 'KL47LBEP1SB238464', 'KL79MMSL3TB036801', '1GT4UNE74SF372871',
    '1GTUUDE83TZ135520', '1GTUUGELXTZ136217', '1GKS2BR89SR402156', '5GAEVAKS9TJ135067',
    '5GAERAKS7TJ135122', '5GAEVBKSXTJ135634', '1GTUUCE80TZ141186', '3GKALUEG1TL245278',
    '1GCUKGEL9TZ144122', '1GNS6DRD4SR407992', '2FMPK3G95HBC24899', '2G1FK1EJ8A9138610',
    '1GKS2CKJXJR151391', '1GNS6ERD2SR162776', '1GNS6ERD7SR162899', '1GNS6RRD6SR160391',
    '1GNEVNKW6PJ101951', '1GTUUHE84PZ109246', '1GNSKCKC0KR122553', '5XYRKDLF0PG204553',
    '1GC4YPEYXRF140522', '1C4RDJEG2FC154143', '1C6HJTAG3PL531271', '1GCRYBEK8NZ179557',
    '2C3CDXCT2MH581393', '1FTEW1EF8GKE94503', '1G1FF1R75L0135700', '3C6RR7KT9EG288687',
    '3GNAXHEV0KS519779', '1N6AD0EV1GN748327', '2GNAXNEV7L6116137', '1GNEVGKW7LJ283133',
    '5XXG34J28RG232497'
]

def extract_received_vins():
    """Extract VINs from the actual CAO results file"""
    csv_file = Path(r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\orders\Rusty_Drewing_Chevrolet_Buick_GMC\20250903_115229\RUSTYDREWINGCHEVROLETBUICKGMC_09-03 - BILLING.csv")
    
    received_vins = []
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        
        for row in reader:
            if len(row) >= 5 and row[4]:  # VIN is in 5th column (index 4)
                vin = row[4].strip()
                if vin and vin != 'VINLOG:':  # Skip header rows
                    received_vins.append(vin)
    
    return received_vins

def analyze_extra_vins():
    """Analyze the extra VINs that shouldn't have been included"""
    print("=== ANALYZING EXTRA VINs IN CAO RESULTS ===")
    
    received_vins = extract_received_vins()
    extra_vins = [vin for vin in received_vins if vin not in EXPECTED_VINS]
    
    print(f"Total VINs received: {len(received_vins)}")
    print(f"Total VINs expected: {len(EXPECTED_VINS)}")
    print(f"Extra VINs (should have been filtered): {len(extra_vins)}")
    
    if not extra_vins:
        print("[OK] No extra VINs found")
        return
    
    print(f"\n=== ANALYZING {min(20, len(extra_vins))} EXTRA VINs ===")
    
    # Analyze first 20 extra VINs to identify patterns
    problem_categories = {
        'in_transit': [],
        'blank_stock': [],
        'missing_stock': [],
        'offlot_status': [],
        'other': []
    }
    
    for i, vin in enumerate(extra_vins[:20]):
        print(f"\n--- Extra VIN #{i+1}: {vin} ---")
        
        # Get raw data for this VIN
        raw_query = """
            SELECT rvd.vin, rvd.type, rvd.status, rvd.stock, rvd.location,
                   rvd.price, rvd.make, rvd.model, rvd.year, rvd.on_lot_status
            FROM raw_vehicle_data rvd
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE si.status = 'active' 
            AND rvd.location ILIKE '%rusty%drewing%'
            AND rvd.vin = %s
        """
        
        raw_result = db_manager.execute_query(raw_query, [vin])
        if not raw_result:
            print(f"[ERROR] VIN not found in raw data: {vin}")
            continue
        
        raw_data = raw_result[0]
        print(f"Type: {raw_data['type']}")
        print(f"Status: {raw_data['status']}")
        print(f"Stock Number: '{raw_data['stock']}'")
        print(f"On-Lot Status: {raw_data['on_lot_status']}")
        print(f"Year/Make/Model: {raw_data['year']} {raw_data['make']} {raw_data['model']}")
        print(f"Price: {raw_data['price']}")
        
        # Check normalized data
        norm_query = """
            SELECT nvd.vin, nvd.vehicle_condition, nvd.lot_status, nvd.stock_number
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE si.status = 'active'
            AND rvd.location ILIKE '%rusty%drewing%'
            AND nvd.vin = %s
        """
        
        norm_result = db_manager.execute_query(norm_query, [vin])
        if norm_result:
            norm_data = norm_result[0]
            print(f"NORMALIZED - Condition: {norm_data['vehicle_condition']}, Lot Status: {norm_data['lot_status']}")
            
            # Categorize the problem
            if norm_data['lot_status'] == 'offlot':
                problem_categories['offlot_status'].append(vin)
                print("[ISSUE] Vehicle is OFF-LOT - should have been filtered")
            elif not raw_data['stock'] or raw_data['stock'].strip() == '':
                problem_categories['blank_stock'].append(vin)
                print("[ISSUE] Blank stock number - should have been filtered")
            elif 'transit' in (raw_data['status'] or '').lower():
                problem_categories['in_transit'].append(vin)
                print("[ISSUE] In-transit status - should have been filtered")
            else:
                problem_categories['other'].append(vin)
                print("[UNKNOWN] Reason not immediately clear")
        else:
            print("[ERROR] VIN not found in normalized data")
    
    # Summary
    print(f"\n=== PROBLEM CATEGORY SUMMARY ===")
    for category, vins in problem_categories.items():
        if vins:
            print(f"{category.upper()}: {len(vins)} VINs")
            for vin in vins[:5]:  # Show first 5
                print(f"  {vin}")

def check_dealership_filtering_rules():
    """Check what filtering rules should apply to Rusty Drewing"""
    print("\n=== DEALERSHIP FILTERING CONFIGURATION ===")
    
    # Check if there are specific filtering rules for Rusty Drewing
    config_query = """
        SELECT dealership_name, vehicle_types, filters, active
        FROM dealership_configs 
        WHERE dealership_name ILIKE '%rusty%drewing%'
    """
    
    try:
        config_result = db_manager.execute_query(config_query)
        if config_result:
            config = config_result[0]
            print(f"Dealership: {config['dealership_name']}")
            print(f"Vehicle Types: {config['vehicle_types']}")
            print(f"Filters: {config['filters']}")
            print(f"Active: {config['active']}")
        else:
            print("[WARNING] No specific dealership configuration found")
    except Exception as e:
        print(f"[ERROR] Could not check dealership config: {e}")

def main():
    print("=== ANALYZING RUSTY DREWING RAW DATA FOR FILTERING ISSUES ===")
    print(f"Analysis started at: {datetime.now()}")
    
    # Step 1: Analyze the extra VINs
    analyze_extra_vins()
    
    # Step 2: Check dealership filtering rules
    check_dealership_filtering_rules()
    
    print(f"\nAnalysis completed at: {datetime.now()}")

if __name__ == '__main__':
    main()