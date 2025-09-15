import sys
import os

# Add the correct paths for database connection
sys.path.insert(0, r'C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\scripts')

# Import with the correct database config
import psycopg2
import json

# Use the same database configuration as the working system
DB_CONFIG = {
    'host': 'localhost', 
    'database': 'vehicle_inventory',
    'user': 'postgres',
    'password': 'password'
}

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print('=' * 60)
    print('PORSCHE ST. LOUIS CONFIG (WORKING TEMPLATE - DO NOT ALTER)')
    print('=' * 60)
    cursor.execute("""
        SELECT name, filtering_rules, output_rules, qr_output_path, is_active 
        FROM dealership_configs 
        WHERE name ILIKE '%porsche%'
    """)
    
    porsche_result = cursor.fetchall()
    if porsche_result:
        for row in porsche_result:
            print(f'Name: {row[0]}')
            print(f'Active: {row[4]}')
            print(f'QR Path: {row[3]}')
            print('Filtering Rules:')
            if row[1]:
                print(json.dumps(row[1], indent=2))
            else:
                print('  (No filtering rules)')
            print('Output Rules:')
            if row[2]:
                print(json.dumps(row[2], indent=2))
            else:
                print('  (No output rules)')
    else:
        print('ERROR: No Porsche config found!')
    
    print()
    print('=' * 60)
    print('SUNTRUP KIA SOUTH CONFIG (NEEDS FIXING)')
    print('=' * 60)
    cursor.execute("""
        SELECT name, filtering_rules, output_rules, qr_output_path, is_active 
        FROM dealership_configs 
        WHERE name ILIKE '%suntrup%kia%south%'
    """)
    
    suntrup_result = cursor.fetchall()
    if suntrup_result:
        for row in suntrup_result:
            print(f'Name: {row[0]}')
            print(f'Active: {row[4]}')
            print(f'QR Path: {row[3]}')
            print('Filtering Rules:')
            if row[1]:
                print(json.dumps(row[1], indent=2))
            else:
                print('  (No filtering rules)')
            print('Output Rules:')
            if row[2]:
                print(json.dumps(row[2], indent=2))
            else:
                print('  (No output rules)')
    else:
        print('ERROR: No Suntrup Kia South config found!')
    
    cursor.close()
    conn.close()
    
    print()
    print('=' * 60)
    print('ANALYSIS SUMMARY')
    print('=' * 60)
    print('✅ Porsche St. Louis: WORKING template (do not modify)')
    print('🔧 Suntrup Kia South: Needs config update using Porsche template')
    
except Exception as e:
    print(f'Database connection error: {e}')
    print('Make sure the Flask server is running and database is accessible')