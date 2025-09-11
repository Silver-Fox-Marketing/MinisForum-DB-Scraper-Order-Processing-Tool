# VIN LOG IMPORT HANDOVER DOCUMENTATION
## Silver Fox Marketing - Standardized VIN Log Import Process

**Created:** January 10, 2025  
**Purpose:** Standardize VIN log CSV imports to prevent data loss and maintain consistency

---

## 🚨 CRITICAL REQUIREMENTS

### **MUST IMPORT ALL VINS - INCLUDING DUPLICATES**
- **VIN logs track EVERY graphics order** - duplicates represent repeat orders for the same vehicle
- **NEVER use ON CONFLICT DO NOTHING** - this loses duplicate VIN records
- **NEVER use unique constraints on VIN column** - VINs can and should repeat across orders
- **Each row represents a graphics order event** - not just a unique vehicle

---

## 📊 VIN LOG TABLE STRUCTURE

### **Standard VIN Log Table Schema**
```sql
CREATE TABLE dealership_name_vin_log (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,  -- NOT UNIQUE! VINs can repeat
    dealership VARCHAR(255) NOT NULL,
    order_number VARCHAR(50),
    order_date DATE,
    order_type VARCHAR(20),  -- 'CAO' or 'LIST'
    template_type VARCHAR(50),
    processed_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- NO UNIQUE CONSTRAINT ON VIN!
    INDEX idx_vin (vin),
    INDEX idx_order_number (order_number),
    INDEX idx_dealership (dealership)
);
```

### **Naming Convention**
- **Table name format:** `dealership_name_vin_log` (all lowercase, underscores)
- **Examples:** 
  - `pappas_toyota_vin_log`
  - `bmw_west_stl_vin_log`
  - `suntrup_ford_westport_vin_log`

---

## 📁 CSV FILE FORMATS

### **Format 1: Order Number in First Column**
```csv
,VINS
40410,JTDBCMFE6R3062394
,3TMLB5JN4RM023368
,JTEAAAAH7RJ185811
40503,3TMLB5JN4RM037089
,3TMLB5JN6RM043038
```
- **First column:** Order number (only on first VIN of each order group)
- **Second column:** VIN
- **Order number propagates** to all following VINs until next order number

### **Format 2: Standard Three Column**
```csv
VIN,Order Number,Order Date
JTDBCMFE6R3062394,40410,2024-08-09
3TMLB5JN4RM023368,40410,2024-08-09
JTEAAAAH7RJ185811,40410,2024-08-09
```
- All data explicitly provided per row

### **Format 3: VIN Only**
```csv
VIN
JTDBCMFE6R3062394
3TMLB5JN4RM023368
JTEAAAAH7RJ185811
```
- Requires manual order number assignment

---

## 🔧 IMPORT PROCESS

### **Step 1: Verify Dealership Configuration**
```python
# Check dealership exists in system
SELECT name FROM dealership_configs WHERE LOWER(name) LIKE '%dealership_name%'
```

### **Step 2: Identify VIN Log Table**
```python
# Find correct table name
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE '%dealership_name%vin_log%'
```

### **Step 3: Prepare Table**
```python
# Add missing columns if needed (don't drop table!)
ALTER TABLE dealership_vin_log 
ADD COLUMN IF NOT EXISTS dealership VARCHAR(255);

ALTER TABLE dealership_vin_log 
ADD COLUMN IF NOT EXISTS order_date DATE;

# Remove unique constraint if exists
ALTER TABLE dealership_vin_log 
DROP CONSTRAINT IF EXISTS unique_vin;
```

### **Step 4: Import Process**

#### **CRITICAL: Handle Duplicates Properly**
```python
# WRONG - Loses duplicate VINs:
INSERT INTO table (vin, order_number...) 
VALUES (...) 
ON CONFLICT (vin) DO NOTHING  # DON'T DO THIS!

# CORRECT - Keeps all records including duplicates:
INSERT INTO table (vin, order_number, order_date, dealership...) 
VALUES 
    ('VIN1', '40410', '2024-08-09', 'Dealership Name'),
    ('VIN1', '40503', '2024-08-10', 'Dealership Name'),  # Same VIN, different order!
    ('VIN2', '40410', '2024-08-09', 'Dealership Name')
# No ON CONFLICT clause - let duplicates insert!
```

### **Step 5: Order Number Propagation**
When CSV has order numbers only on first VIN of group:
```python
current_order_number = None

for row in csv_rows:
    order_num = row[0].strip()
    vin = row[1].strip()
    
    # Update order number if present
    if order_num:
        current_order_number = order_num
    
    # Use propagated order number for this VIN
    if current_order_number and vin:
        insert_record(vin, current_order_number, ...)
```

---

## 📝 COMPLETE IMPORT SCRIPT TEMPLATE

