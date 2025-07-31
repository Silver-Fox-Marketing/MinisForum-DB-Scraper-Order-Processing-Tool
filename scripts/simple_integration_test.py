#!/usr/bin/env python3
"""
Simple Integration Test
=======================

Tests the core QR-before-CSV functionality without VIN comparison complexity.

Author: Silver Fox Assistant  
Created: 2025-07-29
"""

import os
import sys
import csv
import json
import logging
from datetime import datetime
from pathlib import Path

# Add project paths
current_file = Path(__file__).resolve()
scripts_dir = current_file.parent
sys.path.insert(0, str(scripts_dir))

from database_connection import db_manager
from order_processing_workflow import OrderProcessingWorkflow

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_qr_csv_integration():
    """Test QR generation before CSV with real database data"""
    logger.info("🚀 TESTING QR-BEFORE-CSV INTEGRATION")
    logger.info("=" * 50)
    
    try:
        workflow = OrderProcessingWorkflow()
        
        # Get real vehicles from database with URLs
        vehicles = db_manager.execute_query("""
            SELECT vin, stock, make, model, year, vehicle_url, location, type
            FROM raw_vehicle_data 
            WHERE location = %s 
            AND vehicle_url IS NOT NULL 
            LIMIT 5
        """, ('Columbia Honda',))
        
        logger.info(f"Found {len(vehicles)} vehicles with URLs")
        
        if not vehicles:
            logger.error("No vehicles found!")
            return False
        
        # Show sample data
        for i, vehicle in enumerate(vehicles[:2]):
            logger.info(f"Vehicle {i+1}: {vehicle['year']} {vehicle['make']} {vehicle['model']} - VIN: {vehicle['vin']}")
            logger.info(f"  URL: {vehicle['vehicle_url']}")
        
        # Create test folders
        test_output = Path("simple_test_output")
        qr_folder = test_output / "qr_codes"
        csv_folder = test_output / "adobe"
        
        qr_folder.mkdir(parents=True, exist_ok=True)
        csv_folder.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Generate QR codes FIRST
        logger.info("\n📱 Step 1: Generating QR codes...")
        qr_paths = workflow.generate_qr_codes(vehicles, 'Columbia Honda', qr_folder)
        
        logger.info(f"Generated {len(qr_paths)} QR codes")
        for path in qr_paths[:3]:  # Show first 3
            logger.info(f"  QR: {path}")
        
        # Verify QR files exist
        qr_files_exist = all(os.path.exists(path) for path in qr_paths)
        logger.info(f"QR files exist: {qr_files_exist}")
        
        # Step 2: Generate Adobe CSV with QR paths
        logger.info("\n📊 Step 2: Generating Adobe CSV with QR paths...")
        csv_path = workflow.generate_adobe_csv(vehicles, 'Columbia Honda', csv_folder, qr_paths)
        
        logger.info(f"CSV file created: {csv_path}")
        
        # Step 3: Verify CSV content
        logger.info("\n✅ Step 3: Verifying CSV contains QR paths...")
        
        if not os.path.exists(csv_path):
            logger.error("CSV file doesn't exist!")
            return False
        
        # Read and analyze CSV
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            rows = list(reader)
        
        logger.info(f"CSV headers: {headers}")
        logger.info(f"CSV contains {len(rows)} rows")
        
        # Check for QR_Code_Path column
        has_qr_column = 'QR_Code_Path' in headers
        logger.info(f"Has QR_Code_Path column: {has_qr_column}")
        
        # Check QR paths in rows
        qr_paths_in_csv = [row.get('QR_Code_Path', '') for row in rows if row.get('QR_Code_Path')]
        logger.info(f"Rows with QR paths: {len(qr_paths_in_csv)}")
        
        # Show sample CSV data
        if rows:
            logger.info("\nSample CSV row:")
            sample_row = rows[0]
            for key, value in sample_row.items():
                if value:  # Only show non-empty values
                    logger.info(f"  {key}: {value}")
        
        # Final verification
        success = (
            qr_files_exist and 
            has_qr_column and 
            len(qr_paths_in_csv) > 0 and
            len(qr_paths) == len(qr_paths_in_csv)
        )
        
        logger.info("\n🏆 RESULTS:")
        logger.info(f"QR files generated: {len(qr_paths)}")
        logger.info(f"QR files exist: {qr_files_exist}")
        logger.info(f"CSV has QR column: {has_qr_column}")
        logger.info(f"CSV rows with QR paths: {len(qr_paths_in_csv)}")
        logger.info(f"Paths match: {len(qr_paths) == len(qr_paths_in_csv)}")
        
        if success:
            logger.info("🎉 SUCCESS: QR-before-CSV integration working correctly!")
        else:
            logger.error("❌ FAILED: Integration issues detected")
        
        return success
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_list_order_processing():
    """Test list-based order processing with real VINs"""
    logger.info("\n🚀 TESTING LIST ORDER PROCESSING")
    logger.info("=" * 50)
    
    try:
        workflow = OrderProcessingWorkflow()
        
        # Get some real VINs from database
        vins_data = db_manager.execute_query("""
            SELECT vin FROM raw_vehicle_data 
            WHERE location = %s 
            AND vehicle_url IS NOT NULL 
            LIMIT 3
        """, ('Columbia Honda',))
        
        test_vins = [row['vin'] for row in vins_data]
        logger.info(f"Testing with VINs: {test_vins}")
        
        # Process list order
        result = workflow.process_list_order('Columbia Honda', test_vins)
        
        logger.info(f"List order result: {result}")
        
        success = result['success'] and result['found_vehicles'] > 0
        
        if success:
            logger.info("🎉 SUCCESS: List order processing working!")
        else:
            logger.error("❌ FAILED: List order processing issues")
        
        return success
        
    except Exception as e:
        logger.error(f"List order test failed: {e}")
        return False

def main():
    """Run simple integration tests"""
    logger.info("SIMPLE INTEGRATION TESTS")
    logger.info("=" * 60)
    
    test1_success = test_qr_csv_integration()
    test2_success = test_list_order_processing()
    
    total_tests = 2
    passed_tests = sum([test1_success, test2_success])
    success_rate = (passed_tests / total_tests) * 100
    
    logger.info("\n" + "=" * 60)
    logger.info("📊 FINAL RESULTS")
    logger.info("=" * 60)
    logger.info(f"Total tests: {total_tests}")
    logger.info(f"Passed: {passed_tests}")
    logger.info(f"Failed: {total_tests - passed_tests}")
    logger.info(f"Success rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        logger.info("🎉 ALL TESTS PASSED!")
        return True
    else:
        logger.warning("⚠️ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)