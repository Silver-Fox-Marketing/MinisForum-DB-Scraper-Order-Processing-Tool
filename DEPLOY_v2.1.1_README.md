# Version 2.1.1 Hotfix Deployment Guide
## Critical Fix: LIST Order Dealership Filtering

---

## What This Fix Does

This hotfix resolves critical issues with LIST order processing:

1. **Vehicle Type Filtering**: LIST orders now properly respect dealership `vehicle_types` configuration
   - Example: Columbia Honda (configured for "used only") will no longer process NEW vehicles

2. **Stock Number Filtering**: Vehicles with missing or invalid stock numbers are properly filtered out
   - Filters: `null`, `N/A`, `AUTO`, `TBD`, `TBA`, empty values

3. **UI Preview Filtering**: Filtered results now display correctly in the UI review phase
   - Before: All VINs showed in preview, even if they didn't match filters
   - After: Only VINs matching dealership config show in preview

---

## Deployment Instructions

### Prerequisites
- **Production Server Path**: `C:\SilverFox\releases\v2.1.0`
- **Versioned Deployment**: Production uses version-based releases
- **Access**: Administrator privileges required
- **Backup**: Automatic backup created by deployment script to `C:\SilverFox\backups\code\`

### Step 1: Run the Deployment Script

1. Navigate to the development folder:
   ```
   C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package
   ```

2. Run the deployment script:
   ```
   deploy_v2.1.1_hotfix.bat
   ```

3. Follow the on-screen prompts

### Step 2: Restart Production Server

**Option A - If running as Windows Service:**
```batch
net stop SilverFoxOrderProcessing
net start SilverFoxOrderProcessing
```

**Option B - If running manually:**
1. Stop the current server process (Ctrl+C or close terminal)
2. Restart the server:
   ```batch
   cd C:\SilverFox\releases\v2.1.0\web_gui
   python production_server.py
   ```

### Step 3: Verify Deployment

1. **Check Server Logs**:
   - Look for startup without errors
   - Location: `C:\SilverFox\shared\logs\` or server console

2. **Test LIST Order**:
   - Create a LIST order for "Columbia Honda" (configured for used only)
   - Add VINs that include NEW vehicles
   - **Expected**: NEW vehicles should be filtered out
   - **Expected**: Only USED vehicles should appear in preview

3. **Test Stock Filtering**:
   - Create a LIST order for "CDJR of Columbia"
   - Include VINs with missing stock numbers
   - **Expected**: VINs with invalid stock (null, AUTO, N/A) should be filtered out

---

## Files Modified

**Single File Update**:
- `scripts/correct_order_processing.py` (Lines 465-471, 561, 1166-1213)

**Changes**:
- Added filtering to `prepare_list_data()` function
- Added filtering to `process_list_order()` function
- Enhanced `_apply_dealership_filters()` with stock, price, and exclude_conditions filters

---

## Rollback Procedure

If you encounter issues, the deployment script creates an automatic backup.

**To rollback:**

1. **Automatic Backup Location**:
   ```
   C:\SilverFox\backups\code\v2.1.1_hotfix_[TIMESTAMP]\
   ```

2. **Restore Command**:
   ```batch
   copy /Y "C:\SilverFox\backups\code\v2.1.1_hotfix_[TIMESTAMP]\correct_order_processing.py.backup" ^
         "C:\SilverFox\releases\v2.1.0\scripts\correct_order_processing.py"
   ```
   (Replace `[TIMESTAMP]` with actual backup folder timestamp)

3. **Restart Server** (see Step 2 above)

---

## Testing Checklist

After deployment, verify the following:

- [ ] Server starts without errors
- [ ] Database connection works
- [ ] CAO orders still process correctly
- [ ] LIST orders for "used only" dealerships filter out NEW vehicles
- [ ] LIST orders filter out vehicles with missing stock numbers
- [ ] UI preview phase shows filtered results (not all VINs)
- [ ] Final order processing respects all filters

---

## Support

**GitHub Release**: [v2.1.1](https://github.com/Silver-Fox-Marketing/MinisForum-DB-Scraper-Order-Processing-Tool/releases/tag/v2.1.1)

**Commit**: `ecfa78f` - "Fix LIST order dealership filtering for vehicle types and stock requirements"

**Tested On**:
- Columbia Honda (used only config)
- CDJR of Columbia (stock filtering)

---

## Version Information

**Version**: 2.1.1
**Type**: Hotfix (Critical Bug Fix)
**Release Date**: October 10, 2025
**Downtime**: ~30-60 seconds (server restart only)
**Database Changes**: None (no migrations required)
**Rollback Available**: Yes (automatic backup created)

---

**Deployment Status**: ✅ Ready for Production
