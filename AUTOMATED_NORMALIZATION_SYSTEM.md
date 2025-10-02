# 🤖 Automated Normalization System - CRITICAL ORDER PROCESSING AUTOMATION
**Updated: September 8, 2025 - Production Ready with Full Column & Name Mapping**

## 📋 System Overview

The Automated Normalization Manager consolidates and automates the manual normalization process that has been required after each data import. This system ensures that raw scraper data is properly converted to the standardized format needed for CAO (Comparative Analysis Order) processing.

**MAJOR UPDATE**: Fixed critical bugs and added comprehensive column/dealership name mapping for seamless CSV import and processing.

## 🎯 Why This System Is Critical

**Without proper normalization, CAO processing fails!** The normalization step is essential because:

1. **Raw scraper data** contains dealer-specific formats and statuses
2. **CAO processing** requires standardized vehicle conditions and lot statuses  
3. **Manual normalization** was time-consuming and error-prone
4. **Missing normalized data** causes CAO to return 0 vehicles instead of actual counts

## 🔧 Core Components

### 1. AutomatedNormalizationManager (`automated_normalization_manager.py`)
**Main automation class that handles the complete normalization workflow**

#### Key Methods:
- `normalize_import_data()` - Main normalization function
- `ensure_clean_normalization_state()` - Prevents contamination from previous imports
- `validate_normalization_completeness()` - Ensures 100% completion
- `normalize_single_record()` - Applies standardization rules to individual vehicles
- `batch_insert_normalized_data()` - **FIXED**: Now creates ALL normalized records (not 1 per dealership)

#### Critical Fixes Applied:
- **❌ OLD BUG**: Used `upsert_data()` with conflict resolution, only creating 1 record per dealership
- **✅ FIXED**: Now uses `execute_batch_insert()` to create individual normalized records for each raw record

#### Normalization Logic:
```python
# Vehicle Type Normalization (condition → vehicle_condition)
'New' → 'new'
'Used' / 'Pre-Owned' → 'po' 
'Certified Pre-Owned' / 'CPO' → 'cpo'

# Lot Status Normalization (status → on_lot_status)  
'In Stock' / 'Available' / 'On-Lot' → 'onlot'
'In Transit' / 'Being Built' / 'Off-Lot' → 'offlot'

# CRITICAL OVERRIDES:
# - No stock number → 'offlot'
# - 'In Transit' status → 'offlot' (regardless of other factors)
```

### 2. CSV Import Integration (`csv_importer_complete.py`)
**Enhanced CSV importer with automatic column and dealership name mapping**

#### Column Mapping (CSV → Database):
```
"Vin" → vin
"Stock" → stock  
"Type" → type (Vehicle condition: "Pre-Owned", "New", "CPO")
"Status" → status (Lot status: "In Stock", "Available", "", etc.)
"Year" → year
"Make" → make
"Model" → model
"Trim" → trim
"Ext Color" → ext_color
"Price" → price
"Body Style" → body_style
"Fuel Type" → fuel_type
"MSRP" → msrp
"Date In Stock" → date_in_stock
"Location" → location (Dealership name)
"Vechile URL" → vehicle_url (Note: CSV has typo "Vechile")
```

#### Dealership Name Standardization:
```python
# CSV Import Mappings (CSV Name → Standardized Name)
'South County Dodge Chrysler Jeep RAM' → 'South County DCJR'
'BMW of West St Louis' → 'BMW of West St. Louis'  # Add missing period
'Glendale Chrysler Jeep Dodge Ram' → 'Glendale CDJR'
# Most other names import as-is
```

### 3. CAO Processing Integration (`correct_order_processing.py`)
**Updated name mapping for CAO processing**

#### CAO Name Mapping (Config Name → Data Name):
```python
# Maps dealership config names to actual data location names
'HW Kia' → 'HW Kia of West County'  # Map config to CSV name
'BMW of West St. Louis' → 'BMW of West St Louis'  # Handle period difference
'South County DCJR' → 'South County Dodge Chrysler Jeep RAM'  # Map to full CSV name
'Glendale CDJR' → 'Glendale Chrysler Jeep Dodge Ram'  # Map to full CSV name
```

### 4. API Integration (`app.py`)
**Web API endpoints for automation control**

#### Available Endpoints:
- `POST /api/normalization/run` - Run automated normalization
- `GET /api/normalization/validate` - Validate current normalization status
- `GET /api/normalization/status` - Get normalization overview

### 3. Automatic Trigger Integration
**Normalization runs automatically after CSV imports**

The system automatically triggers normalization in the scraper pipeline:
```python
# After successful CSV import:
normalization_result = normalize_active_import()
```

## 📊 Validation & Quality Assurance

### Completion Validation
```python
# Ensures 1:1 correspondence between raw and normalized data
raw_records: 259 vehicles
normalized_records: 259 vehicles  
completion_rate: 100%
```

