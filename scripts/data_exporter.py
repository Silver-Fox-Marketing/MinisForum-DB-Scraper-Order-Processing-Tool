"""
Data export script for dealership database
Exports filtered data for order processing with QR code paths
"""
import csv
import json
import os
from datetime import datetime, date
from typing import List, Dict, Optional
import pandas as pd
from database_connection import db_manager
from database_config import config
import logging

logger = logging.getLogger(__name__)

class DataExporter:
    """Handles data export with filtering and QR code path generation"""
    
    def __init__(self, db_manager_instance=None):
        self.db = db_manager_instance or db_manager
    
    def get_dealership_config(self, dealership_name: str) -> Dict:
        """Get configuration for a specific dealership"""
        result = self.db.execute_query(
            """
            SELECT filtering_rules, output_rules, qr_output_path
            FROM dealership_configs
            WHERE name = %s AND is_active = true
            """,
            (dealership_name,),
            fetch='one'
        )
        
        if not result:
            logger.warning(f"No active configuration found for {dealership_name}")
            return {
                'filtering_rules': {},
                'output_rules': {},
                'qr_output_path': None
            }
        
        return {
            'filtering_rules': result['filtering_rules'] or {},
            'output_rules': result['output_rules'] or {},
            'qr_output_path': result['qr_output_path']
        }
    
    def apply_filters(self, dealership_name: str, base_query_conditions: List[str] = None) -> str:
        """Build WHERE clause based on dealership filtering rules"""
        config = self.get_dealership_config(dealership_name)
        filters = config['filtering_rules']
        
        conditions = base_query_conditions or []
        
        # Always filter by dealership
        conditions.append(f"n.location = '{dealership_name}'")
        
        # Vehicle condition filters
        if 'exclude_conditions' in filters:
            exclude = "', '".join(filters['exclude_conditions'])
            conditions.append(f"n.vehicle_condition NOT IN ('{exclude}')")
        
        # Stock requirement
        if filters.get('require_stock', True):
            conditions.append("n.stock IS NOT NULL AND n.stock != ''")
        
        # Price filters
        if 'min_price' in filters:
            conditions.append(f"n.price >= {filters['min_price']}")
        if 'max_price' in filters:
            conditions.append(f"n.price <= {filters['max_price']}")
        
        # Year filters
        if 'year_min' in filters:
            conditions.append(f"n.year >= {filters['year_min']}")
        if 'year_max' in filters:
            conditions.append(f"n.year <= {filters['year_max']}")
        
        # Make filters
        if 'exclude_makes' in filters and filters['exclude_makes']:
            exclude_makes = "', '".join(filters['exclude_makes'])
            conditions.append(f"n.make NOT IN ('{exclude_makes}')")
        
        if 'include_only_makes' in filters and filters['include_only_makes']:
            include_makes = "', '".join(filters['include_only_makes'])
            conditions.append(f"n.make IN ('{include_makes}')")
        
        # Model filters
        if 'exclude_models' in filters and filters['exclude_models']:
            exclude_models = "', '".join(filters['exclude_models'])
            conditions.append(f"n.model NOT IN ('{exclude_models}')")
        
        # Recent inventory only (last 7 days by default)
        days_back = filters.get('days_back', 7)
        conditions.append(f"n.last_seen_date >= CURRENT_DATE - INTERVAL '{days_back} days'")
        
        return " AND ".join(conditions)
    
    def export_dealership_data(self, dealership_name: str, output_file: str = None) -> str:
        """Export data for a specific dealership"""
        config = self.get_dealership_config(dealership_name)
        output_rules = config['output_rules']
        qr_path = config['qr_output_path']
        
        # Build query
        where_clause = self.apply_filters(dealership_name)
        
        # Determine fields to select
        default_fields = [
            'n.vin', 'n.stock', 'n.year', 'n.make', 'n.model', 
            'n.trim', 'n.price', 'n.vehicle_condition', 'n.status'
        ]
        
        fields = output_rules.get('fields', default_fields)
        
        # Add QR code path if configured
        if output_rules.get('include_qr', True) and qr_path:
            qr_field = f"'{qr_path}' || n.stock || '.png' as qr_code_path"
            fields.append(qr_field)
        
        # Build the query
        query = f"""
            SELECT {', '.join(fields)}
            FROM normalized_vehicle_data n
            WHERE {where_clause}
        """
        
        # Add sorting
        if 'sort_by' in output_rules:
            sort_fields = ', '.join([f"n.{field}" for field in output_rules['sort_by']])
            query += f" ORDER BY {sort_fields}"
        else:
            query += " ORDER BY n.make, n.model, n.year"
        
        # Execute query
        logger.info(f"Exporting data for {dealership_name}")
        results = self.db.execute_query(query)
        
        if not results:
            logger.warning(f"No data found for {dealership_name}")
            return None
        
        # Determine output file path
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(
                config.export_path,
                f"{dealership_name}_{timestamp}.csv"
            )
        
        # Write to CSV
        df = pd.DataFrame(results)
        
        # Group by condition if specified
        if output_rules.get('group_by') == 'vehicle_condition':
            df = df.sort_values(['vehicle_condition', 'make', 'model'])
        
        df.to_csv(output_file, index=False)
        logger.info(f"Exported {len(results)} vehicles to {output_file}")
        
        return output_file
    
    def export_all_active_dealerships(self, output_dir: str = None) -> List[str]:
        """Export data for all active dealerships"""
        # Get all active dealerships
        dealerships = self.db.execute_query(
            "SELECT name FROM dealership_configs WHERE is_active = true"
        )
        
        if not output_dir:
            output_dir = os.path.join(config.export_path, 
                                    datetime.now().strftime('%Y%m%d_%H%M%S'))
        
        os.makedirs(output_dir, exist_ok=True)
        
        exported_files = []
        
        for dealership in dealerships:
            try:
                output_file = os.path.join(output_dir, f"{dealership['name']}.csv")
                file_path = self.export_dealership_data(dealership['name'], output_file)
                if file_path:
                    exported_files.append(file_path)
            except Exception as e:
                logger.error(f"Failed to export {dealership['name']}: {e}")
        
        logger.info(f"Exported {len(exported_files)} dealership files to {output_dir}")
        return exported_files
    
    def export_duplicate_vins_report(self, output_file: str = None) -> str:
        """Export report of VINs appearing at multiple dealerships"""
        query = """
            WITH duplicate_vins AS (
                SELECT 
                    vin,
                    COUNT(DISTINCT location) as location_count,
                    array_agg(DISTINCT location ORDER BY location) as locations,
                    MAX(last_seen_date) as most_recent_date
                FROM normalized_vehicle_data
                WHERE last_seen_date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY vin
                HAVING COUNT(DISTINCT location) > 1
            )
            SELECT 
                dv.vin,
                dv.location_count,
                array_to_string(dv.locations, ', ') as dealerships,
                n.year,
                n.make,
                n.model,
                n.trim,
                n.price,
                n.location as current_location,
                dv.most_recent_date
            FROM duplicate_vins dv
            JOIN normalized_vehicle_data n ON dv.vin = n.vin
            WHERE n.last_seen_date = dv.most_recent_date
            ORDER BY dv.location_count DESC, n.make, n.model
        """
        
        results = self.db.execute_query(query)
        
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(
                config.export_path,
                f"duplicate_vins_report_{timestamp}.csv"
            )
        
        df = pd.DataFrame(results)
        df.to_csv(output_file, index=False)
        
        logger.info(f"Exported {len(results)} duplicate VINs to {output_file}")
        return output_file
    
    def export_inventory_summary(self, output_file: str = None) -> str:
        """Export summary statistics by dealership"""
        query = """
            SELECT 
                n.location as dealership,
                n.vehicle_condition,
                COUNT(*) as vehicle_count,
                AVG(n.price)::numeric(10,2) as avg_price,
                MIN(n.price)::numeric(10,2) as min_price,
                MAX(n.price)::numeric(10,2) as max_price,
                COUNT(DISTINCT n.make) as unique_makes,
                COUNT(DISTINCT n.model) as unique_models
            FROM normalized_vehicle_data n
            JOIN dealership_configs d ON n.location = d.name
            WHERE n.last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
                AND d.is_active = true
            GROUP BY n.location, n.vehicle_condition
            ORDER BY n.location, n.vehicle_condition
        """
        
        results = self.db.execute_query(query)
        
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(
                config.export_path,
                f"inventory_summary_{timestamp}.csv"
            )
        
        df = pd.DataFrame(results)
        df.to_csv(output_file, index=False)
        
        logger.info(f"Exported inventory summary to {output_file}")
        return output_file

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Export dealership data')
    parser.add_argument('--dealership', help='Export specific dealership')
    parser.add_argument('--all', action='store_true', help='Export all active dealerships')
    parser.add_argument('--duplicates', action='store_true', help='Export duplicate VINs report')
    parser.add_argument('--summary', action='store_true', help='Export inventory summary')
    parser.add_argument('--output', help='Output file/directory path')
    
    args = parser.parse_args()
    
    exporter = DataExporter()
    
    try:
        if args.dealership:
            output = exporter.export_dealership_data(args.dealership, args.output)
            print(f"Exported to: {output}")
        
        elif args.all:
            files = exporter.export_all_active_dealerships(args.output)
            print(f"Exported {len(files)} dealership files")
        
        elif args.duplicates:
            output = exporter.export_duplicate_vins_report(args.output)
            print(f"Duplicate VINs report: {output}")
        
        elif args.summary:
            output = exporter.export_inventory_summary(args.output)
            print(f"Inventory summary: {output}")
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"Export failed: {e}")
        raise

if __name__ == "__main__":
    main()