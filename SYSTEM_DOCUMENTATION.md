# Silver Fox Marketing - System Documentation
**Dealership Management System v2.3**  
*Comprehensive Technical Documentation*

## 📚 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Web Interface Guide](#web-interface-guide)
4. [API Reference](#api-reference)
5. [Database Schema](#database-schema)
6. [Queue Management](#queue-management)
7. [Data Search Engine](#data-search-engine)
8. [Testing Framework](#testing-framework)
9. [Deployment Guide](#deployment-guide)
10. [Troubleshooting](#troubleshooting)

---

## 🌐 System Overview

The Silver Fox Dealership Management System is a comprehensive web-based platform designed to:

- **Automate vehicle data collection** from 40+ dealership websites with live API scraping
- **Manage daily order processing** through a queue-based workflow
- **Generate QR codes** for vehicle inventory management
- **Export data** in multiple formats for Adobe integration
- **Provide real-time monitoring** with live scraper console and WebSocket updates
- **Import working scrapers** directly from scraper 18 system

### Current Version: 2.3 - Real Scraper Integration & Progress Monitoring

**🎉 Latest Achievements (July 29, 2025):**
- ✅ **Dave Sinclair Lincoln South** scraper imported and operational (375+ live vehicles)
- ✅ **Real-time Scraper Console** with live progress updates via Socket.IO
- ✅ **Interactive Dealership Selection** dropdown with 50 dealerships
- ✅ **JavaScript Error Resolution** for robust DOM element handling
- ✅ **Progress Bar Integration** with visual completion tracking
- ✅ **Database Registration** for automated scraper configuration
- **v2.1**: Unified data search, integrated system console
- **v2.0**: Queue management system, order processing wizard
- **v1.0**: Initial scraper integration, database foundation

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Interface (Flask)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ Scraper  │ │  Order   │ │   Data   │ │    System    │   │
│  │ Control  │ │  Queue   │ │  Search  │ │    Status    │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
                               │
                         Flask Routes
                               │
┌─────────────────────────────────────────────────────────────┐
│                  Business Logic Layer                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────┐  │
│  │ Queue Manager   │  │ Order Processor │  │  Scraper   │  │
│  │                 │  │                 │  │ Integration│  │
│  └─────────────────┘  └─────────────────┘  └────────────┘  │
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────────┐   │
│  │ PostgreSQL  │  │ File System │  │  External APIs   │   │
│  │  Database   │  │   Storage   │  │  (Dealerships)   │   │
│  └─────────────┘  └─────────────┘  └───────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Backend**: Python 3.8+, Flask, Flask-SocketIO
- **Database**: PostgreSQL 16
- **Real-time**: WebSocket (Socket.IO)
- **External**: Dealership APIs, QR Code Libraries

---

## 🖥️ Web Interface Guide

### Dashboard Layout (v2.1)

#### **1. Scraper Control**
Enhanced dealership scraping interface with:
- **Select Dealerships**: Multi-select interface for specific scraping
- **Schedule**: Configure automated daily scraping
- **Start Scrape (All)**: Process all dealerships at once
- **Real-time Progress**: Live updates via WebSocket

#### **2. Order Queue**
Visual queue management system:
- **Left Panel**: 
  - Day buttons (Monday-Sunday)
  - Individual dealership list
  - Click to add to queue
- **Right Panel**:
  - Processing queue display
  - CAO/List radio buttons per dealership
  - Delete functionality
  - Process Queue button

#### **3. Data (NEW in v2.1)**
Unified vehicle search engine:
- **Search Bar**: Full-text vehicle search
- **Filter Options**:
  - Show by: Date/Dealer dropdown
  - Data type: Raw/Normalized/Both radios
- **Results Table**:
  - Sortable columns
  - Filterable fields
  - Export capabilities

#### **4. System Status (Enhanced in v2.1)**
Integrated monitoring interface:
- **System Metrics**:
  - Active scrapers count
  - Database health status
  - Order processing readiness
  - Total vehicle inventory
- **Integrated Console**:
  - Landscape orientation
  - Real-time system logs
  - Error tracking
  - Performance metrics

#### **5. System Tests**
Comprehensive testing interface:
- Run stress tests
- View test results
- Performance benchmarks
- System diagnostics

---

## 🔌 API Reference

### Core Endpoints

#### Queue Management
```http
GET    /api/queue/today                 # Get today's queue
POST   /api/queue/populate-today        # Populate from schedule
POST   /api/queue/process/{id}          # Process specific order
DELETE /api/queue/remove/{id}           # Remove from queue
GET    /api/queue/summary-today         # Queue statistics
```

#### Data Search (NEW in v2.1)
```http
GET    /api/data/search                 # Search vehicles
       ?query=<search_term>
       &filter_by=date|dealer
       &data_type=raw|normalized|both
       &sort_by=<field>
       &order=asc|desc
       &limit=<number>
       &offset=<number>

GET    /api/data/dealers                # Get dealer list
GET    /api/data/date-range             # Get available dates
POST   /api/data/export                 # Export search results
```

#### Scraper Control
```http
GET    /api/dealerships                 # List all dealerships
POST   /api/scraper/start               # Start scraping
GET    /api/scraper/status              # Get scraper status
POST   /api/scraper/stop                # Stop scraping
```

#### System Monitoring
```http
GET    /api/system/status               # System health
GET    /api/system/logs                 # Recent logs
GET    /api/system/metrics              # Performance metrics
WS     /socket.io                       # Real-time updates
```

---

## 💾 Database Schema

### Primary Tables

#### `raw_vehicle_data`
```sql
CREATE TABLE raw_vehicle_data (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) UNIQUE NOT NULL,
    stock_number VARCHAR(50),
    dealer_name VARCHAR(255),
    location VARCHAR(255),
    year INTEGER,
    make VARCHAR(50),
    model VARCHAR(100),
    trim VARCHAR(100),
    body_style VARCHAR(50),
    exterior_color VARCHAR(50),
    interior_color VARCHAR(50),
    engine VARCHAR(100),
    transmission VARCHAR(50),
    drivetrain VARCHAR(20),
    mileage INTEGER,
    price DECIMAL(10,2),
    vehicle_type VARCHAR(20),
    condition VARCHAR(20),
    description TEXT,
    features TEXT,
    images JSONB,
    dealer_website VARCHAR(255),
    vehicle_url VARCHAR(500),
    last_seen_date TIMESTAMP,
    import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50),
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `order_queue`
```sql
CREATE TABLE order_queue (
    queue_id SERIAL PRIMARY KEY,
    dealership_name VARCHAR(255) NOT NULL,
    order_type VARCHAR(50) NOT NULL,
    template_type VARCHAR(50) NOT NULL,
    vehicle_types TEXT[],
    scheduled_date DATE NOT NULL,
    day_of_week VARCHAR(20) NOT NULL,
    priority INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'pending',
    assigned_to VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    processed_by VARCHAR(100),
    result JSONB,
    error_message TEXT
);
```

#### `template_configurations`
```sql
CREATE TABLE template_configurations (
    template_id SERIAL PRIMARY KEY,
    template_name VARCHAR(100) UNIQUE NOT NULL,
    template_type VARCHAR(50) NOT NULL,
    field_mappings JSONB NOT NULL,
    formatting_rules JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes for Performance
```sql
-- Vehicle search optimization
CREATE INDEX idx_vehicle_search ON raw_vehicle_data 
USING gin(to_tsvector('english', 
    COALESCE(make,'') || ' ' || 
    COALESCE(model,'') || ' ' || 
    COALESCE(year::text,'')
));

-- Date-based queries
CREATE INDEX idx_vehicle_dates ON raw_vehicle_data(import_timestamp, last_seen_date);

-- Dealer queries
CREATE INDEX idx_vehicle_dealer ON raw_vehicle_data(dealer_name, location);
```

---

## 📋 Queue Management

### Workflow Process

```
1. Build Queue          2. Process Queue         3. Review Output
┌─────────────┐        ┌─────────────────┐      ┌─────────────┐
│ Select Days │   ───> │ Launch Wizard   │ ───> │ Inspect CSV │
│ Add Dealers │        │ CAO: Automatic  │      │ Check QR    │
│ Set Types   │        │ List: VIN Entry │      │ Adobe Ready │
└─────────────┘        └─────────────────┘      └─────────────┘
```

### Queue States
- **pending**: Awaiting processing
- **in_progress**: Currently being processed
- **completed**: Successfully processed
- **failed**: Processing error occurred

### Default Schedule
```javascript
weeklySchedule = {
    monday: ['Columbia Honda', 'BMW of West St. Louis'],
    tuesday: ['Dave Sinclair Lincoln South', 'Suntrup Ford West'],
    wednesday: ['Joe Machens Toyota', 'Thoroughbred Ford'],
    thursday: ['Suntrup Ford Kirkwood', 'Joe Machens Hyundai'],
    friday: ['Columbia Honda', 'BMW of West St. Louis', 'Dave Sinclair Lincoln South'],
    saturday: [],
    sunday: []
}
```

---

## 🔍 Data Search Engine (NEW in v2.1)

### Search Capabilities

#### Full-Text Search
- VIN numbers
- Make/Model combinations
- Stock numbers
- Dealer names

#### Filter Options
- **By Date**: Date range selection
- **By Dealer**: Single or multiple dealers
- **Data Type**: Raw, Normalized, or Both

#### Sort Options
- Price (ascending/descending)
- Year (newest/oldest)
- Mileage (lowest/highest)
- Date Added (recent/oldest)

### Implementation Details

```javascript
// Search request example
const searchParams = {
    query: "2023 Honda Accord",
    filter_by: "dealer",
    dealer_names: ["Columbia Honda", "Joe Machens Honda"],
    data_type: "both",
    sort_by: "price",
    order: "asc",
    limit: 50,
    offset: 0
};

// API call
const results = await fetch('/api/data/search?' + new URLSearchParams(searchParams));
```

---

## 🧪 Testing Framework

### Comprehensive Stress Test

```bash
python scripts/comprehensive_stress_test.py
```

**Test Coverage:**
1. **Queue Management**
   - Population accuracy
   - Retrieval performance
   - Status tracking

2. **Order Processing**
   - CAO automation
   - List processing
   - Template generation

3. **QR Code Generation**
   - File creation
   - Quality validation
   - Batch performance

4. **Data Search**
   - Query performance
   - Filter accuracy
   - Sort functionality

5. **System Performance**
   - Database load testing
   - Concurrent operations
   - Memory usage

### Test Results
- **Green (0 errors)**: Production ready
- **Yellow (1-2 errors)**: Minor fixes needed
- **Red (3+ errors)**: Major issues

---

## 🚀 Deployment Guide

### Prerequisites
1. **System Requirements**
   - Windows 10/11 or Linux
   - Python 3.8+
   - PostgreSQL 16
   - 8GB RAM minimum
   - 20GB disk space

2. **Software Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Production Setup

1. **Database Configuration**
   ```python
   # database_config.py
   PRODUCTION_CONFIG = {
       'host': 'production-server',
       'database': 'silverfox_prod',
       'user': 'prod_user',
       'password': os.environ.get('DB_PASSWORD'),
       'pool_size': 20,
       'max_overflow': 40
   }
   ```

2. **Web Server Configuration**
   ```python
   # production_config.py
   class ProductionConfig:
       HOST = '0.0.0.0'
       PORT = 5000
       DEBUG = False
       THREADED = True
       SSL_CERT = 'path/to/cert.pem'
       SSL_KEY = 'path/to/key.pem'
   ```

3. **Process Management**
   ```bash
   # Using supervisord
   [program:silverfox_web]
   command=python /path/to/web_gui/app.py
   autostart=true
   autorestart=true
   stderr_logfile=/var/log/silverfox/error.log
   stdout_logfile=/var/log/silverfox/access.log
   ```

### Security Considerations
- Use HTTPS in production
- Implement authentication
- Regular database backups
- Log rotation
- Rate limiting

---

## 🛠️ Troubleshooting

### Common Issues

#### **Web Interface Not Loading**
```bash
# Check Flask is running
ps aux | grep python | grep app.py

# Check port availability
netstat -an | grep 5000

# Review logs
tail -f web_gui.log
```

#### **Database Connection Errors**
```sql
-- Check PostgreSQL status
SELECT version();
SELECT current_database();

-- Test connection pool
SELECT count(*) FROM pg_stat_activity;
```

#### **Scraper Failures**
```python
# Test individual scraper
from real_scraper_integration import RealScraperIntegration
scraper = RealScraperIntegration()
result = scraper.test_scraper("Columbia Honda")
```

#### **Queue Processing Issues**
```sql
-- Check queue status
SELECT status, COUNT(*) 
FROM order_queue 
WHERE scheduled_date = CURRENT_DATE 
GROUP BY status;

-- Reset stuck orders
UPDATE order_queue 
SET status = 'pending' 
WHERE status = 'in_progress' 
AND started_at < NOW() - INTERVAL '1 hour';
```

### Performance Optimization

1. **Database Tuning**
   ```sql
   -- Update statistics
   VACUUM ANALYZE;
   
   -- Monitor slow queries
   SELECT query, calls, mean_exec_time
   FROM pg_stat_statements
   ORDER BY mean_exec_time DESC
   LIMIT 10;
   ```

2. **Application Caching**
   ```python
   # Implement Redis caching
   from redis import Redis
   cache = Redis(host='localhost', port=6379)
   ```

3. **Resource Monitoring**
   ```bash
   # CPU and Memory
   htop
   
   # Disk I/O
   iotop
   
   # Network
   iftop
   ```

---

## 📈 Future Enhancements

### Planned Features (v2.2)
- [ ] Advanced analytics dashboard
- [ ] Mobile responsive design
- [ ] API rate limiting
- [ ] Automated backup system
- [ ] Multi-user authentication
- [ ] Export scheduling
- [ ] Email notifications
- [ ] Advanced reporting

### Integration Roadmap
- [ ] Salesforce CRM integration
- [ ] Google Analytics tracking
- [ ] SMS notifications
- [ ] Cloud storage backup
- [ ] Third-party API access

---

## 📝 Changelog

### v2.1 (July 29, 2025)
- Added unified Data search tab
- Integrated system console into Status tab
- Enhanced UI/UX with landscape console
- Improved navigation flow

### v2.0 (July 29, 2025)
- Implemented queue management system
- Created order processing wizard
- Enhanced scraper control
- Added comprehensive testing

### v1.0 (June 2025)
- Initial system release
- Basic scraper integration
- Database foundation
- Web interface framework

---

**Silver Fox Marketing - Dealership Management System**  
*Building the future of automotive inventory management*