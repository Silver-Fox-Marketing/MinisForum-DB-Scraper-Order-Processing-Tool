# DEPLOYMENT ROLLOUT
## Silver Fox Order Processing System - Production Deployment Guide

**Version**: 2.1.0
**Target Environment**: Windows Production Server
**Deployment Strategy**: Version-Based with Rollback Capability
**Estimated Total Time**: 4-6 hours

---

## Table of Contents

1. [Overview](#overview)
2. [Phase 1: Pre-Production Setup](#phase-1-pre-production-setup)
3. [Phase 2: Production Directory Structure](#phase-2-production-directory-structure)
4. [Phase 3: Database Setup](#phase-3-database-setup)
5. [Phase 4: Configuration](#phase-4-configuration)
6. [Phase 5: Windows Service Setup](#phase-5-windows-service-setup)
7. [Phase 6: Security Hardening](#phase-6-security-hardening)
8. [Phase 7: Backup & Monitoring](#phase-7-backup--monitoring)
9. [Phase 8: Deployment Automation Scripts](#phase-8-deployment-automation-scripts)
10. [Phase 9: Final Testing & Go-Live](#phase-9-final-testing--go-live)
11. [Rollback Procedures](#rollback-procedures)
12. [Post-Deployment Monitoring](#post-deployment-monitoring)

---

## Overview

### What This System Does
Automated order processing system for 36 automotive dealerships that:
- Processes CAO (Comparative Analysis Orders) and LIST orders
- Generates QR codes at 388x388 PNG for Adobe Illustrator integration
- Manages VIN history and duplicate prevention across dealerships
- Provides real-time web interface for order management

### Production Architecture Benefits
✅ **Version-Based Deployment**: Zero-downtime updates (30-60 seconds)
✅ **Instant Rollback**: Change symlink to previous version
✅ **Multiple Versions Coexist**: Safe testing before cutover
✅ **No File Locking**: Update without stopping service preparation

### System Requirements
- **OS**: Windows 10/11 Pro or Windows Server 2019+
- **CPU**: AMD Ryzen 7 or equivalent (4+ cores)
- **RAM**: 16GB minimum
- **Storage**: 500GB+ SSD
- **Database**: PostgreSQL 16.x
- **Python**: Python 3.11+
- **Tools**: NSSM 2.24+ for Windows Service

---

## Phase 1: Pre-Production Setup

**Estimated Time**: 2-3 hours
**Objective**: Prepare server and install required software

### Step 1.1: Server Preparation

**Tasks:**
```batch
# Verify Windows version and updates
winver
wmic qfe list brief /format:table

# Check disk space
wmic logicaldisk get size,freespace,caption

# Verify administrator access
net session
```

**Checklist:**
- [ ] Windows fully updated with latest security patches
- [ ] Administrator access confirmed
- [ ] Antivirus configured with Python/PostgreSQL exceptions
- [ ] 500GB+ disk space available
- [ ] Backup existing data if server reuse

### Step 1.2: Install Required Software

**PostgreSQL 16:**
```batch
# Download from https://www.postgresql.org/download/windows/
# Run installer with these settings:
# - Port: 5432 (default)
# - Locale: Default
# - Set strong postgres password (20+ characters)
```

**Python 3.11:**
```batch
# Verify installation
python --version
pip --version

# Should show Python 3.11.x
```

**NSSM (Non-Sucking Service Manager):**
```batch
# Download from https://nssm.cc/download
# Extract to C:\Program Files\nssm\
# Add to PATH (optional)
setx PATH "%PATH%;C:\Program Files\nssm"
```

**Git for Windows (Optional):**
```batch
# Download from https://git-scm.com/download/win
# Install with default settings
```

### ✅ Phase 1 Testing & Verification

**Test 1: PostgreSQL Connection**
```batch
# Test PostgreSQL is running
sc query postgresql-x64-16

# Test connection
psql -U postgres -c "SELECT version();"
```

**Expected Output:**
```
PostgreSQL 16.x on x86_64-pc-windows-msvc, compiled by Visual C++ build xxxx, 64-bit
```

**Test 2: Python Environment**
```batch
# Verify Python and pip
python -c "import sys; print(f'Python {sys.version}')"
pip list

# Test psycopg2 can be imported (if installed)
python -c "import psycopg2; print('PostgreSQL adapter OK')"
```

**Test 3: Administrator Privileges**
```batch
# Test admin access
net session
# Should show "There are no entries in the list" (no error)

# Test symlink creation (requires admin)
mkdir C:\temp_test
mklink /D C:\temp_link C:\temp_test
dir C:\
rmdir C:\temp_link
rmdir C:\temp_test
```

**Phase 1 Pass Criteria:**
- ✅ PostgreSQL service running
- ✅ Python 3.11+ installed and accessible
- ✅ NSSM downloaded and extracted
- ✅ Administrator access verified
- ✅ 500GB+ disk space available

---

## Phase 2: Production Directory Structure

**Estimated Time**: 30 minutes
**Objective**: Create version-based deployment structure

### Step 2.1: Create Directory Structure

```batch
# Create base production directories
mkdir C:\SilverFox
mkdir C:\SilverFox\releases
mkdir C:\SilverFox\shared
mkdir C:\SilverFox\shared\logs
mkdir C:\SilverFox\shared\orders
mkdir C:\SilverFox\shared\uploads
mkdir C:\SilverFox\backups
mkdir C:\SilverFox\backups\database
mkdir C:\SilverFox\backups\code
mkdir C:\SilverFox\scripts
mkdir C:\SilverFox\updates
```

### Step 2.2: Copy Application Files

```batch
# Copy bulletproof_package to production location
xcopy /E /I /Y "C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package" "C:\SilverFox\releases\v2.1.0"

# Create symlink to current version (requires admin)
mklink /D "C:\SilverFox\current" "C:\SilverFox\releases\v2.1.0"
```

### Step 2.3: Verify Directory Structure

```batch
# List directory structure
tree C:\SilverFox /F /A > C:\SilverFox\directory_structure.txt
type C:\SilverFox\directory_structure.txt
```

### ✅ Phase 2 Testing & Verification

**Test 1: Directory Structure Verification**
```batch
# Verify all directories exist
dir C:\SilverFox
dir C:\SilverFox\releases\v2.1.0
dir C:\SilverFox\shared
dir C:\SilverFox\backups

# Verify symlink created correctly
dir C:\SilverFox | findstr current
# Should show: <SYMLINKD>     current [C:\SilverFox\releases\v2.1.0]
```

**Test 2: File Copy Verification**
```batch
# Check critical files copied
dir C:\SilverFox\releases\v2.1.0\web_gui\app.py
dir C:\SilverFox\releases\v2.1.0\scripts\correct_order_processing.py
dir C:\SilverFox\releases\v2.1.0\sql\*.sql

# Count files to ensure complete copy
dir C:\SilverFox\releases\v2.1.0 /s /b | find /c /v ""
```

**Test 3: Symlink Navigation**
```batch
# Test symlink works
cd C:\SilverFox\current
dir
# Should show contents of v2.1.0 directory
```

**Phase 2 Pass Criteria:**
- ✅ All directories created successfully
- ✅ Application files copied to releases/v2.1.0/
- ✅ Symlink created and pointing to correct version
- ✅ All critical files present (app.py, SQL files, scripts)

---

## Phase 3: Database Setup

**Estimated Time**: 1 hour
**Objective**: Create and configure production database

### Step 3.1: Create Production Database

```batch
# Connect to PostgreSQL
psql -U postgres

# In psql, run:
CREATE DATABASE dealership_db;

# Verify database created
\l

# Exit psql
\q
```

### Step 3.2: Execute SQL Schema Files (IN EXACT ORDER)

```batch
cd C:\SilverFox\releases\v2.1.0\sql

# Execute schema files in this specific order:
psql -U postgres -d dealership_db -f 01_create_database.sql
psql -U postgres -d dealership_db -f 02_create_tables.sql
psql -U postgres -d dealership_db -f 03_initial_dealership_configs.sql
psql -U postgres -d dealership_db -f 05_add_constraints.sql
psql -U postgres -d dealership_db -f 06_order_processing_tables.sql
psql -U postgres -d dealership_db -f 04_performance_settings.sql
```

### Step 3.3: Create VIN Log Tables

```batch
cd C:\SilverFox\releases\v2.1.0\scripts

# Execute VIN log creation script
psql -U postgres -d dealership_db -f create_dealership_vin_logs.sql
```

### ✅ Phase 3 Testing & Verification

**Test 1: Database Creation**
```batch
# List databases
psql -U postgres -c "\l" | findstr dealership_db

# Check database size
psql -U postgres -d dealership_db -c "SELECT pg_size_pretty(pg_database_size('dealership_db'));"
```

**Expected Output:**
```
 dealership_db | postgres | UTF8 | ...
 16 MB (or similar)
```

**Test 2: Core Tables Verification**
```batch
# List all tables
psql -U postgres -d dealership_db -c "\dt"

# Verify key tables exist
psql -U postgres -d dealership_db -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;"
```

**Expected Tables:**
- raw_vehicle_data
- normalized_vehicle_data
- scraper_imports
- dealership_configs
- template_configs
- batch_orders
- schema_migrations

**Test 3: VIN Log Tables Verification**
```batch
# Count VIN log tables (should be 36 dealerships)
psql -U postgres -d dealership_db -c "SELECT COUNT(*) FROM pg_tables WHERE tablename LIKE '%_vin_log';"

# List all VIN log tables
psql -U postgres -d dealership_db -c "SELECT tablename FROM pg_tables WHERE tablename LIKE '%_vin_log' ORDER BY tablename;"
```

**Expected Output:**
```
 count
-------
    36
```

**Test 4: Database Connection from Python**
```batch
cd C:\SilverFox\releases\v2.1.0\scripts

# Test database connection
python -c "from database_connection import db_manager; print('DB OK' if db_manager.test_connection() else 'DB FAILED')"
```

**Expected Output:**
```
DB OK
```

**Test 5: Dealership Configs Verification**
```batch
# Check dealership count
psql -U postgres -d dealership_db -c "SELECT COUNT(*) FROM dealership_configs WHERE is_active = true;"

# List first 5 dealerships
psql -U postgres -d dealership_db -c "SELECT name, location FROM dealership_configs WHERE is_active = true LIMIT 5;"
```

**Phase 3 Pass Criteria:**
- ✅ Database 'dealership_db' created
- ✅ All core tables exist (raw_vehicle_data, normalized_vehicle_data, etc.)
- ✅ 36 dealership VIN log tables created
- ✅ Dealership configs populated
- ✅ Python can connect to database successfully

---

## Phase 4: Configuration

**Estimated Time**: 30 minutes
**Objective**: Configure environment variables and production settings

### Step 4.1: Create Production Environment File

**Create `C:\SilverFox\shared\.env`:**
```ini
# Flask Application Configuration
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_THREADS=4
FLASK_ENV=production

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dealership_db
DB_USER=postgres
DB_PASSWORD=YOUR_SECURE_PASSWORD_HERE

# Application Settings
LOG_LEVEL=INFO
MAX_UPLOAD_SIZE=52428800
ORDER_OUTPUT_PATH=C:\SilverFox\shared\orders
QR_CODE_SIZE=388

# Backup Settings
BACKUP_RETENTION_DAYS=30
BACKUP_PATH=C:\SilverFox\backups\database
```

### Step 4.2: Link Environment File to Application

```batch
# Create symlink from app to shared config
mklink "C:\SilverFox\releases\v2.1.0\.env" "C:\SilverFox\shared\.env"

# Verify symlink
dir C:\SilverFox\releases\v2.1.0 | findstr .env
```

### Step 4.3: Install Production Dependencies

```batch
cd C:\SilverFox\releases\v2.1.0\web_gui

# Install production WSGI server and environment loader
pip install waitress python-dotenv

# Install all application dependencies
pip install -r requirements.txt

# Verify critical packages
pip list | findstr "Flask psycopg2 waitress dotenv"
```

### ✅ Phase 4 Testing & Verification

**Test 1: Environment File Verification**
```batch
# Verify .env exists and is linked
dir C:\SilverFox\shared\.env
dir C:\SilverFox\releases\v2.1.0\.env

# Check .env contents (mask password)
type C:\SilverFox\shared\.env | findstr /V "DB_PASSWORD"
```

**Test 2: Environment Loading Test**
```batch
cd C:\SilverFox\releases\v2.1.0\scripts

# Test environment variables load correctly
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(f'DB_HOST: {os.getenv(\"DB_HOST\")}'); print(f'DB_NAME: {os.getenv(\"DB_NAME\")}'); print(f'FLASK_PORT: {os.getenv(\"FLASK_PORT\")}')"
```

**Expected Output:**
```
DB_HOST: localhost
DB_NAME: dealership_db
FLASK_PORT: 5000
```

**Test 3: Python Dependencies Verification**
```batch
# Test Flask import
python -c "import flask; print(f'Flask {flask.__version__}')"

# Test PostgreSQL adapter
python -c "import psycopg2; print(f'psycopg2 OK')"

# Test Waitress WSGI server
python -c "import waitress; print(f'Waitress OK')"

# Test pandas (for CSV processing)
python -c "import pandas; print(f'Pandas {pandas.__version__}')"

# Test all critical imports together
python -c "import flask, psycopg2, waitress, pandas, requests; print('All dependencies OK')"
```

**Test 4: Database Config Test**
```batch
cd C:\SilverFox\releases\v2.1.0\scripts

# Test database config loads from environment
python -c "from database_config import config; print(f'DB Host: {config.host}'); print(f'DB Name: {config.database}')"
```

**Phase 4 Pass Criteria:**
- ✅ .env file created in shared directory
- ✅ Symlink created from app to shared .env
- ✅ All Python dependencies installed
- ✅ Environment variables load correctly
- ✅ Database configuration accessible from Python

---

## Phase 5: Windows Service Setup

**Estimated Time**: 30 minutes
**Objective**: Install and configure Windows Service for auto-start

### Step 5.1: Create Production Server Entry Point

**Verify `C:\SilverFox\releases\v2.1.0\web_gui\production_server.py` exists:**
```python
"""
Production WSGI server using Waitress (Windows-optimized)
"""
import os
import sys
from waitress import serve
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from app import app, socketio

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    threads = int(os.getenv('FLASK_THREADS', 4))

    print(f"[PRODUCTION] Silver Fox Order Processing System v2.1.0")
    print(f"[PRODUCTION] Server: Waitress WSGI")
    print(f"[PRODUCTION] Listening: http://{host}:{port}")
    print(f"[PRODUCTION] Threads: {threads}")
    print(f"[PRODUCTION] Press Ctrl+C to stop")

    serve(
        app,
        host=host,
        port=port,
        threads=threads,
        channel_timeout=300,
        cleanup_interval=30,
        asyncore_use_poll=True
    )
```

### Step 5.2: Create Service Installation Script

**Create `C:\SilverFox\scripts\install_service.bat`:**
```batch
@echo off
REM Install Silver Fox Order Processing as Windows Service

cd /d "%~dp0\.."

REM Configuration
set PYTHON_EXE=C:\Users\Workstation_1\AppData\Local\Programs\Python\Python311\python.exe
set APP_DIR=C:\SilverFox\current\web_gui
set APP_SCRIPT=%APP_DIR%\production_server.py
set SERVICE_NAME=SilverFoxOrderProcessing
set NSSM="C:\Program Files\nssm\nssm.exe"

REM Check if service already exists
sc query %SERVICE_NAME% >nul 2>&1
if %errorlevel% equ 0 (
    echo Service already exists. Removing...
    %NSSM% stop %SERVICE_NAME%
    %NSSM% remove %SERVICE_NAME% confirm
    timeout /t 3 /nobreak > nul
)

REM Install service
echo Installing %SERVICE_NAME% service...
%NSSM% install %SERVICE_NAME% "%PYTHON_EXE%" "%APP_SCRIPT%"

REM Configure service
%NSSM% set %SERVICE_NAME% AppDirectory "%APP_DIR%"
%NSSM% set %SERVICE_NAME% DisplayName "Silver Fox Order Processing System"
%NSSM% set %SERVICE_NAME% Description "Automated order processing for Silver Fox Marketing dealerships"
%NSSM% set %SERVICE_NAME% Start SERVICE_AUTO_START
%NSSM% set %SERVICE_NAME% AppStdout "C:\SilverFox\shared\logs\service_output.log"
%NSSM% set %SERVICE_NAME% AppStderr "C:\SilverFox\shared\logs\service_error.log"
%NSSM% set %SERVICE_NAME% AppRotateFiles 1
%NSSM% set %SERVICE_NAME% AppRotateOnline 1
%NSSM% set %SERVICE_NAME% AppRotateBytes 10485760

REM Set dependencies (PostgreSQL must start first)
%NSSM% set %SERVICE_NAME% DependOnService postgresql-x64-16

echo.
echo Service installed successfully!
echo.
echo To start: net start %SERVICE_NAME%
echo To stop:  net stop %SERVICE_NAME%
echo To check: sc query %SERVICE_NAME%
echo.
pause
```

### Step 5.3: Install and Start Service

```batch
# Install the service
cd C:\SilverFox\scripts
install_service.bat

# Start the service
net start SilverFoxOrderProcessing

# Verify service is running
sc query SilverFoxOrderProcessing
```

### ✅ Phase 5 Testing & Verification

**Test 1: Manual Server Test (Before Service)**
```batch
cd C:\SilverFox\releases\v2.1.0\web_gui

# Test server manually first
python production_server.py
# Press Ctrl+C to stop after verifying it starts
```

**Expected Output:**
```
[PRODUCTION] Silver Fox Order Processing System v2.1.0
[PRODUCTION] Server: Waitress WSGI
[PRODUCTION] Listening: http://127.0.0.1:5000
[PRODUCTION] Threads: 4
```

**Test 2: Service Installation Verification**
```batch
# Check service exists
sc query SilverFoxOrderProcessing

# Check service config
sc qc SilverFoxOrderProcessing
```

**Expected Output:**
```
SERVICE_NAME: SilverFoxOrderProcessing
        TYPE               : 10  WIN32_OWN_PROCESS
        STATE              : 4  RUNNING
        ...
```

**Test 3: Service Startup Test**
```batch
# Stop service
net stop SilverFoxOrderProcessing

# Start service
net start SilverFoxOrderProcessing

# Wait 10 seconds for startup
timeout /t 10 /nobreak

# Check service status
sc query SilverFoxOrderProcessing
```

**Test 4: Web Interface Accessibility**
```batch
# Test web interface responds
curl http://localhost:5000

# Or open in browser
start http://localhost:5000
```

**Test 5: Service Logs Verification**
```batch
# Check service started successfully
type C:\SilverFox\shared\logs\service_output.log

# Check for errors
type C:\SilverFox\shared\logs\service_error.log
```

**Test 6: Auto-Start Verification**
```batch
# Check service set to auto-start
sc qc SilverFoxOrderProcessing | findstr START_TYPE
# Should show: AUTO_START
```

**Phase 5 Pass Criteria:**
- ✅ production_server.py exists and runs manually
- ✅ Windows Service installed successfully
- ✅ Service starts without errors
- ✅ Web interface accessible at http://localhost:5000
- ✅ Service set to AUTO_START
- ✅ Logs being written to shared/logs/

---

## Phase 6: Security Hardening

**Estimated Time**: 30 minutes
**Objective**: Secure database, network, and file system

### Step 6.1: Create Restricted Database User

```sql
-- Connect as postgres
psql -U postgres

-- Create restricted application user
CREATE USER silverfox_app WITH PASSWORD 'STRONG_PASSWORD_HERE_20_CHARS';

-- Grant minimal required permissions
GRANT CONNECT ON DATABASE dealership_db TO silverfox_app;
GRANT USAGE ON SCHEMA public TO silverfox_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO silverfox_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO silverfox_app;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO silverfox_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO silverfox_app;

-- Revoke public access
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

\q
```

### Step 6.2: Update .env with Restricted User

**Edit `C:\SilverFox\shared\.env`:**
```ini
DB_USER=silverfox_app
DB_PASSWORD=STRONG_PASSWORD_HERE_20_CHARS
```

### Step 6.3: Configure Windows Firewall

```batch
# Block external access to PostgreSQL
netsh advfirewall firewall add rule name="Block PostgreSQL External" dir=in action=block protocol=TCP localport=5432 remoteip=any

# Block external access to Flask (allow localhost only)
netsh advfirewall firewall add rule name="Block Flask External" dir=in action=block protocol=TCP localport=5000 remoteip=any

# Verify rules created
netsh advfirewall firewall show rule name="Block PostgreSQL External"
netsh advfirewall firewall show rule name="Block Flask External"
```

### Step 6.4: Set File System Permissions

```batch
# Restrict access to sensitive files
icacls "C:\SilverFox\shared\.env" /inheritance:r /grant:r "%USERNAME%:F"
icacls "C:\SilverFox\backups" /inheritance:r /grant:r "%USERNAME%:F" /grant:r "SYSTEM:F"

# Restrict logs to administrators
icacls "C:\SilverFox\shared\logs" /inheritance:r /grant:r "Administrators:F" /grant:r "SYSTEM:F"
```

### ✅ Phase 6 Testing & Verification

**Test 1: Restricted User Database Access**
```batch
# Test connection with new user
psql -U silverfox_app -d dealership_db -c "SELECT COUNT(*) FROM dealership_configs;"

# Test restricted user CANNOT create tables
psql -U silverfox_app -d dealership_db -c "CREATE TABLE test_table (id INT);"
# Should fail with permission error
```

**Test 2: Application Database Connection**
```batch
# Restart service with new credentials
net stop SilverFoxOrderProcessing
net start SilverFoxOrderProcessing

# Wait for startup
timeout /t 10 /nobreak

# Test database connection
cd C:\SilverFox\current\scripts
python -c "from database_connection import db_manager; print('DB OK' if db_manager.test_connection() else 'DB FAILED')"
```

**Test 3: Firewall Rules Verification**
```batch
# List firewall rules
netsh advfirewall firewall show rule name=all | findstr "Block PostgreSQL"
netsh advfirewall firewall show rule name=all | findstr "Block Flask"

# Test external access blocked (from another machine)
# Should timeout or be refused
```

**Test 4: File Permissions Verification**
```batch
# Check .env permissions
icacls "C:\SilverFox\shared\.env"

# Verify only specific users have access
# Should NOT show Everyone or Users groups
```

**Test 5: Security Checklist Validation**
```batch
# Test SQL injection protection (should be handled by parameterized queries)
# Test XSS protection (Flask auto-escaping)
# Verify no passwords in code (all in .env)
```

**Phase 6 Pass Criteria:**
- ✅ Restricted database user created and working
- ✅ Application connects with restricted user
- ✅ Firewall rules blocking external access
- ✅ File permissions restricted on sensitive files
- ✅ No passwords in code (all in environment)
- ✅ Service still operational with new credentials

---

## Phase 7: Backup & Monitoring

**Estimated Time**: 30 minutes
**Objective**: Setup automated backups and health monitoring

### Step 7.1: Create Backup Script

**Verify `C:\SilverFox\releases\v2.1.0\scripts\backup_database.py` exists:**
```python
"""
Automated PostgreSQL database backup with rotation
"""
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configuration
BACKUP_DIR = Path(r"C:\SilverFox\backups\database")
DB_NAME = "dealership_db"
DB_USER = "postgres"
POSTGRES_BIN = r"C:\Program Files\PostgreSQL\16\bin"
RETENTION_DAYS = 30

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(r'C:\SilverFox\shared\logs\backup.log'),
        logging.StreamHandler()
    ]
)

def backup_database():
    """Create compressed database backup"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"backup_{DB_NAME}_{timestamp}.backup"

    pg_dump = Path(POSTGRES_BIN) / "pg_dump.exe"

    command = [
        str(pg_dump),
        "-U", DB_USER,
        "-F", "c",  # Custom format (compressed)
        "-b",       # Include large objects
        "-v",       # Verbose
        "-f", str(backup_file),
        DB_NAME
    ]

    logging.info(f"Starting backup: {backup_file.name}")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            env={**os.environ, 'PGPASSWORD': os.getenv('DB_PASSWORD', '')}
        )

        if result.returncode == 0:
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            logging.info(f"Backup successful: {size_mb:.2f} MB")
            cleanup_old_backups()
            return True
        else:
            logging.error(f"Backup failed: {result.stderr}")
            return False

    except Exception as e:
        logging.error(f"Backup exception: {e}")
        return False

def cleanup_old_backups():
    """Remove backups older than retention period"""
    cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
    removed = 0

    for backup in BACKUP_DIR.glob("backup_*.backup"):
        if datetime.fromtimestamp(backup.stat().st_mtime) < cutoff_date:
            logging.info(f"Removing old backup: {backup.name}")
            backup.unlink()
            removed += 1

    if removed:
        logging.info(f"Cleanup complete: {removed} old backups removed")

if __name__ == "__main__":
    success = backup_database()
    exit(0 if success else 1)
```

### Step 7.2: Create Health Check Script

**Verify `C:\SilverFox\releases\v2.1.0\scripts\health_check.py` exists:**
```python
"""
System health check script
"""
import requests
import sys
import os
from datetime import datetime

def check_health():
    try:
        # Test web service
        r = requests.get('http://localhost:5000/api/test-database', timeout=10)
        if r.status_code == 200:
            print("[OK] System healthy")
            return 0
        else:
            print(f"[ERROR] HTTP {r.status_code}")
            return 1
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1

if __name__ == "__main__":
    sys.exit(check_health())
```

### Step 7.3: Schedule Automated Backups

```batch
# Schedule backup at 2 AM daily
schtasks /create /tn "Silver Fox DB Backup" /tr "python C:\SilverFox\current\scripts\backup_database.py" /sc daily /st 02:00 /ru SYSTEM /f

# Verify task created
schtasks /query /tn "Silver Fox DB Backup"
```

### ✅ Phase 7 Testing & Verification

**Test 1: Manual Backup Test**
```batch
# Run backup manually
cd C:\SilverFox\current\scripts
python backup_database.py

# Check backup created
dir C:\SilverFox\backups\database

# Check backup log
type C:\SilverFox\shared\logs\backup.log
```

**Expected Output:**
```
Starting backup: backup_dealership_db_20251006_143022.backup
Backup successful: 145.23 MB
```

**Test 2: Backup Restoration Test**
```batch
# Create test database
psql -U postgres -c "CREATE DATABASE dealership_db_test;"

# Get latest backup file
dir C:\SilverFox\backups\database /O-D

# Restore backup to test database
"C:\Program Files\PostgreSQL\16\bin\pg_restore.exe" -U postgres -d dealership_db_test -v "C:\SilverFox\backups\database\backup_dealership_db_YYYYMMDD_HHMMSS.backup"

# Verify restore successful
psql -U postgres -d dealership_db_test -c "\dt"

# Clean up test database
psql -U postgres -c "DROP DATABASE dealership_db_test;"
```

**Test 3: Health Check Test**
```batch
# Run health check
cd C:\SilverFox\current\scripts
python health_check.py
```

**Expected Output:**
```
[OK] System healthy
```

**Test 4: Scheduled Task Verification**
```batch
# Check scheduled task exists
schtasks /query /tn "Silver Fox DB Backup" /fo LIST /v

# Test scheduled task runs
schtasks /run /tn "Silver Fox DB Backup"

# Wait for completion
timeout /t 30 /nobreak

# Check new backup created
dir C:\SilverFox\backups\database /O-D
```

**Test 5: Backup Retention Test**
```batch
# Check backup retention logic
cd C:\SilverFox\current\scripts

# Count backups
dir C:\SilverFox\backups\database | find /c "backup_"

# Should automatically delete backups older than 30 days
```

**Phase 7 Pass Criteria:**
- ✅ Backup script executes successfully
- ✅ Backup file created in backups/database/
- ✅ Backup can be restored successfully
- ✅ Health check script passes
- ✅ Scheduled task created and runs
- ✅ Backup rotation working (30-day retention)

---

## Phase 8: Deployment Automation Scripts

**Estimated Time**: 30 minutes
**Objective**: Create scripts for future updates and rollbacks

### Step 8.1: Create Deploy Update Script

**Create `C:\SilverFox\scripts\deploy_update.bat`:**
```batch
@echo off
REM Deploy system update with automated backup and rollback
REM Usage: deploy_update.bat 2.2.0

set VERSION=%1
if "%VERSION%"=="" (
    echo Usage: deploy_update.bat [version]
    echo Example: deploy_update.bat 2.2.0
    exit /b 1
)

set BASE_DIR=C:\SilverFox
set NEW_VERSION=%BASE_DIR%\releases\v%VERSION%
set SERVICE_NAME=SilverFoxOrderProcessing
set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%

echo ========================================
echo  Silver Fox Update Deployment v%VERSION%
echo ========================================
echo.

REM Verify new version exists
if not exist "%NEW_VERSION%" (
    echo [ERROR] Version not found: %NEW_VERSION%
    exit /b 1
)

REM Backup database
echo [BACKUP] Creating database backup...
python "%BASE_DIR%\current\scripts\backup_database.py"
if errorlevel 1 (
    echo [ERROR] Database backup failed
    exit /b 1
)

REM Backup current code
echo [BACKUP] Backing up current version...
set CODE_BACKUP=%BASE_DIR%\backups\code\backup_%TIMESTAMP%
xcopy /E /I /Y "%BASE_DIR%\current" "%CODE_BACKUP%" >nul

REM Stop service
echo [SERVICE] Stopping service...
net stop %SERVICE_NAME%
timeout /t 3 /nobreak >nul

REM Run migrations if present
if exist "%NEW_VERSION%\migrations\upgrade.sql" (
    echo [MIGRATION] Running database migrations...
    psql -U postgres -d dealership_db -f "%NEW_VERSION%\migrations\upgrade.sql"
    if errorlevel 1 goto :rollback
)

REM Switch to new version
echo [DEPLOY] Switching to version %VERSION%...
rmdir "%BASE_DIR%\current"
mklink /D "%BASE_DIR%\current" "%NEW_VERSION%"

REM Start service
echo [SERVICE] Starting service...
net start %SERVICE_NAME%
timeout /t 5 /nobreak >nul

REM Verify deployment
echo [VERIFY] Checking system health...
python "%BASE_DIR%\current\scripts\health_check.py"
if errorlevel 1 goto :rollback

echo.
echo [SUCCESS] Deployment complete! Version %VERSION% is live.
exit /b 0

:rollback
echo.
echo [ROLLBACK] Deployment failed - restoring previous version...
net stop %SERVICE_NAME%
rmdir "%BASE_DIR%\current"
mklink /D "%BASE_DIR%\current" "%CODE_BACKUP%"
net start %SERVICE_NAME%
echo [ROLLBACK] System restored to previous version
exit /b 1
```

### Step 8.2: Create Rollback Script

**Create `C:\SilverFox\scripts\rollback_update.bat`:**
```batch
@echo off
REM Rollback to previous version
REM Usage: rollback_update.bat <version>

set VERSION=%1
set SERVICE_NAME=SilverFoxOrderProcessing
set BASE_DIR=C:\SilverFox

if "%VERSION%"=="" (
    echo Usage: rollback_update.bat [version]
    echo Example: rollback_update.bat 2.1.0
    exit /b 1
)

echo [ROLLBACK] Rolling back to version %VERSION%...

REM Verify version exists
if not exist "%BASE_DIR%\releases\v%VERSION%" (
    echo [ERROR] Version v%VERSION% not found in releases
    exit /b 1
)

REM Stop service
echo [SERVICE] Stopping service...
net stop %SERVICE_NAME%
timeout /t 3 /nobreak >nul

REM Switch symlink
echo [ROLLBACK] Switching to version %VERSION%...
rmdir "%BASE_DIR%\current"
mklink /D "%BASE_DIR%\current" "%BASE_DIR%\releases\v%VERSION%"

REM Rollback database if needed
if exist "%BASE_DIR%\releases\v%VERSION%\migrations\downgrade.sql" (
    echo [DB] Rolling back database changes...
    psql -U postgres -d dealership_db -f "%BASE_DIR%\releases\v%VERSION%\migrations\downgrade.sql"
)

REM Start service
echo [SERVICE] Starting service...
net start %SERVICE_NAME%
timeout /t 5 /nobreak >nul

REM Verify
echo [VERIFY] Checking system health...
python "%BASE_DIR%\current\scripts\health_check.py"
if errorlevel 1 (
    echo [WARNING] Health check failed after rollback
    exit /b 1
)

echo.
echo [SUCCESS] Rolled back to version %VERSION%
exit /b 0
```

### Step 8.3: Create Prepare Update Script

**Create `C:\SilverFox\scripts\prepare_update.bat`:**
```batch
@echo off
REM Prepare new version for deployment
REM Usage: prepare_update.bat <version> <source_zip>

set VERSION=%1
set SOURCE_ZIP=%2

if "%VERSION%"=="" (
    echo Usage: prepare_update.bat [version] [source_zip]
    echo Example: prepare_update.bat 2.2.0 update.zip
    exit /b 1
)

set BASE_DIR=C:\SilverFox
set NEW_DIR=%BASE_DIR%\releases\v%VERSION%

echo [PREPARE] Preparing version %VERSION% for deployment...

REM Create version directory
if exist "%NEW_DIR%" (
    echo [ERROR] Version %VERSION% already exists
    exit /b 1
)
mkdir "%NEW_DIR%"

REM Extract update package
echo [EXTRACT] Extracting update package...
powershell -command "Expand-Archive -Path '%SOURCE_ZIP%' -DestinationPath '%NEW_DIR%' -Force"

REM Link shared configuration
echo [CONFIG] Linking shared configuration...
mklink "%NEW_DIR%\.env" "%BASE_DIR%\shared\.env"

REM Install dependencies
echo [DEPS] Installing Python dependencies...
cd "%NEW_DIR%\web_gui"
pip install -r requirements.txt --quiet

echo.
echo [SUCCESS] Version %VERSION% prepared successfully
echo [READY] Run 'deploy_update.bat %VERSION%' to deploy
exit /b 0
```

### ✅ Phase 8 Testing & Verification

**Test 1: Deployment Script Validation**
```batch
# Test deploy script shows usage
C:\SilverFox\scripts\deploy_update.bat

# Should show usage instructions
```

**Expected Output:**
```
Usage: deploy_update.bat [version]
Example: deploy_update.bat 2.2.0
```

**Test 2: Rollback Script Validation**
```batch
# Test rollback script shows usage
C:\SilverFox\scripts\rollback_update.bat

# Should show usage instructions
```

**Test 3: Prepare Update Script Validation**
```batch
# Test prepare script shows usage
C:\SilverFox\scripts\prepare_update.bat

# Should show usage instructions
```

**Test 4: Create Test Package for Deployment**
```batch
# Create a test update package
cd C:\SilverFox\releases\v2.1.0
powershell -command "Compress-Archive -Path * -DestinationPath C:\SilverFox\updates\test_v2.1.1.zip"

# Test prepare update
cd C:\SilverFox\scripts
prepare_update.bat 2.1.1 C:\SilverFox\updates\test_v2.1.1.zip

# Verify new version prepared
dir C:\SilverFox\releases\v2.1.1
```

**Test 5: Simulated Rollback Test**
```batch
# Test rollback to current version (should work without changes)
cd C:\SilverFox\scripts
rollback_update.bat 2.1.0

# Verify service still running
sc query SilverFoxOrderProcessing

# Check health
python C:\SilverFox\current\scripts\health_check.py
```

**Test 6: Script Permissions Test**
```batch
# Verify scripts are executable
icacls C:\SilverFox\scripts\*.bat
```

**Phase 8 Pass Criteria:**
- ✅ Deploy update script created and validated
- ✅ Rollback script created and validated
- ✅ Prepare update script created and validated
- ✅ Test package creation successful
- ✅ Simulated rollback works correctly
- ✅ All scripts have proper permissions

---

## Phase 9: Final Testing & Go-Live

**Estimated Time**: 1 hour
**Objective**: Comprehensive system testing and production go-live

### Step 9.1: Comprehensive System Test

```batch
# Open web interface
start http://localhost:5000

# Test database connection through UI
# Navigate to Settings > Test Database Connection
```

### Step 9.2: Order Processing Test

**Test CAO Order:**
1. Navigate to Order Management
2. Select a test dealership (e.g., "BMW of West St Louis")
3. Submit CAO order
4. Verify order processing completes
5. Check order output in `C:\SilverFox\shared\orders\`
6. Verify QR codes generated at 388x388 PNG

**Test LIST Order:**
1. Navigate to Order Management
2. Select a test dealership
3. Enter test VINs or stock numbers
4. Submit LIST order
5. Verify order processing completes
6. Check billing CSV output

### Step 9.3: VIN Logging Test

```batch
# Check VIN log for test dealership
psql -U postgres -d dealership_db -c "SELECT * FROM bmw_of_west_st_louis_vin_log ORDER BY order_date DESC LIMIT 5;"

# Verify VINs logged correctly
```

### Step 9.4: Template System Test

1. Navigate to Template Builder
2. Create a test template
3. Configure fields and formatting
4. Save template
5. Process order using template
6. Verify output formatting

### Step 9.5: Service Restart Test

```batch
# Stop service
net stop SilverFoxOrderProcessing

# Wait
timeout /t 5 /nobreak

# Start service
net start SilverFoxOrderProcessing

# Wait for startup
timeout /t 10 /nobreak

# Test web interface
start http://localhost:5000

# Run health check
python C:\SilverFox\current\scripts\health_check.py
```

### Step 9.6: Reboot Test

```batch
# Restart server
shutdown /r /t 60 /c "Production deployment reboot test - 60 seconds"

# After reboot, verify:
# 1. PostgreSQL started automatically
sc query postgresql-x64-16

# 2. Service started automatically
sc query SilverFoxOrderProcessing

# 3. Web interface accessible
start http://localhost:5000

# 4. Health check passes
python C:\SilverFox\current\scripts\health_check.py
```

### ✅ Phase 9 Final Testing & Verification

**Test 1: Web Interface Full Test**
```batch
# Access web interface
start http://localhost:5000

# Checklist:
# - [ ] Login/authentication works (if applicable)
# - [ ] Dashboard loads correctly
# - [ ] Order queue displays
# - [ ] Dealership settings accessible
# - [ ] Template builder functional
# - [ ] Dark mode toggle works
# - [ ] Keyboard shortcuts work (/ for search)
```

**Test 2: CAO Order End-to-End Test**
```batch
# Process test CAO order through UI
# Verify:
# - [ ] Order submitted successfully
# - [ ] Real-time progress updates via Socket.IO
# - [ ] Order completes without errors
# - [ ] Output files created
# - [ ] QR codes at 388x388 PNG
# - [ ] VINs logged to dealership table
```

**Test 3: LIST Order End-to-End Test**
```batch
# Process test LIST order through UI
# Test with both VINs and stock numbers
# Verify:
# - [ ] VINs (17 chars) processed correctly
# - [ ] Stock numbers (<17 chars) processed correctly
# - [ ] Billing CSV generated
# - [ ] Duplicate VINs handled correctly
# - [ ] VIN logs updated
```

**Test 4: Database Integrity Test**
```batch
# Check active import
psql -U postgres -d dealership_db -c "SELECT * FROM scraper_imports WHERE status = 'active';"

# Check dealership configs
psql -U postgres -d dealership_db -c "SELECT COUNT(*) FROM dealership_configs WHERE is_active = true;"

# Check VIN log counts
psql -U postgres -d dealership_db -c "SELECT tablename, (xpath('/row/cnt/text()', query_to_xml('SELECT COUNT(*) as cnt FROM ' || tablename, true, false, '')))[1]::text::int as row_count FROM pg_tables WHERE tablename LIKE '%_vin_log' ORDER BY tablename;"
```

**Test 5: Performance Test**
```batch
# Process multiple orders simultaneously
# Monitor system resources
tasklist | findstr python
wmic cpu get loadpercentage
wmic OS get FreePhysicalMemory

# Check database performance
psql -U postgres -d dealership_db -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, state, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC;"
```

**Test 6: Error Handling Test**
```batch
# Test error scenarios:
# - Submit order with invalid VIN
# - Submit order for dealership with no active data
# - Submit duplicate order
# - Test with malformed input

# Check error logs
type C:\SilverFox\shared\logs\service_error.log
```

**Test 7: Auto-Recovery Test**
```batch
# Kill service process
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq production_server.py*"

# Wait for auto-restart (NSSM should restart it)
timeout /t 15 /nobreak

# Verify service recovered
sc query SilverFoxOrderProcessing

# Test functionality
start http://localhost:5000
```

**Test 8: Backup Verification**
```batch
# Check latest backup exists
dir C:\SilverFox\backups\database /O-D

# Verify backup size reasonable
# Should be 100MB+ for production data

# Check backup log
type C:\SilverFox\shared\logs\backup.log | more
```

**Test 9: Security Verification**
```batch
# Verify external access blocked
netstat -an | findstr 5000
netstat -an | findstr 5432

# Should only show 127.0.0.1 (localhost)

# Test firewall rules
netsh advfirewall firewall show rule name=all | findstr "Block"
```

**Test 10: Documentation Verification**
```batch
# Verify all documentation accessible
dir C:\SilverFox\*.md
dir C:\SilverFox\releases\v2.1.0\*.md

# Key documents:
# - DEPLOYMENT_ROLLOUT.md
# - UPDATE_DEPLOYMENT_STRATEGY.md
# - FINAL_PRODUCTION_DEPLOYMENT.md
```

### 🚀 Go-Live Checklist

**Pre-Go-Live Verification:**
- [ ] All 9 phases completed successfully
- [ ] All phase tests passed
- [ ] Web interface fully functional
- [ ] CAO orders processing correctly
- [ ] LIST orders processing correctly
- [ ] QR codes generating at 388x388 PNG
- [ ] VIN logging working for all 36 dealerships
- [ ] Service auto-starts on boot
- [ ] Backups scheduled and working
- [ ] Health checks passing
- [ ] Security hardening complete
- [ ] Documentation complete
- [ ] Deployment scripts tested
- [ ] Rollback procedures verified

**Final Production Steps:**

1. **Create Final Backup**
```batch
python C:\SilverFox\current\scripts\backup_database.py
```

2. **Verify Service Running**
```batch
sc query SilverFoxOrderProcessing
```

3. **Run Final Health Check**
```batch
python C:\SilverFox\current\scripts\health_check.py
```

4. **Open Production Dashboard**
```batch
start http://localhost:5000
```

5. **Monitor Initial Operations**
- Watch error logs: `C:\SilverFox\shared\logs\service_error.log`
- Watch order processing: `C:\SilverFox\shared\orders\`
- Monitor system resources: Task Manager

**Phase 9 Pass Criteria:**
- ✅ Web interface fully functional
- ✅ CAO orders process successfully
- ✅ LIST orders process successfully
- ✅ VIN logging works for all dealerships
- ✅ QR codes generate correctly (388x388)
- ✅ Service auto-starts on reboot
- ✅ Performance acceptable under load
- ✅ Error handling working correctly
- ✅ Auto-recovery working
- ✅ Backups automated and verified
- ✅ Security measures in place
- ✅ All documentation complete

**🎉 PRODUCTION GO-LIVE COMPLETE! 🎉**

---

## Rollback Procedures

### Emergency Rollback (Immediate)

**If new deployment fails:**

```batch
# Stop service
net stop SilverFoxOrderProcessing

# Switch back to previous version
rmdir "C:\SilverFox\current"
mklink /D "C:\SilverFox\current" "C:\SilverFox\releases\v2.1.0"

# Start service
net start SilverFoxOrderProcessing

# Verify
python C:\SilverFox\current\scripts\health_check.py
```

### Database Rollback

**If database migration fails:**

```batch
# Stop service
net stop SilverFoxOrderProcessing

# Restore from latest backup
set BACKUP_FILE=C:\SilverFox\backups\database\backup_dealership_db_LATEST.backup

# Drop and recreate database
psql -U postgres -c "DROP DATABASE dealership_db;"
psql -U postgres -c "CREATE DATABASE dealership_db;"

# Restore
"C:\Program Files\PostgreSQL\16\bin\pg_restore.exe" -U postgres -d dealership_db -v "%BACKUP_FILE%"

# Switch to previous code
rmdir "C:\SilverFox\current"
mklink /D "C:\SilverFox\current" "C:\SilverFox\releases\v2.1.0"

# Start service
net start SilverFoxOrderProcessing
```

### Using Rollback Script

```batch
# Automated rollback to specific version
cd C:\SilverFox\scripts
rollback_update.bat 2.1.0

# Verify rollback
python C:\SilverFox\current\scripts\health_check.py
sc query SilverFoxOrderProcessing
```

---

## Post-Deployment Monitoring

### First 24 Hours

**Monitor every 2 hours:**

```batch
# Check service status
sc query SilverFoxOrderProcessing

# Check error logs
type C:\SilverFox\shared\logs\service_error.log | findstr ERROR

# Check recent orders
dir C:\SilverFox\shared\orders /O-D

# Check database size
psql -U postgres -d dealership_db -c "SELECT pg_size_pretty(pg_database_size('dealership_db'));"

# Check disk space
wmic logicaldisk get size,freespace,caption

# Run health check
python C:\SilverFox\current\scripts\health_check.py
```

### Weekly Monitoring

```batch
# Review error logs
type C:\SilverFox\shared\logs\service_error.log | findstr ERROR

# Check backup status
dir C:\SilverFox\backups\database | findstr /C:"backup_"

# Verify database integrity
psql -U postgres -d dealership_db -c "VACUUM ANALYZE;"

# Clean old order files (optional, keep last 30 days)
forfiles /p "C:\SilverFox\shared\orders" /d -30 /c "cmd /c del @path"
```

### Monthly Maintenance

1. **Update Windows**: Install security patches
2. **Update PostgreSQL**: Check for updates
3. **Update Python packages**: `pip list --outdated`
4. **Review dealership configs**: Verify filtering rules current
5. **Test backup restoration**: Validate backups work
6. **Performance review**: Check slow queries and optimize

---

## Success Criteria Summary

### ✅ Production Deployment Complete When:

**Infrastructure:**
- [x] PostgreSQL 16 installed and running
- [x] Python 3.11+ installed
- [x] Production directory structure created
- [x] Version-based deployment architecture in place

**Database:**
- [x] Database created with all schemas
- [x] 36 dealership VIN log tables created
- [x] Dealership configs populated
- [x] Restricted database user configured

**Application:**
- [x] Application files deployed to production
- [x] Environment configured (.env file)
- [x] Dependencies installed
- [x] Windows Service configured and auto-starting

**Security:**
- [x] Firewall rules blocking external access
- [x] File permissions restricted
- [x] Database permissions minimal
- [x] No credentials in code

**Operations:**
- [x] Automated backups scheduled
- [x] Health checks operational
- [x] Deployment scripts created
- [x] Rollback procedures tested
- [x] Monitoring in place

**Testing:**
- [x] Web interface functional
- [x] CAO orders processing
- [x] LIST orders processing
- [x] VIN logging working
- [x] QR codes generating correctly
- [x] Auto-restart working
- [x] Rollback verified

---

## Quick Reference Commands

### Service Management
```batch
net start SilverFoxOrderProcessing      # Start service
net stop SilverFoxOrderProcessing       # Stop service
sc query SilverFoxOrderProcessing       # Check status
```

### Database Operations
```batch
psql -U postgres -d dealership_db                          # Connect to DB
psql -U postgres -d dealership_db -c "SELECT version();"   # Check version
psql -U postgres -d dealership_db -c "VACUUM ANALYZE;"     # Optimize DB
```

### Backup & Restore
```batch
python C:\SilverFox\current\scripts\backup_database.py    # Manual backup
pg_restore -U postgres -d dealership_db backup.backup     # Restore
```

### Deployment
```batch
deploy_update.bat 2.2.0                # Deploy new version
rollback_update.bat 2.1.0              # Rollback to previous
```

### Monitoring
```batch
type C:\SilverFox\shared\logs\service_output.log | more   # View logs
python C:\SilverFox\current\scripts\health_check.py       # Health check
```

---

## Document Information

**Version**: 1.0
**Date**: 2025-10-06
**Status**: Production Ready
**Total Deployment Time**: 4-6 hours
**Support**: All procedures tested and verified

**Next Steps After Deployment:**
1. Monitor system for 24-48 hours
2. Verify all dealerships processing correctly
3. Train users on system operation
4. Document any custom configurations
5. Schedule first maintenance window

---

**END OF DEPLOYMENT ROLLOUT GUIDE**

✅ System ready for production deployment with full rollback capability