```python
import csv
from datetime import datetime
import sys

sys.path.append(r'C:\...\scripts')
from database_connection import DatabaseManager

def import_dealership_vinlog(dealership_name, csv_path, default_order_date='2024-08-09'):
    """
    Import VIN log for a dealership, preserving ALL records including duplicates
    """
    db = DatabaseManager()
    
    # Find correct table name
    table_result = db.execute_query(f"""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%{dealership_name.lower().replace(' ', '_')}%vin_log%'
    """)
    
    if not table_result:
        print(f"ERROR: No VIN log table found for {dealership_name}")
        return
    
    table_name = table_result[0]['table_name']
    print(f"Using table: {table_name}")
    
    # Read CSV and process
    processed_data = []
    current_order_number = None
    
    with open(csv_path, 'r', encoding='utf-8-sig') as file:
        csv_reader = csv.reader(file)
        headers = next(csv_reader)
        
        for row in csv_reader:
            if len(row) < 2:
                continue
            
            # Handle order number propagation
            order_num = row[0].strip() if row[0] else ''
            vin = row[1].strip() if row[1] else ''
            
            if not vin:
                continue
            
            if order_num:
                current_order_number = order_num
            
            if current_order_number and vin:
                processed_data.append({
                    'vin': vin,
                    'dealership': dealership_name,
                    'order_number': current_order_number,
                    'order_date': default_order_date
                })
    
    print(f"Processing {len(processed_data)} VIN records")
    
    # CRITICAL: Insert ALL records, don't skip duplicates!
    for record in processed_data:
        try:
            db.execute_query(f"""
                INSERT INTO {table_name} 
                (vin, dealership, order_number, order_date, created_at)
                VALUES 
                ('{record['vin']}', '{record['dealership']}', 
                 '{record['order_number']}', '{record['order_date']}', NOW())
            """)
        except Exception as e:
            # Log error but continue - don't stop on individual failures
            print(f"Error inserting {record['vin']}: {e}")
    
    # Verify import
    total = db.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
    print(f"Total records in {table_name}: {total[0]['count']}")
    
    # Show duplicate VINs (this is EXPECTED and CORRECT!)
    duplicates = db.execute_query(f"""
        SELECT vin, COUNT(*) as order_count 
        FROM {table_name}
        GROUP BY vin 
        HAVING COUNT(*) > 1
        ORDER BY order_count DESC
        LIMIT 5
    """)
    
    if duplicates:
        print("\nVINs with multiple orders (this is correct!):")
        for dup in duplicates:
            print(f"  {dup['vin']}: {dup['order_count']} orders")
```

---

## ⚠️ COMMON MISTAKES TO AVOID

### **1. Using ON CONFLICT DO NOTHING**
- **Problem:** Loses duplicate VIN records
- **Solution:** Don't use ON CONFLICT for VIN logs

### **2. Unique Constraint on VIN**
- **Problem:** Prevents legitimate duplicate orders
- **Solution:** Remove unique constraints from VIN column

### **3. Not Propagating Order Numbers**
- **Problem:** VINs without order numbers
- **Solution:** Track and propagate current_order_number

### **4. Wrong Table Naming**
- **Problem:** Creates multiple tables for same dealership
- **Solution:** Always use `dealership_name_vin_log` format

### **5. Clearing Entire Table**
- **Problem:** Loses historical data
- **Solution:** Only clear if explicitly requested

---

## 🔍 VERIFICATION CHECKLIST

After import, verify:

1. **Total record count matches CSV rows**
   ```sql
   SELECT COUNT(*) FROM dealership_vin_log;
   -- Should equal total rows in CSV (including duplicates)
   ```

2. **All order numbers present**
   ```sql
   SELECT DISTINCT order_number FROM dealership_vin_log ORDER BY order_number;
   ```

3. **Duplicate VINs preserved**
   ```sql
   SELECT vin, COUNT(*) as count 
   FROM dealership_vin_log 
   GROUP BY vin 
   HAVING COUNT(*) > 1;
   -- Should show VINs with multiple orders
   ```

4. **Dealership name consistent**
   ```sql
   SELECT DISTINCT dealership FROM dealership_vin_log;
   -- Should show only one dealership name
   ```

---

## 📋 QUICK REFERENCE

### **Import Command**
```bash
python import_vinlog.py --dealership "Pappas Toyota" --csv "path/to/vinlog.csv" --date "2024-08-09"
```

### **Table Naming**
- `pappas_toyota_vin_log` ✅
- `bmw_west_stl_vin_log` ✅
- `vin_log_pappas_toyota` ❌ (wrong format)
- `PappasToyotaVinLog` ❌ (wrong format)

### **Required Fields**
- `vin` - Vehicle Identification Number
- `dealership` - Consistent dealership name
- `order_number` - Graphics order number
- `order_date` - Date of order (use default if not in CSV)

---

## 🚀 NEXT STEPS

1. **Audit all existing VIN log tables** for proper structure
2. **Remove unique constraints** on VIN columns
3. **Standardize table naming** across all dealerships
4. **Create automated import script** using this template
5. **Document dealership-specific requirements** as discovered

---

**Remember:** VIN logs track EVERY graphics order. A vehicle appearing multiple times means multiple graphics orders were placed - this is correct and expected behavior!