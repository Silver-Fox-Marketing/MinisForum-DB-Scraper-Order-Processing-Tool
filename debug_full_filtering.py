"""
Debug the FULL CAO filtering logic including status and stock filters
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'projects', 'minisforum_database_transfer', 'bulletproof_package', 'scripts'))

from database_connection import db_manager

print("=== DEBUGGING FULL CAO FILTERING ===")

# Step 1: Base CAO query (what we tested before)
base_query = """
    SELECT nvd.vin, nvd.vehicle_condition, rvd.status as raw_status,
           rvd.stock, nvd.on_lot_status
    FROM normalized_vehicle_data nvd
    JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
    JOIN scraper_imports si ON rvd.import_id = si.import_id
    WHERE nvd.location = %s 
    AND nvd.on_lot_status IN ('onlot', 'on lot')
    AND si.status = 'active'
    AND nvd.vin NOT IN (SELECT vin FROM pappas_toyota_vin_log WHERE vin IS NOT NULL)
"""

base_result = db_manager.execute_query(base_query, ('Pappas Toyota',))
print(f"Step 1 - Base CAO query: {len(base_result)} vehicles")

# Step 2: Add vehicle type filtering (new, po, cpo)
type_query = base_query + """
    AND nvd.vehicle_condition IN ('new', 'po', 'cpo')
"""

type_result = db_manager.execute_query(type_query, ('Pappas Toyota',))
print(f"Step 2 - After vehicle type filter: {len(type_result)} vehicles")

# Step 3: Add status exclusions (In-Transit, Sold, Allocated)
status_query = type_query + """
    AND (rvd.status NOT ILIKE '%In-Transit%' 
         AND rvd.status NOT ILIKE '%Sold%' 
         AND rvd.status NOT ILIKE '%Allocated%')
"""

status_result = db_manager.execute_query(status_query, ('Pappas Toyota',))
print(f"Step 3 - After status exclusions: {len(status_result)} vehicles")

# Step 4: Add stock requirement (exclude missing stock)
stock_query = status_query + """
    AND rvd.stock IS NOT NULL 
    AND rvd.stock != '' 
    AND rvd.stock != '*'
"""

stock_result = db_manager.execute_query(stock_query, ('Pappas Toyota',))
print(f"Step 4 - After stock requirements: {len(stock_result)} vehicles")

print(f"\n=== FILTERING IMPACT ===")
print(f"Base query → Type filter: -{len(base_result) - len(type_result)} vehicles")
print(f"Type filter → Status filter: -{len(type_result) - len(status_result)} vehicles") 
print(f"Status filter → Stock filter: -{len(status_result) - len(stock_result)} vehicles")

# Check what's being filtered out at each step
if len(status_result) != len(stock_result):
    print(f"\n=== VEHICLES FILTERED BY STOCK REQUIREMENTS ===")
    
    # Get vehicles that fail stock requirements
    stock_issues_query = status_query + """
        AND (rvd.stock IS NULL 
             OR rvd.stock = '' 
             OR rvd.stock = '*')
    """
    
    stock_issues = db_manager.execute_query(stock_issues_query, ('Pappas Toyota',))
    print(f"Vehicles with stock issues: {len(stock_issues)}")
    
    for i, vehicle in enumerate(stock_issues[:5]):
        print(f"  {i+1}. {vehicle['vin']} - Stock: '{vehicle['stock']}'")

if len(type_result) != len(status_result):
    print(f"\n=== VEHICLES FILTERED BY STATUS EXCLUSIONS ===")
    
    # Get vehicles that fail status requirements
    status_issues_query = type_query + """
        AND (rvd.status ILIKE '%In-Transit%' 
             OR rvd.status ILIKE '%Sold%' 
             OR rvd.status ILIKE '%Allocated%')
    """
    
    status_issues = db_manager.execute_query(status_issues_query, ('Pappas Toyota',))
    print(f"Vehicles with status issues: {len(status_issues)}")
    
    for i, vehicle in enumerate(status_issues[:5]):
        print(f"  {i+1}. {vehicle['vin']} - Status: '{vehicle['raw_status']}'")

print(f"\n=== FINAL RESULT ===")
print(f"Expected: 27 vehicles")
print(f"Actual after all filtering: {len(stock_result)} vehicles")

if len(stock_result) == 27:
    print("SUCCESS: Filtering works correctly!")
elif len(stock_result) == 80:
    print("ISSUE: Filtering is not being applied in the CAO system")
else:
    print(f"PARTIAL: Some filtering is working, but not complete")