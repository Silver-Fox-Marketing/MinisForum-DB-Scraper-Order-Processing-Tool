@echo off
REM ============================================================================
REM Silver Fox Order Processing - Version 2.1.1 Hotfix Deployment
REM Critical Fix: LIST order dealership filtering
REM ============================================================================

echo.
echo ========================================================================
echo  Silver Fox Order Processing System
echo  Hotfix Deployment: v2.1.1
echo ========================================================================
echo.
echo  CRITICAL FIX: LIST order dealership filtering for vehicle types
echo               and stock requirements
echo.
echo  This update fixes:
echo  - LIST orders now respect dealership vehicle_types config
echo  - Stock number filtering (excludes missing/invalid stock numbers)
echo  - Filtering applied in UI preview phase
echo.
echo ========================================================================
echo.

REM Configuration
set PROD_PATH=C:\SilverFox
set DEV_PATH=C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package
set BACKUP_DIR=%PROD_PATH%\backups\v2.1.1_hotfix_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set CRITICAL_FILE=scripts\correct_order_processing.py

echo [STEP 1/6] Verifying production path...
if not exist "%PROD_PATH%" (
    echo [ERROR] Production path not found: %PROD_PATH%
    echo Please verify the production installation path.
    pause
    exit /b 1
)
echo [OK] Production path verified

echo.
echo [STEP 2/6] Creating backup...
mkdir "%BACKUP_DIR%"
copy "%PROD_PATH%\%CRITICAL_FILE%" "%BACKUP_DIR%\correct_order_processing.py.backup"
if errorlevel 1 (
    echo [ERROR] Backup failed!
    pause
    exit /b 1
)
echo [OK] Backup created: %BACKUP_DIR%

echo.
echo [STEP 3/6] Copying updated file from development...
copy /Y "%DEV_PATH%\%CRITICAL_FILE%" "%PROD_PATH%\%CRITICAL_FILE%"
if errorlevel 1 (
    echo [ERROR] File copy failed!
    echo [ROLLBACK] Restoring from backup...
    copy /Y "%BACKUP_DIR%\correct_order_processing.py.backup" "%PROD_PATH%\%CRITICAL_FILE%"
    pause
    exit /b 1
)
echo [OK] Updated file copied successfully

echo.
echo [STEP 4/6] Stopping production server...
echo NOTE: You may need to manually stop the server if it's running as a service
echo       or in a separate terminal window.
echo.
pause

echo.
echo [STEP 5/6] Deployment complete! Updated file:
echo     %PROD_PATH%\%CRITICAL_FILE%
echo.
echo [STEP 6/6] Next steps:
echo     1. Start the production server
echo     2. Test LIST order functionality
echo     3. Verify filtering is working correctly
echo.
echo ========================================================================
echo  ROLLBACK INSTRUCTIONS (if needed):
echo ========================================================================
echo  If you encounter issues, restore the backup:
echo.
echo  copy /Y "%BACKUP_DIR%\correct_order_processing.py.backup" ^
echo           "%PROD_PATH%\%CRITICAL_FILE%"
echo.
echo  Then restart the server.
echo ========================================================================
echo.

echo Deployment script completed!
echo Backup location: %BACKUP_DIR%
echo.
pause
