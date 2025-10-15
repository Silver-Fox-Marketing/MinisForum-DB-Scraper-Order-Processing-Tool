import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
os.chdir(os.path.join(os.path.dirname(__file__), 'web_gui'))

from database_connection import db_manager
from datetime import date

# VINs in new system but NOT in current system
extra_vins = [
    '19XFL2H58RE033068',
    '1FTER4FH1MLD23008',
    '1G1BE5SM6G7301261',
    '1GKS2CKJ9JR183832',
    '1HGCT2B80FA006758',
    '1HGCV1F32NA098103',
    '1HGCV3F15JA005630',
    '1HGCY1F32RA057743',
    '1HGCY1F3XPA002891',
    '1HGCY1F42SA069132',
    '1HGCY1F44SA068550',
    '1HGCY2F70SA080064',
    '1HGCY2F71SA079425',
    '1LN6L9RP8L5602444',
    '1VWBT7A38GC068702',
    '2GNAXJEV5L6168097',
    '2HGFE1E50TH472657',
    '2HGFE2F20TH524069',
    '2HGFE2F2XSH532999',
    '2HGFE2F53PH519996',
    '2HGFE2F58TH525545',
    '2HGFE2F59TH525571',
    '2HGFE4F82TH315738',
    '2HGFE4F82TH316355',
    '2HKRS4H2XTH431483',
    '2HKRS4H40SH460815',
    '2HKRS4H41TH435049',
    '2HKRS4H48TH431984',
    '3CZRU5H57MM707439',
    '3CZRZ1H79PM718460',
    '3CZRZ2H37PM720906',
    '3CZRZ2H38TM736400',
    '3CZRZ2H58TM733420',
    '3CZRZ2H59TM734317',
    '3CZRZ2H76TM735703',
    '5FNRL6H66TB015084',
    '5FNRL6H68TB012557',
    '5FNRL6H70TB011959',
    '5FNRL6H71NB035609',
    '5FNRL6H74TB005694',
    '5FNRL6H77JB103146',
    '5FNRL6H90TB012398',
    '5FNRL6H92TB016582',
    '5FNRL6H95TB017645',
    '5FNYF6H66KB049866',
    '5FNYF9H35TB036292',
    '5FNYF9H36TB037256',
    '5FNYG1H32SB168469',
    '5FNYG1H41SB167841',
    '5FNYG1H62SB170295',
    '5FNYG1H69SB160945',
    '5FNYG1H70SB169414',
    '5FNYG1H75SB169621',
    '5FNYG1H79SB170352',
    '5FNYG1H7XSB167217',
    '5FNYG1H89SB174071',
    '5FNYG2H5XPB005678',
    '5FPYK3F59TB000657',
    '5FPYK3F61SB045910',
    '5J6RW2H95LL030886',
    '7FARS4H28TE003012',
    '7FARS6H62TE052642',
    '7FARS6H98TE052283'
]

print("=" * 80)
print(f"CHECKING DATE_IN_STOCK FOR {len(extra_vins)} EXTRA VINs")
print("=" * 80)
print()

# Get active import
active_import = db_manager.execute_query("""
    SELECT import_id FROM scraper_imports
    WHERE %s = ANY(dealerships_list)
    AND status = 'active'
    LIMIT 1
""", ("Serra Honda O'Fallon",), fetch='one')

if not active_import:
    print("[ERROR] No active import found")
    sys.exit(1)

import_id = active_import['import_id']

# Query for these VINs
placeholders = ','.join(['%s'] * len(extra_vins))
query = f"""
    SELECT vin, stock, date_in_stock, type
    FROM raw_vehicle_data
    WHERE import_id = %s
    AND vin IN ({placeholders})
    ORDER BY date_in_stock DESC
"""

params = [import_id] + extra_vins
results = db_manager.execute_query(query, tuple(params))

print(f"Found {len(results)} of {len(extra_vins)} VINs in active import")
print()

less_than_7 = 0
seven_or_more = 0
no_date = 0

for vehicle in results:
    date_in_stock = vehicle['date_in_stock']

    if not date_in_stock:
        no_date += 1
        print(f"VIN: ...{vehicle['vin'][-8:]} | Stock: {vehicle['stock']} | NO DATE_IN_STOCK")
        continue

    if isinstance(date_in_stock, str):
        from datetime import datetime
        date_in_stock = datetime.strptime(date_in_stock, '%Y-%m-%d').date()
    elif hasattr(date_in_stock, 'date'):
        date_in_stock = date_in_stock.date()

    days_on_lot = (date.today() - date_in_stock).days

    if days_on_lot < 7:
        less_than_7 += 1
        status = "[< 7 DAYS]"
    else:
        seven_or_more += 1
        status = "[>= 7 DAYS]"

    print(f"VIN: ...{vehicle['vin'][-8:]} | Stock: {vehicle['stock']} | Date: {date_in_stock} | Days: {days_on_lot} {status}")

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"VINs with < 7 days on lot: {less_than_7}")
print(f"VINs with >= 7 days on lot: {seven_or_more}")
print(f"VINs with no date_in_stock: {no_date}")
print()

if seven_or_more > 0:
    print("[ISSUE] These VINs SHOULD have been included (>= 7 days)")
    print("This suggests the seasoning filter may not be working correctly!")
else:
    print("[OK] All extra VINs are < 7 days old")
    print("Seasoning filter appears to be working correctly")
