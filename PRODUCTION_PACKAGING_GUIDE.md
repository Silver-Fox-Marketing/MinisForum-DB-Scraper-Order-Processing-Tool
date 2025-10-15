# Production Packaging Guide
## Silver Fox Order Processing System

---

## Overview

This guide covers all steps needed to package and deploy the Order Processing System for production use on Windows.

---

## 1. Production Server Configuration

### Current State (Development)
- Using Flask development server (`app.run()`)
- Single-threaded, not secure
- Not suitable for production

### Production Requirements
- **WSGI Server**: Waitress (Windows-optimized)
- **Process Management**: Windows Service or Task Scheduler
- **Database**: PostgreSQL with connection pooling (already configured)
- **Environment Variables**: Secure configuration management

---

## 2. Required Changes for Production

### A. Add Production WSGI Server

**Update `web_gui/requirements.txt`:**
```
Flask>=2.3.0
Flask-SocketIO>=5.3.0
psycopg2-binary>=2.9.9
pandas>=2.0.0
requests>=2.28.0
python-socketio>=5.8.0
eventlet>=0.33.0
schedule>=1.2.0
psutil>=5.9.0
numpy>=1.24.0
waitress>=2.1.2        # Add this for production WSGI server
python-dotenv>=1.0.0   # Add this for environment variables
```

### B. Create Production Server Entry Point

**Create `web_gui/production_server.py`:**
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
    # Production configuration
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    threads = int(os.getenv('FLASK_THREADS', 4))

    print(f"[PRODUCTION] Starting Silver Fox Order Processing System")
    print(f"[PRODUCTION] Server: Waitress WSGI")
    print(f"[PRODUCTION] Host: {host}")
    print(f"[PRODUCTION] Port: {port}")
    print(f"[PRODUCTION] Threads: {threads}")

    # Serve with Waitress (production-ready WSGI server)
    serve(
        app,
        host=host,
        port=port,
        threads=threads,
        channel_timeout=300,        # 5 minute timeout for long operations
        cleanup_interval=30,        # Clean up connections every 30 seconds
        asyncore_use_poll=True     # Better performance on Windows
    )
```

### C. Environment Configuration

**Create `.env` file (for local development):**
```
# Flask Configuration
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_THREADS=4
FLASK_ENV=production

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dealership_db
DB_USER=postgres
DB_PASSWORD=your_secure_password_here

# Application Settings
LOG_LEVEL=INFO
MAX_UPLOAD_SIZE=52428800  # 50MB
```

**Create `.env.example` (template for deployment):**
```
# Flask Configuration
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_THREADS=4
FLASK_ENV=production

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dealership_db
DB_USER=postgres
DB_PASSWORD=CHANGE_ME

# Application Settings
LOG_LEVEL=INFO
MAX_UPLOAD_SIZE=52428800
```

### D. Update Database Configuration

**Modify `scripts/database_config.py` to use environment variables:**
```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseConfig:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', 5432))
        self.database = os.getenv('DB_NAME', 'dealership_db')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', '')

        # Connection pooling
        self.min_connections = 2
        self.max_connections = 10

    @property
    def connection_dict(self):
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password
        }

config = DatabaseConfig()
```

---

## 3. Windows Service Setup

### Option A: NSSM (Recommended - GUI-based)

**Install NSSM (Non-Sucking Service Manager):**
1. Download from https://nssm.cc/download
2. Extract to `C:\Program Files\nssm\`

**Create Windows Service:**
```batch
@echo off
REM Install Silver Fox Order Processing as Windows Service

cd /d "%~dp0"

REM Set paths
set PYTHON_PATH=C:\Users\Workstation_1\AppData\Local\Programs\Python\Python311\python.exe
set APP_PATH=%CD%\web_gui\production_server.py
set SERVICE_NAME=SilverFoxOrderProcessing

REM Install service using NSSM
"C:\Program Files\nssm\nssm.exe" install %SERVICE_NAME% "%PYTHON_PATH%" "%APP_PATH%"

