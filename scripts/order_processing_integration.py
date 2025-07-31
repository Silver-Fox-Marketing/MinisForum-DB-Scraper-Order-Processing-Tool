#!/usr/bin/env python3
"""
Order Processing Integration for MinisForum Database
===================================================

This module provides the interface between the database system and the 
order processing/QR generation tool. It handles:

1. Order processing job management
2. QR code file tracking and validation
3. Data export for Adobe Illustrator workflows
4. Integration with dealership-specific configurations

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import os
import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
from database_connection import db_manager
from qr_code_generator import QRCodeGenerator

logger = logging.getLogger(__name__)

class OrderProcessingIntegrator:
    """Handles integration between database and order processing tools"""
    
    def __init__(self, db_manager_instance=None):
        self.db = db_manager_instance or db_manager
        self.qr_generator = QRCodeGenerator(self.db)
        self.base_qr_path = Path("C:/qr_codes")
        self.base_export_path = Path("C:/exports")
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        try:
            self.base_qr_path.mkdir(parents=True, exist_ok=True)
            self.base_export_path.mkdir(parents=True, exist_ok=True)
            
            # Create dealership-specific QR directories
            configs = self.get_active_dealership_configs()
            for config in configs:
                qr_path = Path(config['qr_output_path'])
                qr_path.mkdir(parents=True, exist_ok=True)
                
        except Exception as e:
            logger.warning(f"Could not create directories: {e}")
    
    def get_active_dealership_configs(self) -> List[Dict]:
        """Get all active dealership configurations"""
        try:
            return self.db.execute_query("""
                SELECT name, filtering_rules, output_rules, qr_output_path, is_active
                FROM dealership_configs 
                WHERE is_active = true
                ORDER BY name
            """)
        except Exception as e:
            logger.error(f"Failed to get dealership configs: {e}")
            return []
    
    def create_order_processing_job(self, 
                                   dealership_name: str,
                                   job_type: str = "standard",
                                   filters: Optional[Dict] = None) -> Dict:
        """
        Create a new order processing job
        
        Args:
            dealership_name: Name of the dealership
            job_type: Type of job (standard, premium, custom)
            filters: Additional filters to apply
            
        Returns:
            Job details with file paths and vehicle count
        """
        try:
            # Get dealership config
            config = self.db.execute_query("""
                SELECT * FROM dealership_configs 
                WHERE name = %s AND is_active = true
            """, (dealership_name,))
            
            if not config:
                raise ValueError(f"No active configuration found for {dealership_name}")
            
            config = config[0]
            # Handle both string and dict JSON data from PostgreSQL
            filtering_rules = config['filtering_rules'] if isinstance(config['filtering_rules'], dict) else (json.loads(config['filtering_rules']) if config['filtering_rules'] else {})
            output_rules = config['output_rules'] if isinstance(config['output_rules'], dict) else (json.loads(config['output_rules']) if config['output_rules'] else {})
            
            # Apply additional filters if provided
            if filters:
                filtering_rules.update(filters)
            
            # Build query for vehicles
            base_query = """
                SELECT 
                    n.vin, n.stock, n.year, n.make, n.model, n.trim,
                    n.price, n.msrp, n.vehicle_condition, n.last_seen_date,
                    d.qr_output_path
                FROM normalized_vehicle_data n
                JOIN dealership_configs d ON n.location = d.name
                WHERE n.location = %s 
                AND n.last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
                AND d.is_active = true
            """
            
            query_params = [dealership_name]
            
            # Apply filtering rules
            if filtering_rules.get('exclude_conditions'):
                excluded = filtering_rules['exclude_conditions']
                placeholders = ','.join(['%s'] * len(excluded))
                base_query += f" AND n.vehicle_condition NOT IN ({placeholders})"
                query_params.extend(excluded)
            
            if filtering_rules.get('min_price'):
                base_query += " AND n.price >= %s"
                query_params.append(filtering_rules['min_price'])
            
            if filtering_rules.get('max_price'):
                base_query += " AND n.price <= %s"
                query_params.append(filtering_rules['max_price'])
            
            if filtering_rules.get('year_min'):
                base_query += " AND n.year >= %s"
                query_params.append(filtering_rules['year_min'])
            
            if filtering_rules.get('year_max'):
                base_query += " AND n.year <= %s"
                query_params.append(filtering_rules['year_max'])
            
            if filtering_rules.get('require_stock'):
                base_query += " AND n.stock IS NOT NULL AND n.stock != ''"
            
            # Apply sorting from output rules
            sort_fields = output_rules.get('sort_by', ['make', 'model', 'year'])
            base_query += f" ORDER BY {', '.join(f'n.{field}' for field in sort_fields)}"
            
            # Execute query
            vehicles = self.db.execute_query(base_query, query_params)
            
            # Create job record
            job_id = self.create_job_record(dealership_name, job_type, len(vehicles))
            
            # Generate export file
            export_filename = f"{dealership_name.replace(' ', '_').lower()}_{job_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            export_path = self.base_export_path / export_filename
            
            # Create DataFrame and export
            if vehicles:
                df = pd.DataFrame(vehicles)
                
                # Add QR code paths
                df['qr_code_path'] = df.apply(
                    lambda row: self.generate_qr_path(row['vin'], config['qr_output_path']), 
                    axis=1
                )
                
                # Apply field selection from output rules
                if output_rules.get('fields'):
                    available_fields = [f for f in output_rules['fields'] if f in df.columns]
                    df = df[available_fields + ['qr_code_path']]
                
                df.to_csv(export_path, index=False)
                
                # Generate QR codes for all vehicles
                qr_results = self.generate_qr_codes_for_job(vehicles, job_id)
                
                # Update job record with file path and QR status
                self.update_job_record(job_id, str(export_path), len(vehicles), qr_results)
                
                logger.info(f"Created order processing job {job_id} for {dealership_name}: {len(vehicles)} vehicles, {qr_results['success']} QR codes generated")
                
                return {
                    'success': True,
                    'job_id': job_id,
                    'dealership': dealership_name,
                    'job_type': job_type,
                    'vehicle_count': len(vehicles),
                    'vehicles': vehicles,
                    'export_file': str(export_path),
                    'qr_output_path': config['qr_output_path'],
                    'qr_generation': qr_results,
                    'created_at': datetime.now().isoformat()
                }
            else:
                logger.warning(f"No vehicles found for {dealership_name} with current filters")
                return {
                    'success': False,
                    'job_id': job_id,
                    'dealership': dealership_name,
                    'vehicle_count': 0,
                    'export_file': None,
                    'error': 'No vehicles match the filtering criteria'
                }
                
        except Exception as e:
            logger.error(f"Failed to create order processing job for {dealership_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'dealership': dealership_name
            }
    
    def generate_qr_path(self, vin: str, base_qr_path: str) -> str:
        """Generate QR code file path for a VIN"""
        return os.path.join(base_qr_path, f"{vin}.png")
    
    def create_job_record(self, dealership_name: str, job_type: str, vehicle_count: int) -> int:
        """Create a job record in the database"""
        try:
            # First ensure the order_processing_jobs table exists
            self.ensure_order_processing_tables()
            
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO order_processing_jobs 
                    (dealership_name, job_type, vehicle_count, status, created_at)
                    VALUES (%s, %s, %s, 'created', CURRENT_TIMESTAMP)
                    RETURNING id
                """, (dealership_name, job_type, vehicle_count))
                result = cursor.fetchone()
            
            return result['id']
            
        except Exception as e:
            logger.error(f"Failed to create job record: {e}")
            # Return a temporary ID if database fails
            return int(datetime.now().timestamp())
    
    def update_job_record(self, job_id: int, export_file: str, final_count: int, qr_results: Optional[Dict] = None):
        """Update job record with completion details"""
        try:
            notes = ""
            if qr_results:
                notes = f"QR Codes - Success: {qr_results['success']}, Failed: {qr_results['failed']}, Skipped: {qr_results['skipped']}"
            
            self.db.execute_non_query("""
                UPDATE order_processing_jobs 
                SET export_file = %s, 
                    final_vehicle_count = %s,
                    status = 'completed',
                    completed_at = CURRENT_TIMESTAMP,
                    notes = %s
                WHERE id = %s
            """, (export_file, final_count, notes, job_id))
            
        except Exception as e:
            logger.warning(f"Could not update job record {job_id}: {e}")
    
    def generate_qr_codes_for_job(self, vehicles: List[Dict], job_id: int) -> Dict:
        """Generate QR codes for all vehicles in a job"""
        results = {
            'total': len(vehicles),
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        for vehicle in vehicles:
            try:
                # Check if QR already exists and is valid
                if self.qr_generator.verify_qr_file_exists(vehicle['vin'], vehicle['location']):
                    results['skipped'] += 1
                    continue
                
                # Generate QR code
                success, message = self.qr_generator.generate_qr_code(
                    vehicle['vin'], 
                    vehicle['stock'], 
                    vehicle['location']
                )
                
                if success:
                    results['success'] += 1
                    # Update QR tracking with job ID
                    self.db.execute_query("""
                        UPDATE qr_file_tracking 
                        SET job_id = %s 
                        WHERE vin = %s AND dealership_name = %s
                    """, (job_id, vehicle['vin'], vehicle['location']))
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'vin': vehicle['vin'],
                        'stock': vehicle['stock'],
                        'error': message
                    })
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'vin': vehicle['vin'],
                    'stock': vehicle.get('stock', 'unknown'),
                    'error': str(e)
                })
        
        return results
    
    def ensure_order_processing_tables(self):
        """Ensure order processing tables exist"""
        try:
            # Create order processing jobs table
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS order_processing_jobs (
                    id SERIAL PRIMARY KEY,
                    dealership_name VARCHAR(100) NOT NULL,
                    job_type VARCHAR(50) NOT NULL,
                    vehicle_count INTEGER DEFAULT 0,
                    final_vehicle_count INTEGER,
                    export_file TEXT,
                    status VARCHAR(20) DEFAULT 'created',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    notes TEXT
                );
            """)
            
            # Create QR file tracking table
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS qr_file_tracking (
                    id SERIAL PRIMARY KEY,
                    vin VARCHAR(17) NOT NULL,
                    dealership_name VARCHAR(100) NOT NULL,
                    qr_file_path TEXT NOT NULL,
                    file_exists BOOLEAN DEFAULT false,
                    file_size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_verified TIMESTAMP,
                    job_id INTEGER REFERENCES order_processing_jobs(id)
                );
            """)
            
            # Create export history table
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS export_history (
                    id SERIAL PRIMARY KEY,
                    export_type VARCHAR(50) NOT NULL,
                    dealership_name VARCHAR(100),
                    file_path TEXT NOT NULL,
                    record_count INTEGER DEFAULT 0,
                    export_date DATE DEFAULT CURRENT_DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    job_id INTEGER REFERENCES order_processing_jobs(id)
                );
            """)
            
            logger.info("Order processing tables ensured")
            
        except Exception as e:
            logger.warning(f"Could not create order processing tables: {e}")
    
    def validate_qr_files(self, dealership_name: str, job_id: Optional[int] = None) -> Dict:
        """
        Validate that QR code files exist for vehicles
        
        Args:
            dealership_name: Name of the dealership
            job_id: Optional job ID to validate specific job
            
        Returns:
            Validation results with counts and missing files
        """
        try:
            # Get vehicles for this dealership
            query = """
                SELECT n.vin, n.stock, d.qr_output_path
                FROM normalized_vehicle_data n
                JOIN dealership_configs d ON n.location = d.name
                WHERE n.location = %s 
                AND n.last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
                AND d.is_active = true
            """
            
            vehicles = self.db.execute_query(query, (dealership_name,))
            
            validation_results = {
                'dealership': dealership_name,
                'total_vehicles': len(vehicles),
                'qr_files_exist': 0,
                'qr_files_missing': 0,
                'missing_files': [],
                'validation_date': datetime.now().isoformat()
            }
            
            for vehicle in vehicles:
                qr_file_path = self.generate_qr_path(vehicle['vin'], vehicle['qr_output_path'])
                
                if Path(qr_file_path).exists():
                    validation_results['qr_files_exist'] += 1
                    
                    # Update tracking table
                    self.track_qr_file(vehicle['vin'], dealership_name, qr_file_path, True, job_id)
                else:
                    validation_results['qr_files_missing'] += 1
                    validation_results['missing_files'].append({
                        'vin': vehicle['vin'],
                        'stock': vehicle['stock'],
                        'expected_path': qr_file_path
                    })
                    
                    # Update tracking table
                    self.track_qr_file(vehicle['vin'], dealership_name, qr_file_path, False, job_id)
            
            logger.info(f"QR validation for {dealership_name}: {validation_results['qr_files_exist']}/{validation_results['total_vehicles']} files exist")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Failed to validate QR files for {dealership_name}: {e}")
            return {
                'dealership': dealership_name,
                'error': str(e),
                'validation_date': datetime.now().isoformat()
            }
    
    def track_qr_file(self, vin: str, dealership_name: str, file_path: str, exists: bool, job_id: Optional[int] = None):
        """Track QR file status in database"""
        try:
            file_size = None
            if exists and Path(file_path).exists():
                file_size = Path(file_path).stat().st_size
            
            # Upsert QR file tracking record
            self.db.execute_query("""
                INSERT INTO qr_file_tracking 
                (vin, dealership_name, qr_file_path, file_exists, file_size, last_verified, job_id)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
                ON CONFLICT (vin, dealership_name) 
                DO UPDATE SET
                    qr_file_path = EXCLUDED.qr_file_path,
                    file_exists = EXCLUDED.file_exists,
                    file_size = EXCLUDED.file_size,
                    last_verified = CURRENT_TIMESTAMP,
                    job_id = EXCLUDED.job_id
            """, (vin, dealership_name, file_path, exists, file_size, job_id))
            
        except Exception as e:
            logger.warning(f"Could not track QR file for {vin}: {e}")
    
    def get_job_status(self, job_id: int) -> Optional[Dict]:
        """Get status of an order processing job"""
        try:
            result = self.db.execute_query("""
                SELECT * FROM order_processing_jobs WHERE id = %s
            """, (job_id,))
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {e}")
            return None
    
    def get_recent_jobs(self, limit: int = 10) -> List[Dict]:
        """Get recent order processing jobs"""
        try:
            return self.db.execute_query("""
                SELECT * FROM order_processing_jobs 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (limit,))
            
        except Exception as e:
            logger.error(f"Failed to get recent jobs: {e}")
            return []
    
    def cleanup_old_exports(self, days_old: int = 30):
        """Clean up old export files and job records"""
        try:
            # Get old job records
            old_jobs = self.db.execute_query("""
                SELECT export_file FROM order_processing_jobs 
                WHERE created_at < CURRENT_DATE - INTERVAL '%s days'
                AND export_file IS NOT NULL
            """, (days_old,))
            
            # Delete old files
            deleted_files = 0
            for job in old_jobs:
                if job['export_file'] and Path(job['export_file']).exists():
                    try:
                        Path(job['export_file']).unlink()
                        deleted_files += 1
                    except Exception as e:
                        logger.warning(f"Could not delete {job['export_file']}: {e}")
            
            # Delete old records
            self.db.execute_query("""
                DELETE FROM qr_file_tracking 
                WHERE created_at < CURRENT_DATE - INTERVAL '%s days'
            """, (days_old,))
            
            self.db.execute_query("""
                DELETE FROM export_history 
                WHERE created_at < CURRENT_DATE - INTERVAL '%s days'
            """, (days_old,))
            
            self.db.execute_query("""
                DELETE FROM order_processing_jobs 
                WHERE created_at < CURRENT_DATE - INTERVAL '%s days'
            """, (days_old,))
            
            logger.info(f"Cleanup completed: {deleted_files} files deleted, old records removed")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old exports: {e}")

