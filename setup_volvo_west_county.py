#!/usr/bin/env python3
"""
Setup Volvo Cars West County dealership
- Create dealership config based on South County DCJR template
- Create VIN log table
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'projects/minisforum_database_transfer/bulletproof_package/scripts'))

from database_connection import db_manager
import json

def setup_volvo_dealership():
    """Setup Volvo Cars West County with config and VIN log table"""

    dealership_name = "Volvo Cars West County"
    print(f"=== SETTING UP {dealership_name} ===\n")

    # Step 1: Get South County DCJR template configuration
    print("[STEP 1] Getting South County DCJR template configuration...")

    template_config = db_manager.execute_query("""
        SELECT filtering_rules, output_rules
        FROM dealership_configs
        WHERE name = 'South County DCJR'
    """)

    if not template_config:
        print("[ERROR] Could not find South County DCJR template!")
        return False

    filtering_rules = template_config[0]['filtering_rules']
    output_rules = template_config[0]['output_rules']

    if isinstance(filtering_rules, str):
        filtering_rules = json.loads(filtering_rules)
    if isinstance(output_rules, str):
        output_rules = json.loads(output_rules)

    print(f"[OK] Template configuration loaded")
    print(f"    Filtering rules: {json.dumps(filtering_rules, indent=2)}")

    # Step 2: Check if Volvo config already exists
    print(f"\n[STEP 2] Checking if {dealership_name} config exists...")

    existing_config = db_manager.execute_query("""
        SELECT name FROM dealership_configs
        WHERE name = %s
    """, (dealership_name,))

    if existing_config:
        print(f"[WARNING] Config for {dealership_name} already exists!")
        print("Updating existing configuration...")

        # Update existing config
        db_manager.execute_query("""
            UPDATE dealership_configs
            SET filtering_rules = %s,
                output_rules = %s,
                qr_output_path = %s,
                is_active = true,
                updated_at = CURRENT_TIMESTAMP
            WHERE name = %s
        """, (
            json.dumps(filtering_rules),
            json.dumps(output_rules),
            'C:\\qr_codes\\volvo_cars_west_county\\',
            dealership_name
        ))

        print(f"[OK] Updated existing configuration")
    else:
        # Step 3: Insert new dealership config
        print(f"[STEP 3] Creating new dealership config for {dealership_name}...")

        db_manager.execute_query("""
            INSERT INTO dealership_configs (name, filtering_rules, output_rules, qr_output_path, is_active)
            VALUES (%s, %s, %s, %s, true)
        """, (
            dealership_name,
            json.dumps(filtering_rules),
            json.dumps(output_rules),
            'C:\\qr_codes\\volvo_cars_west_county\\'
        ))

        print(f"[OK] Created dealership configuration")

    # Step 4: Create VIN log table
    print(f"\n[STEP 4] Creating VIN log table...")

    # Generate table name following standard pattern
    table_name = dealership_name.lower()
    table_name = table_name.replace(' ', '_')
    table_name = table_name.replace('&', 'and')
    table_name = table_name.replace('.', '')
    table_name = table_name.replace(',', '')
    table_name = table_name.replace("'", '')
    table_name = table_name.replace('-', '_')
    table_name = table_name.replace('/', '_')
    table_name = table_name.replace('__', '_')
    table_name = f'{table_name}_vin_log'

    print(f"    Table name: {table_name}")

    # Check if table already exists
    table_exists = db_manager.execute_query("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = %s
    """, (table_name,))

    if table_exists:
        print(f"[WARNING] Table {table_name} already exists!")
    else:
        # Create VIN log table with same structure as others
        create_table_query = f"""
            CREATE TABLE {table_name} (
                vin VARCHAR(17) PRIMARY KEY,
                order_number VARCHAR(50),
                processed_date DATE DEFAULT CURRENT_DATE,
                order_type VARCHAR(20) DEFAULT 'HISTORICAL',
                template_type VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                order_date DATE,
                dealership VARCHAR(100)
            )
        """

        db_manager.execute_query(create_table_query)
        print(f"[OK] Created VIN log table: {table_name}")

        # Create indexes for performance
        db_manager.execute_query(f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_order_number
            ON {table_name}(order_number)
        """)

        db_manager.execute_query(f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_processed_date
            ON {table_name}(processed_date)
        """)

        db_manager.execute_query(f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_order_type
            ON {table_name}(order_type)
        """)

        print(f"[OK] Created indexes for {table_name}")

    # Step 5: Add name mapping to correct_order_processing.py
    print(f"\n[STEP 5] Name mapping reminder...")
    print(f"[NOTE] The name mapping is already correct:")
    print(f"    Config name: 'Volvo Cars West County'")
    print(f"    Scraper name: 'Volvo Cars West County'")
    print(f"    No additional mapping needed (direct match)")

    # Step 6: Verify setup
    print(f"\n[STEP 6] Verification...")

    # Verify config
    verify_config = db_manager.execute_query("""
        SELECT name, is_active, filtering_rules
        FROM dealership_configs
        WHERE name = %s
    """, (dealership_name,))

    if verify_config:
        print(f"[OK] Config verified: {dealership_name} is ACTIVE")

        # Display key filters
        config_rules = verify_config[0]['filtering_rules']
        if isinstance(config_rules, str):
            config_rules = json.loads(config_rules)

        print(f"\n    Key filters applied:")
        print(f"    - exclude_missing_stock_number: {config_rules.get('exclude_missing_stock_number')}")
        print(f"    - vehicle_types: {config_rules.get('vehicle_types')}")
        print(f"    - allowed_vehicle_types: {config_rules.get('allowed_vehicle_types')}")
        print(f"    - exclude_status: {config_rules.get('exclude_status')}")
    else:
        print(f"[ERROR] Could not verify config")

    # Verify VIN log table
    verify_table = db_manager.execute_query("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = %s
    """, (table_name,))

    if verify_table:
        print(f"[OK] VIN log table verified: {table_name} exists")
    else:
        print(f"[ERROR] VIN log table not found")

    print(f"\n=== SETUP COMPLETE ===")
    print(f"\nSummary for {dealership_name}:")
    print("1. Dealership config created/updated with South County DCJR template")
    print("2. All filtering rules applied (including exclude_missing_stock_number)")
    print("3. VIN log table created: " + table_name)
    print("4. Name mapping: Direct match (no additional mapping needed)")
    print("\n[ACTION] You can now adjust new/used/both settings from the dealership settings panel")

    return True

if __name__ == "__main__":
    success = setup_volvo_dealership()
    if not success:
        print("\n[ERROR] Setup failed!")
        sys.exit(1)