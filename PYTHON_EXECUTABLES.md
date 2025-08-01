# Python Executable Paths - Silver Fox Order Processing System

## Critical System Information

**Python executable locations for this Windows environment:**

### Primary Python Executables:
1. **Windows Store Python**: `C:\Users\Workstation_1\AppData\Local\Microsoft\WindowsApps\python.exe`
2. **Standard Python 3.11**: `C:\Users\Workstation_1\AppData\Local\Programs\Python\Python311\python.exe`

### Usage Notes:
- Always use full path when running Python scripts from Flask or other web applications
- The Windows Store version may have permission restrictions
- Python 3.11 installation is the preferred version for this project

### Flask Server Restart Commands:
```bash
# Navigate to web_gui directory
cd C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\web_gui

# Start with full Python path
C:\Users\Workstation_1\AppData\Local\Programs\Python\Python311\python.exe app.py
```

### Script Execution Commands:
```bash
# Order Processing Script
C:\Users\Workstation_1\AppData\Local\Programs\Python\Python311\python.exe scripts/correct_order_processing.py

# WebSocket Test Script
C:\Users\Workstation_1\AppData\Local\Programs\Python\Python311\python.exe test_websocket_connection.py
```

## Important Reminders:
- **Never use just `python`** - always use full path
- **Flask app.py requires full path** - server startup will fail otherwise
- **Background scraper processes need full path** - avoid "python executable not found" errors
- **Database schema fix requires full path** when running SQL scripts

## Real Scraper Integration Status:
✅ **BREAKTHROUGH ACHIEVED (August 1, 2025):**
- Real scraper system now working with proper Python paths
- WebSocket integration providing live progress updates
- 36 dealership scrapers successfully integrated
- Database pipeline 99% complete (final constraint fix pending)

## Environment Verification:
To verify Python installation and packages:
```bash
C:\Users\Workstation_1\AppData\Local\Programs\Python\Python311\python.exe --version
C:\Users\Workstation_1\AppData\Local\Programs\Python\Python311\python.exe -m pip list
```

## Recent Success Examples:
```bash
# Start Silver Fox Order Processing System v2.0
C:\Users\Workstation_1\AppData\Local\Programs\Python\Python311\python.exe app.py

# Expected Output:
# ✅ Socket.IO configuration valid  
# ✅ Scraper18Controller configured with SocketIO
# ✅ Scraper18WebController initialized with 36 dealerships
# * Running on http://127.0.0.1:5000
```

---
*Last Updated: August 1, 2025 - 4:15 PM*
*Project: Silver Fox Order Processing System v2.0*
*Status: Real Scraper Integration 99% Complete*