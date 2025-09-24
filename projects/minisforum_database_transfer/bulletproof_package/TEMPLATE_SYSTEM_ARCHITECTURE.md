# Template System Architecture & Name Mapping Requirements

## Executive Summary
The template system allows users to create custom output templates for different dealerships, replacing hardcoded logic with a flexible, visual template builder. This document outlines the architecture and critical name mapping requirements.

## Current State Analysis

### Template Types Currently Used
1. **`shortcut_pack`** (34 dealerships) - Default template with VIN + QR code columns
2. **`shortcut`** (3 dealerships) - Simplified template (Porsche St. Louis, Volvo Cars West County, CDJR Columbia for new)

### Dealerships with Special Templates
- **Porsche St. Louis**: Uses `shortcut` for all conditions
- **Volvo Cars West County**: Uses `shortcut` for all conditions
- **CDJR of Columbia**: Uses `shortcut` for new vehicles, `shortcut_pack` for used

## Name Mapping Architecture

### Three-Layer Name System
The system must handle three different name formats:

1. **Display Name** (User-facing)
   - Example: `"South County DCJR"`
   - Used in: UI dropdowns, reports, user selections

2. **Database Name** (normalized_vehicle_data.location)
   - Example: `"South County Dodge Chrysler Jeep RAM"`
   - Used in: Scraper data, vehicle queries

3. **Table Slug** (VIN log tables)
   - Example: `"south_county_dcjr_vin_log"`
   - Transformation: `name.lower().replace(' ', '_').replace("'", '').replace('&', 'and')`

### Known Name Mappings
```python
NAME_MAPPINGS = {
    # Display Name -> Database Name
    'South County DCJR': 'South County Dodge Chrysler Jeep RAM',
    'Glendale Subaru': 'Glendale Chrysler Jeep Dodge Ram',
    'BMW of West St Louis': 'BMW of West St. Louis',
    # Add more as discovered
}
```

## Template System Components

### 1. Database Schema (Complete)
```sql
-- Core template storage
template_configs {
    id: SERIAL PRIMARY KEY
    template_name: VARCHAR(100) UNIQUE
    description: TEXT
    template_type: VARCHAR(50)
    fields: JSONB  -- Template field configuration
    created_by: VARCHAR(100)
    is_active: BOOLEAN
    is_system_default: BOOLEAN
}

-- Dealership-template mapping
dealership_template_mapping {
    dealership_name: VARCHAR(200)  -- Uses Display Name
    template_id: INTEGER
    vehicle_condition: VARCHAR(50)  -- new/used/cpo/null
    priority: INTEGER
}

-- Available field definitions
template_field_definitions {
    field_key: VARCHAR(50)
    field_label: VARCHAR(100)
    field_type: VARCHAR(50)  -- text/number/date/url/concatenated/calculated/special
    data_source: VARCHAR(100)  -- Column from normalized_vehicle_data
}
```

### 2. Field Types Available

#### Basic Fields (Direct Mapping)
- VIN, Stock Number, Year, Make, Model, Trim
- Price, MSRP, Condition, Status
- Date In Stock, Location, Vehicle URL

#### Concatenated Fields
- `year_make_model`: "{year} {make} {model}"
- `stock_vin`: "{stock} - {vin}"
- `full_description`: "{year} {make} {model} {trim}"
- Custom concatenations defined by user

#### Calculated Fields
- `days_on_lot`: Calculated from date_in_stock
- Custom calculations defined by user

#### Special Fields
- `qr_code`: Generated QR code image path
- Custom special handlers

### 3. Template Field Structure (JSONB)
```json
{
  "columns": [
    {
      "key": "vin",
      "label": "VIN",
      "type": "text",
      "source": "vin",
      "width": "30%",
      "order": 1,
      "formatting": null
    },
    {
      "key": "year_make_model",
      "label": "Vehicle",
      "type": "concatenated",
      "format": "{year} {make} {model}",
      "width": "40%",
      "order": 2
    },
    {
      "key": "qr_code",
      "label": "QR Code",
      "type": "special",
      "source": "qr_code",
      "width": "30%",
      "order": 3
    }
  ]
}
```

