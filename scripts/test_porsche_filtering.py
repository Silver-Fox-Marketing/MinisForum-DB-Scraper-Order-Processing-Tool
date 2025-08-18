"""
Test Porsche stock filtering to match Nick's 22 vehicle result
"""
import sys
sys.path.insert(0, 'scripts')
from database_connection import db_manager

def main():
    print("=== TESTING CORRECT STOCK FILTERING FOR PORSCHE ===")

    # Get new VINs that have VALID stock numbers (not 'NaN' string)
    filtered_query = """
    SELECT DISTINCT vin, stock, make, model, year, status
    FROM raw_vehicle_data 
    WHERE location = %s
    AND vin NOT IN (SELECT vin FROM porsche_st_louis_vin_log)
    AND stock IS NOT NULL 
    AND stock <> ''
    AND stock <> 'NaN'
    ORDER BY vin;
    """

    filtered_vehicles = db_manager.execute_query(filtered_query, ('Porsche St. Louis',))

    nicks_vins = {
        'WP1AE2AY2SDA17074', 'WP1BA2AY2SDA32139', 'WP0AA2YA6SL010964', 'WP0AA2YAXSL010949',
        'WP0AD2Y10SSA50361', 'WP1AB2XA9SL153644', 'WP1AN2AY2SDA22713', 'WP1AG2AY1SDA26116',
        'WP0CA2A82SK212948', 'WP0AB2A83SK261659', 'WP1AA2A55SLB15197', 'WP1AC2XA8SL176362',
        'WP1AG2A51SLB43769', 'WP1AA2A52SLB15299', 'WP1AA2A55SLB15300', 'WP1AA2A5XSLB15292',
        'WP1AA2XAXSL003397', 'WP0BB2A96PS233990', 'WP1BA2AY5SDA30921', 'WP0AA2A9XSS206203',
        'WP0BB2A9XMS235253', 'WDDZF8KB8JA374280'
    }

    print(f"Vehicles with valid stock numbers (should get graphics): {len(filtered_vehicles)}")

    matching_nicks = []
    not_in_nicks = []

    for vehicle in filtered_vehicles:
        vin = vehicle['vin']
        if vin in nicks_vins:
            matching_nicks.append(vehicle)
        else:
            not_in_nicks.append(vehicle)

    print(f"Matching Nick's list: {len(matching_nicks)}")
    print(f"Not in Nick's list: {len(not_in_nicks)}")

    print(f"\nVehicles matching Nick's list (with valid stock):")
    for vehicle in matching_nicks:
        print(f"  {vehicle['vin']} - Stock: {vehicle['stock']} - {vehicle['year']} {vehicle['make']} {vehicle['model']}")

    print(f"\nFirst 5 vehicles NOT in Nick's list (with valid stock):")
    for vehicle in not_in_nicks[:5]:
        print(f"  {vehicle['vin']} - Stock: {vehicle['stock']} - {vehicle['year']} {vehicle['make']} {vehicle['model']}")

    print(f"\n=== ANALYSIS ===")
    print(f"With proper stock filtering: {len(filtered_vehicles)} vehicles would get graphics")
    print(f"Of those, {len(matching_nicks)} match Nick's list of 22")
    print(f"Missing from our result: {22 - len(matching_nicks)} vehicles")

    # Check what VINs from Nick's list have 'NaN' stock (the issue)
    print(f"\n=== NICK'S VINS WITH 'NaN' STOCK (THE PROBLEM) ===")
    
    for nick_vin in sorted(nicks_vins):
        # Check this VIN in our data
        vin_query = """
        SELECT vin, stock, status
        FROM raw_vehicle_data
        WHERE location = %s AND vin = %s
        LIMIT 1;
        """
        
        result = db_manager.execute_query(vin_query, ('Porsche St. Louis', nick_vin))
        if result:
            vehicle = result[0]
            if vehicle['stock'] == 'NaN':
                print(f"  {nick_vin} - Has 'NaN' stock (would be filtered out)")
            else:
                print(f"  {nick_vin} - Stock: {vehicle['stock']} (should be included)")
        else:
            print(f"  {nick_vin} - NOT in current inventory (Nick has newer data)")

    print(f"\n=== SOLUTION NEEDED ===")
    print("1. Fix CSV importer to handle empty stock fields properly (not convert to 'NaN')")
    print("2. Update filtering logic to match expected behavior")
    print("3. Or get more recent scraper data that matches Nick's timeframe")

if __name__ == "__main__":
    main()