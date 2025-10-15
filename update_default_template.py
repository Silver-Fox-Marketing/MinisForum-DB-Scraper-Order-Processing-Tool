import sys
sys.path.insert(0, 'C:/Users/Workstation_1/Documents/Tools/ClaudeCode/projects/minisforum_database_transfer/bulletproof_package/scripts')
sys.path.insert(0, 'C:/Users/Workstation_1/Documents/Tools/ClaudeCode/projects/minisforum_database_transfer/bulletproof_package/web_gui')

from database_connection import DatabaseManager

db_manager = DatabaseManager()

print("="*60)
print("CURRENT TEMPLATES:")
print("="*60)
templates = db_manager.execute_query('SELECT id, template_name, is_system_default, is_active FROM template_configs ORDER BY id')
for t in templates:
    print(f"  ID: {t['id']}, Name: {t['template_name']}, System Default: {t['is_system_default']}, Active: {t['is_active']}")

print("\n" + "="*60)
print("UPDATING TEMPLATES...")
print("="*60)

# Remove system default flag from "Default Shortcut Pack"
db_manager.execute_query("UPDATE template_configs SET is_system_default = false WHERE template_name = 'Default Shortcut Pack'")
print("[OK] Removed system default flag from 'Default Shortcut Pack'")

# Set "ShortCut Pack" as the new system default
db_manager.execute_query("UPDATE template_configs SET is_system_default = true WHERE template_name = 'ShortCut Pack'")
print("[OK] Set 'ShortCut Pack' as new system default")

print("\n" + "="*60)
print("UPDATED TEMPLATES:")
print("="*60)
templates = db_manager.execute_query('SELECT id, template_name, is_system_default, is_active FROM template_configs ORDER BY id')
for t in templates:
    print(f"  ID: {t['id']}, Name: {t['template_name']}, System Default: {t['is_system_default']}, Active: {t['is_active']}")

print("\n" + "="*60)
print("UPDATE COMPLETE!")
print("="*60)