## Integration Requirements

### 1. Name Mapping Service
Create a centralized service to handle all name mappings:

```python
class DealershipNameMapper:
    def get_display_name(self, any_name: str) -> str
    def get_database_name(self, any_name: str) -> str
    def get_table_slug(self, any_name: str) -> str
    def get_vin_log_table(self, any_name: str) -> str
```

### 2. Template Resolution
When processing an order:
1. Get dealership display name
2. Map to database name for queries
3. Check dealership_template_mapping for custom template
4. Fall back to default template if none found
5. Apply template to generate output

### 3. UI Requirements

#### Template Builder Interface
- Drag-and-drop field arrangement
- Field property editor (label, width, formatting)
- Live preview with sample data
- Save/export template configuration

#### Template Management
- List all templates
- Clone existing template
- Map template to dealership
- Set condition-specific templates (new/used)

## Migration Strategy

### Phase 1: Foundation (Complete)
✅ Database schema created
✅ API endpoints implemented
✅ Field definitions populated

### Phase 2: Name Mapping Service
- [ ] Create unified name mapping service
- [ ] Populate all known mappings
- [ ] Update order processing to use service

### Phase 3: Template Builder UI
- [ ] Create React component for template builder
- [ ] Implement drag-and-drop interface
- [ ] Add live preview functionality
- [ ] Integrate with API endpoints

### Phase 4: Integration
- [ ] Update order processor to use template system
- [ ] Migrate existing hardcoded templates
- [ ] Test with all 36 dealerships

### Phase 5: Enhancement
- [ ] Add more field types
- [ ] Support conditional formatting
- [ ] Add template versioning
- [ ] Create template marketplace

## Critical Considerations

### 1. Backwards Compatibility
- Keep existing `shortcut` and `shortcut_pack` working
- Gradual migration path for dealerships

### 2. Performance
- Cache template configurations
- Minimize database queries during processing

### 3. Data Consistency
- Ensure name mappings are consistent across system
- Validate template fields against available data

### 4. User Experience
- Intuitive template builder interface
- Clear error messages for invalid configurations
- Template preview before applying

## Next Steps

1. **Immediate**: Create unified name mapping service
2. **Short-term**: Build template builder UI component
3. **Medium-term**: Integrate with order processor
4. **Long-term**: Expand field types and capabilities

## Appendix: All Dealerships

### Current Active Dealerships (40)
1. Auffenberg Hyundai
2. BMW of Columbia
3. BMW of West St Louis
4. Bommarito Cadillac
5. Bommarito West County
6. CDJR of Columbia
7. Columbia Honda
8. Dave Sinclair Lincoln
9. Dave Sinclair Lincoln St. Peters
10. Frank Leta Honda
11. Glendale CDJR
12. Honda of Frontenac
13. HW Kia of West County
14. Indigo Auto Group
15. Jaguar Rancho Mirage
16. Joe Machens Hyundai
17. Joe Machens Nissan
18. Joe Machens Toyota
19. KIA of Columbia
20. Land Rover Rancho Mirage
21. Mini of St. Louis
22. Pappas Toyota
23. Porsche St. Louis
24. Pundmann Ford
25. Rusty Drewing Cadillac
26. Rusty Drewing Chevy BGMC
27. Serra Honda O'Fallon
28. South County DCJR
29. Spirit Lexus
30. Suntrup Buick GMC
31. Suntrup Ford Kirkwood
32. Suntrup Ford Westport
33. Suntrup Hyundai South
34. Suntrup Kia South
35. Thoroughbred Ford
36. Volvo Cars West County
37. Weber Chevrolet
38. McMahon Ford
39. Weiss Toyota of South County
40. Newbold BMW