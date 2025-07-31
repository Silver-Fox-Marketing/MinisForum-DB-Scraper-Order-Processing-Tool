@echo off
echo Starting MinisForum Database Web GUI...
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install requirements if needed
echo Installing Python dependencies...
pip install -r requirements.txt

REM Start the Flask application
echo.
echo Starting web server on http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

python app.py

pause