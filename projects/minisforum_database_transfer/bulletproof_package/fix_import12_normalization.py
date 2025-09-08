import sys
sys.path.insert(0, 'scripts')
from database_connection import db_manager
from scraper_data_normalizer import ScraperDataNormalizer

print('=== EMERGENCY FIX: NORMALIZE IMPORT 12 MISSING DATA ===')

def fix_import12_normalization():
    """Normalize the missing 1429 records from Import 12"""
    
    try:
        # Check current normalization status
        print('1. Check current Import 12 normalization status...')
        coverage_query = """
            SELECT 
                COUNT(rvd.id) as total_raw,
                COUNT(nvd.id) as total_normalized,
                COUNT(rvd.id) - COUNT(nvd.id) as missing_normalized
            FROM raw_vehicle_data rvd
            LEFT JOIN normalized_vehicle_data nvd ON rvd.id = nvd.raw_data_id
            WHERE rvd.import_id = 12
        """
        
        coverage = db_manager.execute_query(coverage_query)
        if coverage:
            cov = coverage[0]
            print(f'  Total RAW records: {cov["total_raw"]}')
            print(f'  Total NORMALIZED records: {cov["total_normalized"]}') 
            print(f'  Missing NORMALIZED records: {cov["missing_normalized"]}')
            
            if cov["missing_normalized"] == 0:
                print('  SUCCESS: No missing normalized records!')
                return True
        
        # Get the raw records that need normalization
        print('\n2. Get raw records needing normalization...')
        missing_records_query = """
            SELECT rvd.id as raw_data_id, rvd.vin, rvd.location, rvd.type
            FROM raw_vehicle_data rvd
            LEFT JOIN normalized_vehicle_data nvd ON rvd.id = nvd.raw_data_id
            WHERE rvd.import_id = 12
            AND nvd.id IS NULL
            ORDER BY rvd.id
            LIMIT 10
        """
        
        missing_records = db_manager.execute_query(missing_records_query)
        print(f'Sample of {len(missing_records)} missing records:')
        for record in missing_records:
            print(f'  - {record["vin"]} | Location: {record["location"]} | Type: {record["type"]}')
        
        # Initialize the normalizer
        print('\n3. Initialize normalizer and process missing records...')
        normalizer = ScraperDataNormalizer()
        
        # Process all missing records in batches
        batch_size = 1000
        processed_count = 0
        
        while True:
            # Get next batch of missing records
            batch_query = """
                SELECT rvd.*
                FROM raw_vehicle_data rvd
                LEFT JOIN normalized_vehicle_data nvd ON rvd.id = nvd.raw_data_id
                WHERE rvd.import_id = 12
                AND nvd.id IS NULL
                ORDER BY rvd.id
                LIMIT %s
            """
            
            batch_records = db_manager.execute_query(batch_query, [batch_size])
            
            if not batch_records:
                print(f'  No more records to process. Total processed: {processed_count}')
                break
            
            print(f'  Processing batch of {len(batch_records)} records...')
            
            # Normalize each record in the batch
            for raw_record in batch_records:
                try:
                    normalized_record = normalizer.normalize_vehicle(raw_record)
                    
                    # Insert normalized record
                    insert_query = """
                        INSERT INTO normalized_vehicle_data 
                        (raw_data_id, vin, year, make, model, trim, vehicle_condition, 
                         price, location, on_lot_status, fuel_type, transmission, 
                         drivetrain, body_style, exterior_color, interior_color, 
                         mileage, stock_number, certified, vehicle_url, image_url)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    db_manager.execute_query(insert_query, [
                        normalized_record['raw_data_id'],
                        normalized_record['vin'],
                        normalized_record['year'],
                        normalized_record['make'],
                        normalized_record['model'],
                        normalized_record['trim'],
                        normalized_record['vehicle_condition'],
                        normalized_record['price'],
                        normalized_record['location'],
                        normalized_record['on_lot_status'],
                        normalized_record['fuel_type'],
                        normalized_record['transmission'],
                        normalized_record['drivetrain'],
                        normalized_record['body_style'],
                        normalized_record['exterior_color'],
                        normalized_record['interior_color'],
                        normalized_record['mileage'],
                        normalized_record['stock_number'],
                        normalized_record['certified'],
                        normalized_record['vehicle_url'],
                        normalized_record['image_url']
                    ])
                    
                    processed_count += 1
                    
                    if processed_count % 100 == 0:
                        print(f'    Processed {processed_count} records...')
                        
                except Exception as e:
                    print(f'    ERROR normalizing {raw_record.get("vin", "unknown")}: {e}')
                    continue
        
        # Verify the fix
        print('\n4. Verify normalization fix...')
        final_coverage = db_manager.execute_query(coverage_query)
        if final_coverage:
            cov = final_coverage[0]
            print(f'  Final RAW records: {cov["total_raw"]}')
            print(f'  Final NORMALIZED records: {cov["total_normalized"]}')
            print(f'  Remaining missing: {cov["missing_normalized"]}')
            
            if cov["missing_normalized"] == 0:
                print('  SUCCESS: All Import 12 records now normalized!')
                return True
            else:
                print(f'  WARNING: Still {cov["missing_normalized"]} records missing')
                return False
        
        return False
        
    except Exception as e:
        print(f'ERROR during normalization fix: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = fix_import12_normalization()
    if success:
        print('\nIMPORT 12 NORMALIZATION FIX COMPLETED SUCCESSFULLY!')
    else:
        print('\nIMPORT 12 NORMALIZATION FIX FAILED - MANUAL INTERVENTION REQUIRED')