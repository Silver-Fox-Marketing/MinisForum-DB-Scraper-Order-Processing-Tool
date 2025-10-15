# FUTURE_FILTER_IMPLEMENTATION_FRONTEND_BACKEND.md

## Filter Implementation System Guide
*Complete guide for implementing new dealership-specific filters and output configurations*

---

## Overview

This document details how the Glendale price display feature was implemented and provides a comprehensive template for implementing similar dealership-specific filters and output configurations in the future.

## System Architecture

### Core Components

1. **Database Layer** - `dealership_configs.output_rules` (JSON column)
2. **Backend Processing** - `correct_order_processing.py`
3. **Frontend Configuration** - Dealership Settings Modal UI
4. **Frontend Display** - Dynamic table headers and column rendering
5. **Context Bridge** - Fallback pattern for modal/main app data access

---

## Implementation Pattern

### 1. Database Schema (`dealership_configs` table)

```sql
-- Existing structure
CREATE TABLE dealership_configs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    filtering_rules JSONB,
    output_rules JSONB,  -- New filters go here
    is_active BOOLEAN DEFAULT true
);

-- Example output_rules structure
{
    "template_variant": "glendale_format",  -- Output format type
    "price_markup": 2000,                   -- Markup amount in dollars
    "custom_columns": ["YEARMODEL", "TRIM", "PRICE"],  -- Future: custom column order
    "date_format": "MM/DD/YYYY"             -- Future: custom date formatting
}
```

### 2. Frontend Configuration (Dealership Settings Modal)

**File**: `web_gui/templates/index.html`

**Location**: Dealership Settings Modal (`#dealershipModal`)

```html
<!-- Add new filter section to modal -->
<div class="settings-section">
    <h4>Output Format Settings</h4>

    <!-- Template Variant Dropdown -->
    <div class="form-group">
        <label for="templateVariant">Template Format:</label>
        <select id="templateVariant" name="template_variant" class="modern-input">
            <option value="standard">Standard Format</option>
            <option value="glendale_format">SCP + $</option>
            <!-- Future formats go here -->
            <option value="custom_format">Custom Format</option>
        </select>
    </div>

    <!-- Price Markup Input -->
    <div class="form-group">
        <label for="priceMarkup">Price Markup ($):</label>
        <input type="number" id="priceMarkup" name="price_markup"
               class="modern-input" placeholder="0" step="100">
    </div>

    <!-- Future filters follow same pattern -->
    <div class="form-group">
        <label for="dateFormat">Date Format:</label>
        <select id="dateFormat" name="date_format" class="modern-input">
            <option value="MM/DD/YYYY">MM/DD/YYYY</option>
            <option value="DD/MM/YYYY">DD/MM/YYYY</option>
        </select>
    </div>
</div>
```

### 3. Frontend JavaScript Integration

**File**: `web_gui/static/js/app.js`

#### A. Modal Population (showDealershipModal function)

```javascript
showDealershipModal(dealershipName) {
    // ... existing code ...

    // Populate output rules fields
    const outputRules = dealership.output_rules || {};

    // Template variant
    const templateVariantSelect = document.getElementById('templateVariant');
    if (templateVariantSelect) {
        templateVariantSelect.value = outputRules.template_variant || 'standard';
    }

    // Price markup
    const priceMarkupInput = document.getElementById('priceMarkup');
    if (priceMarkupInput) {
        priceMarkupInput.value = outputRules.price_markup || '';
    }

    // Future filters follow same pattern
    const dateFormatSelect = document.getElementById('dateFormat');
    if (dateFormatSelect) {
        dateFormatSelect.value = outputRules.date_format || 'MM/DD/YYYY';
    }
}
```

#### B. Modal Save (saveDealershipSettings function)

