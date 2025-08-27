#!/usr/bin/env python3
"""Enhanced test Flask server with database integration for manual VIN import"""

import sys
import os
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add the scripts directory to Python path for imports
scripts_dir = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

# Import database connection
try:
    from database_connection import db_manager
    DEMO_MODE = False
    print("OK Database connection imported successfully")
except ImportError as e:
    print(f"Warning: Could not import database_connection: {e}")
    DEMO_MODE = True
    db_manager = None

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/')
def home():
    return f"Enhanced Test Server Running! (Database: {'Connected' if not DEMO_MODE else 'Demo Mode'})"

@app.route('/api/test-manual-vin-import', methods=['POST'])
def test_manual_vin_import():
    """Enhanced manual VIN import endpoint with real database integration"""
    try:
        data = request.get_json()
        dealership_name = data.get('dealership_name', 'Unknown')
        vins = data.get('vins', [])
        import_date = data.get('import_date')
        source = data.get('source', 'manual_entry')
        
        if DEMO_MODE or not db_manager:
            # Demo mode - just return success without database operations
            return jsonify({
                'success': True,
                'imported_count': len(vins),
                'message': f'Demo mode: {len(vins)} VINs would be imported for {dealership_name}',
                'demo': True
            })
        
        # Real database integration
        def get_dealership_vin_log_table(dealership_name):
            slug = dealership_name.lower()
            slug = slug.replace(' ', '_')
            slug = slug.replace('&', 'and')
            slug = slug.replace('.', '')
            slug = slug.replace(',', '')
            slug = slug.replace('-', '_')
            slug = slug.replace('/', '_')
            slug = slug.replace("'", '')
            slug = slug.replace('__', '_')
            return f'{slug}_vin_log'
        
        table_name = get_dealership_vin_log_table(dealership_name)
        print(f"Using VIN log table: {table_name}")
        
        # Check if table exists, create if not
        table_check = db_manager.execute_query("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s 
            AND table_name = %s
        """, ('public', table_name))
        
        if not table_check:
            print(f"Creating VIN log table: {table_name}")
            create_table_sql = f"""
            CREATE TABLE {table_name} (
                vin VARCHAR(17) NOT NULL,
                processed_date TIMESTAMP DEFAULT NOW(),
                order_type VARCHAR(50),
                template_type VARCHAR(50),
                order_number VARCHAR(100),
                order_date TIMESTAMP,
                source VARCHAR(50) DEFAULT 'manual_entry',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY (vin, processed_date)
            );
            """
            db_manager.execute_query(create_table_sql)
            print(f"Created VIN log table: {table_name}")
        
        # Process VINs
        imported_count = 0
        errors = []
        
        for vin_data in vins:
            try:
                vin = vin_data['vin'].strip().upper()
                order_number = vin_data.get('order_number', '')
                processed_date = vin_data.get('processed_date', import_date)
                
                if not vin or len(vin) != 17:
                    errors.append(f"Invalid VIN: {vin}")
                    continue
                
                # Check if VIN already exists (prevent duplicates)
                existing_check = db_manager.execute_query(f"""
                    SELECT vin FROM {table_name} WHERE vin = %s
                """, (vin,))
                
                if existing_check:
                    print(f"VIN {vin} already exists in {table_name}, skipping")
                    continue
                
                # Insert VIN into dealership-specific VIN log
                insert_sql = f"""
                    INSERT INTO {table_name} 
                    (vin, order_number, order_date, source, processed_date, order_type, template_type) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                
                db_manager.execute_query(insert_sql, (
                    vin,
                    order_number,
                    processed_date,  # Use as order_date
                    source,
                    processed_date,  # Use as processed_date
                    'manual',        # order_type
                    'manual_entry'   # template_type
                ))
                
                imported_count += 1
                print(f"Imported VIN {vin} to {table_name}")
                
            except Exception as e:
                error_msg = f"Error processing VIN {vin_data.get('vin', 'unknown')}: {str(e)}"
                errors.append(error_msg)
                print(error_msg)
        
        return jsonify({
            'success': True,
            'imported_count': imported_count,
            'errors': errors,
            'dealership': dealership_name,
            'table_name': table_name
        })
        
    except Exception as e:
        print(f"Error in manual VIN import: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting simple test server...")
    app.run(debug=True, port=5001)