# Database Schema Fix Instructions

## Issue Fixed
The Order Processing Wizard was generating exactly 100 vehicles every time due to a database constraint error that caused a fallback to a hardcoded LIMIT 100 query.

## Root Cause
Schema mismatch between different VIN history table definitions:
- Some files used `scan_date` column
- Others used `order_date` column  
- Missing unique constraint caused conflicts
- Missing columns needed for enhanced VIN logic

## Files Modified

### 1. Database Schema Fix
- **`scripts/fix_vin_history_schema.sql`** - Comprehensive schema alignment script
- **`scripts/run_schema_fix.py`** - Python script to execute the fix

### 2. Order Processing Logic Fix  
- **`scripts/correct_order_processing.py`** - Removed hardcoded LIMIT 100 from fallback query
- Enhanced VIN logging with proper conflict handling using `ON CONFLICT` clause

## To Apply the Fix

### Option 1: Run the Python Script (Recommended)
```bash
cd scripts/
python run_schema_fix.py
```

### Option 2: Run SQL Directly
```bash
psql -d your_database -f scripts/fix_vin_history_schema.sql
```

## What the Fix Does

1. **Schema Alignment**:
   - Renames `scan_date` to `order_date` if needed
   - Adds missing columns (`vehicle_type`, `source`)
   - Creates proper unique constraint: `(dealership_name, vin, order_date)`
   - Updates indexes for optimal performance

2. **Data Cleanup**:
   - Removes duplicate records before adding unique constraint
   - Updates NULL `order_date` values to `CURRENT_DATE`
   - Preserves existing data integrity

3. **Enhanced Logic Support**:
   - Adds `vehicle_type` column for status change detection
   - Adds `source` column to track order types (`CAO_ORDER`, `LIST_ORDER`)
   - Enables cross-dealership opportunity detection

## Testing the Fix

After running the fix, test the Order Processing Wizard:

1. Go to Order Processing tab
2. Select a dealership (e.g., "BMW of West St. Louis")  
3. Choose template type
4. Click "Generate Order"
5. Verify it processes the actual number of vehicles (not exactly 100)

## Expected Results

- **Before**: Always exactly 100 vehicles processed
- **After**: Real vehicle count based on dealership inventory and VIN logic

## Files Created
- `scripts/fix_vin_history_schema.sql` - Database schema fix
- `scripts/run_schema_fix.py` - Automated fix script  
- `DATABASE_FIX_INSTRUCTIONS.md` - This instruction file

The Order Processing Wizard should now work correctly without arbitrary limits.