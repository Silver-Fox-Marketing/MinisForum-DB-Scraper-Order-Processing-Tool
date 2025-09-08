"""
Automated Normalization Manager - CRITICAL ORDER PROCESSING STEP
Consolidates and automates the manual normalization process for imported scraper data
This ensures proper CAO processing until the scraper is fully optimized
"""
import logging
import json
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional
from database_connection import db_manager
from scraper_data_normalizer import normalizer
from scraper_import_manager import ScraperImportManager

logger = logging.getLogger(__name__)

class AutomatedNormalizationManager:
    """Manages automated normalization of imported scraper data"""
    
    def __init__(self, db_manager_instance=None):
        self.db = db_manager_instance or db_manager
        self.import_manager = ScraperImportManager()
        self.normalization_stats = {
            'total_raw_records': 0,
            'normalized_records': 0,
            'dealerships_processed': 0,
            'errors': []
        }
    
    def get_active_import_id(self) -> Optional[int]:
        """Get the current active import ID"""
        active_import = self.db.execute_query(
            "SELECT import_id FROM scraper_imports WHERE status = 'active' LIMIT 1"
        )
        return active_import[0]['import_id'] if active_import else None
    
    def ensure_clean_normalization_state(self, import_id: int) -> bool:
        """
        CRITICAL: Ensure clean normalization state by removing old normalized data
        This prevents contamination from previous import sessions
        """
        try:
            logger.info(f"CLEANING: Removing existing normalized data for Import ID {import_id}")
            
            # Remove any existing normalized records for this import
            cleanup_query = """
                DELETE FROM normalized_vehicle_data 
                WHERE raw_data_id IN (
                    SELECT id FROM raw_vehicle_data WHERE import_id = %s
                )
            """
            cleanup_result = self.db.execute_non_query(cleanup_query, (import_id,))
            logger.info(f"CLEANING: Removed {cleanup_result} existing normalized records")
            
            return True
            
        except Exception as e:
            logger.error(f"CRITICAL: Failed to clean normalization state: {e}")
            return False
    
    def normalize_import_data(self, import_id: int = None) -> Dict:
        """
        MAIN NORMALIZATION FUNCTION - Automates the manual normalization process
        This is the critical step that ensures CAO processing works correctly
        """
        try:
            # Get active import ID if not provided
            if import_id is None:
                import_id = self.get_active_import_id()
                if not import_id:
                    raise Exception("No active import found to normalize")
            
            logger.info(f"AUTOMATION: Starting normalization for Import ID {import_id}")
            
            # STEP 1: Ensure clean normalization state
            if not self.ensure_clean_normalization_state(import_id):
                raise Exception("Failed to clean normalization state")
            
            # STEP 2: Get all raw data that needs normalization
            raw_data_query = """
                SELECT DISTINCT location 
                FROM raw_vehicle_data 
                WHERE import_id = %s
                ORDER BY location
            """
            dealerships = self.db.execute_query(raw_data_query, (import_id,))
            
            logger.info(f"AUTOMATION: Found {len(dealerships)} dealerships to normalize")
            
            # STEP 3: Process each dealership individually
            total_normalized = 0
            
            for dealership_row in dealerships:
                dealership_name = dealership_row['location']
                logger.info(f"AUTOMATION: Normalizing {dealership_name}")
                
                # Get raw records for this dealership
                dealership_raw_query = """
                    SELECT id, vin, stock, type, year, make, model, trim, 
                           status, price, msrp, date_in_stock, location, vehicle_url
                    FROM raw_vehicle_data
                    WHERE location = %s AND import_id = %s
                    ORDER BY id
                """
                raw_records = self.db.execute_query(
                    dealership_raw_query, 
                    (dealership_name, import_id)
                )
                
                if not raw_records:
                    logger.warning(f"AUTOMATION: No raw records found for {dealership_name}")
                    continue
                
                logger.info(f"AUTOMATION: Processing {len(raw_records)} records for {dealership_name}")
                
                # STEP 4: Normalize each record
                normalized_data = []
                for record in raw_records:
                    try:
                        normalized_record = self.normalize_single_record(record)
                        if normalized_record:
                            normalized_data.append(normalized_record)
                    except Exception as e:
                        logger.error(f"AUTOMATION: Failed to normalize record ID {record['id']}: {e}")
                        self.normalization_stats['errors'].append(
                            f"{dealership_name} - Record ID {record['id']}: {str(e)}"
                        )
                
                # STEP 5: Batch insert normalized data
                if normalized_data:
                    self.batch_insert_normalized_data(normalized_data, dealership_name)
                    total_normalized += len(normalized_data)
                
                self.normalization_stats['dealerships_processed'] += 1
                logger.info(f"AUTOMATION: Completed {dealership_name} - {len(normalized_data)} records normalized")
            
            # STEP 6: Update import statistics
            self.import_manager.update_import_stats(import_id)
            
            # STEP 7: Final validation
            validation_result = self.validate_normalization_completeness(import_id)
            
            self.normalization_stats['normalized_records'] = total_normalized
            
            logger.info(f"AUTOMATION: Normalization complete - {total_normalized} records normalized")
            
            return {
                'success': True,
                'import_id': import_id,
                'normalized_records': total_normalized,
                'dealerships_processed': self.normalization_stats['dealerships_processed'],
                'validation': validation_result,
                'stats': self.normalization_stats
            }
            
        except Exception as e:
            logger.error(f"AUTOMATION: Normalization failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'stats': self.normalization_stats
            }
    
    def normalize_single_record(self, record: Dict) -> Optional[Tuple]:
        """
        Normalize a single raw vehicle record
        This applies the same logic as the manual normalization process
        """
        try:
            # Extract data from raw record
            condition_data = record.get('type', '')  # Vehicle type (New/Used/CPO)
            status_data = record.get('status', '')   # Vehicle status (In Stock/On-Lot/etc)
            stock_data = record.get('stock', '')     # Stock number
            
            # CORE NORMALIZATION: Apply the same logic as manual process
            
            # 1. Normalize vehicle type (condition)
            normalized_vehicle_type = normalizer.normalize_vehicle_type(condition_data)
            
            # 2. Normalize lot status from STATUS field
            normalized_lot_status = normalizer.normalize_lot_status(status_data)
            
            # 3. CRITICAL: Apply stock-based and transit-based overrides
            if (not stock_data or 
                'in-transit' in status_data.lower() or 
                'in transit' in status_data.lower() or
                'being built' in status_data.lower()):
                normalized_lot_status = 'offlot'
            
            # 4. Handle NULL stock values for database constraints
            stock_value = stock_data if stock_data else 'AUTO'
            
            # 5. Build normalized record tuple
            normalized_tuple = (
                record['id'],  # raw_data_id
                record['vin'],
                stock_value,  # Use 'AUTO' for NULL stock
                normalized_vehicle_type,  # vehicle_condition (po, cpo, new)
                record['year'],
                record['make'],
                record['model'],
                record['trim'],
                normalized_lot_status,  # status (onlot, offlot)
                record['price'],
                record['msrp'],
                record['date_in_stock'],
                record['location'],
                record['vehicle_url'],
                normalized_lot_status,  # on_lot_status column
                datetime.now(),  # created_at
                datetime.now(),  # updated_at
                date.today()  # last_seen_date
            )
            
            return normalized_tuple
            
        except Exception as e:
            logger.error(f"Failed to normalize record ID {record.get('id', 'unknown')}: {e}")
            raise
    
    def batch_insert_normalized_data(self, normalized_data: List[Tuple], dealership_name: str):
        """Batch insert normalized data using upsert logic"""
        try:
            norm_columns = [
                'raw_data_id', 'vin', 'stock', 'vehicle_condition',
                'year', 'make', 'model', 'trim', 'status', 'price',
                'msrp', 'date_in_stock', 'location', 'vehicle_url', 'on_lot_status',
                'created_at', 'updated_at', 'last_seen_date'
            ]
            
            # Use batch insert - each raw record needs its own normalized record
            result = self.db.execute_batch_insert(
                'normalized_vehicle_data', 
                norm_columns, 
                normalized_data
            )
            
            logger.info(f"AUTOMATION: Upserted {result} normalized records for {dealership_name}")
            
        except Exception as e:
            logger.error(f"AUTOMATION: Failed to insert normalized data for {dealership_name}: {e}")
            raise
    
    def validate_normalization_completeness(self, import_id: int) -> Dict:
        """
        Validate that normalization is complete and correct
        This ensures CAO processing will work properly
        """
        try:
            # Count raw vs normalized records
            raw_count_query = """
                SELECT COUNT(*) as count 
                FROM raw_vehicle_data 
                WHERE import_id = %s
            """
            raw_count = self.db.execute_query(raw_count_query, (import_id,), fetch='one')
            
            normalized_count_query = """
                SELECT COUNT(*) as count 
                FROM normalized_vehicle_data nvd
                JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
                WHERE rvd.import_id = %s
            """
            normalized_count = self.db.execute_query(normalized_count_query, (import_id,), fetch='one')
            
            raw_total = raw_count['count'] if raw_count else 0
            normalized_total = normalized_count['count'] if normalized_count else 0
            
            # Check for missing normalized records
            missing_records = 0
            if raw_total > normalized_total:
                missing_records = raw_total - normalized_total
                logger.warning(f"VALIDATION: {missing_records} records missing normalized data")
            
            # Check dealership consistency
            dealership_validation = self.validate_dealership_consistency(import_id)
            
            validation_result = {
                'raw_records': raw_total,
                'normalized_records': normalized_total,
                'missing_records': missing_records,
                'completion_rate': round((normalized_total / raw_total * 100), 2) if raw_total > 0 else 0,
                'dealership_consistency': dealership_validation,
                'is_complete': missing_records == 0
            }
            
            if validation_result['is_complete']:
                logger.info(f"VALIDATION: ✅ Normalization complete - {normalized_total}/{raw_total} records")
            else:
                logger.error(f"VALIDATION: ❌ Normalization incomplete - {normalized_total}/{raw_total} records")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"VALIDATION: Failed to validate normalization: {e}")
            return {
                'error': str(e),
                'is_complete': False
            }
    
    def validate_dealership_consistency(self, import_id: int) -> Dict:
        """Validate that all dealerships have consistent normalization"""
        try:
            consistency_query = """
                SELECT 
                    rvd.location,
                    COUNT(rvd.id) as raw_count,
                    COUNT(nvd.id) as normalized_count
                FROM raw_vehicle_data rvd
                LEFT JOIN normalized_vehicle_data nvd ON rvd.id = nvd.raw_data_id
                WHERE rvd.import_id = %s
                GROUP BY rvd.location
                ORDER BY rvd.location
            """
            
            results = self.db.execute_query(consistency_query, (import_id,))
            
            dealership_stats = {}
            total_inconsistent = 0
            
            for row in results:
                dealership_name = row['location']
                raw_count = row['raw_count']
                normalized_count = row['normalized_count'] or 0
                
                is_consistent = raw_count == normalized_count
                if not is_consistent:
                    total_inconsistent += 1
                
                dealership_stats[dealership_name] = {
                    'raw_count': raw_count,
                    'normalized_count': normalized_count,
                    'is_consistent': is_consistent,
                    'missing_records': raw_count - normalized_count
                }
            
            return {
                'total_dealerships': len(dealership_stats),
                'consistent_dealerships': len(dealership_stats) - total_inconsistent,
                'inconsistent_dealerships': total_inconsistent,
                'dealership_details': dealership_stats,
                'all_consistent': total_inconsistent == 0
            }
            
        except Exception as e:
            logger.error(f"Failed to validate dealership consistency: {e}")
            return {'error': str(e)}
    
    def run_post_normalization_maintenance(self):
        """Run maintenance tasks after normalization"""
        try:
            logger.info("AUTOMATION: Running post-normalization maintenance")
            
            # Update VIN scan counts
            self.update_vin_scan_counts()
            
            # Vacuum analyze tables for performance
            self.db.vacuum_analyze('normalized_vehicle_data')
            
            logger.info("AUTOMATION: Post-normalization maintenance complete")
            
        except Exception as e:
            logger.error(f"Post-normalization maintenance failed: {e}")
    
    def update_vin_scan_counts(self):
        """Update VIN scan counts in normalized data"""
        try:
            query = """
                UPDATE normalized_vehicle_data n
                SET vin_scan_count = (
                    SELECT COUNT(DISTINCT order_date)
                    FROM vin_history v
                    WHERE v.vin = n.vin AND v.dealership_name = n.location
                )
                WHERE last_seen_date = CURRENT_DATE
            """
            
            updated = self.db.execute_non_query(query)
            logger.info(f"AUTOMATION: Updated VIN scan counts for {updated} vehicles")
            
        except Exception as e:
            logger.error(f"Failed to update VIN scan counts: {e}")

