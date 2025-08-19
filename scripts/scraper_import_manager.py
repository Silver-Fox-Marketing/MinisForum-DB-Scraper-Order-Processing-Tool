#!/usr/bin/env python3
"""
Scraper Import Manager
======================
Manages scraper data imports, archiving, and tracking.
Ensures CAO orders only use the latest import data.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project paths
current_file = Path(__file__).resolve()
scripts_dir = current_file.parent
sys.path.insert(0, str(scripts_dir))

from database_connection import db_manager

logger = logging.getLogger(__name__)

class ScraperImportManager:
    """Manages scraper data imports and archiving"""
    
    def __init__(self):
        self.current_import_id = None
        
    def archive_previous_imports(self):
        """Archive all previous active imports before creating new one"""
        try:
            # Archive previous active imports
            db_manager.execute_query("""
                UPDATE scraper_imports 
                SET status = 'archived', 
                    archived_at = CURRENT_TIMESTAMP
                WHERE status = 'active'
            """)
            
            # Mark all non-archived vehicle data as archived
            db_manager.execute_query("""
                UPDATE raw_vehicle_data 
                SET is_archived = TRUE 
                WHERE is_archived = FALSE OR is_archived IS NULL
            """)
            
            logger.info("Archived all previous imports")
            
        except Exception as e:
            logger.error(f"Error archiving previous imports: {e}")
            raise
    
    def create_new_import(self, source: str = 'automated_scrape', file_name: str = None) -> int:
        """Create a new import session"""
        try:
            # First archive any existing active imports
            self.archive_previous_imports()
            
            # Create new import record
            result = db_manager.execute_query("""
                INSERT INTO scraper_imports 
                (import_date, import_timestamp, import_source, file_name, status)
                VALUES (CURRENT_DATE, CURRENT_TIMESTAMP, %s, %s, 'active')
                RETURNING import_id
            """, (source, file_name))
            
            self.current_import_id = result[0]['import_id']
            logger.info(f"Created new import session: {self.current_import_id}")
            
            return self.current_import_id
            
        except Exception as e:
            logger.error(f"Error creating new import: {e}")
            raise
    
    def update_import_stats(self, import_id: int):
        """Update statistics for an import after vehicles are added"""
        try:
            # Get counts from actual data
            stats = db_manager.execute_query("""
                SELECT 
                    COUNT(DISTINCT vin) as total_vehicles,
                    COUNT(DISTINCT location) as dealerships_count,
                    ARRAY_AGG(DISTINCT location) as dealerships_list
                FROM raw_vehicle_data
                WHERE import_id = %s
            """, (import_id,))
            
            if stats:
                db_manager.execute_query("""
                    UPDATE scraper_imports
                    SET total_vehicles = %s,
                        dealerships_count = %s,
                        dealerships_list = %s
                    WHERE import_id = %s
                """, (
                    stats[0]['total_vehicles'],
                    stats[0]['dealerships_count'],
                    stats[0]['dealerships_list'],
                    import_id
                ))
                
                logger.info(f"Updated import {import_id}: {stats[0]['total_vehicles']} vehicles from {stats[0]['dealerships_count']} dealerships")
                
        except Exception as e:
            logger.error(f"Error updating import stats: {e}")
    
    def get_active_import(self) -> Optional[Dict]:
        """Get the current active import"""
        try:
            result = db_manager.execute_query("""
                SELECT * FROM scraper_imports
                WHERE status = 'active'
                ORDER BY import_timestamp DESC
                LIMIT 1
            """)
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Error getting active import: {e}")
            return None
    
    def get_import_summary(self, limit: int = 50) -> List[Dict]:
        """Get summary of recent imports for display"""
        try:
            imports = db_manager.execute_query("""
                SELECT 
                    si.import_id,
                    si.import_date,
                    si.import_timestamp,
                    si.total_vehicles,
                    si.dealerships_count,
                    si.import_source,
                    si.status,
                    si.file_name,
                    COUNT(DISTINCT rvd.vin) as actual_vehicles,
                    COUNT(DISTINCT rvd.location) as actual_dealerships
                FROM scraper_imports si
                LEFT JOIN raw_vehicle_data rvd ON si.import_id = rvd.import_id
                GROUP BY si.import_id
                ORDER BY si.import_timestamp DESC
                LIMIT %s
            """, (limit,))
            
            return imports
            
        except Exception as e:
            logger.error(f"Error getting import summary: {e}")
            return []
    
    def get_import_vehicles(self, import_id: int, search_term: str = None, 
                           dealership: str = None, limit: int = None) -> List[Dict]:
        """Get vehicles from a specific import with optional filtering"""
        try:
            conditions = ["import_id = %s"]
            params = [import_id]
            
            if search_term:
                # Search by VIN or stock number
                conditions.append("(vin ILIKE %s OR stock ILIKE %s)")
                params.extend([f"%{search_term}%", f"%{search_term}%"])
            
            if dealership:
                conditions.append("location = %s")
                params.append(dealership)
            
            where_clause = " AND ".join(conditions)
            
            query = f"""
                SELECT * FROM raw_vehicle_data
                WHERE {where_clause}
                ORDER BY location, year DESC, make, model
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            vehicles = db_manager.execute_query(query, params)
            return vehicles
            
        except Exception as e:
            logger.error(f"Error getting import vehicles: {e}")
            return []
    
    def search_vehicle_across_imports(self, search_term: str) -> List[Dict]:
        """Search for a specific vehicle across all imports by VIN or stock"""
        try:
            vehicles = db_manager.execute_query("""
                SELECT 
                    rvd.*,
                    si.import_date,
                    si.import_timestamp,
                    si.status as import_status
                FROM raw_vehicle_data rvd
                JOIN scraper_imports si ON rvd.import_id = si.import_id
                WHERE rvd.vin ILIKE %s OR rvd.stock ILIKE %s
                ORDER BY si.import_timestamp DESC, rvd.location
                LIMIT 50
            """, (f"%{search_term}%", f"%{search_term}%"))
            
            return vehicles
            
        except Exception as e:
            logger.error(f"Error searching vehicle: {e}")
            return []
    
    def get_dealership_vin_logs(self) -> List[Dict]:
        """Get list of all dealership VIN log tables"""
        try:
            tables = db_manager.execute_query("""
                SELECT 
                    table_name,
                    REPLACE(REPLACE(table_name, '_vin_log', ''), '_', ' ') as dealership_name
                FROM information_schema.tables
                WHERE table_schema = 'public' 
                AND table_name LIKE '%_vin_log'
                ORDER BY table_name
            """)
            
            # Get counts for each table
            for table in tables:
                try:
                    count_result = db_manager.execute_query(f"""
                        SELECT 
                            COUNT(*) as vin_count,
                            COUNT(DISTINCT order_number) as unique_orders,
                            MIN(processed_date) as earliest_date,
                            MAX(processed_date) as latest_date
                        FROM {table['table_name']}
                    """)
                    if count_result:
                        table['vin_count'] = count_result[0]['vin_count']
                        table['unique_orders'] = count_result[0]['unique_orders'] 
                        table['earliest_date'] = count_result[0]['earliest_date']
                        table['latest_date'] = count_result[0]['latest_date']
                    else:
                        table['vin_count'] = 0
                        table['unique_orders'] = 0
                        table['earliest_date'] = None
                        table['latest_date'] = None
                except:
                    table['vin_count'] = 0
                    table['unique_orders'] = 0
                    table['earliest_date'] = None
                    table['latest_date'] = None
            
            return tables
            
        except Exception as e:
            logger.error(f"Error getting VIN log tables: {e}")
            return []
    
    def get_dealership_vin_history(self, dealership_name: str, limit: int = 1000) -> List[Dict]:
        """Get VIN history for a specific dealership"""
        try:
            # Convert dealership name to table name
            table_name = dealership_name.lower().replace(' ', '_').replace('.', '').replace("'", '') + '_vin_log'
            
            # Check if table exists
            table_check = db_manager.execute_query("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            """, (table_name,))
            
            if not table_check:
                return []
            
            # Get VIN history
            history = db_manager.execute_query(f"""
                SELECT 
                    vin,
                    processed_date,
                    order_number,
                    template_type,
                    created_at
                FROM {table_name}
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting VIN history for {dealership_name}: {e}")
            return []

# Singleton instance
import_manager = ScraperImportManager()