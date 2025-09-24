"""
Template System Database Schema Creation
Creates tables for storing custom output templates for dealership orders
"""

import sys
sys.path.append('.')
from database_connection import db_manager

def create_template_tables():
    """Create template system tables"""

    # Create template_configs table
    create_template_table = """
    CREATE TABLE IF NOT EXISTS template_configs (
        id SERIAL PRIMARY KEY,
        template_name VARCHAR(100) NOT NULL UNIQUE,
        description TEXT,
        template_type VARCHAR(50) DEFAULT 'shortcut_pack',
        fields JSONB NOT NULL,
        created_by VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT true,
        is_system_default BOOLEAN DEFAULT false
    );
    """

    # Create dealership_template_mapping table
    create_mapping_table = """
    CREATE TABLE IF NOT EXISTS dealership_template_mapping (
        id SERIAL PRIMARY KEY,
        dealership_name VARCHAR(200) NOT NULL,
        template_id INTEGER REFERENCES template_configs(id) ON DELETE CASCADE,
        vehicle_condition VARCHAR(50), -- 'new', 'used', 'cpo', or NULL for all
        priority INTEGER DEFAULT 0, -- Higher priority templates are checked first
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(dealership_name, vehicle_condition, template_id)
    );
    """

    # Create template_field_definitions table for available fields
    create_field_definitions = """
    CREATE TABLE IF NOT EXISTS template_field_definitions (
        id SERIAL PRIMARY KEY,
        field_key VARCHAR(50) NOT NULL UNIQUE,
        field_label VARCHAR(100) NOT NULL,
        field_type VARCHAR(50) DEFAULT 'text', -- text, number, date, url, concatenated
        data_source VARCHAR(100), -- column name from normalized_vehicle_data
        default_format VARCHAR(200), -- Default formatting/display
        is_available BOOLEAN DEFAULT true,
        description TEXT
    );
    """

    try:
        # Create tables
        db_manager.execute_query(create_template_table)
        print("[SUCCESS] Created template_configs table")

        db_manager.execute_query(create_mapping_table)
        print("[SUCCESS] Created dealership_template_mapping table")

        db_manager.execute_query(create_field_definitions)
        print("[SUCCESS] Created template_field_definitions table")

        # Insert default field definitions
        field_definitions = [
            ('vin', 'VIN', 'text', 'vin', None, 'Vehicle Identification Number'),
            ('stock', 'Stock Number', 'text', 'stock', None, 'Dealer stock number'),
            ('year', 'Year', 'number', 'year', None, 'Model year'),
            ('make', 'Make', 'text', 'make', None, 'Vehicle manufacturer'),
            ('model', 'Model', 'text', 'model', None, 'Vehicle model'),
            ('trim', 'Trim', 'text', 'trim', None, 'Vehicle trim level'),
            ('price', 'Price', 'number', 'price', '$#,###', 'Vehicle price'),
            ('msrp', 'MSRP', 'number', 'msrp', '$#,###', 'Manufacturer suggested retail price'),
            ('condition', 'Condition', 'text', 'vehicle_condition', None, 'New/Used/CPO'),
            ('status', 'Status', 'text', 'status', None, 'Vehicle status'),
            ('date_in_stock', 'Date In Stock', 'date', 'date_in_stock', 'MM/DD/YYYY', 'Date vehicle arrived'),
            ('days_on_lot', 'Days on Lot', 'calculated', None, None, 'Calculated days on lot'),
            ('vehicle_url', 'Vehicle URL', 'url', 'vehicle_url', None, 'Vehicle detail page URL'),
            ('year_make_model', 'Year Make Model', 'concatenated', None, '{year} {make} {model}', 'Combined year, make, and model'),
            ('stock_vin', 'Stock - VIN', 'concatenated', None, '{stock} - {vin}', 'Stock number and VIN combined'),
            ('full_description', 'Full Description', 'concatenated', None, '{year} {make} {model} {trim}', 'Complete vehicle description'),
            ('location', 'Dealership', 'text', 'location', None, 'Dealership location'),
            ('qr_code', 'QR Code', 'special', None, None, 'QR code image path')
        ]

        for field_def in field_definitions:
            insert_field = """
            INSERT INTO template_field_definitions
            (field_key, field_label, field_type, data_source, default_format, description)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (field_key) DO NOTHING;
            """
            db_manager.execute_query(insert_field, field_def)

        print(f"[SUCCESS] Inserted {len(field_definitions)} field definitions")

        # Create default shortcut_pack template
        default_template = {
            "template_name": "Default Shortcut Pack",
            "description": "Standard shortcut pack template with VIN and QR code",
            "template_type": "shortcut_pack",
            "fields": {
                "columns": [
                    {
                        "key": "vin",
                        "label": "VIN",
                        "type": "text",
                        "source": "vin",
                        "width": "60%",
                        "order": 1
                    },
                    {
                        "key": "qr_code",
                        "label": "QR Code",
                        "type": "special",
                        "source": "qr_code",
                        "width": "40%",
                        "order": 2
                    }
                ]
            },
            "is_system_default": True
        }

        insert_default = """
        INSERT INTO template_configs
        (template_name, description, template_type, fields, is_system_default)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (template_name) DO NOTHING;
        """

        import json
        db_manager.execute_query(insert_default, (
            default_template["template_name"],
            default_template["description"],
            default_template["template_type"],
            json.dumps(default_template["fields"]),
            default_template["is_system_default"]
        ))

        print("[SUCCESS] Created default template")

        return True

    except Exception as e:
        print(f"[ERROR] Failed to create template tables: {e}")
        return False

if __name__ == "__main__":
    print("[INIT] Creating template system schema...")
    if create_template_tables():
        print("[COMPLETE] Template system schema created successfully!")
    else:
        print("[FAILED] Template system schema creation failed")