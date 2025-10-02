import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
os.chdir(os.path.join(os.path.dirname(__file__), 'web_gui'))

from database_connection import db_manager
from datetime import date

dealership = "Serra Honda O'Fallon"

print("=" * 80)
print(f"SEASONING FILTER DIAGNOSTIC: {dealership}")
print("=" * 80)
print()

# Get active import
active_import = db_manager.execute_query("""
    SELECT import_id, import_date, total_vehicles
    FROM scraper_imports
    WHERE %s = ANY(dealerships_list)
    AND status = 'active'
    ORDER BY import_date DESC
    LIMIT 1
""", (dealership,), fetch='one')

if not active_import:
    print("[ERROR] No active import found")
    sys.exit(1)

print(f"Active Import ID: {active_import['import_id']}")
print(f"Import Date: {active_import['import_date']}")
print()

# Check vehicles NOT in VIN log
not_in_log = db_manager.execute_query("""
    SELECT vin, type, stock, date_in_stock
    FROM raw_vehicle_data
    WHERE location = %s
    AND import_id = %s
    AND type IN ('New', 'Used', 'Certified Used')
    AND vin NOT IN (SELECT vin FROM serra_honda_ofallon_vin_log)
""", (dealership, active_import['import_id']))

print(f"Total vehicles NOT in VIN log: {len(not_in_log)}")
print()

# Analyze date_in_stock population
has_date = 0
no_date = 0
missing_stock = 0
seasoned_enough = 0
too_new = 0

seasoning_days = 7

for vehicle in not_in_log:
    # Check stock
    if not vehicle['stock'] or vehicle['stock'] == '' or vehicle['stock'] == '*':
        missing_stock += 1
        continue

    # Check date_in_stock
    date_in_stock = vehicle['date_in_stock']
    if not date_in_stock:
        no_date += 1
        continue

    has_date += 1

    # Calculate days on lot
    if isinstance(date_in_stock, str):
        from datetime import datetime
        date_in_stock = datetime.strptime(date_in_stock, '%Y-%m-%d').date()
    elif hasattr(date_in_stock, 'date'):
        date_in_stock = date_in_stock.date()

    days_on_lot = (date.today() - date_in_stock).days

    if days_on_lot < seasoning_days:
        too_new += 1
    else:
        seasoned_enough += 1

print("FILTER BREAKDOWN")
print("-" * 80)
print(f"Vehicles with missing/blank stock: {missing_stock}")
print(f"Vehicles with NO date_in_stock: {no_date}")
print(f"Vehicles with date_in_stock: {has_date}")
print(f"  - Seasoned enough (>= {seasoning_days} days): {seasoned_enough}")
print(f"  - Too new (< {seasoning_days} days): {too_new}")
print()
print(f"EXPECTED CAO RESULT: {seasoned_enough} vehicles")
print()

# Show sample vehicles with date_in_stock
if has_date > 0:
    print("Sample vehicles with dates:")
    print("-" * 80)
    count = 0
    for vehicle in not_in_log:
        if vehicle['date_in_stock'] and vehicle['stock'] and vehicle['stock'] != '' and vehicle['stock'] != '*':
            date_in_stock = vehicle['date_in_stock']
            if isinstance(date_in_stock, str):
                from datetime import datetime
                date_in_stock = datetime.strptime(date_in_stock, '%Y-%m-%d').date()
            elif hasattr(date_in_stock, 'date'):
                date_in_stock = date_in_stock.date()

            days_on_lot = (date.today() - date_in_stock).days
            status = "PASS" if days_on_lot >= seasoning_days else "FILTERED"

            print(f"  VIN: ...{vehicle['vin'][-8:]} | Stock: {vehicle['stock']} | Date: {date_in_stock} | Days: {days_on_lot} | [{status}]")
            count += 1
            if count >= 10:
                break
