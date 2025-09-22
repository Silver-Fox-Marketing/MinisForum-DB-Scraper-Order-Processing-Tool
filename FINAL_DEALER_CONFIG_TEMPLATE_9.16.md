# Final Dealer Configuration Template - 9.16.2025

## Overview
This document provides the standardized dealership configuration template for the Silver Fox Order Processing System. This template was finalized on September 16, 2025, after resolving critical filtering issues with Glendale CDJR.

## Standard Dealership Configuration Template

### Base Template (Used/New Vehicles)
```json
{
    "notes": "Standardized configuration based on South County DCJR template",
    "order_type": "cao",
    "days_on
    _lot": {
        "max": 999,
        "min": 0
    },
    "price_range": {
        "max": 999999,
        "min": 0
    },
    "require_stock": true,
    "vehicle_types": ["new", "used"],
    "exclude_status": ["In-Transit", "Sold", "Allocated"],
    "exclude_in_transit": true,
    "allowed_vehicle_types": ["new", "cpo", "po", "certified", "pre-owned"],
    "exclude_missing_stock_number": true
}
```

### Used-Only Vehicle Template (e.g., Glendale CDJR)
```json
{
    "notes": "Standardized configuration for used-only dealerships with price filtering",
    "order_type": "cao",
    "days_on_lot": {
        "max": 999,
        "min": 0
    },
    "price_range": {
        "max": 999999,
        "min": 0
    },
    "require_stock": true,
    "vehicle_types": ["used"],
    "exclude_status": ["In-Transit", "Sold", "Allocated"],
    "exclude_in_transit": true,
    "allowed_vehicle_types": ["cpo", "po", "certified", "pre-owned"],
    "exclude_missing_stock_number": true,
    "exclude_missing_price": true
}
```

## Filter Explanations

### Core Order Processing Filters

| Filter | Purpose | Example Values | Impact |
|--------|---------|----------------|--------|
| `order_type` | Defines the type of order processing | `"cao"`, `"list"` | Determines processing workflow |
| `notes` | Documentation for configuration changes | `"Standardized config..."` | Administrative tracking |

### Vehicle Type Filters

| Filter | Purpose | Example Values | Impact |
|--------|---------|----------------|--------|
| `vehicle_types` | High-level vehicle categories wanted | `["new", "used"]` | Broad filtering scope |
| `allowed_vehicle_types` | Specific normalized vehicle conditions | `["new", "cpo", "po", "certified", "pre-owned"]` | Precise inclusion criteria |

**Critical Rule:** `vehicle_types` and `allowed_vehicle_types` must be logically consistent:
- If `vehicle_types: ["used"]`, then `allowed_vehicle_types` should only include used variants: `["cpo", "po", "certified", "pre-owned"]`
- If `vehicle_types: ["new", "used"]`, then `allowed_vehicle_types` can include all: `["new", "cpo", "po", "certified", "pre-owned"]`

### Stock and Inventory Filters

| Filter | Purpose | Example Values | Impact |
|--------|---------|----------------|--------|
| `require_stock` | Ensure vehicles have stock numbers | `true` | Excludes vehicles without stock |
| `exclude_missing_stock_number` | More specific stock requirement | `true` | Excludes NULL/empty stock fields |

### Status and Transit Filters

| Filter | Purpose | Example Values | Impact |
|--------|---------|----------------|--------|
| `exclude_status` | Remove vehicles with specific statuses | `["In-Transit", "Sold", "Allocated"]` | Excludes unavailable vehicles |
| `exclude_in_transit` | Specifically exclude in-transit vehicles | `true` | Additional transit filtering |

**Critical for CAO Processing:** These filters prevent orders from including vehicles that customers cannot actually purchase.

### Price and Financial Filters

| Filter | Purpose | Example Values | Impact |
|--------|---------|----------------|--------|
| `price_range` | Set min/max price limits | `{"min": 0, "max": 999999}` | Broad price boundaries |
| `exclude_missing_price` | Remove vehicles without valid prices | `true` | **CRITICAL: Only use when dealership has pricing issues** |

**Important:** `exclude_missing_price` should only be used for dealerships with systemic pricing data issues (like Glendale CDJR). Most dealerships should leave this as `false` or omit it entirely.

### Lot Management Filters

| Filter | Purpose | Example Values | Impact |
|--------|---------|----------------|--------|
| `days_on_lot` | Filter by how long vehicle has been on lot | `{"min": 0, "max": 999}` | Age-based filtering |

## Configuration Update Process

### Step 1: Identify the Dealership Type
- **Standard Dealership:** Uses both new and used vehicles
- **Used-Only Dealership:** Only processes used vehicles
- **Special Requirements:** Has unique filtering needs (e.g., price filtering)

### Step 2: Choose the Appropriate Template
- Use **Base Template** for standard dealerships
- Use **Used-Only Template** for used-only dealerships
- Modify templates as needed for special requirements

### Step 3: Apply Configuration
```sql
UPDATE dealership_configs
SET filtering_rules = '[JSON_CONFIG]',
    updated_at = CURRENT_TIMESTAMP
WHERE name = '[DEALERSHIP_NAME]' AND is_active = true;
```

### Step 4: Verification
```sql
SELECT name, filtering_rules FROM dealership_configs
WHERE name = '[DEALERSHIP_NAME]' AND is_active = true;
```

## Common Configuration Issues and Solutions

### Issue 1: Contradictory Vehicle Type Filters
**Problem:** `vehicle_types: ["used"]` but `exclude_conditions: ["po", "cpo"]`
**Solution:** Ensure `allowed_vehicle_types` matches `vehicle_types` intention

### Issue 2: Missing Critical Status Filters
**Problem:** Dealership returns vehicles that are In-Transit or Sold
**Solution:** Always include `exclude_status: ["In-Transit", "Sold", "Allocated"]`

### Issue 3: Price Filtering Issues
**Problem:** Vehicles without prices are included in orders
**Solution:** Only add `exclude_missing_price: true` for dealerships with systemic pricing issues

### Issue 4: Stock Number Problems
**Problem:** Vehicles without stock numbers cause processing issues
**Solution:** Always include `exclude_missing_stock_number: true`

## Template Evolution History

- **v1.0 (Early 2025):** Basic vehicle type filtering
- **v2.0 (September 2025):** Added status and transit exclusions
- **v3.0 (September 16, 2025):** Standardized template based on South County DCJR success, added price filtering for special cases

## Validation Checklist

Before applying any dealership configuration:

- [ ] `vehicle_types` and `allowed_vehicle_types` are logically consistent
- [ ] Status exclusions include `["In-Transit", "Sold", "Allocated"]`
- [ ] Stock filtering is enabled: `exclude_missing_stock_number: true`
- [ ] Transit filtering is enabled: `exclude_in_transit: true`
- [ ] Price filtering is only enabled for dealerships with pricing issues
- [ ] Configuration has been tested with a test order
- [ ] Results match expected vehicle count for the dealership

## Success Metrics

A properly configured dealership should:
- Return 0 vehicles if all inventory is filtered out (expected for some dealerships)
- Return only vehicles that customers can actually purchase
- Exclude vehicles without proper pricing (when price filter is enabled)
- Exclude vehicles without stock numbers
- Exclude vehicles that are In-Transit, Sold, or Allocated

## Contact and Updates

This template should be updated whenever new filtering requirements are discovered or when the order processing logic changes. All changes should be documented with version numbers and dates.

**Last Updated:** September 16, 2025
**Template Version:** 3.0
**Validated Against:** South County DCJR, Glendale CDJR, Porsche St. Louis