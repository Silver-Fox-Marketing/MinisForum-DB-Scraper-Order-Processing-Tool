#!/usr/bin/env python3
"""
Import Updated VIN Logs with Order Number Grouping
=================================================

This script imports updated VIN logs from Excel files with proper order number assignment.
Each VIN gets the order number that appears to the left of the first VIN in its group.
Empty rows separate different order groups.

Author: Silver Fox Assistant
Created: 2025-08-18
"""

import os
import sys
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add project paths
current_file = Path(__file__).resolve()
scripts_dir = current_file.parent
sys.path.insert(0, str(scripts_dir))

from database_connection import db_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vin_log_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VINLogImporter:
    """Import VIN logs with order number grouping"""
    
    def __init__(self):
        self.vin_logs_path = Path("C:/Users/Workstation_1/Documents/Tools/ClaudeCode/projects/shared_resources/VIN LOGS")
        self.dealership_mapping = self._create_dealership_mapping()
        
    def _create_dealership_mapping(self) -> Dict[str, str]:
        """Create mapping from file names to dealership table names"""
        return {
            "AUDIRANCHOMIRAGE_VINLOG.xlsx": "audi_ranch_mirage_vin_log",
            "AUFFENBERG_HYUNDAI_VINLOG.xlsx": "auffenberg_hyundai_vin_log", 
            "BMW_WEST_STL_VINLOG.xlsx": "bmw_of_west_st_louis_vin_log",
            "BOMM_CADILLAC_VINLOG.xlsx": "bommarito_cadillac_vin_log",
            "BOMM_WCPO_VINLOG.xlsx": "bommarito_west_county_vin_log",
            "COMOBMW_VINLOG.xlsx": "columbia_bmw_vin_log",
            "COMO_HONDA_VINLOG.xlsx": "columbia_honda_vin_log",
            "DAVESINCLAIRSTPETERS_VINLOG.xlsx": "dave_sinclair_lincoln_st_peters_vin_log",
            "DSINCLAIRLINC_VINLOG.xlsx": "dave_sinclair_lincoln_vin_log",
            "FRANKLETA_HONDA_VINLOG.xlsx": "frank_leta_honda_vin_log",
            "GLENDALE_VINLOG.xlsx": "glendale_chrysler_jeep_vin_log",
            "HONDAofFRONTENAC_VINLOG.xlsx": "honda_of_frontenac_vin_log",
            "HW_KIA_VINLOG.xlsx": "hw_kia_vin_log",
            "INDIGOAUTOGROUP_VINLOG.xlsx": "indigo_auto_group_vin_log",
            "JAGUARRANCHOMIRAGE_VINLOG.xlsx": "jaguar_ranch_mirage_vin_log",
            "JM NISSAN LOG.xlsx": "joe_machens_nissan_vin_log",
            "JMCDJR_VINLOG.xlsx": "joe_machens_cdjr_vin_log",
            "JMHYUNDAI_VINLOG.xlsx": "joe_machens_hyundai_vin_log",
            "JM_TOYOTA_VINLOG.xlsx": "joe_machens_toyota_vin_log",
            "KIACOMO_VINLOG.xlsx": "kia_of_columbia_vin_log",
            "LANDROVERRANCHOMIRAGE_VINLOG.xlsx": "land_rover_ranch_mirage_vin_log",
            "Mini_of_St_Louis_VINLOG.xlsx": "mini_of_st_louis_vin_log",
            "PAPPAS_TOYOTA_VINLOG.xlsx": "pappas_toyota_vin_log",
            "PORSCHESTL_VINLOG.xlsx": "porsche_st_louis_vin_log",
            "PUNDMANN_VINLOG.xlsx": "pundmann_ford_vin_log",
            "RDCADILLAC_VINLOG.xlsx": "rusty_drewing_cadillac_vin_log",
            "RDCHEVY_VINLOG.xlsx": "rusty_drewing_chevrolet_vin_log",
            "SERRAHONDA_VINLOG.xlsx": "serra_honda_ofallon_vin_log",
            "SOCODCJR_VINLOG.xlsx": "south_county_autos_vin_log",
            "SPIRIT_LEXUS_VINLOG.xlsx": "spirit_lexus_vin_log",
            "SUNTRUP_BGMC_VINLOG.xlsx": "suntrup_buick_gmc_vin_log",
            "SUNTRUP_FORD_KIRKWOOD_VINLOG.xlsx": "suntrup_ford_kirkwood_vin_log",
            "SUNTRUP_FORD_WESTPORT_VINLOG.xlsx": "suntrup_ford_west_vin_log",
            "SUNTRUP_HYUNDAI_VINLOG.xlsx": "suntrup_hyundai_south_vin_log",
            "SUNTRUP_KIA_VINLOG.xlsx": "suntrup_kia_south_vin_log",
            "TBRED_FORD_VINLOG.xlsx": "thoroughbred_ford_vin_log",
            "TOMSTEHOUWER_VINLOG.xlsx": "stehouwer_auto_vin_log",
            "TWINCITYTOYO_VINLOG.xlsx": "twin_city_toyota_vin_log",
            "VOLVO_WC_VINLOG.xlsx": "west_county_volvo_cars_vin_log",
            "WEBER_VINLOG.xlsx": "weber_chevrolet_vin_log"
        }
    
    def delete_all_vin_logs(self):
        """Delete all existing dealership VIN log tables"""
        logger.info("🗑️  DELETING ALL EXISTING VIN LOG TABLES")
        
        try:
            # Get all VIN log tables
            tables = db_manager.execute_query("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%_vin_log'
                ORDER BY table_name
            """)
            
            logger.info(f"Found {len(tables)} VIN log tables to delete")
            
            for table in tables:
                table_name = table['table_name']
                try:
                    db_manager.execute_query(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                    logger.info(f"✅ Deleted table: {table_name}")
                except Exception as e:
                    logger.error(f"❌ Error deleting {table_name}: {e}")
                    
            logger.info("🎯 All VIN log tables deleted successfully")
            
        except Exception as e:
            logger.error(f"❌ Error during VIN log deletion: {e}")
            raise
    
    def parse_excel_with_order_numbers(self, file_path: Path) -> List[Tuple[str, str]]:
        """
        Parse Excel file to extract VINs with their order numbers
        Expected format: Column 0 = Order Number, Column 1 = VIN
        Returns list of (vin, order_number) tuples
        """
        try:
            # Read Excel file - get all data as strings to preserve formatting
            df = pd.read_excel(file_path, dtype=str, header=None)
            
            vin_order_pairs = []
            current_order_number = None
            
            logger.info(f"📊 Processing Excel file: {file_path.name}")
            logger.info(f"   Rows: {len(df)}, Columns: {len(df.columns)}")
            
            for index, row in df.iterrows():
                # Skip header row if it contains "ORDER" and "VINS"
                if index == 0:
                    row_str = str(row.values).lower()
                    if 'order' in row_str and 'vin' in row_str:
                        logger.debug(f"   Skipping header row: {row.values}")
                        continue
                
                # Extract column values
                col_0 = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
                col_1 = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) and len(df.columns) > 1 else ''
                
                # Skip completely empty rows
                if (col_0 == '' or col_0 == 'nan') and (col_1 == '' or col_1 == 'nan'):
                    logger.debug(f"   Empty row at {index} - continuing")
                    continue
                
                # Check if column 0 has an order number (not empty, not 'nan')
                if col_0 != '' and col_0 != 'nan' and col_0.lower() != 'empty':
                    # This could be a new order number
                    # Check if it looks like an order (not a VIN)
                    if (len(col_0) < 20 and  # Order numbers are shorter than VINs
                        (col_0.lower() == 'baseline' or
                         any(c.isalpha() for c in col_0) or
                         len(col_0) < 10)):  # VINs are typically 17 characters
                        current_order_number = col_0
                        logger.info(f"🏷️  New order group: {current_order_number}")
                
                # Check if column 1 has a VIN
                if col_1 != '' and col_1 != 'nan':
                    # Validate that this looks like a VIN
                    if (len(col_1) >= 10 and  # VINs are usually 17 chars, being flexible
                        col_1.replace('-', '').replace('_', '').isalnum()):
                        if current_order_number:
                            vin_order_pairs.append((col_1, current_order_number))
                            logger.debug(f"   Added VIN: {col_1} -> {current_order_number}")
                        else:
                            # VIN without order number - assign a default
                            default_order = f"UNKNOWN_ORDER_{index}"
                            vin_order_pairs.append((col_1, default_order))
                            logger.warning(f"⚠️  VIN without order number: {col_1} -> {default_order}")
            
            logger.info(f"✅ Extracted {len(vin_order_pairs)} VIN-Order pairs from {file_path.name}")
            
            # Show order summary
            order_counts = {}
            for vin, order in vin_order_pairs:
                order_counts[order] = order_counts.get(order, 0) + 1
            
            logger.info("📋 Order Summary:")
            for order, count in order_counts.items():
                logger.info(f"   {order}: {count} VINs")
            
            return vin_order_pairs
            
        except Exception as e:
            logger.error(f"❌ Error parsing {file_path}: {e}")
            return []
    
    def create_vin_log_table(self, table_name: str):
        """Create a VIN log table for a dealership"""
        try:
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                vin VARCHAR(50) PRIMARY KEY,
                order_number VARCHAR(100),
                processed_date DATE NOT NULL DEFAULT CURRENT_DATE,
                order_type VARCHAR(20) DEFAULT 'HISTORICAL',
                template_type VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            db_manager.execute_query(create_sql)
            logger.info(f"✅ Created table: {table_name}")
            
        except Exception as e:
            logger.error(f"❌ Error creating table {table_name}: {e}")
            raise
    
    def import_vin_log_file(self, file_path: Path, table_name: str) -> Dict[str, Any]:
        """Import a single VIN log file"""
        try:
            logger.info(f"🔄 Importing {file_path.name} -> {table_name}")
            
            # Parse Excel file to get VIN-Order pairs
            vin_order_pairs = self.parse_excel_with_order_numbers(file_path)
            
            if not vin_order_pairs:
                logger.warning(f"⚠️  No VIN-Order pairs found in {file_path.name}")
                return {
                    'success': False,
                    'file': file_path.name,
                    'table': table_name,
                    'error': 'No VINs found',
                    'vins_imported': 0
                }
            
            # Create table
            self.create_vin_log_table(table_name)
            
            # Import VINs with order numbers
            imported_count = 0
            for vin, order_number in vin_order_pairs:
                try:
                    insert_sql = f"""
                    INSERT INTO {table_name} (vin, order_number, processed_date, order_type)
                    VALUES (%s, %s, CURRENT_DATE, 'HISTORICAL')
                    ON CONFLICT (vin) DO UPDATE SET 
                        order_number = EXCLUDED.order_number,
                        imported_at = CURRENT_TIMESTAMP
                    """
                    db_manager.execute_query(insert_sql, (vin, order_number))
                    imported_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error inserting VIN {vin}: {e}")
            
            logger.info(f"✅ Imported {imported_count} VINs to {table_name}")
            
            return {
                'success': True,
                'file': file_path.name,
                'table': table_name,
                'vins_imported': imported_count,
                'total_pairs': len(vin_order_pairs)
            }
            
        except Exception as e:
            logger.error(f"❌ Error importing {file_path}: {e}")
            return {
                'success': False,
                'file': file_path.name,
                'table': table_name,
                'error': str(e),
                'vins_imported': 0
            }
    
    def import_all_vin_logs(self):
        """Import all VIN log files"""
        logger.info("🚀 STARTING VIN LOG IMPORT WITH ORDER NUMBERS")
        logger.info(f"📁 Source directory: {self.vin_logs_path}")
        
        if not self.vin_logs_path.exists():
            logger.error(f"❌ VIN logs directory not found: {self.vin_logs_path}")
            return
        
        # Get all Excel files
        excel_files = list(self.vin_logs_path.glob("*.xlsx"))
        logger.info(f"📊 Found {len(excel_files)} Excel files to process")
        
        results = []
        
        for file_path in excel_files:
            file_name = file_path.name
            
            if file_name in self.dealership_mapping:
                table_name = self.dealership_mapping[file_name]
                result = self.import_vin_log_file(file_path, table_name)
                results.append(result)
            else:
                logger.warning(f"⚠️  Unknown file: {file_name} (no mapping found)")
                results.append({
                    'success': False,
                    'file': file_name,
                    'table': 'unknown',
                    'error': 'No mapping found',
                    'vins_imported': 0
                })
        
        # Summary
        logger.info("📊 IMPORT SUMMARY")
        total_vins = 0
        successful_files = 0
        
        for result in results:
            if result['success']:
                logger.info(f"✅ {result['file']}: {result['vins_imported']} VINs imported")
                total_vins += result['vins_imported']
                successful_files += 1
            else:
                logger.error(f"❌ {result['file']}: {result.get('error', 'Unknown error')}")
        
        logger.info(f"🎯 FINAL RESULTS: {successful_files}/{len(results)} files processed successfully")
        logger.info(f"🎯 TOTAL VINS IMPORTED: {total_vins}")
        
        return results
    
    def verify_import(self):
        """Verify the import by checking table counts and order numbers"""
        logger.info("🔍 VERIFYING IMPORT RESULTS")
        
        try:
            # Get all VIN log tables
            tables = db_manager.execute_query("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%_vin_log'
                ORDER BY table_name
            """)
            
            total_vins = 0
            
            for table in tables:
                table_name = table['table_name']
                
                # Get count and sample data
                count_result = db_manager.execute_query(f"""
                    SELECT COUNT(*) as total_vins,
                           COUNT(DISTINCT order_number) as unique_orders
                    FROM {table_name}
                """)
                
                sample_result = db_manager.execute_query(f"""
                    SELECT vin, order_number 
                    FROM {table_name} 
                    ORDER BY created_at 
                    LIMIT 3
                """)
                
                count_data = count_result[0]
                total_vins += count_data['total_vins']
                
                logger.info(f"📋 {table_name}:")
                logger.info(f"   VINs: {count_data['total_vins']}")
                logger.info(f"   Orders: {count_data['unique_orders']}")
                
                if sample_result:
                    logger.info("   Sample VINs:")
                    for sample in sample_result[:3]:
                        logger.info(f"     {sample['vin']} -> {sample['order_number']}")
            
            logger.info(f"🎯 VERIFICATION COMPLETE: {total_vins} total VINs across {len(tables)} tables")
            
        except Exception as e:
            logger.error(f"❌ Error during verification: {e}")

def main():
    """Main execution function"""
    importer = VINLogImporter()
    
    try:
        # Step 1: Delete existing VIN logs
        importer.delete_all_vin_logs()
        
        # Step 2: Import updated VIN logs with order numbers
        results = importer.import_all_vin_logs()
        
        # Step 3: Verify the import
        importer.verify_import()
        
        logger.info("🎉 VIN LOG IMPORT WITH ORDER NUMBERS COMPLETED SUCCESSFULLY!")
        
    except Exception as e:
        logger.error(f"💥 FATAL ERROR: {e}")
        raise

if __name__ == "__main__":
    main()