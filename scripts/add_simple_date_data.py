#!/usr/bin/env python3
"""
Add Simple Date Test Data
=========================

Manually update some existing records with different import_timestamp values
to test date filtering functionality.

Author: Silver Fox Assistant  
Created: 2025-07-29
"""

import sys
from pathlib import Path
from database_connection import db_manager
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_timestamps_for_date_testing():
    """Update timestamps of existing records to create date spread"""
    
    try:
        print("\n" + "="*60)
        print(">> UPDATING TIMESTAMPS FOR DATE TESTING")
        print("="*60)
        
        # Update some BMW records to be 7 days ago
        seven_days_ago = datetime.now() - timedelta(days=7)
        result1 = db_manager.execute_query("""
            UPDATE raw_vehicle_data 
            SET import_timestamp = %s 
            WHERE make = 'BMW' 
            AND id IN (SELECT id FROM raw_vehicle_data WHERE make = 'BMW' LIMIT 50)
        """, (seven_days_ago,))
        
        # Update some Ford records to be 14 days ago
        fourteen_days_ago = datetime.now() - timedelta(days=14)
        result2 = db_manager.execute_query("""
            UPDATE raw_vehicle_data 
            SET import_timestamp = %s 
            WHERE make = 'Ford' 
            AND id IN (SELECT id FROM raw_vehicle_data WHERE make = 'Ford' LIMIT 50)
        """, (fourteen_days_ago,))
        
        # Update some Lincoln records to be 30 days ago
        thirty_days_ago = datetime.now() - timedelta(days=30)
        result3 = db_manager.execute_query("""
            UPDATE raw_vehicle_data 
            SET import_timestamp = %s 
            WHERE make = 'Lincoln' 
            AND id IN (SELECT id FROM raw_vehicle_data WHERE make = 'Lincoln' LIMIT 100)
        """, (thirty_days_ago,))
        
        print(f"[UPDATE] BMW records updated to {seven_days_ago.strftime('%Y-%m-%d')}")
        print(f"[UPDATE] Ford records updated to {fourteen_days_ago.strftime('%Y-%m-%d')}")
        print(f"[UPDATE] Lincoln records updated to {thirty_days_ago.strftime('%Y-%m-%d')}")
        
        # Get updated date range
        date_stats = db_manager.execute_query("""
            SELECT 
                MIN(import_timestamp) as earliest,
                MAX(import_timestamp) as latest,
                COUNT(DISTINCT DATE(import_timestamp)) as unique_dates,
                COUNT(*) as total_records
            FROM raw_vehicle_data
        """)
        
        if date_stats:
            stats = date_stats[0]
            print(f"\n[STATS] Date range: {stats['earliest']} to {stats['latest']}")
            print(f"[STATS] Unique dates: {stats['unique_dates']}")
            print(f"[STATS] Total records: {stats['total_records']}")
        
        # Show date distribution
        date_dist = db_manager.execute_query("""
            SELECT 
                DATE(import_timestamp) as date,
                COUNT(*) as count,
                STRING_AGG(DISTINCT make, ', ') as sample_makes
            FROM raw_vehicle_data 
            GROUP BY DATE(import_timestamp) 
            ORDER BY date DESC
        """)
        
        if date_dist:
            print("\n[DISTRIBUTION] Vehicles by date:")
            for row in date_dist:
                print(f"  {row['date']}: {row['count']} vehicles ({row['sample_makes'][:50]}...)")
        
        print("\n" + "="*60)
        print(">> DATE UPDATE COMPLETE!")
        print("="*60)
        print("Ready to test date filtering:")
        print("1. Search for 'BMW' and filter by last 7 days")
        print("2. Search for 'Ford' and filter by 14-20 days ago")
        print("3. Search for 'Lincoln' and filter by 30+ days ago")
        print("4. Use date range filters in the Data tab")
        print("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating timestamps: {e}")
        return False

if __name__ == "__main__":
    update_timestamps_for_date_testing()