```javascript
async saveDealershipSettings() {
    // ... existing filtering_rules logic ...

    // Collect output rules
    const outputRules = {};

    // Template variant
    const templateVariant = document.getElementById('templateVariant')?.value;
    if (templateVariant && templateVariant !== 'standard') {
        outputRules.template_variant = templateVariant;
    }

    // Price markup
    const priceMarkup = document.getElementById('priceMarkup')?.value;
    if (priceMarkup && priceMarkup !== '') {
        outputRules.price_markup = parseInt(priceMarkup);
    }

    // Future filters
    const dateFormat = document.getElementById('dateFormat')?.value;
    if (dateFormat && dateFormat !== 'MM/DD/YYYY') {
        outputRules.date_format = dateFormat;
    }

    // Include in update payload
    const updateData = {
        filtering_rules: filteringRules,
        output_rules: outputRules,  // Add this line
        is_active: isActive
    };
}
```

#### C. Dynamic Display Logic (updateTableHeaders function)

```javascript
updateTableHeaders() {
    // Get current dealership context
    const currentDealership = this.selectedReviewDealership ||
                            (this.processedOrders && this.processedOrders[0] && this.processedOrders[0].dealership);

    if (!currentDealership) return;

    // CRITICAL: Use fallback pattern for modal context
    const dealerships = this.dealerships || window.app?.dealerships;
    const dealershipData = dealerships?.find(d => d.name === currentDealership);

    // Extract output rules
    const outputRules = dealershipData?.output_rules || {};
    const templateVariant = outputRules.template_variant || 'standard';
    const isSpecialFormat = templateVariant !== 'standard';

    // Apply dynamic headers
    const headerRow = document.querySelector('#modalVehicleDataTable thead tr');
    if (!headerRow) return;

    if (templateVariant === 'glendale_format') {
        headerRow.innerHTML = `
            <th></th>
            <th>Year/Model</th>
            <th>Trim</th>
            <th>Price</th>
            <th>Stock</th>
            <th>VIN</th>
            <th class="raw-status-header">Raw Status</th>
            <th class="data-toggle-header">Data Type</th>
            <th></th>
        `;
    } else if (templateVariant === 'custom_format') {
        // Future custom format implementation
        headerRow.innerHTML = generateCustomHeaders(outputRules);
    } else {
        // Standard format
        headerRow.innerHTML = `
            <th></th>
            <th>Year/Make</th>
            <th>Model</th>
            <th>Trim</th>
            <th>Stock</th>
            <th>VIN</th>
            <th class="raw-status-header">Raw Status</th>
            <th class="data-toggle-header">Data Type</th>
            <th></th>
        `;
    }
}
```

#### D. Dynamic Row Rendering (renderVehicleTable function)

```javascript
renderVehicleTable(vehicles) {
    // ... existing code ...

    // CRITICAL: Use fallback pattern for modal context
    const dealerships = this.dealerships || window.app?.dealerships;
    const dealershipData = dealerships?.find(d => d.name === currentDealership);

    const outputRules = dealershipData?.output_rules || {};
    const templateVariant = outputRules.template_variant || 'standard';
    const isGlendaleFormat = templateVariant === 'glendale_format';

    const rows = vehicles.map((vehicle, index) => {
        if (isGlendaleFormat) {
            // Glendale format: YEARMODEL, TRIM, PRICE, STOCK, VIN
            return `
                <tr data-vehicle-index="${index}">
                    <td><span class="vehicle-number">${index + 1}</span></td>
                    <td>${vehicle.yearmodel || ''}</td>
                    <td>${vehicle.trim || ''}</td>
                    <td>${vehicle.price || ''}</td>
                    <td>${vehicle.stock || ''}</td>
                    <td>${vehicle.vin || ''}</td>
                    <td class="raw-status-cell" data-vin="${vehicle.vin}">Loading...</td>
                    <td class="data-type-cell">${dataType}</td>
                    <td>${editButton}</td>
                </tr>
            `;
        } else {
            // Standard format: YEARMAKE, MODEL, TRIM, STOCK, VIN
            return generateStandardRow(vehicle, index);
        }
    });
}
```

### 4. Backend Processing Integration

**File**: `scripts/correct_order_processing.py`

#### A. Retrieve Output Rules

```python
def _generate_adobe_csv(self, vehicles, dealership_name, template='Shortcut Pack', order_number=None):
    # ... existing code ...

    # Get output rules for dealership
    output_rules = {}
    try:
        dealership_config = self.db.get_dealership_config(dealership_name)
        if dealership_config and dealership_config.get('output_rules'):
            output_rules = dealership_config['output_rules']
    except Exception as e:
        print(f"Warning: Could not retrieve output rules for {dealership_name}: {e}")

    # Extract configuration
    template_variant = output_rules.get('template_variant', 'standard')
    price_markup = output_rules.get('price_markup', 0)
    date_format = output_rules.get('date_format', 'MM/DD/YYYY')
```