REM Configure service
"C:\Program Files\nssm\nssm.exe" set %SERVICE_NAME% AppDirectory "%CD%\web_gui"
"C:\Program Files\nssm\nssm.exe" set %SERVICE_NAME% DisplayName "Silver Fox Order Processing System"
"C:\Program Files\nssm\nssm.exe" set %SERVICE_NAME% Description "Automated order processing for Silver Fox Marketing dealerships"
"C:\Program Files\nssm\nssm.exe" set %SERVICE_NAME% Start SERVICE_AUTO_START
"C:\Program Files\nssm\nssm.exe" set %SERVICE_NAME% AppStdout "%CD%\logs\service_output.log"
"C:\Program Files\nssm\nssm.exe" set %SERVICE_NAME% AppStderr "%CD%\logs\service_error.log"

echo Service installed successfully!
echo Use 'net start %SERVICE_NAME%' to start the service
pause
```

**Start/Stop Service Commands:**
```batch
REM Start service
net start SilverFoxOrderProcessing

REM Stop service
net stop SilverFoxOrderProcessing

REM Check service status
sc query SilverFoxOrderProcessing
```

### Option B: Task Scheduler (Alternative)

**Create startup script `start_production_service.bat`:**
```batch
@echo off
REM Start Silver Fox Order Processing System

cd /d "%~dp0\web_gui"

REM Activate virtual environment if using one
REM call ..\venv\Scripts\activate

REM Start production server
python production_server.py

pause
```

**Configure Task Scheduler:**
1. Open Task Scheduler
2. Create Basic Task → "Silver Fox Order Processing"
3. Trigger: "At system startup"
4. Action: Start program → `start_production_service.bat`
5. Settings:
   - Run whether user logged on or not
   - Run with highest privileges

---

## 4. Database Backup Strategy

### A. Automated Backup Script

**Create `scripts/backup_database.py`:**
```python
"""
Automated PostgreSQL database backup
"""
import os
import subprocess
from datetime import datetime
from pathlib import Path

# Configuration
BACKUP_DIR = Path(r"C:\SilverFox\Backups\Database")
DB_NAME = "dealership_db"
DB_USER = "postgres"
POSTGRES_BIN = r"C:\Program Files\PostgreSQL\16\bin"
RETENTION_DAYS = 30  # Keep backups for 30 days

def backup_database():
    """Create database backup"""
    # Create backup directory
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"backup_{DB_NAME}_{timestamp}.sql"

    # Create backup using pg_dump
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

    print(f"[BACKUP] Starting database backup...")
    print(f"[BACKUP] File: {backup_file}")

    try:
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            print(f"[BACKUP] SUCCESS - {size_mb:.2f} MB")
            cleanup_old_backups()
            return True
        else:
            print(f"[BACKUP] ERROR: {result.stderr}")
            return False

    except Exception as e:
        print(f"[BACKUP] EXCEPTION: {e}")
        return False

def cleanup_old_backups():
    """Remove backups older than retention period"""
    from datetime import timedelta

    cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)

    for backup in BACKUP_DIR.glob("backup_*.sql"):
        if datetime.fromtimestamp(backup.stat().st_mtime) < cutoff_date:
            print(f"[CLEANUP] Removing old backup: {backup.name}")
            backup.unlink()

if __name__ == "__main__":
    backup_database()
