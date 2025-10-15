# Update & Patch Deployment Strategy
## Silver Fox Order Processing System

---

## Current Architecture Limitations

### Issues with Basic Service Deployment:
1. **File Locking**: Windows Service locks `.py` files - can't replace while running
2. **No Versioning**: Direct file replacement = no rollback capability
3. **Downtime Required**: Must stop service to update files
4. **Database Schema**: No migration system for schema changes
5. **Testing Gap**: No staged deployment/testing process

---

## Recommended Production Architecture

### Option 1: Version-Based Deployment (Recommended)

**Directory Structure:**
```
C:\SilverFox\
├── current -> releases/v2.1.0/          # Symlink to current version
├── releases/
│   ├── v2.0.0/                          # Previous version (rollback ready)
│   ├── v2.1.0/                          # Current production
│   └── v2.2.0/                          # New version (staged)
├── shared/
│   ├── .env                             # Shared environment config
│   ├── logs/                            # Shared logs directory
│   ├── orders/                          # Shared orders output
│   └── uploads/                         # Shared upload directory
└── backups/
    ├── database/                        # Database backups
    └── code/                            # Code rollback archives
```

**Benefits:**
- ✅ Zero-downtime deployments (prepare new version, then switch symlink)
- ✅ Instant rollback (just change symlink back)
- ✅ Multiple versions can coexist
- ✅ Safe testing before cutover

### Option 2: Blue-Green Deployment

**Two Complete Environments:**
```
C:\SilverFox\
├── blue/                    # Production environment A
│   └── bulletproof_package/
├── green/                   # Production environment B
│   └── bulletproof_package/
├── shared/                  # Shared data/config
└── nginx/                   # Reverse proxy to switch environments
```

**Benefits:**
- ✅ True zero-downtime
- ✅ Full testing in production-like environment
- ✅ Instant rollback via proxy switch
- ❌ More complex, requires reverse proxy

---

## Recommended: Version-Based Deployment

### Implementation

#### 1. Create Deployment Script

**Create `deploy_update.bat`:**
```batch
@echo off
REM Silver Fox Update Deployment Script
REM Usage: deploy_update.bat <version>

set VERSION=%1
if "%VERSION%"=="" (
    echo Error: Version number required
    echo Usage: deploy_update.bat 2.2.0
    exit /b 1
)

set BASE_DIR=C:\SilverFox
set RELEASES_DIR=%BASE_DIR%\releases
set NEW_VERSION_DIR=%RELEASES_DIR%\v%VERSION%
set SERVICE_NAME=SilverFoxOrderProcessing

echo [DEPLOY] Starting deployment of version %VERSION%
echo.

REM 1. Verify new version exists
if not exist "%NEW_VERSION_DIR%" (
    echo [ERROR] Version directory not found: %NEW_VERSION_DIR%
    exit /b 1
)

REM 2. Run pre-deployment tests
echo [TEST] Running pre-deployment tests...
python "%NEW_VERSION_DIR%\scripts\health_check.py"
if errorlevel 1 (
    echo [ERROR] Health check failed
    exit /b 1
)

REM 3. Backup current version
echo [BACKUP] Creating backup of current version...
set BACKUP_DIR=%BASE_DIR%\backups\code\backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
mkdir "%BACKUP_DIR%"
xcopy /E /I /Y "%BASE_DIR%\current" "%BACKUP_DIR%"

REM 4. Backup database
echo [BACKUP] Backing up database...
python "%BASE_DIR%\current\scripts\backup_database.py"

REM 5. Stop service
echo [SERVICE] Stopping service...
net stop %SERVICE_NAME%
timeout /t 5 /nobreak > nul

REM 6. Run database migrations (if any)
if exist "%NEW_VERSION_DIR%\migrations\upgrade.sql" (
    echo [MIGRATION] Running database migrations...
    psql -U postgres -d dealership_db -f "%NEW_VERSION_DIR%\migrations\upgrade.sql"
    if errorlevel 1 (
        echo [ERROR] Database migration failed - ROLLING BACK
        goto :rollback
    )
)

REM 7. Update symlink to new version
echo [DEPLOY] Switching to new version...
rmdir "%BASE_DIR%\current"
mklink /D "%BASE_DIR%\current" "%NEW_VERSION_DIR%"

REM 8. Start service
echo [SERVICE] Starting service with new version...
net start %SERVICE_NAME%
timeout /t 10 /nobreak > nul

REM 9. Verify deployment
echo [VERIFY] Verifying deployment...
python "%BASE_DIR%\current\scripts\health_check.py"
if errorlevel 1 (
    echo [ERROR] Post-deployment health check failed - ROLLING BACK
    goto :rollback
)

echo.
echo [SUCCESS] Deployment complete!
echo [SUCCESS] Version %VERSION% is now live
exit /b 0

:rollback
echo.
echo [ROLLBACK] Deployment failed - rolling back to previous version...
net stop %SERVICE_NAME%
rmdir "%BASE_DIR%\current"
mklink /D "%BASE_DIR%\current" "%BACKUP_DIR%"
net start %SERVICE_NAME%
echo [ROLLBACK] Rollback complete - system restored to previous version
exit /b 1
```

