"""
Verify the correct details for the extra VIN from our normalized dataset
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_connection import db_manager

def verify_extra_vin_details():
    """Get the correct details for the extra VIN from our database"""
    
    print("="*60)
    print("VERIFYING EXTRA VIN DETAILS FROM NORMALIZED DATASET")
    print("="*60)
    
    # Test database connection
    if not db_manager.test_connection():
        print("[ERROR] Database connection failed")
        return False
    
    extra_vin = '1FTFW1ED9PFD07359'
    
    print(f"Checking VIN: {extra_vin}")
    
    try:
        # Get complete details from normalized and raw data
        detail_query = """
        SELECT 
            nvd.vin,
            rvd.year,
            rvd.make,
            rvd.model,
            rvd.trim,
            rvd.stock,
            rvd.type as raw_type,
            rvd.price,
            nvd.vehicle_condition,
            nvd.on_lot_status,
            rvd.location
        FROM normalized_vehicle_data nvd
        JOIN raw_vehicle_data rvd ON nvd.raw_data_id = rvd.id
        JOIN scraper_imports si ON rvd.import_id = si.import_id
        WHERE nvd.vin = %s
        AND si.status = 'active'
        """
        
        result = db_manager.execute_query(detail_query, (extra_vin,))
        
        if result:
            vehicle = result[0]
            print(f"\n[CORRECT DETAILS FROM DATABASE]")
            print(f"VIN: {vehicle['vin']}")
            print(f"Year: {vehicle['year']}")
            print(f"Make: {vehicle['make']}")
            print(f"Model: {vehicle['model']}")
            print(f"Trim: {vehicle['trim'] or 'N/A'}")
            print(f"Stock #: {vehicle['stock']}")
            print(f"Raw Type: {vehicle['raw_type']}")
            print(f"Price: ${vehicle['price'] or 'N/A'}")
            print(f"Vehicle Condition: {vehicle['vehicle_condition']}")
            print(f"On Lot Status: {vehicle['on_lot_status']}")
            print(f"Location: {vehicle['location']}")
            
            # Full vehicle description
            full_description = f"{vehicle['year']} {vehicle['make']} {vehicle['model']}"
            if vehicle['trim']:
                full_description += f" {vehicle['trim']}"
            
            print(f"\nFull Description: {full_description}")
            print(f"Stock Number: {vehicle['stock']}")
            
        else:
            print(f"[ERROR] VIN not found in normalized dataset")
            return False
        
    except Exception as e:
        print(f"[ERROR] Failed to get vehicle details: {str(e)}")
        return False
    
    print(f"\n{'='*60}")
    print("VERIFICATION COMPLETE")
    print('='*60)
    
    return True

if __name__ == "__main__":
    verify_extra_vin_details()