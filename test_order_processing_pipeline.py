"""
Test Order Processing Pipeline
Tests the complete flow from scraped data → filtering → QR generation → Adobe CSV
"""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent / "scripts"
sys.path.append(str(scripts_dir))

from order_processing_workflow import OrderProcessingWorkflow
from database_connection import db_manager
import json

def test_order_pipeline():
    """Test the complete order processing pipeline"""
    
    print("=" * 60)
    print("TESTING ORDER PROCESSING PIPELINE")
    print("=" * 60)
    
    # Initialize workflow
    workflow = OrderProcessingWorkflow()
    
    # Test with Dave Sinclair Lincoln (we know it has data)
    dealership_name = "Dave Sinclair Lincoln"
    
    print(f"\n1. Testing with {dealership_name}")
    print("-" * 40)
    
    # Check if we have vehicles in database
    vehicle_count = db_manager.execute_query("""
        SELECT COUNT(*) as count
        FROM raw_vehicle_data
        WHERE location = %s
    """, (dealership_name,))
    
    print(f"Found {vehicle_count[0]['count']} vehicles in database")
    
    # Get dealership config
    config = db_manager.execute_query("""
        SELECT filtering_rules, output_rules
        FROM dealership_configs
        WHERE name = %s
    """, (dealership_name,))
    
    if config:
        print("\nDealership Configuration:")
        filtering_rules = config[0]['filtering_rules']
        if isinstance(filtering_rules, str):
            filtering_rules = json.loads(filtering_rules)
        print(f"Vehicle Types: {filtering_rules.get('vehicle_types', ['all'])}")
        print(f"Min Year: {filtering_rules.get('min_year', 'None')}")
        print(f"Min Price: {filtering_rules.get('min_price', 0)}")
    
    # Test CAO order processing
    print("\n2. Testing CAO Order Processing")
    print("-" * 40)
    
    result = workflow.process_cao_order(dealership_name, ['new'])
    
    if result['success']:
        print(f"[SUCCESS] CAO Order processed!")
        print(f"Total vehicles: {result['total_vehicles']}")
        print(f"New vehicles: {result['new_vehicles']}")
        print(f"QR codes generated: {result['qr_codes_generated']}")
        print(f"QR folder: {result['qr_folder']}")
        print(f"CSV file: {result['csv_file']}")
        
        # Check if files were created
        qr_folder = Path(result['qr_folder'])
        if qr_folder.exists():
            qr_files = list(qr_folder.glob("*.png"))
            print(f"\n[VERIFIED] {len(qr_files)} QR code files created")
            if qr_files:
                print(f"Sample QR file: {qr_files[0].name}")
        
        csv_file = Path(result['csv_file']) if result['csv_file'] else None
        if csv_file and csv_file.exists():
            print(f"\n[VERIFIED] Adobe CSV created: {csv_file.name}")
            print(f"CSV size: {csv_file.stat().st_size} bytes")
            
            # Read first few lines of CSV
            with open(csv_file, 'r') as f:
                lines = f.readlines()[:5]
                print("\nCSV Preview:")
                for line in lines:
                    print(f"  {line.strip()}")
    else:
        print(f"[FAILED] Error: {result.get('error', 'Unknown error')}")
    
    # Test filtering
    print("\n3. Testing Vehicle Filtering")
    print("-" * 40)
    
    vehicles = workflow.filter_vehicles_by_type(dealership_name, ['new'])
    print(f"Filtered to {len(vehicles)} new vehicles")
    
    if vehicles:
        sample = vehicles[0]
        print("\nSample vehicle:")
        print(f"  VIN: {sample.get('vin')}")
        print(f"  Year: {sample.get('year')}")
        print(f"  Make: {sample.get('make')}")
        print(f"  Model: {sample.get('model')}")
        print(f"  Type: {sample.get('type')}")
        print(f"  Price: {sample.get('price')}")
        print(f"  URL: {sample.get('vehicle_url')}")

if __name__ == "__main__":
    test_order_pipeline()