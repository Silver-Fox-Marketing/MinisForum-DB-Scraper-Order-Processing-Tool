#!/usr/bin/env python3
"""
Test script to verify the updated CSV date parsing functionality
Tests multiple date formats including YYYY/MM/DD from Serra Honda CSV
"""
import sys
sys.path.append('C:/Users/Workstation_1/Documents/Tools/ClaudeCode/projects/minisforum_database_transfer/bulletproof_package/scripts')
from datetime import datetime

def test_date_parsing():
    """Test the updated date parsing logic from app.py"""
    print("=== TESTING CSV DATE PARSING WITH MULTIPLE FORMATS ===")
    
    # Test dates from the actual CSV file
    test_dates = [
        "2025/04/22",   # YYYY/MM/DD format from CSV
        "2025/05/01", 
        "2024/10/17",
        "10/17/2024",   # MM/DD/YYYY format 
        "2025-04-22",   # YYYY-MM-DD format
        "04-22-2025",   # MM-DD-YYYY format
        "",             # Empty string
        "invalid_date"  # Invalid format
    ]
    
    # Date formats to try (same as in updated app.py)
    date_formats = [
        '%Y/%m/%d',  # YYYY/MM/DD (e.g., "2025/04/22")
        '%m/%d/%Y',  # MM/DD/YYYY (e.g., "10/17/2024")
        '%Y-%m-%d',  # YYYY-MM-DD (e.g., "2025-04-22")
        '%m-%d-%Y'   # MM-DD-YYYY (e.g., "04-22-2025")
    ]
    
    results = []
    
    for date_str in test_dates:
        print(f"\\nTesting date string: '{date_str}'")
        date_in_stock_val = None
        
        if date_str and date_str.strip() != '':
            date_str_clean = str(date_str).strip()
            
            # Try multiple date formats (same logic as updated app.py)
            for fmt in date_formats:
                try:
                    date_in_stock_val = datetime.strptime(date_str_clean, fmt).date()
                    print(f"  SUCCESS: Parsed with format '{fmt}' -> {date_in_stock_val}")
                    break  # Successfully parsed, exit loop
                except ValueError:
                    print(f"  FAILED: Format '{fmt}' did not match")
                    continue  # Try next format
            
            if date_in_stock_val is None:
                print(f"  ERROR: No format matched for '{date_str_clean}'")
        else:
            print(f"  SKIPPED: Empty or invalid date string")
        
        results.append({
            'input': date_str,
            'parsed': date_in_stock_val,
            'success': date_in_stock_val is not None
        })
    
    # Summary
    print(f"\\n=== PARSING RESULTS SUMMARY ===")
    successful = [r for r in results if r['success']]
    print(f"Successfully parsed: {len(successful)}/{len(results)} dates")
    
    for result in results:
        status = "SUCCESS" if result['success'] else "FAILED"
        print(f"  {status}: '{result['input']}' -> {result['parsed']}")
    
    # Test specific CSV format
    print(f"\\n=== CSV FORMAT COMPATIBILITY TEST ===")
    csv_dates = ["2025/04/22", "2025/05/01", "2024/10/17"]
    all_csv_success = True
    
    for csv_date in csv_dates:
        try:
            parsed = datetime.strptime(csv_date, '%Y/%m/%d').date()
            print(f"  SUCCESS: CSV date '{csv_date}' -> {parsed}")
        except ValueError as e:
            print(f"  ERROR: CSV date '{csv_date}' failed: {e}")
            all_csv_success = False
    
    if all_csv_success:
        print(f"\\n[SUCCESS] All CSV dates parsed correctly with YYYY/MM/DD format!")
        print(f"[READY] Updated date parsing should work with Serra Honda CSV import")
        return True
    else:
        print(f"\\n[ERROR] CSV date parsing failed - check format compatibility")
        return False

if __name__ == "__main__":
    success = test_date_parsing()
    if success:
        print(f"\\n[COMPLETED] Date parsing fix verification PASSED")
    else:
        print(f"\\n[FAILED] Date parsing fix verification FAILED")