#### 2. Update Preparation Script

**Create `prepare_update.bat`:**
```batch
@echo off
REM Prepare new version for deployment
REM Usage: prepare_update.bat <version> <source_zip>

set VERSION=%1
set SOURCE_ZIP=%2

if "%VERSION%"=="" (
    echo Usage: prepare_update.bat 2.2.0 update.zip
    exit /b 1
)

set BASE_DIR=C:\SilverFox
set NEW_DIR=%BASE_DIR%\releases\v%VERSION%

echo [PREPARE] Preparing version %VERSION% for deployment...

REM 1. Create version directory
mkdir "%NEW_DIR%"

REM 2. Extract update package
echo [EXTRACT] Extracting update package...
powershell -command "Expand-Archive -Path '%SOURCE_ZIP%' -DestinationPath '%NEW_DIR%' -Force"

REM 3. Copy shared configuration
echo [CONFIG] Copying shared configuration...
copy "%BASE_DIR%\shared\.env" "%NEW_DIR%\.env"

REM 4. Create symlinks to shared directories
echo [LINKS] Creating links to shared directories...
mklink /D "%NEW_DIR%\logs" "%BASE_DIR%\shared\logs"
mklink /D "%NEW_DIR%\orders" "%BASE_DIR%\shared\orders"
mklink /D "%NEW_DIR%\uploads" "%BASE_DIR%\shared\uploads"

REM 5. Install dependencies
echo [DEPS] Installing Python dependencies...
cd "%NEW_DIR%\web_gui"
pip install -r requirements.txt --quiet

REM 6. Run tests
echo [TEST] Running test suite...
python "%NEW_DIR%\scripts\run_tests.py"
if errorlevel 1 (
    echo [ERROR] Tests failed - review before deploying
    exit /b 1
)

echo.
echo [SUCCESS] Version %VERSION% prepared successfully
echo [READY] Run 'deploy_update.bat %VERSION%' to deploy
exit /b 0
```

#### 3. Rollback Script

**Create `rollback_update.bat`:**
```batch
@echo off
REM Rollback to previous version
REM Usage: rollback_update.bat <version>

set VERSION=%1
set SERVICE_NAME=SilverFoxOrderProcessing
set BASE_DIR=C:\SilverFox

echo [ROLLBACK] Rolling back to version %VERSION%...

REM Stop service
net stop %SERVICE_NAME%

REM Switch symlink
rmdir "%BASE_DIR%\current"
mklink /D "%BASE_DIR%\current" "%BASE_DIR%\releases\v%VERSION%"

REM Rollback database if needed
if exist "%BASE_DIR%\releases\v%VERSION%\migrations\downgrade.sql" (
    echo [DB] Rolling back database changes...
    psql -U postgres -d dealership_db -f "%BASE_DIR%\releases\v%VERSION%\migrations\downgrade.sql"
)

REM Start service
net start %SERVICE_NAME%

echo [SUCCESS] Rolled back to version %VERSION%
exit /b 0
```

---

## Database Schema Updates

