@echo off
echo Starting Silver Fox Order Processing Server...
echo.

REM Set Python path
set PYTHON_PATH=C:\Users\Workstation_1\AppData\Local\Programs\Python\Python311\python.exe

REM Check if Python exists at the specified path
if not exist "%PYTHON_PATH%" (
    echo Error: Python not found at %PYTHON_PATH%
    pause
    exit /b 1
)

REM Start the Flask application
echo.
echo Starting web server on http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

"%PYTHON_PATH%" app.py

pause