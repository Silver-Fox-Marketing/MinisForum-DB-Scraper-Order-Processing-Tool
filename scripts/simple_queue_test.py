#!/usr/bin/env python3
"""
Simple Queue Test
================

Simple test of the order queue system with template generation.

Author: Silver Fox Assistant
Created: 2025-07-29
"""

import os
import sys
from datetime import date
from pathlib import Path

# Add project paths
current_file = Path(__file__).resolve()
scripts_dir = current_file.parent
sys.path.insert(0, str(scripts_dir))

from database_connection import db_manager
from order_queue_manager import OrderQueueManager

def main():
    print("[START] Testing Order Queue System")
    print("=" * 50)
    
    # Clear the queue first
    today = date.today()
    db_manager.execute_query("DELETE FROM order_queue WHERE scheduled_date = %s", (today,))
    print("Queue cleared")
    
    queue_manager = OrderQueueManager()
    
    # Test 1: Create a simple order for Columbia Honda with Shortcut Pack template
    print("\n[ADD] Adding test order...")
    db_manager.execute_query("""
        INSERT INTO order_queue 
        (dealership_name, order_type, template_type, vehicle_types, scheduled_date, day_of_week)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, ('Columbia Honda', 'TEST', 'Shortcut Pack', ['new'], today, 'Test'))
    
    # Get the order
    orders = queue_manager.get_daily_queue(today)
    if not orders:
        print("[ERROR] No orders found")
        return
        
    order = orders[0]
    print(f"[OK] Order created: {order['dealership_name']} - {order['template_type']}")
    
    # Test 2: Process the order
    print("\n[PROCESS] Processing order...")
    result = queue_manager.process_queue_order(order['queue_id'])
    
    if result['success']:
        print(f"[SUCCESS] Order completed!")
        print(f"   Vehicles processed: {result['vehicles_processed']}")
        print(f"   QR codes generated: {result['qr_codes_generated']}")
        print(f"   CSV file: {result['csv_file']}")
        
        # Show CSV content
        if os.path.exists(result['csv_file']):
            print("\n[CSV] CSV Content Preview:")
            with open(result['csv_file'], 'r', encoding='utf-8') as f:
                lines = f.readlines()[:5]  # First 5 lines
                for i, line in enumerate(lines):
                    print(f"   {i+1}: {line.strip()}")
                    
            # Check if NEW prefix is being added
            if len(lines) > 1:
                data_line = lines[1].strip()
                if data_line.startswith('NEW'):
                    print("[OK] NEW prefix correctly added to year field!")
                else:
                    print("[WARNING] NEW prefix may not be working")
        
    else:
        print(f"[FAILED] {result.get('error', 'Unknown error')}")
    
    # Test 3: Show queue summary
    print("\n[SUMMARY] Final queue summary:")
    summary = queue_manager.get_queue_summary(today)
    print(f"   Total orders: {summary.get('total_orders', 0)}")
    print(f"   Completed: {summary.get('completed_orders', 0)}")
    print(f"   Completion rate: {summary.get('completion_percentage', 0)}%")

if __name__ == "__main__":
    main()