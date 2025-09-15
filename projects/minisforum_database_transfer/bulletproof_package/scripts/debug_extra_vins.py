from database_connection import db_manager

# Check the extra VINs with correct columns
extra_vins = ['1FMCU9DZ2MUA82497', '1FTFW1E55MFA81051']

print('Debugging why 2 extra VINs are not filtered out:')
print('='*60)

for vin in extra_vins:
    result = db_manager.execute_query('''
        SELECT vin, stock, type, price, on_lot_status
        FROM raw_vehicle_data 
        WHERE vin = %s AND location = 'Suntrup Ford Westport'
        ORDER BY import_id DESC LIMIT 1
    ''', (vin,))
    
    if result:
        r = result[0]
        print(f'\n[EXTRA VIN] {vin}:')
        print(f'  Stock: "{r["stock"]}" (missing: {not r["stock"] or r["stock"].strip() == ""})')
        print(f'  Type: "{r["type"]}"')
        print(f'  Price: {r["price"]}')
        print(f'  On Lot Status: "{r["on_lot_status"]}"')
        
        # Check filter conditions
        missing_stock = not r['stock'] or r['stock'].strip() == ''
        bad_status = r['on_lot_status'] in ['in-transit', 'off-lot'] if r['on_lot_status'] else False
        is_new = r['type'] and r['type'].lower() == 'new'
        
        print(f'  Missing stock: {missing_stock}')
        print(f'  Bad status (in-transit/off-lot): {bad_status}')
        print(f'  Is new vehicle: {is_new}')
        print(f'  SHOULD BE FILTERED: {missing_stock or bad_status or is_new}')