# Dealership Standardization Process

## Overview

This document outlines the systematic process for standardizing dealership configurations and VIN log synchronization to achieve production-ready status for CAO (Comparative Analysis Order) processing in the Silver Fox Order Processing System.

**Current Status:** 11 of 36 dealerships completed (30.6% complete)

## Template Reference

The standardized configuration template is located at:
```
C:\Users\Workstation_1\Documents\Tools\ClaudeCode\FINAL_DEALER_CONFIG_TEMPLATE_9.16.md
```

This template contains the master configuration format that all dealerships should follow for consistent CAO processing behavior.

## Standardization Process

### Phase 1: Configuration Analysis
1. **Check Current Configuration**
   ```bash
   cd projects/minisforum_database_transfer/bulletproof_package/scripts
   py -c "
   from database_connection import db_manager
   import json
   result = db_manager.execute_query(
       'SELECT filtering_rules FROM dealership_configs WHERE name = \"[DEALERSHIP_NAME]\" AND is_active = true',
       fetch='one'
   )
   config = result['filtering_rules'] if result else None
   print(json.dumps(config, indent=2) if config else 'No config found')
   "
   ```

2. **Identify Issues**
   - Old format fields (`exclude_conditions` instead of `exclude_status`)
   - Missing critical filters (`exclude_missing_stock_number`, `exclude_in_transit`)
   - Incorrect `order_type` (should be `"cao"`)
   - Contradictory vehicle type settings

### Phase 2: VIN Log Synchronization

#### Step 1: Assess Current VIN Log
```bash
# Check existing VIN log entries
SELECT COUNT(*) as total_entries,
       COUNT(DISTINCT vin) as unique_vins,
       MAX(order_date) as last_order_date
FROM [dealership_name]_vin_log;
```

#### Step 2: Analyze CSV Structure
- Locate current system VIN log CSV file
- Examine format (usually ORDER, VINS columns)
- Count total entries and identify duplicates
- Note order number patterns

#### Step 3: Modify Table Structure (if needed)
```sql
-- Remove unique constraint to allow duplicate VINs
ALTER TABLE [dealership_name]_vin_log
DROP CONSTRAINT [dealership_name]_vin_log_vin_key;
```

#### Step 4: Complete VIN Log Import
```python
# Parse CSV with order tracking
current_order = None
vin_entries = []

for row in csv_reader:
    order = row.get('ORDER', '').strip()
    vin = row.get('VINS', '').strip()

    if order:
        current_order = order

    if vin and len(vin) > 5:
        order_number = current_order if current_order else 'BASELINE'
        vin_entries.append({
            'vin': vin,
            'order_number': order_number
        })

# Import with required fields
insert_data = []
for entry in vin_entries:
    insert_data.append((
        entry['vin'],
        '[DEALERSHIP_NAME]',
        date(2025, 9, 15),    # order_date
        'HISTORICAL',         # order_type
        entry['order_number'], # order_number
        datetime.now(),       # created_at
        date(2025, 9, 15),    # processed_date
        'shortcut_pack'       # template_type
    ))
```

### Phase 3: Configuration Update

#### Step 1: Apply Standardized Template
```python
from datetime import datetime
import json

# Standard configuration template
config = {
    "notes": "Standardized configuration based on South County DCJR template - CACHE BUST " + datetime.now().isoformat(),
    "order_type": "cao",
    "days_on_lot": {"min": 0, "max": 999},
    "price_range": {"max": 999999, "min": 0},
    "require_stock": True,
    "vehicle_types": ["new", "used"],
    "exclude_status": ["In-Transit", "Sold", "Allocated"],
    "exclude_in_transit": True,
    "allowed_vehicle_types": ["new", "cpo", "po", "certified", "pre-owned"],
    "exclude_missing_stock_number": True
}

# Update database
UPDATE dealership_configs
SET filtering_rules = %s,
    updated_at = CURRENT_TIMESTAMP
WHERE name = '[DEALERSHIP_NAME]' AND is_active = true
```

