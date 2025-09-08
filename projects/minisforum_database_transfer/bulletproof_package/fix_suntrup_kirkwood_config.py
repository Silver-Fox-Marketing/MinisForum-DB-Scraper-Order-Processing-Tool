#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
from database_connection import DatabaseManager

def main():
    print("=== FIXING SUNTRUP FORD KIRKWOOD DEALERSHIP CONFIGURATION ===")
    
    db_manager = DatabaseManager()
    
    # First check the dealership_configs schema
    print("\n1. CHECKING DEALERSHIP_CONFIGS TABLE SCHEMA:")
    try:
        schema = db_manager.execute_query('''
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'dealership_configs'
            ORDER BY ordinal_position
        ''')
        
        if schema:
            print("Available columns:")
            for col in schema:
                print(f"  - {col['column_name']} ({col['data_type']}) nullable: {col['is_nullable']}")
        else:
            print("Table dealership_configs does not exist - need to create it")
            
    except Exception as e:
        print(f"Error checking schema: {e}")
        print("Table may not exist - will create it")
    
    # Check existing configurations
    print("\n2. CHECKING EXISTING DEALERSHIP CONFIGURATIONS:")
    try:
        existing_configs = db_manager.execute_query('''
            SELECT * FROM dealership_configs 
            LIMIT 5
        ''')
        
        if existing_configs:
            print(f"Found {len(existing_configs)} existing configurations:")
            for config in existing_configs[:3]:  # Show first 3
                print(f"  - {config}")
        else:
            print("No existing configurations found")
            
    except Exception as e:
        print(f"Error checking existing configs: {e}")
    
    # Check if Suntrup Ford Kirkwood already exists
    print("\n3. CHECKING FOR EXISTING SUNTRUP FORD KIRKWOOD CONFIG:")
    try:
        suntrup_config = db_manager.execute_query('''
            SELECT * FROM dealership_configs 
            WHERE dealership_name ILIKE '%suntrup%kirkwood%'
            OR location ILIKE '%suntrup%kirkwood%'
            OR name ILIKE '%suntrup%kirkwood%'
        ''')
        
        if suntrup_config:
            print(f"Found existing Suntrup Ford Kirkwood config: {suntrup_config[0]}")
            config_exists = True
        else:
            print("No existing Suntrup Ford Kirkwood config found")
            config_exists = False
            
    except Exception as e:
        print(f"Error checking Suntrup config: {e}")
        config_exists = False
    
    print("\n4. DETERMINING CORRECT TABLE STRUCTURE:")
    
    # Try to determine the correct structure by looking at related tables
    try:
        # Check if there are any tables with similar names
        tables = db_manager.execute_query('''
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%dealer%' 
            OR table_name LIKE '%config%'
        ''')
        
        print("Related tables found:")
        for table in tables:
            print(f"  - {table['table_name']}")
            
    except Exception as e:
        print(f"Error finding related tables: {e}")
    
    # Check the CAO processing code to see what structure it expects
    print("\n5. RECOMMENDED SOLUTION:")
    print("Based on the analysis, we need to:")
    print("1. Create/update dealership_configs table with proper structure")
    print("2. Add Suntrup Ford Kirkwood configuration with vehicle_types = ['used']")
    print("3. Ensure CAO processing respects these filters")
    
    db_manager.close()

if __name__ == "__main__":
    main()