def main():
    """Command-line interface for order processing integration"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Order Processing Database Integration')
    parser.add_argument('action', choices=['create-job', 'validate-qr', 'status', 'cleanup'],
                       help='Action to perform')
    parser.add_argument('--dealership', help='Dealership name')
    parser.add_argument('--job-type', default='standard', help='Job type (standard, premium, custom)')
    parser.add_argument('--job-id', type=int, help='Job ID for status check')
    parser.add_argument('--cleanup-days', type=int, default=30, help='Days old for cleanup')
    
    args = parser.parse_args()
    
    integrator = OrderProcessingIntegrator()
    
    try:
        if args.action == 'create-job':
            if not args.dealership:
                print("Error: --dealership required for create-job")
                return 1
            
            result = integrator.create_order_processing_job(args.dealership, args.job_type)
            print(f"Job created: {json.dumps(result, indent=2)}")
            
        elif args.action == 'validate-qr':
            if not args.dealership:
                print("Error: --dealership required for validate-qr")
                return 1
            
            result = integrator.validate_qr_files(args.dealership, args.job_id)
            print(f"QR Validation: {json.dumps(result, indent=2)}")
            
        elif args.action == 'status':
            if args.job_id:
                result = integrator.get_job_status(args.job_id)
                print(f"Job Status: {json.dumps(result, indent=2)}")
            else:
                results = integrator.get_recent_jobs()
                print(f"Recent Jobs: {json.dumps(results, indent=2)}")
                
        elif args.action == 'cleanup':
            integrator.cleanup_old_exports(args.cleanup_days)
            print(f"Cleanup completed for files older than {args.cleanup_days} days")
            
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())