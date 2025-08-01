# Silver Fox Order Processing System v2.0 
**Integrated Scraper 18 System with Enhanced Error Handling**  
Updated: 2025-08-01

## 🚀 Quick Start

### **Web Interface (Primary Method)**
1. **Start the system**
   ```cmd
   cd web_gui
   python app.py
   ```

2. **Access dashboard**
   - Open browser: http://127.0.0.1:5000
   - **Order Queue** tab - Build and process daily orders
   - **Data** tab - Search all vehicle inventory
   - **System Status** tab - Monitor system with integrated console

### **CLI Backup System (New!)**
1. **Interactive order processing**  
   ```cmd
   python order_processing_cli.py --interactive
   ```

2. **Check system status**
   ```cmd
   python order_processing_cli.py --status
   ```

3. **Process CAO order**
   ```cmd
   python order_processing_cli.py --cao "Columbia Honda" --template shortcut_pack
   ```

4. **Process LIST order**
   ```cmd
   python order_processing_cli.py --list "BMW of West St. Louis" --vins "VIN1,VIN2,VIN3"
   ```

## 🎯 Major Version Updates

### **v2.0 (August 1, 2025) - Integrated Scraper 18 System**
- 🚀 **Complete Scraper 18 Integration**: All 36 proven scrapers directly integrated into web GUI
- 🛡️ **Enhanced Error Handling**: Individual scraper failures no longer crash entire system
- 🔄 **Direct Database Import**: Scraped data automatically imported into PostgreSQL
- ⚡ **Real-time Progress**: Live Socket.IO updates during scraper execution
- 🎯 **36 Active Scrapers**: Optimized dealership list covering primary markets
- 🔗 **Web GUI Selection**: Replaced config.csv with web interface dealership selection
- ✅ **Production Ready**: Fully operational scraper system with proven logic preserved

### **v2.2 (July 29, 2025) - Dynamic Column Filtering**
- 🎛️ **Dynamic Header Filters**: Column-based dropdowns with real-time options
- 📅 **Date Scraped Column**: Track when each vehicle was scraped
- 🔄 **Cascading Filters**: Filters update based on current search results
- 📊 **Massive Dataset**: 65,164+ vehicles from historical scraper sessions
- ⚡ **Performance Optimized**: Fast filtering across large datasets
- 🎨 **Visual Indicators**: Active filter highlighting with vehicle counts

### **v2.1 (July 29, 2025) - Data Search & Console Integration**
- 🔍 **Unified Data Search Tab**: Powerful vehicle inventory search engine
- 📊 **Integrated System Console**: Landscape console within System Status tab
- 🎨 **Enhanced UI/UX**: Streamlined interface with better space utilization
- 🔧 **Improved Navigation**: Logical tab ordering and functionality grouping

### **v2.0 (July 29, 2025) - Queue Management System**
- 📋 **Queue Management**: Visual queue building with day scheduling
- 🧙‍♂️ **Order Processing Wizard**: Guided workflow for CAO and List orders
- 🕷️ **Enhanced Scraper Control**: Multi-select dealership operations
- ✅ **Comprehensive Testing**: Full stress testing framework

## 🎯 Current System Status

### **✅ FULLY OPERATIONAL COMPONENTS**
- **🧠 Enhanced VIN Logic**: 5-rule intelligent processing with 28,289+ VIN database
- **🎛️ Order Processing Wizard v2.0**: Complete web interface with manual data editor
- **🔗 Live Scraper Integration**: 4 active dealerships with real-time inventory
- **🛡️ CLI Backup System**: Full command line fallback interface
- **📊 VIN History Intelligence**: Cross-dealership and status change detection
- **🎯 QR Code Generation**: 388x388 PNG format with custom URLs
- **📋 Adobe CSV Export**: Variable data library compatible format
- **⚡ Smart Filtering**: Prevents duplicate processing while capturing opportunities

### **🔗 ACTIVE SCRAPER INTEGRATIONS (36 Dealerships)**

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
- Glendale Chrysler Jeep
- South County Autos

**Lincoln Network:**
- Dave Sinclair Lincoln
- Dave Sinclair Lincoln South
- Dave Sinclair Lincoln St. Peters

