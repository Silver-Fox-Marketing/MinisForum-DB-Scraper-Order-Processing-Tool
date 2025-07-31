#!/usr/bin/env python3
"""
Dependency Validation Script
===========================

Validates all Python dependencies and system requirements before running
the MinisForum database system.

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import sys
import os
import importlib
from pathlib import Path

# Required packages for the system
REQUIRED_PACKAGES = [
    ('psycopg2', 'psycopg2-binary', 'PostgreSQL database adapter'),
    ('pandas', 'pandas', 'Data processing and CSV handling'),
    ('requests', 'requests', 'HTTP requests for QR generation'),
    ('numpy', 'numpy', 'Numerical computing (pandas dependency)'),
    ('flask', 'Flask', 'Web framework for GUI'),
    ('flask_socketio', 'Flask-SocketIO', 'Web GUI real-time features'),
    ('schedule', 'schedule', 'Task scheduling'),
    ('psutil', 'psutil', 'System monitoring'),
]

WEB_GUI_PACKAGES = [
    ('eventlet', 'eventlet', 'Web server WSGI'),
    ('socketio', 'python-socketio', 'SocketIO implementation'),
]

def check_python_version():
    """Check if Python version is compatible"""
    print("Checking Python version...")
    
    if sys.version_info < (3, 8):
        print(f"✗ Python 3.8+ required, found {sys.version}")
        return False
    else:
        print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        return True

def check_package(import_name, package_name, description):
    """Check if a package can be imported"""
    try:
        importlib.import_module(import_name)
        print(f"✓ {package_name} - {description}")
        return True
    except ImportError:
        print(f"✗ {package_name} - {description} (MISSING)")
        return False

def check_database_config():
    """Check database configuration"""
    print("\nChecking database configuration...")
    
    try:
        # Try to import database config
        sys.path.insert(0, str(Path(__file__).parent))
        from database_config import config
        print("✓ Database configuration loaded")
        
        # Check if password is configured
        if hasattr(config, 'password') and config.password:
            print("✓ Database password configured")
        else:
            print("⚠ Database password not set - using default")
        
        return True
    except Exception as e:
        print(f"✗ Database configuration error: {e}")
        return False

def check_file_structure():
    """Check if all required files exist"""
    print("\nChecking file structure...")
    
    base_path = Path(__file__).parent
    required_files = [
        'database_connection.py',
        'csv_importer_complete.py',
        'order_processing_integration.py',
        'qr_code_generator.py',
        'data_exporter.py',
        'test_complete_pipeline.py',
    ]
    
    missing_files = []
    for file in required_files:
        file_path = base_path / file
        if file_path.exists():
            print(f"✓ {file}")
        else:
            print(f"✗ {file} (MISSING)")
            missing_files.append(file)
    
    return len(missing_files) == 0

def main():
    """Main validation function"""
    print("=" * 60)
    print("MINISFORUM DATABASE DEPENDENCY VALIDATION")
    print("=" * 60)
    
    all_good = True
    
    # Check Python version
    if not check_python_version():
        all_good = False
    
    print("\nChecking core dependencies...")
    missing_packages = []
    
    # Check required packages
    for import_name, package_name, description in REQUIRED_PACKAGES:
        if not check_package(import_name, package_name, description):
            missing_packages.append(package_name)
            all_good = False
    
    print("\nChecking web GUI dependencies...")
    web_missing = []
    
    # Check web GUI packages
    for import_name, package_name, description in WEB_GUI_PACKAGES:
        if not check_package(import_name, package_name, description):
            web_missing.append(package_name)
    
    # Check file structure
    if not check_file_structure():
        all_good = False
    
    # Check database config
    if not check_database_config():
        all_good = False
    
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    
    if all_good and len(web_missing) == 0:
        print("🎉 ALL CHECKS PASSED - SYSTEM READY FOR DEPLOYMENT")
        print("\nYou can now:")
        print("  1. Run the database system: python test_complete_pipeline.py")
        print("  2. Start the web GUI: cd ../web_gui && python app.py")
        return True
    
    elif all_good and len(web_missing) > 0:
        print("⚠️  CORE SYSTEM READY - WEB GUI DEPENDENCIES MISSING")
        print("\nCore database functions will work, but web GUI may have issues.")
        print("To install missing web GUI packages:")
        print(f"pip install {' '.join(web_missing)}")
        return True
    
    else:
        print("❌ CRITICAL DEPENDENCIES MISSING - DO NOT DEPLOY")
        
        if missing_packages:
            print("\nTo install missing core packages:")
            print(f"pip install {' '.join(missing_packages)}")
        
        if web_missing:
            print("\nTo install missing web GUI packages:")
            print(f"pip install {' '.join(web_missing)}")
        
        print("\nOr install all dependencies:")
        print("pip install -r requirements.txt")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)