### Migration System

**Create `migrations/` directory structure:**
```
migrations/
├── v2.1.0_to_v2.2.0/
│   ├── upgrade.sql          # Schema changes to apply
│   ├── downgrade.sql        # Rollback changes
│   └── README.md            # Migration notes
└── migration_log.txt        # Track applied migrations
```

**Example Migration (`migrations/v2.1.0_to_v2.2.0/upgrade.sql`):**
```sql
-- Migration: Add maintenance tracking to Serra Honda
-- Version: 2.1.0 -> 2.2.0
-- Date: 2025-10-03

BEGIN;

-- Add new columns
ALTER TABLE serra_honda_ofallon_vin_log
ADD COLUMN IF NOT EXISTS maintenance_completed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS maintenance_date TIMESTAMP;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_serra_maintenance
ON serra_honda_ofallon_vin_log(maintenance_completed, maintenance_date);

-- Update migration log
INSERT INTO schema_migrations (version, applied_at, description)
VALUES ('2.2.0', CURRENT_TIMESTAMP, 'Add maintenance tracking to Serra Honda');

COMMIT;
```

**Downgrade script (`migrations/v2.1.0_to_v2.2.0/downgrade.sql`):**
```sql
-- Rollback migration: Remove maintenance tracking
-- Version: 2.2.0 -> 2.1.0

BEGIN;

-- Remove index
DROP INDEX IF EXISTS idx_serra_maintenance;

-- Remove columns
ALTER TABLE serra_honda_ofallon_vin_log
DROP COLUMN IF EXISTS maintenance_completed,
DROP COLUMN IF EXISTS maintenance_date;

-- Remove from migration log
DELETE FROM schema_migrations WHERE version = '2.2.0';

COMMIT;
```

---

## Update Workflow (Step-by-Step)

### Developer Workflow:

1. **Create Update Package**
   ```batch
   # On development machine
   git tag v2.2.0
   git archive --format=zip --output=update_v2.2.0.zip v2.2.0
   ```

2. **Transfer to Production Server**
   ```batch
   # Copy update_v2.2.0.zip to C:\SilverFox\updates\
   ```

3. **Prepare Update**
   ```batch
   cd C:\SilverFox
   prepare_update.bat 2.2.0 updates\update_v2.2.0.zip
   ```
   - Extracts files to `releases/v2.2.0/`
   - Copies shared config
   - Installs dependencies
   - Runs tests

4. **Review & Test**
   ```batch
   # Manual testing of new version
   cd C:\SilverFox\releases\v2.2.0\web_gui
   python production_server.py  # Test on different port
   ```

5. **Deploy Update**
   ```batch
   deploy_update.bat 2.2.0
   ```
   - Backs up current version + database
   - Stops service
   - Runs migrations
   - Switches to new version
   - Starts service
   - Verifies health

6. **Monitor**
   - Check logs: `C:\SilverFox\shared\logs\`
   - Verify functionality
   - Monitor for 24-48 hours

7. **Rollback if Needed**
   ```batch
   rollback_update.bat 2.1.0
   ```

---

## Patch Types & Strategies

### 1. **Hotfix (Critical Bug)**
- **Downtime**: ~30 seconds
- **Steps**: Prepare → Deploy → Verify
- **Rollback**: Instant (symlink switch)

### 2. **Feature Update**
- **Downtime**: ~1-2 minutes (includes migration)
- **Steps**: Prepare → Test → Deploy during maintenance window
- **Rollback**: Available (includes database rollback)

### 3. **Database Schema Change**
- **Downtime**: Depends on migration complexity
- **Steps**: Backup → Migrate → Deploy → Verify
- **Rollback**: Database downgrade script required

### 4. **Configuration Only**
- **Downtime**: None (edit `.env` in shared/)
- **Steps**: Edit config → Service auto-reloads
- **Rollback**: Edit config back

---

## Version Control Integration

### Git Workflow for Updates:

```bash
# Development
git checkout -b feature/maintenance-tracking
# ... make changes ...
git commit -m "Add maintenance tracking"
git push origin feature/maintenance-tracking