#### Step 2: Cache Busting
```bash
# Kill all Python processes to clear module cache
powershell "Get-Process python | Stop-Process -Force"

# Restart Flask server
cd "projects/minisforum_database_transfer/bulletproof_package/web_gui"
py app.py
```

### Phase 4: Verification

#### Step 1: Verify Configuration Loading
Check server logs for:
```
[CACHE DEBUG] Loaded fresh config for [DEALERSHIP_NAME]: {
  "order_type": "cao",
  "exclude_status": ["In-Transit", "Sold", "Allocated"],
  ...
}
```

#### Step 2: Test CAO Processing Impact
```sql
-- Check current inventory vs VIN log
SELECT
    (SELECT COUNT(DISTINCT vin) FROM normalized_vehicle_data
     WHERE location = '[DEALERSHIP_NAME]') as current_inventory,
    (SELECT COUNT(DISTINCT vin) FROM normalized_vehicle_data
     WHERE location = '[DEALERSHIP_NAME]'
     AND vin NOT IN (SELECT vin FROM [dealership_name]_vin_log)) as new_vins,
    (SELECT COUNT(*) FROM [dealership_name]_vin_log) as total_log_entries;
```

#### Step 3: Production Test
- Run test CAO order through web interface
- Verify reduced VIN count (should exclude historical VINs)
- Confirm QR code generation and CSV output

## Success Criteria

A dealership is considered **production-ready** when:

1. ✅ **Configuration matches template** (all required filters present)
2. ✅ **VIN log is complete** (all historical VINs imported including duplicates)
3. ✅ **CAO processing excludes historical VINs** properly
4. ✅ **Returns reasonable VIN count** (typically 0-50 for mature dealerships)
5. ✅ **QR codes generate successfully**
6. ✅ **CSV output is properly formatted**

## Common Issues and Solutions

### Issue 1: High VIN Count Despite Correct Configuration
**Cause:** Incomplete VIN log missing historical orders
**Solution:** Complete VIN log reimport with all duplicates

### Issue 2: Configuration Not Loading
**Cause:** Server-side module caching
**Solution:** Kill Python processes and restart Flask server

### Issue 3: Duplicate Key Violations During Import
**Cause:** Table has unique constraint on VIN column
**Solution:** Remove unique constraint to allow duplicates

### Issue 4: Old Configuration Format
**Cause:** Outdated field names (`exclude_conditions` vs `exclude_status`)
**Solution:** Apply standardized template with current field names

## Completed Dealerships

1. ✅ South County DCJR (template baseline)
2. ✅ Glendale CDJR (price filtering variant)
3. ✅ Auffenberg Hyundai (configuration + VIN sync)
4. ✅ Thoroughbred Ford (complete VIN log reimport)
5. ✅ [7 additional dealerships - names to be documented]

## Tools and Scripts

### Configuration Check Script
```bash
# Check dealership configuration
cd projects/minisforum_database_transfer/bulletproof_package/scripts
py -c "from database_connection import db_manager; import json; ..."
```

### VIN Log Import Template
```python
# See: import_thoroughbred_vinlog_complete.py
# Adaptable template for any dealership VIN log import
```

### Verification Queries
```sql
-- Standard verification queries for any dealership
SELECT COUNT(*) FROM [dealership]_vin_log;
SELECT order_number, COUNT(*) FROM [dealership]_vin_log GROUP BY order_number;
```

## Next Steps

1. **Identify next dealership** requiring standardization
2. **Follow systematic process** outlined above
3. **Document any new edge cases** discovered
4. **Update template if needed** based on dealership-specific requirements
5. **Continue until all 36 dealerships** are production-ready

## Process Evolution

This standardization process was developed through systematic debugging of:
- Cache-busting issues (Auffenberg Hyundai)
- VIN log completeness problems (Thoroughbred Ford)
- Configuration template inconsistencies
- Database constraint conflicts

The process continues to be refined as additional dealerships are standardized.

---

**Last Updated:** September 18, 2025
**Template Version:** Based on FINAL_DEALER_CONFIG_TEMPLATE_9.16.md
**Process Status:** 11/36 dealerships completed (30.6%)