#### B. Apply Output Rules

```python
# Apply template-specific CSV generation
if template_variant == 'glendale_format':
    # Glendale format headers
    writer.writerow(['YEARMODEL', 'TRIM', 'PRICE', 'STOCK', 'VIN', '@QR', 'QRYEARMODEL', 'QRSTOCK', '@QR2', 'MISC'])

    for vehicle in vehicles:
        # Apply price markup
        price = vehicle.get('price', '')
        if price and price_markup:
            try:
                price_value = float(price.replace(',', '').replace('$', '')) + float(price_markup)
                price_str = f"{int(price_value):,}"
            except (ValueError, TypeError):
                price_str = price
        else:
            price_str = price

        # Generate row with custom format
        row_data = [
            f"{vehicle.get('year', '')} {vehicle.get('model', '')}",  # YEARMODEL
            vehicle.get('trim', ''),                                  # TRIM
            price_str,                                               # PRICE (with markup)
            vehicle.get('stock', ''),                                # STOCK
            vehicle.get('vin', ''),                                  # VIN
            qr_path,                                                 # @QR
            f"{vehicle.get('year', '')} {vehicle.get('model', '')} - {vehicle.get('stock', '')}", # QRYEARMODEL
            f"USED - {vehicle.get('vin', '')}",                      # QRSTOCK
            qr_path,                                                 # @QR2
            f"{vehicle.get('year', '')} {vehicle.get('model', '')} - {vehicle.get('vin', '')} - {vehicle.get('stock', '')}" # MISC
        ]

        writer.writerow(row_data)

elif template_variant == 'custom_format':
    # Future: implement custom format logic
    apply_custom_format(writer, vehicles, output_rules)

else:
    # Standard format (existing logic)
    generate_standard_csv(writer, vehicles)
```

---

## Implementation Checklist for New Filters

### Phase 1: Database Design
- [ ] Design JSON structure for `output_rules`
- [ ] Add new filter fields to JSON schema
- [ ] Test database updates via API

### Phase 2: Frontend Configuration UI
- [ ] Add form fields to dealership settings modal
- [ ] Implement field population in `showDealershipModal()`
- [ ] Implement field collection in `saveDealershipSettings()`
- [ ] Test modal save/load functionality

### Phase 3: Frontend Display Logic
- [ ] Update `updateTableHeaders()` with new format logic
- [ ] Update `renderVehicleTable()` with new row rendering
- [ ] **CRITICAL**: Use fallback pattern: `this.dealerships || window.app?.dealerships`
- [ ] Test modal context display

### Phase 4: Backend Processing
- [ ] Add output rules retrieval to processing functions
- [ ] Implement new format logic in CSV generation
- [ ] Test backend processing with new filters

### Phase 5: Integration Testing
- [ ] Test CAO functionality (ensure no breaking changes)
- [ ] Test modal wizard functionality
- [ ] Test CSV output correctness
- [ ] Test edge cases and error handling

---

## Critical Patterns & Best Practices

### 1. Context-Safe Data Access
**ALWAYS use this pattern in frontend functions that may run in modal context:**

```javascript
// ✅ CORRECT: Works in both main app and modal contexts
const dealerships = this.dealerships || window.app?.dealerships;
const dealershipData = dealerships?.find(d => d.name === currentDealership);

// ❌ INCORRECT: Fails in modal context
const dealershipData = this.dealerships?.find(d => d.name === currentDealership);
```

### 2. Non-Breaking Backend Integration
**Pattern for safe output rules integration:**

```python
# ✅ CORRECT: Graceful fallback if output_rules don't exist
output_rules = dealership_config.get('output_rules', {})
template_variant = output_rules.get('template_variant', 'standard')

# Apply rules only if they exist
if template_variant != 'standard':
    apply_custom_format()
else:
    apply_standard_format()  # Existing logic preserved
```

