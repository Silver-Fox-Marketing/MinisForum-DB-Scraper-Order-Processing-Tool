import psycopg2
import json

# Database configuration matching the bulletproof system
DB_CONFIG = {
    'host': 'localhost', 
    'database': 'vehicle_inventory',
    'user': 'postgres',
    'password': 'password'
}

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print('=== PORSCHE ST. LOUIS CONFIG ===')
    cursor.execute("""
        SELECT name, filtering_rules, output_rules, qr_output_path, is_active 
        FROM dealership_configs 
        WHERE name ILIKE '%porsche%'
    """)
    
    porsche_result = cursor.fetchall()
    if porsche_result:
        for row in porsche_result:
            print(f'Name: {row[0]}')
            print(f'Filtering Rules: {json.dumps(row[1], indent=2)}')
            print(f'Output Rules: {json.dumps(row[2], indent=2)}')
            print(f'QR Path: {row[3]}')
            print(f'Active: {row[4]}')
    else:
        print('No Porsche config found')
    
    print()
    print('=== SUNTRUP KIA SOUTH CONFIG ===')
    cursor.execute("""
        SELECT name, filtering_rules, output_rules, qr_output_path, is_active 
        FROM dealership_configs 
        WHERE name ILIKE '%suntrup%kia%south%'
    """)
    
    suntrup_result = cursor.fetchall()
    if suntrup_result:
        for row in suntrup_result:
            print(f'Name: {row[0]}')
            print(f'Filtering Rules: {json.dumps(row[1], indent=2)}')
            print(f'Output Rules: {json.dumps(row[2], indent=2)}')
            print(f'QR Path: {row[3]}')
            print(f'Active: {row[4]}')
    else:
        print('No Suntrup Kia South config found')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'Error: {e}')