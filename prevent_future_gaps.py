#!/usr/bin/env python3
"""
Prevent Future Normalization Gaps
=================================
Implement measures to ensure this normalization gap issue never happens again.
"""

import sys
from pathlib import Path

current_file = Path(__file__).resolve()
sys.path.insert(0, str(current_file.parent / 'scripts'))

from database_connection import db_manager

def create_normalization_monitoring():
    """Create database functions and triggers to monitor normalization gaps"""
    
    print('=== IMPLEMENTING FUTURE NORMALIZATION GAP PREVENTION ===')
    
    try:
        # 1. Create a function to check normalization completeness
        print('1. Creating normalization completeness check function...')
        
        completeness_function = """
        CREATE OR REPLACE FUNCTION check_normalization_completeness(import_id_param INTEGER)
        RETURNS TABLE(
            import_id INTEGER,
            total_raw INTEGER,
            total_normalized INTEGER,
            missing_normalized INTEGER,
            completion_percentage NUMERIC
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                si.import_id,
                COUNT(rvd.id)::INTEGER as total_raw,
                COUNT(nvd.id)::INTEGER as total_normalized,
                (COUNT(rvd.id) - COUNT(nvd.id))::INTEGER as missing_normalized,
                CASE 
                    WHEN COUNT(rvd.id) = 0 THEN 0
                    ELSE ROUND((COUNT(nvd.id)::NUMERIC / COUNT(rvd.id)::NUMERIC) * 100, 2)
                END as completion_percentage
            FROM scraper_imports si
            JOIN raw_vehicle_data rvd ON si.import_id = rvd.import_id
            LEFT JOIN normalized_vehicle_data nvd ON rvd.id = nvd.raw_data_id
            WHERE si.import_id = import_id_param
            GROUP BY si.import_id;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        db_manager.execute_query(completeness_function)
        print('   Normalization completeness check function created')
        
        # 2. Create a function to check for active import normalization issues
        print('2. Creating active import monitoring function...')
        
        active_import_check = """
        CREATE OR REPLACE FUNCTION check_active_import_normalization()
        RETURNS TABLE(
            import_id INTEGER,
            dealership_count INTEGER,
            total_raw INTEGER,
            total_normalized INTEGER,
            missing_normalized INTEGER,
            completion_percentage NUMERIC,
            status VARCHAR
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                si.import_id,
                COUNT(DISTINCT rvd.location)::INTEGER as dealership_count,
                COUNT(rvd.id)::INTEGER as total_raw,
                COUNT(nvd.id)::INTEGER as total_normalized,
                (COUNT(rvd.id) - COUNT(nvd.id))::INTEGER as missing_normalized,
                CASE 
                    WHEN COUNT(rvd.id) = 0 THEN 0
                    ELSE ROUND((COUNT(nvd.id)::NUMERIC / COUNT(rvd.id)::NUMERIC) * 100, 2)
                END as completion_percentage,
                si.status
            FROM scraper_imports si
            JOIN raw_vehicle_data rvd ON si.import_id = rvd.import_id
            LEFT JOIN normalized_vehicle_data nvd ON rvd.id = nvd.raw_data_id
            WHERE si.status = 'active'
            GROUP BY si.import_id, si.status;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        db_manager.execute_query(active_import_check)
        print('   Active import monitoring function created')
        
        # 3. Test the monitoring functions
        print('3. Testing monitoring functions...')
        
        # Test with Import 12
        test_completeness = db_manager.execute_query("SELECT * FROM check_normalization_completeness(12)")
        if test_completeness:
            result = test_completeness[0]
            print(f'   Import 12 completeness: {result["completion_percentage"]}% ({result["total_normalized"]}/{result["total_raw"]})')
        
        # Test active imports
        test_active = db_manager.execute_query("SELECT * FROM check_active_import_normalization()")
        if test_active:
            print('   Active imports:')
            for result in test_active:
                print(f'     Import {result["import_id"]}: {result["completion_percentage"]}% complete ({result["missing_normalized"]} missing)')
        
        # 4. Create a view for easy monitoring
        print('4. Creating monitoring view...')
        
        monitoring_view = """
        CREATE OR REPLACE VIEW normalization_health_check AS
        SELECT 
            si.import_id,
            si.status,
            si.import_date,
            COUNT(DISTINCT rvd.location) as dealership_count,
            COUNT(rvd.id) as total_raw,
            COUNT(nvd.id) as total_normalized,
            (COUNT(rvd.id) - COUNT(nvd.id)) as missing_normalized,
            CASE 
                WHEN COUNT(rvd.id) = 0 THEN 0
                ELSE ROUND((COUNT(nvd.id)::NUMERIC / COUNT(rvd.id)::NUMERIC) * 100, 2)
            END as completion_percentage,
            CASE
                WHEN si.status = 'active' AND (COUNT(rvd.id) - COUNT(nvd.id)) > 0 THEN 'CRITICAL'
                WHEN si.status = 'active' AND (COUNT(rvd.id) - COUNT(nvd.id)) = 0 THEN 'HEALTHY'
                WHEN si.status != 'active' THEN 'ARCHIVED'
                ELSE 'UNKNOWN'
            END as health_status
        FROM scraper_imports si
        LEFT JOIN raw_vehicle_data rvd ON si.import_id = rvd.import_id
        LEFT JOIN normalized_vehicle_data nvd ON rvd.id = nvd.raw_data_id
        GROUP BY si.import_id, si.status, si.import_date
        ORDER BY si.import_id DESC;
        """
        
        db_manager.execute_query(monitoring_view)
        print('   Monitoring view created')
        
        # 5. Test the monitoring view
        test_view = db_manager.execute_query("SELECT * FROM normalization_health_check WHERE status = 'active' LIMIT 5")
        if test_view:
            print('   Active import health status:')
            for result in test_view:
                print(f'     Import {result["import_id"]}: {result["health_status"]} ({result["completion_percentage"]}% complete)')
        
        return True
        
    except Exception as e:
        print(f'ERROR creating monitoring functions: {e}')
        import traceback
        traceback.print_exc()
        return False

def create_prevention_recommendations():
    """Document prevention recommendations"""
    
    recommendations = """
# NORMALIZATION GAP PREVENTION GUIDE
=====================================

## Immediate Monitoring
1. **Check Active Import Health**: 
   SELECT * FROM normalization_health_check WHERE status = 'active' AND health_status = 'CRITICAL';

2. **Before CAO Processing**:
   - Always verify active import is 100% normalized
   - Use: SELECT * FROM check_active_import_normalization();

## Future Import Process Improvements

### 1. Enhanced Import Manager
Update `scraper_import_manager.py` to:
- Automatically check normalization completeness after import
- Refuse to mark import as 'active' if normalization is incomplete
- Add automatic retry logic for failed normalizations

### 2. CAO Process Validation
Update `correct_order_processing.py` to:
- Check normalization health before processing
- Fail fast if active import has normalization gaps
- Add validation logging

### 3. Database Constraints
Consider adding:
- Trigger to prevent active imports with incomplete normalization
- Foreign key constraints to ensure data integrity
- Regular automated health checks

## Emergency Response Plan
If normalization gaps are detected:
1. Identify missing records: check_normalization_completeness(import_id)
2. Run emergency normalization: normalize_existing_[dealership].py
3. Verify fix: SELECT * FROM normalization_health_check WHERE import_id = X
4. Test CAO process before proceeding

## Monthly Maintenance
- Review normalization_health_check view
- Archive old imports with 100% normalization
- Clean up duplicate normalized records
- Monitor for new gap patterns
"""
    
    # Write recommendations to file
    recommendations_file = Path(__file__).parent / 'NORMALIZATION_PREVENTION_GUIDE.md'
    recommendations_file.write_text(recommendations)
    print(f'Prevention guide written to: {recommendations_file}')

if __name__ == '__main__':
    success = create_normalization_monitoring()
    if success:
        print('\nMONITORING FUNCTIONS CREATED SUCCESSFULLY!')
        create_prevention_recommendations()
        print('\nFUTURE NORMALIZATION GAPS PREVENTION IMPLEMENTED!')
    else:
        print('\nFAILED TO CREATE MONITORING FUNCTIONS')