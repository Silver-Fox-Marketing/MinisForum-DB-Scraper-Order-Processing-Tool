@echo off
echo.
echo ========================================
echo  SILVER FOX STRESS TEST RUNNER
echo ========================================
echo.

REM Change to the correct directory
cd /d "%~dp0"

REM Check if we're in the right directory
if not exist "scripts\comprehensive_order_stress_test.py" (
    echo ERROR: Cannot find stress test script
    echo Current directory: %CD%
    echo Expected: bulletproof_package directory
    echo.
    pause
    exit /b 1
)

echo Starting comprehensive stress test...
echo.

REM Try different Python commands
set PYTHON_CMD=

REM Try python3 first
python3 --version >nul 2>&1
if %ERRORLEVEL% == 0 (
    set PYTHON_CMD=python3
    echo Using python3
    goto :run_tests
)

REM Try python
python --version >nul 2>&1
if %ERRORLEVEL% == 0 (
    set PYTHON_CMD=python
    echo Using python
    goto :run_tests
)

REM Try py launcher
py --version >nul 2>&1
if %ERRORLEVEL% == 0 (
    set PYTHON_CMD=py
    echo Using py launcher
    goto :run_tests
)

REM Check specific paths
if exist "C:\Python39\python.exe" (
    set PYTHON_CMD=C:\Python39\python.exe
    echo Using C:\Python39\python.exe
    goto :run_tests
)

if exist "C:\Python38\python.exe" (
    set PYTHON_CMD=C:\Python38\python.exe
    echo Using C:\Python38\python.exe
    goto :run_tests
)

echo ERROR: No Python installation found
echo Please install Python or add it to your PATH
echo.
pause
exit /b 1

:run_tests
echo.
echo ========================================
echo  RUNNING MINIMAL WEB GUI TEST
echo ========================================
echo.

echo Starting minimal web GUI on port 5001...
echo Access at: http://127.0.0.1:5001/test
echo.

cd web_gui
start "Minimal GUI" %PYTHON_CMD% app_minimal.py

echo Waiting 5 seconds for server to start...
timeout /t 5 /nobreak > nul

echo.
echo ========================================
echo  RUNNING COMPREHENSIVE STRESS TESTS
echo ========================================
echo.

cd ..\scripts
%PYTHON_CMD% comprehensive_order_stress_test.py

echo.
echo ========================================
echo  STRESS TEST COMPLETE
echo ========================================
echo.

echo Check the minimal web GUI at: http://127.0.0.1:5001/test
echo.
pause