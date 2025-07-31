# Silver Fox Order Processing System v2.0

A comprehensive automotive dealership graphics order processing system with enhanced VIN intelligence, real-time scraper integration, and advanced duplicate prevention logic.

## 🚀 Features

### Core Capabilities
- **Enhanced VIN Logic**: 5-rule intelligent processing system with cross-dealership detection
- **Order Processing Wizard v2.0**: Web interface with manual data editor and QR verification
- **VIN History Database**: Track vehicle processing across multiple dealerships
- **Real Scraper Integration**: Live inventory data from dealership websites
- **CLI Backup System**: Complete command-line fallback interface
- **QR Code Generation**: 388x388 PNG format with custom URLs
- **Adobe CSV Export**: Variable data library compatible format

### Business Intelligence
- **Cross-Dealership Detection**: Captures revenue when vehicles move between dealers
- **Status Change Processing**: Handles NEW → USED → CERTIFIED transitions
- **Smart Duplicate Prevention**: Avoids reprocessing while capturing opportunities
- **Time-based Filtering**: Intelligent 1-day and 7-day processing windows

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 16
- 4GB RAM minimum
- 10GB disk space recommended

## 🔧 Installation

1. Clone the repository:
```bash
git clone [your-repo-url]
cd silver-fox-order-processing
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up PostgreSQL database:
```bash
# Create database
createdb silverfox_db

# Run SQL scripts in order
psql -d silverfox_db -f sql/01_create_database.sql
psql -d silverfox_db -f sql/02_create_tables.sql
psql -d silverfox_db -f sql/03_initial_dealership_configs.sql
psql -d silverfox_db -f sql/04_performance_settings.sql
psql -d silverfox_db -f sql/05_add_constraints.sql
psql -d silverfox_db -f sql/06_order_processing_tables.sql
```

4. Configure database connection:
```bash
# Copy sample config
cp config/database_config.sample.json config/database_config.json

# Edit with your database credentials
# Default: localhost:5432, user: postgres
```

## 💻 Usage

### Web Interface (Primary)
```bash
cd web_gui
python app.py
# Access at http://127.0.0.1:5000
```

### CLI Backup System
```bash
# Interactive mode
python order_processing_cli.py --interactive

# Check system status
python order_processing_cli.py --status

# Process CAO order
python order_processing_cli.py --cao "Columbia Honda" --template shortcut_pack

# Process LIST order
python order_processing_cli.py --list "BMW of West St. Louis" --vins "VIN1,VIN2,VIN3"
```

## 📊 Enhanced VIN Logic Rules

1. **Same dealership + any type ≤ 1 day**: SKIP (recent processing)
2. **Same dealership + same type ≤ 7 days**: SKIP (duplicate prevention)
3. **Different dealership**: PROCESS (cross-dealership opportunity)
4. **Same dealership + different type**: PROCESS (status change)
5. **No history**: PROCESS (genuinely new vehicle)

## 🗂️ Project Structure

```
├── web_gui/                # Web interface
│   ├── app.py             # Flask application
│   ├── static/            # Frontend assets
│   └── templates/         # HTML templates
├── scripts/               # Core processing logic
│   ├── correct_order_processing.py
│   ├── database_connection.py
│   └── real_scraper_integration.py
├── sql/                   # Database setup scripts
├── docs/                  # Documentation
└── order_processing_cli.py # CLI backup system
```

## 📈 Performance Benchmarks

- **VIN Lookup Speed**: <5ms per VIN
- **Enhanced Logic Processing**: <100ms overhead
- **QR Code Generation**: ~50ms per code
- **CSV File Creation**: <100ms for 100 vehicles
- **Concurrent Users**: 5+ simultaneous operators

## 🔐 Security Notes

- Configure strong database passwords
- Keep `database_config.json` secure
- Regular database backups recommended
- No PII stored - vehicle data only

## 📝 License

Proprietary - Silver Fox Marketing

## 🤝 Contributing

This is a private repository. For access or contributions, contact Silver Fox Marketing development team.

## 📞 Support

For technical support, contact the Silver Fox Marketing development team.

---

**Silver Fox Marketing - Automotive Order Processing System**  
*Powered by Enhanced VIN Intelligence*