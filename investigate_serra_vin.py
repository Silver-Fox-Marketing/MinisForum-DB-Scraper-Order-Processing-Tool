"""
Investigate Serra Honda VIN issue - why VINs are appearing in CAO when they shouldn't
"""
import sys
sys.path.insert(0, r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts')

from database_connection import db_manager

def investigate_vin(vin):
    """Investigate a specific VIN across all relevant tables"""

    print(f"\n{'='*80}")
    print(f"INVESTIGATING VIN: {vin}")
    print(f"{'='*80}\n")

    # 1. Check raw_vehicle_data with active import
    print("[1] Checking raw_vehicle_data (active imports only)...")
    raw_query = """
        SELECT
            rvd.id, rvd.vin, rvd.location, rvd.status, rvd.stock, rvd.price,
            rvd.type, rvd.import_id,
            si.status as import_status, si.import_timestamp as import_date
        FROM raw_vehicle_data rvd
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE rvd.vin = %s
        ORDER BY si.import_timestamp DESC
    """
    raw_results = db_manager.execute_query(raw_query, (vin,))

    if raw_results:
        for row in raw_results:
            print(f"  Raw Data ID: {row['id']}")
            print(f"  Location: {row['location']}")
            print(f"  Status: {row['status']}")
            print(f"  Type: {row['type']}")
            print(f"  Stock: {row['stock']}")
            print(f"  Price: {row['price']}")
            print(f"  Import ID: {row['import_id']}")
            print(f"  Import Status: {row['import_status']}")
            print(f"  Import Date: {row['import_date']}")
            print()
    else:
        print("  [NOT FOUND] VIN not in raw_vehicle_data")

    # 2. Check normalized_vehicle_data
    print("[2] Checking normalized_vehicle_data...")
    norm_query = """
        SELECT
            nvd.id, nvd.vin, nvd.location, nvd.vehicle_condition,
            nvd.on_lot_status, nvd.stock, nvd.raw_data_id,
            rvd.price, rvd.status as raw_status,
            si.status as import_status
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.vin = %s
        ORDER BY nvd.created_at DESC
    """
    norm_results = db_manager.execute_query(norm_query, (vin,))

    if norm_results:
        for row in norm_results:
            print(f"  Normalized ID: {row['id']}")
            print(f"  Location: {row['location']}")
            print(f"  Vehicle Condition: {row['vehicle_condition']}")
            print(f"  On-Lot Status: {row['on_lot_status']}")
            print(f"  Stock: {row['stock']}")
            print(f"  Price (from raw): {row['price']}")
            print(f"  Raw Status: {row['raw_status']}")
            print(f"  Import Status: {row['import_status']}")
            print()
    else:
        print("  [NOT FOUND] VIN not in normalized_vehicle_data")

    # 3. Check Serra Honda VIN log
    print("[3] Checking serra_honda_vin_log...")
    vinlog_query = """
        SELECT vin, order_type, created_at
        FROM serra_honda_vin_log
        WHERE vin = %s
        ORDER BY created_at DESC
    """
    vinlog_results = db_manager.execute_query(vinlog_query, (vin,))

    if vinlog_results:
        for row in vinlog_results:
            print(f"  VIN: {row['vin']}")
            print(f"  Order Type: {row['order_type']}")
            print(f"  Processed Date: {row['created_at']}")
            print()
    else:
        print("  [NOT FOUND] VIN not in serra_honda_vin_log")
        print("  ** THIS IS WHY IT'S APPEARING IN CAO RESULTS **")

    # 4. Check if VIN would match CAO query for Serra Honda
    print("[4] Testing CAO query logic for Serra Honda...")

    # Get Serra Honda config
    config_query = """
        SELECT vehicle_types, exclude_conditions
        FROM dealership_configs
        WHERE dealership_name = 'Serra Honda'
    """
    config = db_manager.execute_query(config_query, fetch='one')

    if config:
        print(f"  Serra Honda Config:")
        print(f"    Vehicle Types: {config['vehicle_types']}")
        print(f"    Exclude Conditions: {config['exclude_conditions']}")

    # Simulate CAO query
    cao_query = """
        SELECT nvd.vin, nvd.vehicle_condition, nvd.on_lot_status,
               rvd.price, rvd.status as raw_status, si.status as import_status
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = 'Serra Honda'
        AND nvd.vin = %s
        AND si.status = 'active'
        AND nvd.on_lot_status IN ('onlot', 'on lot')
    """
    cao_results = db_manager.execute_query(cao_query, (vin,))

    if cao_results:
        print("\n  [CAO MATCH] This VIN WOULD be returned by CAO query:")
        for row in cao_results:
            print(f"    VIN: {row['vin']}")
            print(f"    Vehicle Condition: {row['vehicle_condition']}")
            print(f"    On-Lot Status: {row['on_lot_status']}")
            print(f"    Price: {row['price']}")
            print(f"    Raw Status: {row['raw_status']}")
            print(f"    Import Status: {row['import_status']}")
    else:
        print("\n  [NO CAO MATCH] This VIN would NOT be returned by CAO query")

    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    # Investigate the specific VIN
    investigate_vin("5J6RW2H95LL030886")

    # Also check how many other VINs are in this situation
    print("\n[BONUS] Checking how many Serra Honda vehicles are NOT in VIN log...")

    count_query = """
        SELECT COUNT(*) as missing_count
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.location = 'Serra Honda'
        AND si.status = 'active'
        AND nvd.on_lot_status IN ('onlot', 'on lot')
        AND nvd.vin NOT IN (SELECT vin FROM serra_honda_vin_log)
    """

    result = db_manager.execute_query(count_query, fetch='one')
    if result:
        print(f"  Total Serra Honda vehicles NOT in VIN log: {result['missing_count']}")

        # Show sample of these VINs
        sample_query = """
            SELECT nvd.vin, nvd.vehicle_condition, rvd.price
            FROM normalized_vehicle_data nvd
            JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
            JOIN scraper_imports si ON rvd.import_id = si.import_id
            WHERE nvd.location = 'Serra Honda'
            AND si.status = 'active'
            AND nvd.on_lot_status IN ('onlot', 'on lot')
            AND nvd.vin NOT IN (SELECT vin FROM serra_honda_vin_log)
            LIMIT 10
        """
        samples = db_manager.execute_query(sample_query)

        if samples:
            print(f"\n  Sample VINs (showing first 10):")
            for s in samples:
                print(f"    {s['vin']} - {s['vehicle_condition']} - ${s['price']}")
