
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
