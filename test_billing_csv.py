"""
Test script for billing CSV generation
Tests with South County DCJR sample data
"""
import sys
sys.path.insert(0, 'scripts')
from correct_order_processing import CorrectOrderProcessor
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_billing_csv():
    """Test billing CSV generation with sample data"""
    
    # Initialize the order processor
    processor = CorrectOrderProcessor()
    
    # Create test vehicles (simulating South County DCJR data)
    test_ordered_vehicles = [
        {'vin': '1C4JJXP60MW850122', 'type': 'new', 'year': 2025, 'make': 'Jeep', 'model': 'Wrangler'},
        {'vin': '1C4JJXP69NW178255', 'type': 'new', 'year': 2025, 'make': 'Jeep', 'model': 'Wrangler'},
        {'vin': '1C4PJMCS0FW668550', 'type': 'used', 'year': 2024, 'make': 'Jeep', 'model': 'Cherokee'},
        {'vin': '1C4RJFAG0LC383671', 'type': 'used', 'year': 2023, 'make': 'Jeep', 'model': 'Grand Cherokee'},
        {'vin': '1C4RJFCG0EC181557', 'type': 'new', 'year': 2025, 'make': 'Jeep', 'model': 'Grand Cherokee'},
    ]
    
    test_produced_vehicles = [
        {'vin': '1C4JJXP60MW850122', 'type': 'new', 'year': 2025, 'make': 'Jeep', 'model': 'Wrangler'},
        {'vin': '3GCPYBEH2LG248025', 'type': 'new', 'year': 2025, 'make': 'GMC', 'model': 'Sierra'},
        {'vin': '1FATP8UH8J5139276', 'type': 'used', 'year': 2024, 'make': 'Ford', 'model': 'Mustang'},
        {'vin': '1C6SRFFT6MN678884', 'type': 'new', 'year': 2025, 'make': 'Ram', 'model': '1500'},
        {'vin': '1C4JJXP69NW178255', 'type': 'new', 'year': 2025, 'make': 'Jeep', 'model': 'Wrangler'},
    ]
    
    # Create output folder
    output_folder = Path('test_billing_output')
    output_folder.mkdir(exist_ok=True)
    
    try:
        # Generate billing CSV
        billing_path = processor._generate_billing_csv(
            ordered_vehicles=test_ordered_vehicles,
            produced_vehicles=test_produced_vehicles,
            dealership_name='South County Dodge Chrysler Jeep Ram',
            order_date='8.19',
            output_folder=output_folder
        )
        
        print(f"SUCCESS: Billing CSV generated successfully: {billing_path}")
        
        # Read and display the first few lines
        with open(billing_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print("\nBilling CSV Preview (first 15 lines):")
            print("-" * 60)
            for i, line in enumerate(lines[:15], 1):
                print(f"{i:2}: {line.rstrip()}")
            print("-" * 60)
            
        print(f"\nTest completed successfully!")
        print(f"Full file available at: {billing_path}")
        
        return True
        
    except Exception as e:
        print(f"ERROR during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_billing_csv()
    sys.exit(0 if success else 1)