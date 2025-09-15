# CLAUDE.md - Silver Fox Marketing Assistant Configuration

## Silver Fox Order Processing System - Near Production Ready (90% Complete)

### **System Overview**
Order processing system for automotive dealership graphics generation nearing production readiness. Processes CAO (Comparative Analysis Orders) and LIST orders with QR code generation for 36 dealerships. System is 90% complete with remaining optimization work on CAO order processing for several dealerships and output format tweaks.

### **Core Database Schema**

#### **Raw Data Tables**
- `raw_vehicle_data` - Current inventory from active scraper imports
- `scraper_imports` - Import tracking with status (active/archived)  

#### **Processed Data**
- `normalized_vehicle_data` - Standardized vehicle data for CAO processing
- `dealership_configs` - Filtering rules per dealership

#### **VIN Log Tables** (Order History)
- `[dealership_name]_vin_log` - Individual VIN processing history per dealership
- Purpose: Track which VINs have been processed to prevent duplicates

### **CAO Processing Logic**
```sql
-- Core CAO query: Find vehicles needing graphics
SELECT * FROM normalized_vehicle_data nvd
JOIN scraper_imports si ON nvd.import_id = si.import_id  
WHERE nvd.location = 'Dealership Name'
  AND si.status = 'active'
  AND nvd.vehicle_condition IN (dealership_vehicle_types)
  AND nvd.vin NOT IN (SELECT vin FROM dealership_vin_log)
```

### **Critical System Rules**

#### **ACTIVE DATASET RULE**
- CAO processing ONLY uses scraper datasets marked `status = 'active'`
- NEVER use import dates/timestamps to determine dataset currency
- Only one import can be active at a time

#### **VIN LOG PURPOSE**
- VIN logs contain ORDER HISTORY of processed VINs
- NOT current inventory - that's in raw_vehicle_data
- Purpose: Prevent reprocessing same vehicles

#### **VEHICLE TYPE FILTERING**
- `vehicle_types: ['used']` = Include all used types: 'used', 'po', 'cpo', 'certified', 'pre-owned'
- `vehicle_types: ['new']` = Include only 'new' vehicles
- `vehicle_types: ['new', 'used']` = Include all vehicle types

#### **NAME MAPPING CONSISTENCY**  
- Dealership config name MUST match raw_vehicle_data location exactly
- VIN log table name: `dealership_name.lower().replace(' ', '_').replace("'", '') + '_vin_log'`

### **Windows Compatibility**
- **NO UNICODE CHARACTERS** in Python console output (emojis, arrows, etc.)
- Use ASCII alternatives: `[OK]`, `[ERROR]`, `>>>`, `---`
- Windows CP1252 encoding throws UnicodeEncodeError on Unicode

### **Current Development Status (90% Complete)**
- **36 dealerships** with individual VIN log tables
- **Complete UI/UX** with dark mode and responsive design
- **QR code generation** at 388x388 PNG for Adobe integration
- **Real-time processing** with Socket.IO progress updates

#### **Remaining Tasks for Production:**
- Optimize CAO order processing for several dealerships
- Final tweaks to output format specifications

### **File Locations**
- **Main Application**: `projects/minisforum_database_transfer/bulletproof_package/web_gui/app.py`
- **CAO Processing**: `projects/minisforum_database_transfer/bulletproof_package/scripts/correct_order_processing.py`
- **Database Connection**: `projects/minisforum_database_transfer/bulletproof_package/scripts/database_connection.py`
- **Orders Output**: `projects/minisforum_database_transfer/bulletproof_package/orders/`

### **Testing & Debugging**
- **Expected Results**: CAO should return small numbers (6-20 vehicles) for most dealerships
- **Data Issues**: Check active import status, name mapping, vehicle type filters
- **VIN Log Verification**: Confirm previously processed VINs are excluded

### **Development History**
See `SILVER_FOX_ORDER_SYSTEM_DEVELOPMENT_HISTORY.md` for detailed technical evolution, debugging solutions, and architectural decisions.

---

## Business Context

### **Silver Fox Marketing**
- **Primary**: Automotive dealership graphics and marketing
- **Technology Stack**: Python, Flask, PostgreSQL, JavaScript
- **Client Base**: 36+ automotive dealerships in Missouri/Illinois region

### **Assistant Capabilities**
- Full-stack development (Python, JavaScript, SQL)
- System debugging and optimization
- Database design and data integrity
- Process automation and workflow optimization

### **Security & Isolation**
- Containerized Claude Code environment
- No access to NAS or sensitive systems
- Local development with secure external integrations