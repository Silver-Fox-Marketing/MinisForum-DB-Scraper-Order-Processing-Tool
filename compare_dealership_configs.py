import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
os.chdir(os.path.join(os.path.dirname(__file__), 'web_gui'))

from database_connection import db_manager
import json

print("=" * 80)
print("DEALERSHIP CONFIG COMPARISON: Auffenberg vs Serra Honda")
print("=" * 80)
print()

# Get Auffenberg config
auffenberg = db_manager.execute_query(
    "SELECT name, filtering_rules FROM dealership_configs WHERE name = %s",
    ("Auffenberg Hyundai",),
    fetch='one'
)

# Get Serra config
serra = db_manager.execute_query(
    "SELECT name, filtering_rules FROM dealership_configs WHERE name = %s",
    ("Serra Honda O'Fallon",),
    fetch='one'
)

if not auffenberg:
    print("[ERROR] Auffenberg Hyundai config not found")
    sys.exit(1)

if not serra:
    print("[ERROR] Serra Honda O'Fallon config not found")
    sys.exit(1)

auff_rules = auffenberg['filtering_rules']
serra_rules = serra['filtering_rules']

print("AUFFENBERG HYUNDAI CONFIG:")
print("-" * 80)
print(json.dumps(auff_rules, indent=2))
print()

print("SERRA HONDA O'FALLON CONFIG:")
print("-" * 80)
print(json.dumps(serra_rules, indent=2))
print()

# Compare filter fields
print("=" * 80)
print("FILTER FIELD COMPARISON")
print("=" * 80)
print()

auff_keys = set(auff_rules.keys())
serra_keys = set(serra_rules.keys())

# Fields in Auffenberg but not Serra
missing_in_serra = auff_keys - serra_keys
if missing_in_serra:
    print("[WARNING] Fields in Auffenberg but MISSING in Serra:")
    for key in sorted(missing_in_serra):
        print(f"  - {key}: {auff_rules[key]}")
    print()

# Fields in Serra but not Auffenberg
extra_in_serra = serra_keys - auff_keys
if extra_in_serra:
    print("[INFO] Fields in Serra but not in Auffenberg:")
    for key in sorted(extra_in_serra):
        print(f"  - {key}: {serra_rules[key]}")
    print()

# Common fields with different values
common_keys = auff_keys & serra_keys
print("COMMON FIELDS (with values):")
print("-" * 80)
for key in sorted(common_keys):
    auff_val = auff_rules[key]
    serra_val = serra_rules[key]
    match = "SAME" if auff_val == serra_val else "DIFFERENT"
    print(f"  {key}:")
    print(f"    Auffenberg: {auff_val}")
    print(f"    Serra:      {serra_val}")
    print(f"    [{match}]")
    print()

# Check for contradictions
print("=" * 80)
print("CONTRADICTION CHECK")
print("=" * 80)
print()

def check_contradictions(name, rules):
    issues = []

    vehicle_types = rules.get('vehicle_types', [])
    exclude_conditions = rules.get('exclude_conditions', [])

    if 'used' in vehicle_types:
        # 'used' expands to: used, po, cpo, certified, pre-owned
        problematic = []
        for excluded in exclude_conditions:
            if excluded in ['po', 'cpo', 'certified', 'pre-owned']:
                problematic.append(excluded)

        if problematic:
            issues.append(f"vehicle_types includes 'used' but exclude_conditions blocks: {problematic}")

    if 'new' in vehicle_types and 'new' in exclude_conditions:
        issues.append("vehicle_types includes 'new' but exclude_conditions blocks 'new'")

    return issues

auff_issues = check_contradictions("Auffenberg", auff_rules)
serra_issues = check_contradictions("Serra", serra_rules)

print("Auffenberg Hyundai:")
if auff_issues:
    for issue in auff_issues:
        print(f"  [CONTRADICTION] {issue}")
else:
    print("  [OK] No contradictions found")

print()
print("Serra Honda O'Fallon:")
if serra_issues:
    for issue in serra_issues:
        print(f"  [CONTRADICTION] {issue}")
else:
    print("  [OK] No contradictions found")
print()

if not missing_in_serra and not auff_issues and not serra_issues:
    print("[SUCCESS] Both configs are complete and consistent!")
elif missing_in_serra:
    print(f"[ACTION NEEDED] Add {len(missing_in_serra)} missing fields to Serra config")
elif auff_issues or serra_issues:
    print("[ACTION NEEDED] Fix contradictions in dealership configs")
