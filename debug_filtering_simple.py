"""
Simple debug to test if status and stock filtering works
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'projects', 'minisforum_database_transfer', 'bulletproof_package', 'scripts'))

from database_connection import db_manager

print("=== TESTING FILTERING STEP BY STEP ===")

# Base query
query1 = """
    SELECT COUNT(*) as count FROM normalized_vehicle_data nvd
    JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
    JOIN scraper_imports si ON rvd.import_id = si.import_id
    WHERE nvd.location = %s 
    AND nvd.on_lot_status IN ('onlot', 'on lot')
    AND si.status = 'active'
    AND nvd.vin NOT IN (SELECT vin FROM pappas_toyota_vin_log WHERE vin IS NOT NULL)
"""

result1 = db_manager.execute_query(query1, ('Pappas Toyota',))
count1 = result1[0]['count']
print(f"1. Base CAO query: {count1} vehicles")

# Add vehicle type filter
query2 = query1 + " AND nvd.vehicle_condition IN ('new', 'po', 'cpo')"

result2 = db_manager.execute_query(query2, ('Pappas Toyota',))
count2 = result2[0]['count']
print(f"2. After vehicle type filter: {count2} vehicles (filtered: {count1 - count2})")

# Add status filter
query3 = query2 + """
    AND rvd.status NOT ILIKE '%In-Transit%' 
    AND rvd.status NOT ILIKE '%Sold%' 
    AND rvd.status NOT ILIKE '%Allocated%'
"""

result3 = db_manager.execute_query(query3, ('Pappas Toyota',))
count3 = result3[0]['count']
print(f"3. After status filter: {count3} vehicles (filtered: {count2 - count3})")

# Add stock filter
query4 = query3 + """
    AND rvd.stock IS NOT NULL 
    AND rvd.stock != '' 
    AND rvd.stock != '*'
"""

result4 = db_manager.execute_query(query4, ('Pappas Toyota',))
count4 = result4[0]['count']
print(f"4. After stock filter: {count4} vehicles (filtered: {count3 - count4})")

print(f"\n=== SUMMARY ===")
print(f"Expected final result: 27 vehicles")
print(f"Actual final result: {count4} vehicles")

if count4 == 27:
    print("✓ SUCCESS: All filtering works correctly!")
elif count4 == 80:
    print("✗ ISSUE: No filtering is being applied")
elif count4 > 27:
    print(f"✗ PARTIAL: {count4 - 27} extra vehicles still getting through")
else:
    print(f"✗ OVER-FILTERED: Missing {27 - count4} expected vehicles")

# Check what specific filtering is missing
if count1 == count2:
    print("- Vehicle type filtering: WORKING (no change needed)")
else:
    print(f"- Vehicle type filtering: FILTERED {count1 - count2} vehicles")

if count2 == count3:
    print("- Status filtering: NOT WORKING (no vehicles filtered)")
else:
    print(f"- Status filtering: FILTERED {count2 - count3} vehicles")

if count3 == count4:
    print("- Stock filtering: NOT WORKING (no vehicles filtered)")
else:
    print(f"- Stock filtering: FILTERED {count3 - count4} vehicles")