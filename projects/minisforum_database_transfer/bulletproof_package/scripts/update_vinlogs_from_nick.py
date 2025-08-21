#!/usr/bin/env python3
"""
Update Dealership VIN Logs from Nick's Data
==========================================

Process Excel VIN log files and update individual dealership VIN log tables.
Maps file names to correct dealership tables and formats data appropriately.
"""

import pandas as pd
import sys
from pathlib import Path
from database_connection import db_manager
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VinLogUpdater:
    def __init__(self):
        # Mapping from file names to dealership table names
        self.file_to_table_mapping = {
            'BOMM_WCPO_VINLOG.xlsx': 'bommarito_west_county_vin_log',
            'DSINCLAIRLINC_VINLOG.xlsx': 'dave_sinclair_lincoln_vin_log', 
            'FRANKLETA_HONDA_VINLOG.xlsx': 'frank_leta_honda_vin_log',
            'HONDAofFRONTENAC_VINLOG.xlsx': 'honda_of_frontenac_vin_log',
            'HW_KIA_VINLOG.xlsx': 'hw_kia_vin_log',
            'Mini_of_St_Louis_VINLOG.xlsx': 'mini_of_st_louis_vin_log',
            'PORSCHESTL_VINLOG.xlsx': 'porsche_st_louis_vin_log',
            'SPIRIT_LEXUS_VINLOG.xlsx': 'spirit_lexus_vin_log',
            'SUNTRUP_FORD_KIRKWOOD_VINLOG.xlsx': 'suntrup_ford_kirkwood_vin_log',
            'SUNTRUP_FORD_WESTPORT_VINLOG.xlsx': 'suntrup_ford_west_vin_log',
            'TBRED_FORD_VINLOG (1).xlsx': 'thoroughbred_ford_vin_log',
            'WEBER_VINLOG (1).xlsx': 'weber_chevrolet_vin_log'
        }
        
        # Common column mappings from Excel to database
        self.column_mappings = {
            'VIN': 'vin',
            'vin': 'vin',
            'Vin': 'vin',
            'DATE': 'processed_date',
            'Date': 'processed_date', 
            'date': 'processed_date',
            'processed_date': 'processed_date',
            'ORDER_TYPE': 'order_type',
            'Order Type': 'order_type',
            'order_type': 'order_type',
            'TYPE': 'order_type',
            'TEMPLATE': 'template_type',
            'Template': 'template_type',
            'template': 'template_type',
            'template_type': 'template_type'
        }

    def process_excel_file(self, file_path: Path) -> pd.DataFrame:
        """Process an Excel file with grouped order structure"""
        logger.info(f"Processing {file_path.name}")
        
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            logger.info(f"Read {len(df)} rows from {file_path.name}")
            
            # Show original columns
            logger.info(f"Original columns: {list(df.columns)}")
            
            # Process the grouped structure
            processed_data = []
            current_order = None
            
            # Look for ORDER and VIN/VINS columns
            order_col = None
            vin_col = None
            
            # Special handling for Dave Sinclair Lincoln - use SOCO VINS column only
            if 'DSINCLAIRLINC' in file_path.name.upper():
                logger.info("Processing Dave Sinclair Lincoln - using SOCO VINS column only")
                for col in df.columns:
                    if 'ORDER' in str(col).upper() and 'SOCO' not in str(col).upper():
                        order_col = col
                    if 'SOCO' in str(col).upper() and 'VIN' in str(col).upper():
                        vin_col = col
                        break
            else:
                # Normal processing for other dealerships
                for col in df.columns:
                    if 'ORDER' in str(col).upper():
                        order_col = col
                    if 'VIN' in str(col).upper():
                        vin_col = col
            
            if not order_col or not vin_col:
                logger.error(f"Could not find ORDER and VIN columns in {file_path.name}")
                logger.error(f"Available columns: {list(df.columns)}")
                return None
            
            logger.info(f"Using ORDER column: {order_col}, VIN column: {vin_col}")
            
            # Process rows sequentially
            for idx, row in df.iterrows():
                order_value = row[order_col]
                vin_value = row[vin_col]
                
                # Check if this row contains an order number
                if pd.notna(order_value) and str(order_value).strip():
                    order_str = str(order_value).strip()
                    # Check if this looks like an order number (not a VIN)
                    if len(order_str) != 17:  # Not VIN length
                        current_order = order_str
                        logger.debug(f"Found order: {current_order}")
                        continue
                    elif len(order_str) == 17 and order_str.replace('-', '').replace('_', '').isalnum():
                        # This might be a VIN in the ORDER column
                        vin_value = order_str
                
                # Check if this row contains a VIN
                if pd.notna(vin_value) and str(vin_value).strip():
                    vin_str = str(vin_value).strip().upper()
                    # Validate VIN (17 characters, alphanumeric)
                    if len(vin_str) == 17 and vin_str.replace('-', '').replace('_', '').isalnum():
                        if current_order:
                            processed_data.append({
                                'vin': vin_str,
                                'order_number': current_order,
                                'processed_date': datetime.now().date(),
                                'order_type': 'CAO',
                                'template_type': 'shortcut_pack'
                            })
                        else:
                            logger.warning(f"Found VIN {vin_str} without an order number")
                
                # Check for blank row (end of order group)
                if pd.isna(order_value) and pd.isna(vin_value):
                    current_order = None
            
            if not processed_data:
                logger.error(f"No valid VIN data found in {file_path.name}")
                return None
            
            # Convert to DataFrame
            df_final = pd.DataFrame(processed_data)
            
            # Remove duplicates (keep first occurrence)
            df_final = df_final.drop_duplicates(subset=['vin'], keep='first')
            
            logger.info(f"Final data: {len(df_final)} VINs with {len(df_final['order_number'].unique())} unique orders")
            return df_final
            
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def update_dealership_table(self, table_name: str, data: pd.DataFrame):
        """Update a dealership VIN log table with new data"""
        logger.info(f"Updating table: {table_name}")
        
        try:
            # First, ensure the table has the order_number column
            try:
                db_manager.execute_query(f"""
                    ALTER TABLE {table_name} 
                    ADD COLUMN IF NOT EXISTS order_number VARCHAR(255)
                """)
                logger.info(f"Ensured order_number column exists in {table_name}")
            except Exception as e:
                logger.warning(f"Could not add order_number column: {e}")
            
            # Clear existing data
            db_manager.execute_query(f"DELETE FROM {table_name}")
            logger.info(f"Cleared existing data from {table_name}")
            
            # Insert new data
            insert_count = 0
            for _, row in data.iterrows():
                db_manager.execute_query(f"""
                    INSERT INTO {table_name} (vin, processed_date, order_type, template_type, order_number)
                    VALUES (%s, %s, %s, %s, %s)
                """, (row['vin'], row['processed_date'], row['order_type'], row['template_type'], row['order_number']))
                insert_count += 1
            
            logger.info(f"Successfully inserted {insert_count} VINs into {table_name}")
            
        except Exception as e:
            logger.error(f"Error updating table {table_name}: {e}")
            raise

    def process_all_files(self, vin_logs_path: Path):
        """Process all VIN log files in the directory"""
        logger.info("Starting VIN log update process")
        
        processed_count = 0
        failed_count = 0
        
        for file_name, table_name in self.file_to_table_mapping.items():
            file_path = vin_logs_path / file_name
            
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                failed_count += 1
                continue
            
            # Process Excel file
            data = self.process_excel_file(file_path)
            if data is None:
                failed_count += 1
                continue
            
            # Update database table
            try:
                self.update_dealership_table(table_name, data)
                processed_count += 1
                logger.info(f"✅ Successfully updated {table_name}")
            except Exception as e:
                logger.error(f"❌ Failed to update {table_name}: {e}")
                failed_count += 1
        
        logger.info(f"VIN log update complete: {processed_count} success, {failed_count} failed")
        return processed_count, failed_count

if __name__ == "__main__":
    vin_logs_path = Path(r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\VIN LOGS")
    
    if not vin_logs_path.exists():
        print(f"Error: VIN logs directory not found: {vin_logs_path}")
        sys.exit(1)
    
    updater = VinLogUpdater()
    success_count, fail_count = updater.process_all_files(vin_logs_path)
    
    print(f"\n=== VIN LOG UPDATE SUMMARY ===")
    print(f"Successfully updated: {success_count} dealerships")
    print(f"Failed updates: {fail_count} dealerships")
    print("VIN log update process complete!")