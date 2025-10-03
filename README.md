# Silver Fox Order Processing System

**Version:** 2.0 - Production Ready
**Status:** 90% Complete
**Purpose:** Automated order processing and QR code generation for automotive dealership graphics

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Quick Start](#quick-start)
3. [Order Processing](#order-processing)
4. [VIN Log Management](#vin-log-management)
5. [Template Creation](#template-creation)
6. [System Architecture](#system-architecture)
7. [Troubleshooting](#troubleshooting)

---

## System Overview

The Silver Fox Order Processing System automates the creation of graphics orders for 36+ automotive dealerships. The system:

- **Processes CAO (Comparative Analysis Orders)**: Automatically identifies vehicles needing graphics
- **Handles LIST Orders**: Processes specific VIN lists provided by dealerships
- **Generates QR Codes**: Creates 388x388 PNG QR codes for Adobe template integration
- **Tracks Order History**: Maintains VIN logs to prevent duplicate processing
- **Real-time Progress**: Socket.IO integration for live order processing updates

### Key Features

- Dark mode UI with responsive design
- PostgreSQL database with connection pooling
- Active scraper data integration
- Per-dealership configuration and filtering
- Zero-downtime deployment architecture

---

## Quick Start

### Launch the Application

1. Navigate to the web GUI directory:
   ```bash
   cd C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\web_gui
   ```

2. Start the Flask server:
   ```bash
   py app.py
   ```

3. Open browser to: `http://127.0.0.1:5000`

### First-Time Setup

1. Verify database connection in console output
2. Check that scraper data is imported and marked as `active`
3. Confirm dealership configurations are loaded
4. Verify VIN log tables exist for all dealerships

---

## Order Processing

### Understanding Order Types

The system supports two order types:

1. **CAO (Comparative Analysis Orders)**: Automatically finds vehicles that need graphics
2. **LIST Orders**: Processes specific VIN lists provided by dealerships

### CAO (Comparative Analysis Orders)

**What CAO Does:**

CAO finds vehicles in the active scraper dataset that meet ALL of these criteria:
- Match dealership location exactly
- Match configured vehicle types (new/used/cpo)
- Have been on the lot for minimum seasoning days
- Are NOT in the dealership's VIN log (haven't been processed before)

**How CAO Works:**

```sql
-- Core CAO Logic
SELECT * FROM normalized_vehicle_data nvd
JOIN scraper_imports si ON nvd.import_id = si.import_id
WHERE nvd.location = 'Dealership Name'
  AND si.status = 'active'
  AND nvd.vehicle_condition IN (dealership_vehicle_types)
  AND nvd.vin NOT IN (SELECT vin FROM [dealership]_vin_log)
  AND nvd.first_seen_date <= CURRENT_DATE - seasoning_days
```

**Processing a CAO Order:**

1. Navigate to **Order Processing** page in web interface
2. Select dealership from dropdown menu
3. Click **"Process CAO Order"** button
4. System automatically:
   - Queries active scraper data
   - Applies dealership filtering rules
   - Excludes VINs already in VIN log
   - Generates QR codes (388x388 PNG)
   - Creates order summary file
   - Adds processed VINs to VIN log

**Expected Results:**

- Small dealerships: 6-20 vehicles per order
- Large dealerships: 20-50 vehicles
- If results are abnormally high (100+), investigate:
  - Is scraper data marked as `active`?
  - Is VIN log populated correctly?
  - Are vehicle type filters configured correctly?

**Output Structure:**

```
orders/
  [dealership_name]/
    CAO_[timestamp]/
      qr_codes/
        [vin]_qr.png (388x388 PNG)
      order_summary.txt
      processed_vins.txt
```

### LIST Orders

**What LIST Does:**

Processes a specific list of VINs provided by the dealership, regardless of whether they're in the current inventory or VIN log.

**Processing a LIST Order:**

1. Navigate to **Order Processing** page
2. Select dealership from dropdown
3. Click **"Process LIST Order"**
4. Provide VINs using one of these methods:
   - **Upload CSV**: File with VIN column
   - **Paste VINs**: One VIN per line in text area
5. System will:
   - Validate all VINs (17 characters, alphanumeric)
   - Generate QR codes for each VIN
   - Create order files
   - Add VINs to dealership VIN log

**CSV Format for LIST Orders:**

```csv
VIN
1HGCM82633A123456
2HGFG12828H123457
3VWFE21C04M123458
```

Or with order numbers:

```csv
ORDER #,VIN
42546,1HGCM82633A123456
42546,2HGFG12828H123457
42547,3VWFE21C04M123458
```

### Understanding Order Results

**QR Code Specifications:**

- **Size**: 388x388 pixels
- **Format**: PNG with transparency
- **Error Correction**: High (30% recovery)
- **Content**: VIN number only (17 characters)
- **Resolution**: 300 DPI for print quality

**Order Summary Contains:**

- Order type (CAO/LIST)
- Processing timestamp
- Dealership name
- Total VINs processed
- Vehicle breakdown by condition (new/used/cpo)
- Processing notes/errors
- QR code file paths

### Vehicle Type Filtering

**Configuration Examples:**

```python
# New vehicles only
vehicle_types: ['new']
# Matches: condition = 'new'

# All used vehicles
vehicle_types: ['used']
# Matches: condition IN ('used', 'po', 'cpo', 'certified', 'pre-owned')

# New and used
vehicle_types: ['new', 'used']
# Matches: all conditions
```

**Important:** The term "used" is an UMBRELLA term that includes:
- 'used'
- 'po' (pre-owned)
- 'cpo' (certified pre-owned)
- 'certified'
- 'pre-owned'

### Seasoning Filter

Prevents processing vehicles that just arrived on lot:

```python
dealership_config = {
    'seasoning_days': 7  # Vehicle must be on lot for 7+ days
}

# Example Calculation:
# Today: Monday, Oct 7, 2025
# 7 days ago: Monday, Sep 30, 2025
# Include: Vehicles with first_seen_date <= Sep 30
```

The seasoning filter counts **backwards** from today:
- 7 days = vehicle must have been on lot for at least 7 full days
- Today does NOT count as day 1
- Prevents processing vehicles that just arrived

---

## VIN Log Management

### What Are VIN Logs?

VIN logs are **order history tables** that track which vehicles have been processed for each dealership. They prevent duplicate processing by excluding previously handled VINs from future CAO orders.

**Critical Distinction:**
- VIN logs = ORDER HISTORY (what we've processed)
- raw_vehicle_data = CURRENT INVENTORY (what's on the lot now)

### VIN Log Table Structure

Each dealership has its own VIN log table:

```sql
CREATE TABLE [dealership_name]_vin_log (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    order_number VARCHAR(50),
    order_type VARCHAR(20),
    created_at DATE,
    processed_date DATE NOT NULL
);
```

**Table Naming Convention:**

```
Dealership Name: "Dave Sinclair Lincoln St. Peters"
Table Name: dave_sinclair_lincoln_st_peters_vin_log

Rules:
- Convert to lowercase
- Replace spaces with underscores
- Remove apostrophes
- Append "_vin_log"
```

**Examples:**

| Dealership Name | Table Name |
|----------------|------------|
| BMW of West St. Louis | bmw_of_west_st_louis_vin_log |
| Serra Honda O'Fallon | serra_honda_ofallon_vin_log |
| CDJR of Columbia | cdjr_of_columbia_vin_log |
| Dave Sinclair Lincoln St. Peters | dave_sinclair_lincoln_st_peters_vin_log |

### Importing VIN Logs from CSV

When migrating from legacy systems or bulk-importing historical orders, use VIN log import scripts.

#### CSV Format Requirements

**Format 1: Order Number with VIN Grouping**

Used when order numbers are in first column, VINs in second column, with blank rows separating order groups:

```csv
ORDER,VIN
42546,1HGCM82633A123456
,2HGFG12828H123457
,3VWFE21C04M123458

42547,5FNRL6H78MB123459
,4T1BF1FK8CU123460
```

**Format 2: DictReader Format**

Used when CSV has named column headers:

```csv
ORDER #,VIN
42546,1HGCM82633A123456
42546,2HGFG12828H123457
42547,3VWFE21C04M123458
```

**Format 3: Simple VIN List**

Used when only VINs need to be imported (no order numbers):

```csv
VIN
1HGCM82633A123456
2HGFG12828H123457
3VWFE21C04M123458
```

#### Import Script Template

Create an import script for each dealership using this template:

```python
"""
Import [Dealership Name] VIN log with order number grouping
"""
import sys
import csv
from datetime import datetime
sys.path.insert(0, r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts')

from database_connection import db_manager

# Configuration
CSV_FILE = r"C:\Users\Workstation_1\Downloads\dealership_vinlog.csv"
TABLE_NAME = "dealership_name_vin_log"
IMPORT_DATE = '2025-10-02'
ORDER_TYPE = 'manual'

def parse_order_groups():
    """Parse CSV into order groups (ORDER column, then VIN column)"""

    order_groups = []
    current_order = None
    current_vins = []

    with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header row

        for row_num, row in enumerate(reader, start=2):
            # Blank row - end of order group
            if len(row) < 2:
                if current_order and current_vins:
                    order_groups.append({
                        'order_number': current_order,
                        'vins': current_vins.copy()
                    })
                    print(f"[GROUP] Order {current_order}: {len(current_vins)} VINs")
                current_order = None
                current_vins = []
                continue

            order_col = row[0].strip() if row[0] else ''
            vin_col = row[1].strip() if len(row) > 1 and row[1] else ''

            # New order number
            if order_col:
                # Save previous group if exists
                if current_order and current_vins:
                    order_groups.append({
                        'order_number': current_order,
                        'vins': current_vins.copy()
                    })
                    print(f"[GROUP] Order {current_order}: {len(current_vins)} VINs")

                current_order = order_col
                current_vins = []

                # Check if VIN is in same row
                if vin_col:
                    current_vins.append(vin_col)
            else:
                # VIN belongs to current order
                if vin_col and current_order:
                    current_vins.append(vin_col)

        # Don't forget last group
        if current_order and current_vins:
            order_groups.append({
                'order_number': current_order,
                'vins': current_vins.copy()
            })
            print(f"[GROUP] Order {current_order}: {len(current_vins)} VINs")

    return order_groups

def import_vinlog():
    """Import VIN log with order numbers"""

    print(f"\n{'='*80}")
    print(f"[Dealership Name] VIN Log Import")
    print(f"{'='*80}\n")

    # Parse order groups
    print("[PARSE] Reading CSV and grouping by order number...")
    order_groups = parse_order_groups()

    total_vins = sum(len(g['vins']) for g in order_groups)

    print(f"\n[INFO] Parsed {len(order_groups)} order groups")
    print(f"[INFO] Total VINs: {total_vins}")

    # Show sample
    print(f"\n[SAMPLE] First 5 order groups:")
    for group in order_groups[:5]:
        print(f"  Order {group['order_number']}: {len(group['vins'])} VINs")
        for vin in group['vins'][:3]:
            print(f"    - {vin}")
        if len(group['vins']) > 3:
            print(f"    ... and {len(group['vins']) - 3} more")

    # Check if records already exist
    count_query = f"SELECT COUNT(*) as total FROM {TABLE_NAME}"
    existing = db_manager.execute_query(count_query, fetch='one')

    if existing and existing['total'] > 0:
        print(f"\n[WARNING] {existing['total']} records already exist in {TABLE_NAME}")
        response = input(f"[CONFIRM] Delete existing records and import {total_vins} VINs? (yes/no): ")
        if response.lower() == 'yes':
            delete_query = f"DELETE FROM {TABLE_NAME}"
            deleted = db_manager.execute_non_query(delete_query)
            print(f"[DELETE] Removed {deleted} existing records")
        else:
            print("[CANCELLED] Import cancelled by user")
            return
    else:
        response = input(f"\n[CONFIRM] Import {total_vins} VINs across {len(order_groups)} orders? (yes/no): ")
        if response.lower() != 'yes':
            print("[CANCELLED] Import cancelled by user")
            return

    # Import with order numbers
    print(f"\n[IMPORT] Starting import with order numbers...")

    insert_query = f"""
        INSERT INTO {TABLE_NAME} (vin, order_number, order_type, created_at, processed_date)
        VALUES (%s, %s, %s, %s, %s)
    """

    imported = 0
    errors = 0

    for group in order_groups:
        order_num = group['order_number']
        vins = group['vins']

        for vin in vins:
            try:
                db_manager.execute_non_query(
                    insert_query,
                    (vin, order_num, ORDER_TYPE, IMPORT_DATE, IMPORT_DATE)
                )
                imported += 1
                if imported % 100 == 0:
                    print(f"[PROGRESS] Imported {imported}/{total_vins} VINs...")
            except Exception as e:
                errors += 1
                print(f"[ERROR] Failed to import {vin} for order {order_num}: {e}")

    print(f"\n{'='*80}")
    print(f"[SUCCESS] Import Complete!")
    print(f"{'='*80}")
    print(f"Total VINs processed: {total_vins}")
    print(f"Successfully imported: {imported}")
    print(f"Errors: {errors}")
    print(f"Order groups: {len(order_groups)}")
    print(f"Import date: {IMPORT_DATE}")

    # Verify import
    count_query = f"SELECT COUNT(*) as total FROM {TABLE_NAME} WHERE created_at = %s"
    result = db_manager.execute_query(count_query, (IMPORT_DATE,), fetch='one')

    if result:
        print(f"\n[VERIFY] Total records with date {IMPORT_DATE}: {result['total']}")

    # Show sample with order numbers
    sample_query = f"""
        SELECT vin, order_number
        FROM {TABLE_NAME}
        WHERE created_at = %s
        LIMIT 10
    """
    samples = db_manager.execute_query(sample_query, (IMPORT_DATE,))

    if samples:
        print(f"\n[SAMPLE] Imported records with order numbers:")
        for s in samples:
            print(f"  Order {s['order_number']}: {s['vin']}")

if __name__ == "__main__":
    import_vinlog()
```

#### Running VIN Log Imports

**Step-by-Step Process:**

1. **Create import script** for specific dealership (copy template above)

2. **Update configuration variables:**
   ```python
   CSV_FILE = r"C:\Users\Workstation_1\Downloads\dealership_vinlog.csv"
   TABLE_NAME = "dealership_name_vin_log"
   IMPORT_DATE = '2025-10-02'  # Date to assign to imported records
   ORDER_TYPE = 'manual'        # Order type designation
   ```

3. **Adjust parsing logic** based on CSV format:
   - Use `csv.reader(f)` for indexed column access (row[0], row[1])
   - Use `csv.DictReader(f)` for named column access (row['ORDER #'], row['VIN'])

4. **Run the import script:**
   ```bash
   cd bulletproof_package
   echo yes | py import_dealership_vinlog.py
   ```

   Or manually with confirmation:
   ```bash
   py import_dealership_vinlog.py
   # Type 'yes' when prompted
   ```

5. **Verify results** in console output and database

#### Real Import Examples

**Example 1: CDJR of Columbia**

```bash
# File: reimport_cdjr_columbia_vinlog_with_orders.py
# CSV Format: ORDER #, VIN with blank rows separating groups
# Result: 1,486 VINs across 126 order groups

cd bulletproof_package
echo yes | py reimport_cdjr_columbia_vinlog_with_orders.py
```

**Example 2: Dave Sinclair Lincoln St. Peters**

```bash
# File: import_dave_sinclair_stpeters_vinlog.py
# CSV Format: ORDER, VIN with blank rows separating groups
# Result: 417 VINs across 17 order groups

cd bulletproof_package
echo yes | py import_dave_sinclair_stpeters_vinlog.py
```

#### Verifying VIN Log Imports

**Check import results:**

```sql
-- Count total records
SELECT COUNT(*) FROM dealership_name_vin_log;

-- View sample with order numbers
SELECT vin, order_number, created_at, processed_date
FROM dealership_name_vin_log
ORDER BY created_at DESC
LIMIT 10;

-- Check for duplicates
SELECT vin, COUNT(*) as count
FROM dealership_name_vin_log
GROUP BY vin
HAVING COUNT(*) > 1;

-- Verify import by date
SELECT COUNT(*) as total, order_number
FROM dealership_name_vin_log
WHERE created_at = '2025-10-02'
GROUP BY order_number
ORDER BY order_number;
```

### Managing VIN Logs

**View VIN Log History:**

```sql
-- Recent records
SELECT * FROM dealership_name_vin_log
WHERE created_at >= '2025-10-01'
ORDER BY created_at DESC
LIMIT 100;

-- By order number
SELECT * FROM dealership_name_vin_log
WHERE order_number = '42546'
ORDER BY processed_date;
```

**Delete Specific Order:**

```sql
DELETE FROM dealership_name_vin_log
WHERE order_number = '42546';
```

**Delete by Date Range:**

```sql
DELETE FROM dealership_name_vin_log
WHERE created_at BETWEEN '2025-10-01' AND '2025-10-02';
```

**Clear All Records (use with caution):**

```sql
-- This will make CAO return ALL vehicles on next run
DELETE FROM dealership_name_vin_log;
```

### VIN Log Best Practices

1. **Never delete VIN logs unless migrating/testing**
   - VIN logs are cumulative order history
   - Deleting logs causes duplicate processing

2. **Always include order numbers when importing**
   - Order numbers track which VINs were processed together
   - Helpful for debugging and reporting

3. **Use consistent import dates**
   - Import date represents when VINs were added to system
   - Processed date represents actual order date (if available)

4. **Verify imports before processing CAO**
   - Run count queries to ensure import completed
   - Check for duplicate VINs that shouldn't exist

---

## Template Creation

### Adobe Template Requirements

Templates must be designed with QR code placeholders that the system will populate.

**Template Specifications:**

- **Format**: Adobe InDesign/Illustrator
- **QR Code Placeholder**: 388x388 pixel frame
- **Placeholder Naming**: Clearly labeled for QR code positions
- **Output Format**: PDF or print-ready format

### Template File Organization

```
templates/
  [dealership_name]/
    cao_template.indd
    cao_template_proof.pdf
    list_template.indd
    notes.txt
```

### QR Code Integration Workflow

**Step 1: Designer Creates Template**

1. Design graphics with vehicle information layout
2. Add 388x388 pixel placeholder boxes for QR codes
3. Name/label QR code positions clearly (e.g., "QR_CODE_1", "QR_CODE_2")
4. Export template with placeholder markers
5. Document placeholder positions in notes.txt

**Step 2: System Generates QR Codes**

1. Order processing creates `[vin]_qr.png` files
2. Each QR code is 388x388 pixels with high error correction
3. Files saved in `orders/[dealership]/[order_id]/qr_codes/`
4. Order summary lists all QR code file paths

**Step 3: Designer Populates Template**

1. Open Adobe template file
2. Place QR code PNGs into placeholder frames
3. Verify alignment and sizing (should be exact fit)
4. Export final graphics for printing
5. Send to dealership or printer

### Template Naming Conventions

**File Naming:**

```
[dealership_short_name]_[order_type]_template_v[version].indd

Examples:
serra_honda_cao_template_v2.indd
dave_sinclair_list_template_v1.indd
cdjr_columbia_cao_template_v3.indd
bmw_west_stl_flyout_template_v1.indd
```

**Version Control:**

- **v1**: Initial template
- **v2**: Minor updates (colors, fonts, layout tweaks)
- **v3**: Major revisions (complete redesign)

### QR Code Specifications for Designers

**Technical Specifications:**

```
Dimensions: 388x388 pixels
Resolution: 300 DPI (suitable for print)
Format: PNG with transparency
Color Mode: RGB (convert to CMYK for print)
Error Correction: High (30% damage recovery)
Content: VIN number only (17 characters)
Quiet Zone: Included in 388x388 dimensions
Background: Transparent (can place on any background)
```

**Print Specifications:**

```
Print Size: 1.29" x 1.29" at 300 DPI
Scaling: Do NOT scale - use 100% size
Placement: Center in designated placeholder area
Bleed: Not required (quiet zone handles edge proximity)
```

### Template Types

The system supports multiple template types:

**1. CAO Templates**
- Used for Comparative Analysis Orders
- Multiple QR codes per sheet
- Vehicle information layout with QR code integration

**2. LIST Templates**
- Used for specific VIN lists
- Similar to CAO but may have different styling
- Custom layouts per dealership requirements

**3. Flyout Templates**
- Single vehicle showcase format
- Large QR code with minimal vehicle info
- Quick-print format

**4. Shortcut Templates**
- Compact format with essential details
- Multiple vehicles per page
- High-density QR code placement

**5. Shortcut Pack Templates**
- Bulk processing format
- Grid layout with many vehicles
- Optimized for batch printing

### Testing Templates

**Before Production Use:**

1. **Process test order** (3-5 VINs)
   ```bash
   # Create small test order via web interface
   # Select dealership > Process LIST Order
   # Enter 3-5 test VINs
   ```

2. **Generate QR codes**
   - Verify QR codes are created in orders directory
   - Check file size (should be ~5-10 KB per PNG)
   - Verify dimensions (exactly 388x388 pixels)

3. **Place QR codes in template**
   - Open Adobe template
   - Place all QR code PNGs
   - Verify alignment

4. **Print test sheet**
   - Export to PDF
   - Print on actual paper/material
   - Check quality and sizing

5. **Scan QR codes**
   - Use mobile device camera or QR scanner app
   - Verify each QR code decodes to correct VIN
   - Check that all 17 characters are readable

6. **Verify print quality**
   - Check sharpness and clarity
   - Ensure QR codes are scannable from 6-12 inches away
   - Test under different lighting conditions

**Common Template Issues:**

| Issue | Cause | Solution |
|-------|-------|----------|
| QR codes blurry | Scaled or resized | Use 100% size, no scaling |
| Won't scan | Too small or low resolution | Verify 388x388 at 300 DPI |
| Distorted | Incorrect aspect ratio | Verify square placeholder frame |
| Cut off edges | Insufficient quiet zone | Ensure full 388x388 area visible |
| Color issues | Wrong color mode | Use RGB source, convert to CMYK for print |

### Template Customization

**Per-Dealership Customization:**

Each dealership can have custom:
- Brand colors and logos
- Font styles and sizes
- Layout and spacing
- QR code positioning
- Additional graphics/backgrounds

**Creating Custom Template:**

1. Start with base template (generic format)
2. Apply dealership branding:
   - Replace placeholder logo with dealership logo
   - Update colors to match brand guidelines
   - Adjust fonts to dealership preferences
3. Adjust QR code positions if needed (maintain 388x388 size)
4. Test with sample order
5. Save as versioned template file
6. Document customizations in notes.txt

---

## System Architecture

### Database Structure

**Active Scraper Data:**

- `raw_vehicle_data`: Current inventory from scraper
- `scraper_imports`: Import tracking (status: active/archived)
- `normalized_vehicle_data`: Standardized data for processing

**Configuration:**

- `dealership_configs`: Per-dealership filtering rules
- Individual VIN log tables: `[dealership_name]_vin_log`

**Key Relationships:**

```
scraper_imports (status='active')
  -> raw_vehicle_data (import_id FK)
  -> normalized_vehicle_data (import_id FK)
  -> CAO query (exclude dealership_vin_log)
  -> Order generation
  -> Add VINs to dealership_vin_log
```

### Critical System Rules

**1. ACTIVE DATASET RULE:**

- CAO processing ONLY uses scraper datasets marked `status = 'active'`
- NEVER use import dates/timestamps to determine dataset currency
- Only one import can be active at a time
- Archived imports are excluded from all processing

**2. VIN LOG EXCLUSION:**

- VIN logs contain ORDER HISTORY, not current inventory
- CAO queries MUST exclude VINs from dealership's VIN log
- Purpose: Prevent duplicate processing
- VIN logs are cumulative and should NEVER be cleared (except for testing)

**3. NAME MAPPING CONSISTENCY:**

- Dealership config `name` must match `raw_vehicle_data.location` exactly
- Case-sensitive matching
- VIN log table name derived from dealership name:
  - Convert to lowercase
  - Replace spaces with underscores
  - Remove apostrophes
  - Append `_vin_log`

**4. VEHICLE TYPE FILTERING:**

- `vehicle_types: ['new']` = Only 'new' vehicles
- `vehicle_types: ['used']` = All used types: 'used', 'po', 'cpo', 'certified', 'pre-owned'
- `vehicle_types: ['new', 'used']` = All vehicle types

### File Structure

```
bulletproof_package/
  web_gui/
    app.py                        # Flask application
    static/
      css/style.css               # UI styling
      js/app.js                   # Frontend logic
    templates/
      index.html                  # Main interface

  scripts/
    database_connection.py        # PostgreSQL connection manager
    correct_order_processing.py   # CAO/LIST order logic

  orders/                         # Generated order files
    [dealership_name]/
      CAO_[timestamp]/
        qr_codes/
          [vin]_qr.png
        order_summary.txt
        processed_vins.txt
      LIST_[timestamp]/
        qr_codes/
          [vin]_qr.png
        order_summary.txt

  import_*.py                     # VIN log import scripts

  README.md                       # This file
  PRODUCTION_PACKAGING_GUIDE.md   # Production deployment
  UPDATE_DEPLOYMENT_STRATEGY.md   # Update/rollback procedures
```

### Active Dealerships (36)

**Premium Automotive Brands:**
- Auffenberg Hyundai
- BMW of West St. Louis
- Bommarito Cadillac
- Bommarito West County
- Columbia BMW
- Porsche St. Louis
- Spirit Lexus

**Honda/Acura Network:**
- Columbia Honda
- Frank Leta Honda
- Honda of Frontenac
- Serra Honda O'Fallon

**Ford Network:**
- Pundmann Ford
- Suntrup Ford Kirkwood
- Suntrup Ford West
- Thoroughbred Ford

**General Motors Network:**
- Rusty Drewing Cadillac
- Rusty Drewing Chevrolet Buick GMC
- Suntrup Buick GMC
- Weber Chevrolet

**Hyundai/Kia Network:**
- HW Kia
- Kia of Columbia
- Suntrup Hyundai South
- Suntrup Kia South

**Chrysler/Dodge/Jeep Network:**
- CDJR of Columbia
- Glendale Chrysler Jeep
- South County Autos

**Lincoln Network:**
- Dave Sinclair Lincoln
- Dave Sinclair Lincoln South
- Dave Sinclair Lincoln St. Peters

**Toyota/Lexus/Nissan:**
- Joe Machens Nissan
- Pappas Toyota

**Specialty Imports:**
- Land Rover Ranch Mirage
- Mini of St. Louis
- West County Volvo Cars

**Multi-Brand:**
- Joe Machens CDJR
- Joe Machens Hyundai
- Joe Machens Toyota

---

## Troubleshooting

### CAO Returns No Results

**Check these items:**

1. **Is scraper data marked as active?**
   ```sql
   SELECT import_id, status, import_date
   FROM scraper_imports
   ORDER BY import_date DESC
   LIMIT 5;
   ```

   Expected: One import with `status = 'active'`

   Fix: Mark correct import as active:
   ```sql
   UPDATE scraper_imports SET status = 'archived' WHERE status = 'active';
   UPDATE scraper_imports SET status = 'active' WHERE import_id = [correct_id];
   ```

2. **Does dealership name match exactly?**
   ```sql
   -- Check what names exist in data
   SELECT DISTINCT location FROM raw_vehicle_data ORDER BY location;

   -- Check what names are in config
   SELECT name FROM dealership_configs ORDER BY name;
   ```

   Fix: Update config to match exactly (case-sensitive)

3. **Are all vehicles already in VIN log?**
   ```sql
   -- Count vehicles in current inventory
   SELECT COUNT(*) as inventory_count
   FROM raw_vehicle_data
   WHERE location = 'Dealership Name';

   -- Count VINs in history
   SELECT COUNT(*) as history_count
   FROM dealership_name_vin_log;
   ```

   If history_count >= inventory_count, all vehicles have been processed

4. **Is vehicle type filtering too narrow?**
   ```sql
   -- Check what conditions exist
   SELECT vehicle_condition, COUNT(*) as count
   FROM raw_vehicle_data
   WHERE location = 'Dealership Name'
   GROUP BY vehicle_condition;
   ```

   Compare with dealership config `vehicle_types`

### CAO Returns Too Many Results

**Check these items:**

1. **Vehicle type filtering too broad?**
   - Config has `vehicle_types: ['used']` which includes all used types
   - May need to narrow to specific conditions

2. **Seasoning days threshold too low?**
   - Config has `seasoning_days: 1` allows very recent vehicles
   - Increase to 7-14 days for better filtering

3. **VIN log cleared accidentally?**
   ```sql
   SELECT COUNT(*) FROM dealership_name_vin_log;
   ```
   If count is 0, VIN log was cleared - reimport historical data

### QR Codes Won't Scan

**Check these items:**

1. **Print resolution**
   - Must be 300 DPI minimum
   - Verify in Adobe export settings

2. **Quiet zone**
   - Ensure white space around QR code
   - Don't crop edges of 388x388 PNG

3. **Size**
   - Verify QR codes are 388x388 pixels
   - Do NOT scale - use 100% size in template

4. **Damage tolerance**
   - System uses high error correction (30% damage recovery)
   - Check for severe distortion or printing defects

### Database Connection Errors

**Check these items:**

1. **PostgreSQL service running?**
   ```bash
   # Check Windows services
   services.msc
   # Look for "postgresql-x64-16"
   ```

2. **Connection credentials**
   - Verify in `scripts/database_connection.py`
   - Check password, host, port, database name

3. **Network connectivity**
   - If remote database, check firewall rules
   - Verify port 5432 is accessible

4. **Connection pool exhausted**
   ```python
   # Check pool settings in database_connection.py
   minconn=1, maxconn=10
   ```

### Import Script Errors

**Common Issues:**

1. **Encoding errors**
   ```python
   # Always use utf-8-sig for CSV files
   with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
   ```

2. **Column name mismatches**
   ```python
   # Verify CSV headers match expected format
   # Use csv.DictReader for named columns
   # Use csv.reader for indexed columns
   ```

3. **NULL constraint violations**
   ```sql
   -- Check table structure
   \d dealership_name_vin_log

   -- Ensure all NOT NULL fields have values in INSERT
   INSERT INTO table (vin, order_number, created_at, processed_date)
   VALUES (%s, %s, %s, %s)
   ```

4. **Duplicate VINs**
   ```python
   # Check for UNIQUE constraints
   # Handle duplicates in import logic
   try:
       db_manager.execute_non_query(insert_query, params)
   except Exception as e:
       if 'duplicate' in str(e).lower():
           print(f"[SKIP] Duplicate VIN: {vin}")
   ```

---

## Support & Development

### Development Team

**Silver Fox Marketing**
Automotive dealership graphics and marketing solutions

### System Status

- **Version**: 2.0
- **Completion**: 90%
- **Production Ready**: Yes (final optimizations in progress)
- **Active Dealerships**: 36
- **Total VINs Processed**: 28,000+

### Related Documentation

- `PRODUCTION_PACKAGING_GUIDE.md` - Production server setup with Waitress
- `UPDATE_DEPLOYMENT_STRATEGY.md` - Version-based deployment with instant rollback
- `FINAL_PRODUCTION_DEPLOYMENT.md` - Complete 50-page deployment manual
- `SILVER_FOX_ORDER_SYSTEM_DEVELOPMENT_HISTORY.md` - Technical evolution and debugging

### System Requirements

- Windows 10/11
- PostgreSQL 16
- Python 3.8+
- 4GB RAM minimum
- 10GB disk space recommended

### Security Notes

- Database password should be strong (12+ characters)
- Regular backups recommended (automated daily)
- QR code directories should have proper permissions
- Review firewall rules for PostgreSQL port 5432

---

**Last Updated:** October 3, 2025
**Silver Fox Marketing - Automotive Order Processing System**
