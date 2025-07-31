#!/usr/bin/env python3
"""
Post-Installation Test Suite
===========================
Validates that the database system is working correctly after installation.
"""

import psycopg2
import sys
import os
from datetime import datetime

def test_database_connection():
    """Test basic database connectivity"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="minisforum_dealership_db",
            user="postgres",
            password=input("Enter PostgreSQL password: ")
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print(f"✅ Database connection: SUCCESS")
        print(f"   Version: {version[:50]}...")
        return True
    except Exception as e:
        print(f"❌ Database connection: FAILED - {e}")
        return False

def test_tables_exist():
    """Test that all required tables exist"""
    required_tables = [
        'raw_vehicle_data',
        'normalized_vehicle_data',
        'vin_history', 
        'dealership_configs'
    ]
    
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="minisforum_dealership_db",
            user="postgres",
            password=os.getenv('PGPASSWORD', input("Enter PostgreSQL password: "))
        )
        cursor = conn.cursor()
        
        for table in required_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            print(f"✅ Table {table}: EXISTS ({count} records)")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Table check: FAILED - {e}")
        return False

def test_dealership_configs():
    """Test dealership configurations"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="minisforum_dealership_db", 
            user="postgres",
            password=os.getenv('PGPASSWORD', input("Enter PostgreSQL password: "))
        )
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM dealership_configs WHERE is_active = true;")
        active_configs = cursor.fetchone()[0]
        
        cursor.execute("SELECT name FROM dealership_configs LIMIT 5;")
        sample_names = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        if active_configs >= 30:
            print(f"✅ Dealership configs: {active_configs} active configurations")
            print(f"   Sample: {', '.join(sample_names)}")
            return True
        else:
            print(f"❌ Dealership configs: Only {active_configs} found (expected 30+)")
            return False
    except Exception as e:
        print(f"❌ Dealership config check: FAILED - {e}")
        return False

def main():
    print("🚀 POST-INSTALLATION TEST SUITE")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Table Structure", test_tables_exist),
        ("Dealership Configs", test_dealership_configs)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        if test_func():
            passed += 1
    
    print(f"\n{'='*50}")
    print(f"🏆 RESULTS: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("✅ SYSTEM IS READY FOR PRODUCTION!")
        return 0
    else:
        print("❌ Issues found. Please review and fix before using.")
        return 1

if __name__ == "__main__":
    exit(main())