# Convenience functions for easy usage
def normalize_active_import() -> Dict:
    """
    MAIN FUNCTION: Normalize the current active import
    Call this after importing new scraper data
    """
    manager = AutomatedNormalizationManager()
    result = manager.normalize_import_data()
    
    if result['success']:
        manager.run_post_normalization_maintenance()
    
    return result

def normalize_specific_import(import_id: int) -> Dict:
    """
    Normalize a specific import by ID
    Useful for re-normalizing historical imports
    """
    manager = AutomatedNormalizationManager()
    result = manager.normalize_import_data(import_id)
    
    if result['success']:
        manager.run_post_normalization_maintenance()
    
    return result

def validate_normalization_status() -> Dict:
    """
    Check the normalization status of the active import
    Returns detailed validation information
    """
    manager = AutomatedNormalizationManager()
    active_import_id = manager.get_active_import_id()
    
    if not active_import_id:
        return {'error': 'No active import found'}
    
    return manager.validate_normalization_completeness(active_import_id)

if __name__ == "__main__":
    """
    Command line usage for automated normalization
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated Normalization Manager')
    parser.add_argument('--normalize', action='store_true', 
                       help='Normalize the active import')
    parser.add_argument('--import-id', type=int,
                       help='Specific import ID to normalize')
    parser.add_argument('--validate', action='store_true',
                       help='Validate normalization status')
    
    args = parser.parse_args()
    
    if args.normalize:
        if args.import_id:
            result = normalize_specific_import(args.import_id)
        else:
            result = normalize_active_import()
        
        print("\n" + "="*60)
        print("AUTOMATED NORMALIZATION RESULTS")
        print("="*60)
        
        if result['success']:
            print(f"✅ SUCCESS: Normalized {result['normalized_records']} records")
            print(f"Import ID: {result['import_id']}")
            print(f"Dealerships Processed: {result['dealerships_processed']}")
            
            if result.get('validation'):
                val = result['validation']
                print(f"Completion Rate: {val['completion_rate']}%")
                print(f"Raw Records: {val['raw_records']}")
                print(f"Normalized Records: {val['normalized_records']}")
        else:
            print(f"❌ FAILED: {result['error']}")
        
        if result['stats']['errors']:
            print(f"\nErrors: {len(result['stats']['errors'])}")
            for error in result['stats']['errors'][:5]:
                print(f"  - {error}")
    
    elif args.validate:
        result = validate_normalization_status()
        
        print("\n" + "="*60)
        print("NORMALIZATION VALIDATION STATUS")
        print("="*60)
        
        if 'error' in result:
            print(f"❌ ERROR: {result['error']}")
        else:
            status = "✅ COMPLETE" if result['is_complete'] else "❌ INCOMPLETE"
            print(f"Status: {status}")
            print(f"Raw Records: {result['raw_records']}")
            print(f"Normalized Records: {result['normalized_records']}")
            print(f"Completion Rate: {result['completion_rate']}%")
            
            if result.get('dealership_consistency'):
                dc = result['dealership_consistency']
                print(f"Dealership Consistency: {dc['consistent_dealerships']}/{dc['total_dealerships']} consistent")
    
    else:
        print("Use --normalize to run normalization or --validate to check status")
        print("Use --help for more options")