#!/usr/bin/env python3
"""
Debug Rusty Drewing CAO filtering issue
Compare received VINs vs expected VINs to identify the problem
"""

import sys
import csv
from pathlib import Path
from datetime import datetime

current_file = Path(__file__).resolve()
sys.path.insert(0, str(current_file.parent / 'scripts'))

from database_connection import db_manager

# Expected VINs (correct ones you should have gotten)
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

def analyze_vinlog_status():
    """Check which expected VINs are in the vinlog vs not in vinlog"""
    print("=== ANALYZING VINLOG STATUS ===")
    
    in_vinlog = []
    not_in_vinlog = []
    
    for vin in EXPECTED_VINS:
        check_query = "SELECT vin, order_number, created_at FROM rusty_drewing_chevrolet_buick_gmc_vin_log WHERE vin = %s"
        result = db_manager.execute_query(check_query, [vin])
        
        if result:
            in_vinlog.append(vin)
            print(f"[IN VINLOG] {vin} - Order: {result[0]['order_number']}, Date: {result[0]['created_at']}")
        else:
            not_in_vinlog.append(vin)
            print(f"[NOT IN VINLOG] {vin}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Expected VINs in vinlog: {len(in_vinlog)}")
    print(f"Expected VINs NOT in vinlog: {len(not_in_vinlog)}")
    
    return in_vinlog, not_in_vinlog

def check_current_inventory():
    """Check current active inventory for Rusty Drewing"""
    print("\n=== CHECKING CURRENT ACTIVE INVENTORY ===")
    
    # Get active import ID
    import_query = """
        SELECT import_id, status, location, import_date, vehicle_count 
        FROM scraper_imports 
        WHERE location = 'Rusty Drewing Chevrolet Buick GMC' 
        AND status = 'active'
    """
    
    active_import = db_manager.execute_query(import_query)
    if not active_import:
        print("[ERROR] No active import found for Rusty Drewing")
        return
    
    import_info = active_import[0]
    print(f"Active Import ID: {import_info['import_id']}")
    print(f"Import Date: {import_info['import_date']}")
    print(f"Vehicle Count: {import_info['vehicle_count']}")
    
    # Check how many of expected VINs are in current inventory
    expected_in_inventory = []
    expected_not_in_inventory = []
    
    for vin in EXPECTED_VINS:
        inventory_query = """
            SELECT vin, type, location
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE si.status = 'active' 
            AND si.location = 'Rusty Drewing Chevrolet Buick GMC'
            AND nvd.vin = %s
        """
        
        result = db_manager.execute_query(inventory_query, [vin])
        if result:
            expected_in_inventory.append(vin)
            print(f"[IN INVENTORY] {vin} - Type: {result[0]['type']}")
        else:
            expected_not_in_inventory.append(vin)
            print(f"[NOT IN INVENTORY] {vin}")
    
    print(f"\nExpected VINs in current inventory: {len(expected_in_inventory)}")
    print(f"Expected VINs NOT in current inventory: {len(expected_not_in_inventory)}")

def compare_received_vs_expected():
    """Compare what we received vs what we expected"""
    print("\n=== COMPARING RECEIVED VS EXPECTED ===")
    
    received_vins = extract_received_vins()
    print(f"Total VINs received: {len(received_vins)}")
    print(f"Total VINs expected: {len(EXPECTED_VINS)}")
    
    # Find VINs that were received but shouldn't have been (should be in vinlog)
    extra_vins = [vin for vin in received_vins if vin not in EXPECTED_VINS]
    print(f"\nExtra VINs received (should have been filtered out): {len(extra_vins)}")
    
    # Check if these extra VINs are in the vinlog
    extra_in_vinlog = []
    extra_not_in_vinlog = []
    
    for vin in extra_vins[:10]:  # Check first 10
        check_query = "SELECT vin FROM rusty_drewing_chevrolet_buick_gmc_vin_log WHERE vin = %s"
        result = db_manager.execute_query(check_query, [vin])
        
        if result:
            extra_in_vinlog.append(vin)
            print(f"[EXTRA - IN VINLOG] {vin} (should have been filtered)")
        else:
            extra_not_in_vinlog.append(vin)
            print(f"[EXTRA - NOT IN VINLOG] {vin} (correctly not filtered)")
    
    # Find expected VINs that weren't received
    missing_vins = [vin for vin in EXPECTED_VINS if vin not in received_vins]
    print(f"\nMissing VINs (expected but not received): {len(missing_vins)}")
    for vin in missing_vins:
        print(f"[MISSING] {vin}")

def main():
    print("=== DEBUGGING RUSTY DREWING CAO FILTERING ===")
    print(f"Analysis started at: {datetime.now()}")
    
    # Step 1: Check vinlog status of expected VINs
    analyze_vinlog_status()
    
    # Step 2: Check current inventory 
    check_current_inventory()
    
    # Step 3: Compare received vs expected
    compare_received_vs_expected()
    
    print(f"\nAnalysis completed at: {datetime.now()}")

if __name__ == '__main__':
    main()