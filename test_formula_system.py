"""
Test script for dynamic concatenated field formula system
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from correct_order_processing import CorrectOrderProcessor

def test_formula_processing():
    """Test the _process_concatenated_formula method"""

    processor = CorrectOrderProcessor()

    # Test data matching the CSV files we've seen
    test_vehicle = {
        'yearmake': '2026 Porsche',
        'model': 'Macan',
        'stock': '2026 Macan - TLB40309',
        'raw_stock': 'TLB40309',
        'year': '2026',
        'make': 'Porsche'
    }

    print("=" * 60)
    print("Testing Dynamic Concatenated Field Formula System")
    print("=" * 60)
    print()

    # Test 1: Year Make - Stock Number (Porsche NEW template use case)
    print("Test 1: {yearmake} - {stock_number}")
    formula1 = "{yearmake} - {stock_number}"
    result1 = processor._process_concatenated_formula(formula1, test_vehicle)
    expected1 = "2026 Porsche - TLB40309"
    print(f"  Formula: {formula1}")
    print(f"  Result: {result1}")
    print(f"  Expected: {expected1}")
    print(f"  Status: {'[PASS]' if result1 == expected1 else '[FAIL]'}")
    print()

    # Test 2: Year Make - Model - Stock Number
    print("Test 2: {yearmake} - {model} - {stock_number}")
    formula2 = "{yearmake} - {model} - {stock_number}"
    result2 = processor._process_concatenated_formula(formula2, test_vehicle)
    expected2 = "2026 Porsche - Macan - TLB40309"
    print(f"  Formula: {formula2}")
    print(f"  Result: {result2}")
    print(f"  Expected: {expected2}")
    print(f"  Status: {'[PASS]' if result2 == expected2 else '[FAIL]'}")
    print()

    # Test 3: Year extraction
    print("Test 3: {year} {make}")
    formula3 = "{year} {make}"
    result3 = processor._process_concatenated_formula(formula3, test_vehicle)
    expected3 = "2026 Porsche"
    print(f"  Formula: {formula3}")
    print(f"  Result: {result3}")
    print(f"  Expected: {expected3}")
    print(f"  Status: {'[PASS]' if result3 == expected3 else '[FAIL]'}")
    print()

    # Test 4: Direct field access
    print("Test 4: {model} ({yearmake})")
    formula4 = "{model} ({yearmake})"
    result4 = processor._process_concatenated_formula(formula4, test_vehicle)
    expected4 = "Macan (2026 Porsche)"
    print(f"  Formula: {formula4}")
    print(f"  Result: {result4}")
    print(f"  Expected: {expected4}")
    print(f"  Status: {'[PASS]' if result4 == expected4 else '[FAIL]'}")
    print()

    # Test 5: Stock number extraction from full stock field
    print("Test 5: Stock number extraction from '2026 Macan - TLB40309'")
    test_vehicle_with_dash = {
        'stock': '2026 Macan - TLB40309',
        'yearmake': '2026 Porsche'
    }
    formula5 = "{yearmake} - {stock_number}"
    result5 = processor._process_concatenated_formula(formula5, test_vehicle_with_dash)
    expected5 = "2026 Porsche - TLB40309"
    print(f"  Formula: {formula5}")
    print(f"  Result: {result5}")
    print(f"  Expected: {expected5}")
    print(f"  Status: {'[PASS]' if result5 == expected5 else '[FAIL]'}")
    print()

    # Test 6: Stock number without dash separator
    print("Test 6: Stock number extraction from 'TLB40309' (no dash)")
    test_vehicle_no_dash = {
        'stock': 'TLB40309',
        'yearmake': '2026 Porsche'
    }
    formula6 = "{yearmake} - {stock_number}"
    result6 = processor._process_concatenated_formula(formula6, test_vehicle_no_dash)
    expected6 = "2026 Porsche - TLB40309"
    print(f"  Formula: {formula6}")
    print(f"  Result: {result6}")
    print(f"  Expected: {expected6}")
    print(f"  Status: {'[PASS]' if result6 == expected6 else '[FAIL]'}")
    print()

    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print("All tests check if the backend formula processor correctly:")
    print("  1. Extracts stock numbers from full stock fields")
    print("  2. Processes direct field placeholders like {yearmake}")
    print("  3. Handles special computed fields like {year} and {make}")
    print("  4. Combines multiple fields with custom separators")
    print()
    print("This matches the Porsche St. Louis NEW template requirement:")
    print("  'Year Make - Stock' should show '2026 Porsche - TLB40309'")
    print("  instead of the previous blank '*' placeholders")

if __name__ == "__main__":
    test_formula_processing()
