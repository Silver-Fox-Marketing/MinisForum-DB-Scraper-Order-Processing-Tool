#!/usr/bin/env python3
"""
Test CSV Import Integration
===========================
Verifies that CSV imports properly create scraper import records
"""

import sys
from pathlib import Path

# Add project paths
current_file = Path(__file__).resolve()
scripts_dir = current_file.parent
sys.path.insert(0, str(scripts_dir))

from database_connection import db_manager
from scraper_import_manager import import_manager

def test_import_integration():
    """Test the scraper import integration"""
    print("=== CSV Import Integration Test ===")
    
    # Check current scraper imports
    print("\n1. Current scraper imports:")
    try:
        imports = import_manager.get_import_summary(limit=10)
        if imports:
            for imp in imports:
                print(f"   Import {imp['import_id']}: {imp['import_source']} - {imp['total_vehicles']} vehicles - Status: {imp['status']}")
        else:
            print("   No imports found")
    except Exception as e:
        print(f"   Error getting imports: {e}")
    
    # Check raw vehicle data with import_id
    print("\n2. Recent raw vehicle data with import_id:")
    try:
        recent_data = db_manager.execute_query("""
            SELECT import_id, location, COUNT(*) as count, is_archived
            FROM raw_vehicle_data 
            WHERE import_id IS NOT NULL
            GROUP BY import_id, location, is_archived
            ORDER BY import_id DESC
            LIMIT 10
        """)
        
        if recent_data:
            for row in recent_data:
                print(f"   Import {row['import_id']}: {row['location']} - {row['count']} vehicles - Archived: {row['is_archived']}")
        else:
            print("   No data with import_id found")
    except Exception as e:
        print(f"   Error getting raw data: {e}")
    
    # Check data without import_id (legacy data)
    print("\n3. Data without import_id (legacy):")
    try:
        legacy_count = db_manager.execute_query("""
            SELECT COUNT(*) as count
            FROM raw_vehicle_data 
            WHERE import_id IS NULL
        """)
        
        if legacy_count:
            print(f"   {legacy_count[0]['count']} records without import_id")
        else:
            print("   No legacy data found")
    except Exception as e:
        print(f"   Error checking legacy data: {e}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_import_integration()