# Code review & merge to main
git checkout main
git merge feature/maintenance-tracking

# Create release
git tag -a v2.2.0 -m "Release 2.2.0: Maintenance tracking"
git push origin v2.2.0

# Package for deployment
git archive --format=zip --output=update_v2.2.0.zip v2.2.0
```

---

## Monitoring & Alerts

### Health Check Integration:

**Create `scripts/health_check.py` (enhanced):**
```python
import requests
import sys
import os
from datetime import datetime

def check_health():
    """Comprehensive health check"""
    checks = {
        'web_service': check_web_service(),
        'database': check_database(),
        'disk_space': check_disk_space(),
        'log_errors': check_recent_errors()
    }

    # Log results
    with open('C:/SilverFox/shared/logs/health_check.log', 'a') as f:
        f.write(f"{datetime.now()} - {checks}\n")

    # Return status
    if all(checks.values()):
        print("[OK] All systems healthy")
        return 0
    else:
        print(f"[ERROR] Health check failed: {checks}")
        return 1

def check_web_service():
    try:
        r = requests.get('http://localhost:5000/api/test-database', timeout=5)
        return r.status_code == 200
    except:
        return False

def check_database():
    from database_connection import db_manager
    return db_manager.test_connection()

def check_disk_space():
    import psutil
    disk = psutil.disk_usage('C:/')
    return disk.percent < 90  # Alert if >90% full

def check_recent_errors():
    # Check last 100 lines of logs for ERROR
    log_file = 'C:/SilverFox/shared/logs/service_error.log'
    if not os.path.exists(log_file):
        return True

    with open(log_file, 'r') as f:
        lines = f.readlines()[-100:]
        errors = [l for l in lines if 'ERROR' in l]
        return len(errors) < 5  # Alert if >5 errors in last 100 lines

if __name__ == "__main__":
    sys.exit(check_health())
```

---

## Initial Setup for Version-Based Deployment

### One-Time Migration Script:

**Create `migrate_to_versioned.bat`:**
```batch
@echo off
REM Migrate current installation to version-based deployment
set BASE_DIR=C:\SilverFox

echo [MIGRATE] Setting up version-based deployment structure...

REM 1. Create directory structure
mkdir "%BASE_DIR%\releases"
mkdir "%BASE_DIR%\shared\logs"
mkdir "%BASE_DIR%\shared\orders"
mkdir "%BASE_DIR%\shared\uploads"
mkdir "%BASE_DIR%\backups\database"
mkdir "%BASE_DIR%\backups\code"
mkdir "%BASE_DIR%\updates"

REM 2. Move current installation to v2.1.0
echo [MIGRATE] Moving current installation to releases/v2.1.0...
xcopy /E /I /Y "C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package" "%BASE_DIR%\releases\v2.1.0"

REM 3. Move .env to shared
move "%BASE_DIR%\releases\v2.1.0\.env" "%BASE_DIR%\shared\.env"

REM 4. Create symlinks
mklink /D "%BASE_DIR%\current" "%BASE_DIR%\releases\v2.1.0"
mklink "%BASE_DIR%\releases\v2.1.0\.env" "%BASE_DIR%\shared\.env"
mklink /D "%BASE_DIR%\releases\v2.1.0\logs" "%BASE_DIR%\shared\logs"
mklink /D "%BASE_DIR%\releases\v2.1.0\orders" "%BASE_DIR%\shared\orders"

echo [SUCCESS] Migration complete!
echo [NEXT] Update service to point to: %BASE_DIR%\current\web_gui\production_server.py
```

---

## Summary

### Version-Based Deployment Benefits:

✅ **Safe Updates**: Test before switching, instant rollback
✅ **Minimal Downtime**: 30-60 seconds for most updates
✅ **Database Migrations**: Structured upgrade/downgrade scripts
✅ **Audit Trail**: All versions preserved, full history
✅ **Rollback Ready**: Any version instantly available

### Update Process:
1. Package update → 2. Prepare & test → 3. Deploy (auto-backup) → 4. Verify → 5. Rollback if needed

**Recommended**: Implement version-based deployment **before** going to production for safest update path.