### 3. Database JSON Structure
**Recommended output_rules structure:**

```json
{
    "template_variant": "string",     // Format type identifier
    "price_markup": "number",         // Numeric adjustments
    "custom_columns": "array",        // Column configurations
    "formatting_rules": {             // Nested formatting options
        "date_format": "string",
        "price_format": "string",
        "currency_symbol": "string"
    },
    "conditional_logic": {            // Future: conditional processing
        "hide_if_price_zero": "boolean",
        "filter_by_status": "array"
    }
}
```

### 4. Error Handling
**Implement graceful degradation:**

```javascript
// Frontend
try {
    const outputRules = dealershipData?.output_rules || {};
    const templateVariant = outputRules.template_variant || 'standard';
    applyFormat(templateVariant);
} catch (error) {
    console.warn('Failed to apply custom format, using standard:', error);
    applyStandardFormat();
}
```

```python
# Backend
try:
    output_rules = self.db.get_dealership_config(dealership_name).get('output_rules', {})
    apply_custom_rules(output_rules)
except Exception as e:
    logger.warning(f"Failed to apply output rules for {dealership_name}: {e}")
    apply_standard_processing()
```

---

## File Reference Map

### Frontend Files
- **Modal UI**: `web_gui/templates/index.html` (lines ~1700-1800)
- **JavaScript Logic**: `web_gui/static/js/app.js`
  - `showDealershipModal()`: ~line 2850
  - `saveDealershipSettings()`: ~line 2950
  - `updateTableHeaders()`: ~line 9200
  - `renderVehicleTable()`: ~line 10050

### Backend Files
- **CSV Processing**: `scripts/correct_order_processing.py`
  - `_generate_adobe_csv()`: ~line 400
- **Database Layer**: `scripts/database_connection.py`
  - Dealership config methods

### Configuration Files
- **Database Schema**: `dealership_configs` table
- **Cache-Busting**: `web_gui/templates/index.html` (script tag)

---

## Example Implementation: Date Format Filter

Following this guide, here's how to implement a new "Date Format" filter:

### 1. Database
```json
{
    "template_variant": "standard",
    "date_format": "DD/MM/YYYY"
}
```

### 2. Frontend UI
```html
<div class="form-group">
    <label for="dateFormat">Date Format:</label>
    <select id="dateFormat" name="date_format" class="modern-input">
        <option value="MM/DD/YYYY">MM/DD/YYYY</option>
        <option value="DD/MM/YYYY">DD/MM/YYYY</option>
        <option value="YYYY-MM-DD">YYYY-MM-DD</option>
    </select>
</div>
```

### 3. Frontend Logic
```javascript
// In showDealershipModal
const dateFormatSelect = document.getElementById('dateFormat');
if (dateFormatSelect) {
    dateFormatSelect.value = outputRules.date_format || 'MM/DD/YYYY';
}

// In saveDealershipSettings
const dateFormat = document.getElementById('dateFormat')?.value;
if (dateFormat && dateFormat !== 'MM/DD/YYYY') {
    outputRules.date_format = dateFormat;
}
```

### 4. Backend Processing
```python
def format_date(date_str, format_type):
    """Apply custom date formatting based on output rules"""
    if format_type == 'DD/MM/YYYY':
        return convert_to_dd_mm_yyyy(date_str)
    elif format_type == 'YYYY-MM-DD':
        return convert_to_yyyy_mm_dd(date_str)
    else:
        return date_str  # Default MM/DD/YYYY

# In CSV generation
date_format = output_rules.get('date_format', 'MM/DD/YYYY')
formatted_date = format_date(vehicle_date, date_format)
```

---

## Success Metrics

A properly implemented filter should:

✅ **Preserve CAO Functionality**: All existing order processing works unchanged
✅ **Support Modal Context**: Functions correctly in both main app and modal wizard
✅ **Database Persistence**: Settings save and load correctly per dealership
✅ **UI Responsiveness**: Modal updates immediately reflect configuration changes
✅ **Backend Integration**: CSV output applies rules correctly
✅ **Error Resilience**: Gracefully degrades if rules are missing or invalid

---

*Last Updated: September 20, 2025*
*Implementation Reference: Glendale CDJR Price Display Feature*