**Toyota/Lexus Network:**
- Pappas Toyota

**Nissan Network:**
- Joe Machens Nissan

**CDJR Network:**
- Joe Machens CDJR

**Specialty Imports:**
- Land Rover Ranch Mirage
- Mini of St. Louis
- West County Volvo Cars

**Multi-Brand:**
- Joe Machens Hyundai
- Joe Machens Toyota

## 📋 What's Included

### Core Components
- **Web Dashboard** - Main interface at http://127.0.0.1:5000
- **Real-time Scraper Console** - Live progress monitoring with Socket.IO
- **Order Processing Wizard** - Guided workflow at /order-wizard
- **Database System** - PostgreSQL with optimized schema
- **Live Scraper Integration** - Direct import from scraper 18 system
- **Queue Management** - Daily workflow automation
- **QR Code Generator** - Bulk QR generation system
- **Template Engine** - Flyout, Shortcut, Shortcut Pack templates

### Python Scripts
- `comprehensive_stress_test.py` - Full system validation
- `order_queue_manager.py` - Queue management system
- `order_processing_workflow.py` - Order processing engine
- `csv_importer_complete.py` - CSV import with filtering
- `data_exporter.py` - Data export functionality
- `qr_code_generator.py` - QR code generation
- `database_connection.py` - Database management
- `real_scraper_integration.py` - Live scraper system

### Key Features
- ✅ **Data Search Engine** - Full-text search with filtering
- ✅ **Queue-Based Workflow** - Daily order management
- ✅ **Wizard Processing** - Guided order completion
- ✅ **Real-Time Monitoring** - Integrated system console
- ✅ **36 Dealership Support** - Production-ready scrapers with enhanced error handling
- ✅ **Template System** - Multiple export formats
- ✅ **QR Integration** - Automatic QR generation
- ✅ **Comprehensive Testing** - Stress test framework

## 🏗️ Database Structure

### Core Tables
1. **raw_vehicle_data** - Audit trail of all scraped data
2. **normalized_vehicle_data** - Processed, clean vehicle data
3. **vin_history** - VIN tracking across dealerships
4. **dealership_configs** - Business rules and filtering

### Order Processing Tables *(NEW)*
5. **order_processing_jobs** - Job tracking and status management
6. **qr_file_tracking** - QR code file validation and paths
7. **export_history** - Export audit trail and file management
8. **order_processing_config** - Job type configurations and templates

### Dealership Configurations
Each dealership has configurable:
- **Filtering Rules**: Exclude conditions, price ranges, year limits
- **Output Rules**: Sort order, format preferences, QR inclusion
- **QR Output Paths**: Custom directory structure

## 🔧 Configuration Examples

### Filtering Rules JSON
```json
{
    "exclude_conditions": ["offlot"],
    "require_stock": true,
    "min_price": 0,
    "year_min": 2020,
    "exclude_makes": ["Oldsmobile"],
    "include_only_makes": ["BMW", "Mercedes"]
}
```

### Output Rules JSON
```json
{
    "include_qr": true,
    "format": "premium",
    "sort_by": ["model", "year"],
    "fields": ["vin", "stock", "year", "make", "model", "price"]
}
```

## 🚨 Troubleshooting

### Common Issues
1. **PostgreSQL Connection Failed**
   - Verify PostgreSQL 16 is running
   - Check password is correct
   - Ensure port 5432 is available

2. **CSV Import Errors**
   - Verify CSV has required columns: vin, stock_number, dealer_name
   - Check file encoding (should be UTF-8)
   - Ensure dealership names match config exactly

3. **Performance Issues**
   - Run VACUUM ANALYZE after large imports
   - Check disk space (>2GB recommended)
   - Verify indexes are created

### Support
For technical support, contact Silver Fox Marketing development team.

## 📊 System Requirements
- Windows 10/11
- PostgreSQL 16
- Python 3.8+
- 4GB RAM minimum
- 10GB disk space recommended

## 🔒 Security Notes
- Database password should be strong (12+ characters)
- Regular backups recommended
- QR code directories should have proper permissions

---
**Silver Fox Marketing - Automotive Database System**
*Generated by Claude Assistant - 2025*