```

**Schedule daily backups (Task Scheduler):**
```batch
REM Daily backup at 2 AM
schtasks /create /tn "Silver Fox DB Backup" /tr "python C:\path\to\scripts\backup_database.py" /sc daily /st 02:00 /ru SYSTEM
```

---

## 5. Production Deployment Checklist

### Pre-Deployment
- [ ] Install PostgreSQL 16
- [ ] Install Python 3.11+
- [ ] Create `.env` file with production credentials
- [ ] Update all dependencies: `pip install -r requirements.txt`
- [ ] Run database schema setup (all SQL files in order)
- [ ] Test database connection
- [ ] Configure firewall rules (allow port 5000 locally only)

### Deployment Steps
1. **Install Dependencies**
   ```batch
   pip install -r web_gui\requirements.txt
   ```

2. **Configure Environment**
   - Copy `.env.example` to `.env`
   - Update database credentials
   - Set secure passwords

3. **Test Production Server**
   ```batch
   python web_gui\production_server.py
   ```
   - Verify http://localhost:5000 works
   - Test order processing workflow
   - Check logs for errors

4. **Install Windows Service** (choose NSSM or Task Scheduler)
   ```batch
   install_service.bat
   net start SilverFoxOrderProcessing
   ```

5. **Configure Database Backups**
   ```batch
   schtasks /create /tn "Silver Fox DB Backup" /tr "python scripts\backup_database.py" /sc daily /st 02:00
   ```

6. **Verify Production Operation**
   - [ ] Service starts automatically
   - [ ] Web interface accessible
   - [ ] Database queries working
   - [ ] Order processing functional
   - [ ] QR code generation working
   - [ ] Logs being written correctly

### Post-Deployment
- [ ] Document server credentials (secure location)
- [ ] Test backup restoration procedure
- [ ] Monitor logs for first 48 hours
- [ ] Create operations manual for daily use
- [ ] Schedule monthly maintenance window

---

## 6. Security Hardening

### Application Security
- **Firewall**: Block external access to port 5000
- **Passwords**: Use strong database passwords (20+ characters)
- **File Permissions**: Restrict access to config files
- **Logs**: Rotate and secure log files

### Database Security
```sql
-- Create restricted application user
CREATE USER silverfox_app WITH PASSWORD 'secure_password_here';
GRANT CONNECT ON DATABASE dealership_db TO silverfox_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO silverfox_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO silverfox_app;

-- Revoke unnecessary permissions
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
```

### Windows Security
- Run service as dedicated user (not Administrator)
- Enable Windows Defender
- Keep Windows Updated
- Disable unnecessary network services

---

## 7. Monitoring and Maintenance

### Log Monitoring
**Location:** `logs/`
- `service_output.log` - Service stdout
- `service_error.log` - Service stderr
- `order_processing.log` - Application logs
- `web_gui.log` - Web interface logs

### Health Checks
**Create `scripts/health_check.py`:**
```python
import requests
import sys

def check_health():
    try:
        response = requests.get('http://localhost:5000/api/test-database', timeout=5)
        if response.status_code == 200:
            print("[OK] Service is healthy")
            return 0
        else:
            print(f"[ERROR] Service returned {response.status_code}")
            return 1
    except Exception as e:
        print(f"[ERROR] Service unavailable: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(check_health())
```

**Schedule health checks:**
```batch
schtasks /create /tn "Silver Fox Health Check" /tr "python scripts\health_check.py" /sc hourly /ru SYSTEM
```

### Performance Monitoring
- Monitor database size: `SELECT pg_size_pretty(pg_database_size('dealership_db'));`
- Check connection pool usage in logs
- Monitor disk space in `C:\SilverFox\`
- Review slow query logs

---

## 8. Troubleshooting

### Service Won't Start
1. Check logs: `logs/service_error.log`
2. Verify Python path in service config
3. Test manually: `python web_gui\production_server.py`
4. Check database connectivity

### Database Connection Errors
1. Verify PostgreSQL service running: `sc query postgresql-x64-16`
2. Test connection: `psql -U postgres -d dealership_db`
3. Check `.env` credentials
4. Review firewall settings

### Performance Issues
1. Check database indexes
2. Monitor connection pool size
3. Review slow query logs
4. Increase FLASK_THREADS if needed

---

## 9. Production File Structure

```
bulletproof_package/
├── .env                          # Environment variables (DO NOT COMMIT)
├── .env.example                  # Template for deployment
├── web_gui/
│   ├── production_server.py      # Production WSGI entry point
│   ├── app.py                    # Flask application
│   └── requirements.txt          # Updated with waitress
├── scripts/
│   ├── backup_database.py        # Automated backups
│   ├── health_check.py          # Service monitoring
│   └── database_config.py       # Updated with env vars
├── logs/                         # Application logs
├── install_service.bat           # Service installation
└── start_production_service.bat  # Manual startup script
```

---

## 10. Next Steps

1. **Review this guide** with stakeholders
2. **Test in staging environment** before production
3. **Create deployment schedule** (weekend deployment recommended)
4. **Train operators** on production system
5. **Document rollback procedures** in case of issues

---

**System Status**: Ready for production packaging
**Estimated Deployment Time**: 2-3 hours
**Risk Level**: Low (comprehensive testing completed)
