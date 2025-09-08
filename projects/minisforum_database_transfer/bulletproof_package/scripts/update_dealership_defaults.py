#!/usr/bin/env python3
"""
Update dealership configurations with predefined filtering rules
"""

import sys
import json
sys.path.insert(0, '.')
from database_connection import db_manager

def update_dealership_defaults():
    """Update dealership configurations with predefined filtering rules"""
    
    # Define the dealership filtering defaults
    dealership_defaults = {
        # Premium/Luxury - Used Only
        'BMW of West St. Louis': {'vehicle_types': ['used'], 'rationale': 'Premium luxury - used vehicles only'},
        'Bommarito Cadillac': {'vehicle_types': ['used'], 'rationale': 'Premium luxury - used vehicles only'},
        'Columbia BMW': {'vehicle_types': ['used'], 'rationale': 'Premium luxury - used vehicles only'},
        'Porsche St. Louis': {'vehicle_types': ['used'], 'rationale': 'Premium luxury - used vehicles only'},
        'Spirit Lexus': {'vehicle_types': ['used'], 'rationale': 'Premium luxury - used vehicles only'},
        'Jaguar Ranch Mirage': {'vehicle_types': ['used'], 'rationale': 'Premium luxury - used vehicles only'},
        'Land Rover Ranch Mirage': {'vehicle_types': ['used'], 'rationale': 'Premium luxury - used vehicles only'},
        'Audi Ranch Mirage': {'vehicle_types': ['used'], 'rationale': 'Premium luxury - used vehicles only'},
        'Mini of St. Louis': {'vehicle_types': ['used'], 'rationale': 'Premium luxury - used vehicles only'},
        'West County Volvo Cars': {'vehicle_types': ['used'], 'rationale': 'Premium luxury - used vehicles only'},
        
        # Ford Network - New and Used
        'Pundmann Ford': {'vehicle_types': ['new', 'used'], 'rationale': 'Ford network - mixed inventory'},
        'Suntrup Ford Kirkwood': {'vehicle_types': ['new', 'used'], 'rationale': 'Ford network - mixed inventory'},
        'Suntrup Ford West': {'vehicle_types': ['new', 'used'], 'rationale': 'Ford network - mixed inventory'},
        'Thoroughbred Ford': {'vehicle_types': ['new', 'used'], 'rationale': 'Ford network - mixed inventory'},
        
        # Honda Network - New and Used
        'Columbia Honda': {'vehicle_types': ['new', 'used'], 'rationale': 'Honda network - mixed inventory'},
        'Frank Leta Honda': {'vehicle_types': ['new', 'used'], 'rationale': 'Honda network - mixed inventory'},
        'Honda of Frontenac': {'vehicle_types': ['new', 'used'], 'rationale': 'Honda network - mixed inventory'},
        'Serra Honda O\'Fallon': {'vehicle_types': ['new', 'used'], 'rationale': 'Honda network - mixed inventory'},
        
        # GM Network - New and Used
        'Rusty Drewing Cadillac': {'vehicle_types': ['new', 'used'], 'rationale': 'GM network - mixed inventory'},
        'Rusty Drewing Chevrolet Buick GMC': {'vehicle_types': ['new', 'used'], 'rationale': 'GM network - mixed inventory'},
        'Suntrup Buick GMC': {'vehicle_types': ['new', 'used'], 'rationale': 'GM network - mixed inventory'},
        'Weber Chevrolet': {'vehicle_types': ['new', 'used'], 'rationale': 'GM network - mixed inventory'},
        
        # Hyundai/Kia - New and Used
        'Auffenberg Hyundai': {'vehicle_types': ['new', 'used'], 'rationale': 'Hyundai/Kia network - mixed inventory'},
        'H&W Kia': {'vehicle_types': ['new', 'used'], 'rationale': 'Hyundai/Kia network - mixed inventory'},
        'Kia of Columbia': {'vehicle_types': ['new', 'used'], 'rationale': 'Hyundai/Kia network - mixed inventory'},
        'Suntrup Hyundai South': {'vehicle_types': ['new', 'used'], 'rationale': 'Hyundai/Kia network - mixed inventory'},
        'Suntrup Kia South': {'vehicle_types': ['new', 'used'], 'rationale': 'Hyundai/Kia network - mixed inventory'},
        
        # Chrysler/Jeep - New and Used
        'Glendale Chrysler Jeep': {'vehicle_types': ['new', 'used'], 'rationale': 'Chrysler/Jeep network - mixed inventory'},
        'South County Autos': {'vehicle_types': ['new', 'used'], 'rationale': 'Chrysler/Jeep network - mixed inventory'},
        'Joe Machens CDJR': {'vehicle_types': ['new', 'used'], 'rationale': 'Chrysler/Jeep network - mixed inventory'},
        
        # Lincoln Network - New, Used, Certified
        'Dave Sinclair Lincoln': {'vehicle_types': ['new', 'used', 'certified'], 'rationale': 'Lincoln network - full range'},
        'Dave Sinclair Lincoln South': {'vehicle_types': ['new', 'used', 'certified'], 'rationale': 'Lincoln network - full range'},
        'Dave Sinclair Lincoln St. Peters': {'vehicle_types': ['new', 'used', 'certified'], 'rationale': 'Lincoln network - full range'},
        
        # Multi-Brand - New and Used
        'Joe Machens Hyundai': {'vehicle_types': ['new', 'used'], 'rationale': 'Multi-brand - mixed inventory'},
        'Joe Machens Nissan': {'vehicle_types': ['new', 'used'], 'rationale': 'Multi-brand - mixed inventory'},
        'Joe Machens Toyota': {'vehicle_types': ['new', 'used'], 'rationale': 'Multi-brand - mixed inventory'},
        'Pappas Toyota': {'vehicle_types': ['new', 'used'], 'rationale': 'Toyota network - mixed inventory'},
        'Twin City Toyota': {'vehicle_types': ['new', 'used'], 'rationale': 'Toyota network - mixed inventory'},
        'Bommarito West County': {'vehicle_types': ['new', 'used'], 'rationale': 'Multi-brand volume dealer'},
        'Indigo Auto Group': {'vehicle_types': ['new', 'used'], 'rationale': 'Multi-brand group'},
        'Stehouwer Auto': {'vehicle_types': ['new', 'used'], 'rationale': 'Multi-brand dealer'}
    }

    print('=== UPDATING DEALERSHIP FILTERING RULES ===')
    updated_count = 0
    not_found_count = 0

    for dealership_name, config in dealership_defaults.items():
        # Update the filtering_rules for this dealership
        update_query = '''
            UPDATE dealership_configs 
            SET filtering_rules = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE name = %s
        '''
        
        filtering_rules = {
            'vehicle_types': config['vehicle_types'],
            'rationale': config['rationale']
        }
        
        try:
            # Check if dealership exists first
            check_query = 'SELECT name FROM dealership_configs WHERE name = %s'
            exists = db_manager.execute_query(check_query, [dealership_name])
            
            if exists:
                result = db_manager.execute_query(update_query, [json.dumps(filtering_rules), dealership_name])
                print(f'SUCCESS: Updated {dealership_name}: {config["vehicle_types"]}')
                updated_count += 1
            else:
                print(f'WARNING: Dealership not found: {dealership_name}')
                not_found_count += 1
                
        except Exception as e:
            print(f'ERROR: Failed to update {dealership_name}: {e}')

    print(f'\n=== SUMMARY ===')
    print(f'Updated: {updated_count} dealership configurations')
    print(f'Not found: {not_found_count} dealerships')
    
    # Show current state
    print(f'\n=== VERIFICATION - CURRENT CONFIGURATIONS ===')
    verify_query = '''
        SELECT name, is_active, filtering_rules 
        FROM dealership_configs 
        WHERE filtering_rules IS NOT NULL 
        ORDER BY name
    '''
    results = db_manager.execute_query(verify_query)
    
    for config in results:
        rules = config['filtering_rules']
        vehicle_types = rules.get('vehicle_types', []) if rules else []
        print(f'{config["name"]}: Active={config["is_active"]}, Types={vehicle_types}')

if __name__ == '__main__':
    update_dealership_defaults()