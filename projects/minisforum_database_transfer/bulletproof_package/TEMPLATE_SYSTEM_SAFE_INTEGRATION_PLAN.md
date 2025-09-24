# Template System Safe Integration Plan

## Goal: Add Template System WITHOUT Breaking Current Functionality

### Current System Analysis

#### Existing Template Logic (MUST PRESERVE)
1. **Two hardcoded template types:**
   - `shortcut`: 3-column format (STOCK, MODEL, @QR)
   - `shortcut_pack`: Full format with all fields
   - Special variants like `glendale_format`

2. **Current Flow:**
   ```
   process_cao_order()
   → _get_dealership_template_config() [reads from dealership_configs.output_rules]
   → _generate_csv_from_template_data() [hardcoded formatting based on type]
   ```

3. **Critical Points:**
   - Template type determines CSV abbreviation (SC vs SCP)
   - Template type determines CSV column structure
   - QR path conversions for Nick's computer
   - Special handling for different dealerships

### Safe Integration Strategy

## Phase 1: Add WITHOUT Changing (Safe to Implement Now)

### 1. Database Layer (✅ ALREADY DONE - SAFE)
- New tables created: `template_configs`, `dealership_template_mapping`
- No impact on existing tables or logic
- Existing `dealership_configs` table untouched

### 2. API Endpoints (✅ ALREADY DONE - SAFE)
- New endpoints added under `/api/templates/*`
- Completely separate from existing order processing endpoints
- No modifications to existing endpoints

### 3. Template Resolution Service (NEW - SAFE TO ADD)
Create new service that:
```python
class TemplateResolver:
    def get_template(self, dealership_name, vehicle_condition=None):
        # 1. Check new template_configs table first
        custom_template = self._get_custom_template(dealership_name, vehicle_condition)
        if custom_template:
            return custom_template

        # 2. Fall back to existing logic
        return self._get_legacy_template(dealership_name, vehicle_condition)

    def _get_legacy_template(self, dealership_name, vehicle_condition):
        # Call existing _get_dealership_template_config()
        # Returns 'shortcut' or 'shortcut_pack'
        pass
```

### 4. Modified CSV Generation (CAREFUL IMPLEMENTATION)
```python
def _generate_csv_from_template_data(self, vehicles, dealership_name, template_type, output_folder, qr_paths):
    # Check if template_type is a custom template ID
    if isinstance(template_type, int) or template_type.startswith('custom_'):
        return self._generate_csv_from_custom_template(...)

    # Otherwise, use existing hardcoded logic
    # ALL EXISTING CODE REMAINS UNCHANGED
    if template_type == "shortcut":
        # Existing shortcut logic
    elif template_type == "shortcut_pack":
        # Existing shortcut_pack logic
```

## Phase 2: UI Addition (Safe to Add)

### Template Builder UI
- Completely new page/section
- No changes to existing UI
- Optional feature - dealerships can ignore it

### Features:
1. **Template Creator** - New page at `/templates`
2. **Template Manager** - List, edit, delete templates
3. **Preview Mode** - Test with sample data
4. **Mapping Tool** - Assign templates to dealerships

## Phase 3: Gradual Migration (Optional)

### Per-Dealership Opt-In
1. Create custom template for a dealership
2. Map it in `dealership_template_mapping`
3. Template resolver automatically uses it
4. If issues, simply delete mapping - falls back to legacy

### Migration Path:
```
Current State → Hybrid State → Full Template System
(hardcoded)    (custom+legacy)  (all custom)
```

## Safety Checks

### 1. Backwards Compatibility Tests
```python
def test_legacy_templates_still_work():
    # Process order with existing template types
    assert process_cao_order("Porsche St. Louis") uses "shortcut"
    assert process_cao_order("BMW of Columbia") uses "shortcut_pack"
```

### 2. Fallback Mechanism
```python
try:
    template = get_custom_template(dealership)
except:
    template = get_legacy_template(dealership)  # Always falls back
```

### 3. Feature Flag (Optional Extra Safety)
```python
USE_CUSTOM_TEMPLATES = config.get('enable_custom_templates', False)

if USE_CUSTOM_TEMPLATES:
    # Try new system
else:
    # Use existing system only
```

## Implementation Checklist

### Safe to Do Now:
- [x] Create database tables (DONE - no impact)
- [x] Add API endpoints (DONE - no impact)
- [ ] Create TemplateResolver service (new file, no changes to existing)
- [ ] Build UI components (new files, no changes to existing)
- [ ] Add template preview functionality (new feature, optional)

### Requires Careful Testing:
- [ ] Modify `_generate_csv_from_template_data()` to check for custom templates
- [ ] Add custom template rendering logic
- [ ] Test with one dealership first

### Do Not Change:
- ❌ Existing template type logic for 'shortcut' and 'shortcut_pack'
- ❌ Existing dealership_configs structure
- ❌ Current CSV generation for legacy templates
- ❌ QR path conversion logic
- ❌ File naming conventions

## Rollback Plan

If anything breaks:
1. Delete mapping from `dealership_template_mapping` table
2. System automatically uses legacy templates
3. No code changes needed

## Testing Strategy

### 1. Unit Tests
- Test TemplateResolver returns correct templates
- Test fallback mechanism works
- Test custom template rendering

### 2. Integration Tests
- Process order with legacy template - should work unchanged
- Process order with custom template - should use new logic
- Process order with invalid custom template - should fall back

### 3. Manual Testing
- Test one dealership with custom template
- Verify output matches expected format
- Verify QR codes work
- Verify billing sheet correct

## Conclusion

**This approach is SAFE because:**
1. We're adding new code paths, not modifying existing ones
2. Legacy system remains untouched and is the default
3. Custom templates are opt-in per dealership
4. Instant rollback by deleting database mappings
5. No changes to critical order processing logic

**Recommendation: Proceed with Phase 1 implementation**