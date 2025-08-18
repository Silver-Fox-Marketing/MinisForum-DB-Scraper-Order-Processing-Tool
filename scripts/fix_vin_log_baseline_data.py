#!/usr/bin/env python3
"""
Fix VIN Log Baseline Data
========================
Updates VIN log data to show proper baseline values:
- Keep existing order numbers (42087, BASELINE, etc.)
- Set processed_date to NULL or a baseline date
- Update order_type to 'BASELINE' instead of 'HISTORICAL'
"""

import sys
from pathlib import Path
from datetime import date

# Add project paths
current_file = Path(__file__).resolve()
scripts_dir = current_file.parent
sys.path.insert(0, str(scripts_dir))

from database_connection import db_manager

def fix_vin_log_baseline_data():
    """Update VIN log data with proper baseline values"""
    
    try:
        # Get all VIN log tables
        tables = db_manager.execute_query("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name LIKE '%_vin_log'
            ORDER BY table_name
        """)
        
        print(f"Found {len(tables)} VIN log tables to update")
        
        total_updated = 0
        
        for table_info in tables:
            table_name = table_info['table_name']
            dealership_name = table_name.replace('_vin_log', '').replace('_', ' ').title()
            
            print(f"\nProcessing: {dealership_name} ({table_name})")
            
            # Get current count
            count_result = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
            current_count = count_result[0]['count']
            
            if current_count == 0:
                print(f"  No records found in {table_name}")
                continue
            
            # Update the records to baseline values
            # Use January 1, 2025 as baseline date
            update_query = f"""
                UPDATE {table_name} 
                SET 
                    processed_date = '2025-01-01',
                    order_type = 'BASELINE',
                    template_type = NULL
                WHERE order_type = 'HISTORICAL' OR processed_date = CURRENT_DATE
            """
            
            # Execute the update
            db_manager.execute_query(update_query)
            
            # Verify the update
            verification = db_manager.execute_query(f"""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN order_type = 'BASELINE' THEN 1 END) as baseline_records,
                    COUNT(CASE WHEN processed_date = '2025-01-01' THEN 1 END) as baseline_date_records,
                    array_agg(DISTINCT order_number) as unique_order_numbers
                FROM {table_name}
                LIMIT 1
            """)
            
            if verification:
                result = verification[0]
                print(f"  SUCCESS: Updated {table_name}:")
                print(f"     Total records: {result['total_records']}")
                print(f"     Baseline records: {result['baseline_records']}")
                print(f"     Records with baseline date (2025-01-01): {result['baseline_date_records']}")
                
                order_numbers = result['unique_order_numbers']
                if order_numbers:
                    # Limit display to first 5 order numbers
                    display_numbers = order_numbers[:5] if len(order_numbers) > 5 else order_numbers
                    remaining = len(order_numbers) - len(display_numbers)
                    print(f"     Order numbers: {', '.join(map(str, display_numbers))}", end="")
                    if remaining > 0:
                        print(f" (and {remaining} more)")
                    else:
                        print()
                
                total_updated += result['total_records']
            
        print(f"\nSUCCESS: Successfully updated {total_updated} total VIN records across {len(tables)} dealerships")
        print("\nChanges made:")
        print("  - Set processed_date to 2025-01-01 (baseline date)")
        print("  - Changed order_type from 'HISTORICAL' to 'BASELINE'")
        print("  - Kept existing order numbers intact")
        print("  - Removed template_type values (set to NULL)")
        
    except Exception as e:
        print(f"Error updating VIN log data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_vin_log_baseline_data()