### Dealership Consistency Check
```python
# Verifies each dealership has complete normalization
Honda of Frontenac: 135 raw → 135 normalized ✅
Glendale CDJR: 402 raw → 402 normalized ✅
```

### Error Detection
- Missing normalized records
- Data type validation errors
- Database constraint violations
- Cross-import contamination

## 🚀 Usage Instructions

### **NEW: Simple Import & Normalize Script**
```bash
# Complete CSV import and normalization in one command
cd scripts
python import_and_normalize_csv.py "C:\path\to\complete_data.csv"
```

### Command Line Usage
```bash
# Run normalization on active import
cd scripts
python automated_normalization_manager.py --normalize

# Validate current normalization status
python automated_normalization_manager.py --validate

# Normalize specific import ID
python automated_normalization_manager.py --normalize --import-id 28
```

### API Usage
```javascript
// Run normalization via web API
fetch('/api/normalization/run', {method: 'POST'})

// Check status
fetch('/api/normalization/status')
```

### Test Suite
```bash
# Run comprehensive test suite
python test_automated_normalization.py
```

## 🔄 Complete Workflow

### 1. Data Import Phase
```
CSV Upload → Raw Data Import → AUTOMATIC NORMALIZATION TRIGGER
```

### 2. Normalization Phase  
```
Clean Previous State → Process Each Dealership → Apply Standardization Rules → Validate Completion
```

### 3. Validation Phase
```
Count Verification → Dealership Consistency → Error Detection → Maintenance Tasks
```

### 4. CAO Ready State
```
100% Normalized Data → CAO Processing Available → Order Processing Functional
```

## 🛠️ Integration Points

### CSV Importer Integration
The `CompleteCSVImporter` class has built-in normalization that works seamlessly with this automation system:

```python
# In csv_importer_complete.py line 500-570
# Prepares normalized data during import process
# Uses same normalizer logic as automation system
```

### Order Processing Integration  
CAO processing depends on normalized data:

```python
# In correct_order_processing.py
# CAO queries use normalized_vehicle_data table
# Requires proper vehicle_condition and on_lot_status values
```

## 📈 Performance Benefits

### Before Automation
- ❌ Manual normalization after each import
- ❌ Risk of missing normalization step
- ❌ Inconsistent standardization  
- ❌ CAO processing failures due to missing data
- ❌ Only 1 normalized record per dealership (major bug)
- ❌ Name mapping issues causing 0 VIN results

### After Automation
- ✅ Automatic normalization after every import
- ✅ 100% completion validation
- ✅ Consistent standardization rules
- ✅ Reliable CAO processing
- ✅ **VERIFIED WORKING**: Creates ALL normalized records correctly
- ✅ **VERIFIED WORKING**: HW Kia and Honda of Frontenac name mapping fixed
- ✅ **PRODUCTION READY**: Complete CSV import and normalization pipeline

## 🔍 Troubleshooting

### Common Issues & Solutions

#### Issue: CAO Returns 0 Vehicles
**Cause:** Missing or incomplete normalized data  
**Solution:** Run `python automated_normalization_manager.py --validate`

#### Issue: Normalization Incomplete  
**Cause:** Data validation errors or database constraints  
**Solution:** Check error logs and run `test_automated_normalization.py`

#### Issue: Cross-Import Contamination
**Cause:** Normalized records from archived imports persisting  
**Solution:** System automatically prevents this with `ensure_clean_normalization_state()`

### Validation Commands
```bash
# Check if normalization is needed
python -c "from automated_normalization_manager import validate_normalization_status; print(validate_normalization_status())"

# Get active import info
python -c "from database_connection import db_manager; print(db_manager.execute_query('SELECT * FROM scraper_imports WHERE status = \"active\"'))"
```

## 🚨 Critical Success Factors

1. **Run After Every Import**: Never skip normalization after importing new data
2. **Validate Completion**: Always ensure 100% completion rate
3. **Clean State Management**: System prevents cross-import contamination
4. **Error Monitoring**: Check logs for validation and processing errors
5. **Database Maintenance**: Automatic VACUUM ANALYZE after normalization

## 📝 System Status Dashboard

The web interface provides real-time normalization status:
- Active import information
- Normalization completion percentage  
- Dealership-by-dealership breakdown
- Error reporting and resolution
- One-click normalization execution

## 🔮 Future Enhancements

1. **Real-time Monitoring**: WebSocket progress updates during normalization
2. **Incremental Updates**: Only normalize new/changed records
3. **Custom Rules Engine**: Dealership-specific normalization rules
4. **Performance Optimization**: Parallel processing for large datasets
5. **Quality Scoring**: Data quality metrics and improvement suggestions

---

## 🎯 Summary

The Automated Normalization System eliminates the manual normalization bottleneck that was preventing reliable CAO processing. With this system in place:

- **Data imports** automatically trigger normalization
- **CAO processing** always has properly formatted data
- **Order processing** workflow becomes fully automated
- **System reliability** increases dramatically

**This automation is essential for the production order processing system and eliminates a critical manual step that was prone to errors and delays.**