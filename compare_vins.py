import csv

# Read VINs from billing CSV
billing_vins = set()
with open(r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\minisforum_database_transfer\bulletproof_package\orders\Serra_Honda_OFallon_TESTSERRA_20251002_170017\SERRAHONDAO'FALLON_10-02 - BILLING.csv", 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        if row and row[0] and len(row[0]) == 17:  # VINs are 17 characters
            billing_vins.add(row[0])

# Current system VINs (provided by user)
current_system_vins = {
    '5FPYK3F5X1B001011',  # Note: This appears to be a typo - should be TB not 1B
    '5FPYK3F59TB001212',
    '5FPYK3F57TB001032',
    '5FPYK3F73SB031340',
    '5FPYK3F5LTB001893',  # Note: This appears to be a typo - should be 54 not 5L
    '5FNYG1H7XSB171574',
    '5FNYF9H5XTB038766',
    '2HGFE2F55TH520061',
    '7FARS4H45TE002904',
    '7FARS4H43TE002898',
    '7FARS4H28TE002989',
    '7FARS4H25TE002982',
    '7FARS6H62TE048994',
    '7FARS6H6XTE049536',
    '5FNRL6H60TB015484',
    '7FARS6H82TE049449',
    '5FNRL6H66TB013867',
    '5FNRL6H69TB013975',
    '1N6AA1ED5PN105193',
    '7FARS6H84TE050408',
    '5FNYF6H23NB078288',
    '5FPYK3F19KB038840',
    '2HKRW6H34KH215264',
    '2GNALCEK1G6216732',
    '1HGCV1F33NA061772'
}

# Also check with corrected VINs
current_system_vins.add('5FPYK3F5XTB001011')  # Corrected version
current_system_vins.add('5FPYK3F54TB001893')  # Corrected version

# Find VINs in billing CSV but NOT in current system
vins_not_in_current = sorted(billing_vins - current_system_vins)

print(f"Total VINs in billing CSV: {len(billing_vins)}")
print(f"Total VINs in current system: {len(current_system_vins)}")
print(f"VINs in new system NOT in current system: {len(vins_not_in_current)}")
print()
print("VINs to check against VIN log:")
print("=" * 80)
for vin in vins_not_in_current:
    print(vin)
