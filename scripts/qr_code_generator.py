"""
QR Code Generation Module for Dealership Database
Generates QR codes matching the existing Google Apps Script workflow
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import quote
from database_connection import db_manager
from database_config import config

# Import requests with fallback handling
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    logging.warning("requests library not available - QR generation will be disabled")

logger = logging.getLogger(__name__)

class QRCodeGenerator:
    """Handles QR code generation for vehicle inventory"""
    
    def __init__(self, db_manager_instance=None):
        self.db = db_manager_instance or db_manager
        self.api_endpoint = "https://api.qrserver.com/v1/create-qr-code/"
        self.default_size = "388x388"
        
    def get_dealership_qr_path(self, dealership_name: str) -> Optional[str]:
        """Get QR code output path for a dealership"""
        result = self.db.execute_query(
            """
            SELECT qr_output_path 
            FROM dealership_configs 
            WHERE name = %s AND is_active = true
            """,
            (dealership_name,),
            fetch='one'
        )
        
        if result:
            return result['qr_output_path']
        return None
    
    def generate_qr_code(self, vin: str, stock: str, dealership_name: str, 
                        output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate QR code for a vehicle
        Matches Google Apps Script format: VIN with stock number filename
        """
        # Check if requests library is available
        if not HAS_REQUESTS:
            logger.error("Cannot generate QR code - requests library not installed")
            return {
                'success': False,
                'error': "requests library required for QR generation",
                'vin': vin,
                'dealership': dealership_name
            }
            
        try:
            # Get dealership-specific path if not provided
            if not output_path:
                output_path = self.get_dealership_qr_path(dealership_name)
                if not output_path:
                    return {
                        'success': False,
                        'error': f"No QR output path configured for {dealership_name}",
                        'vin': vin,
                        'dealership': dealership_name
                    }
            
            # Create directory if it doesn't exist
            os.makedirs(output_path, exist_ok=True)
            
            # Generate filename using stock number (matching Apps Script)
            filename = f"{stock}.png"
            full_path = os.path.join(output_path, filename)
            
            # Check if file already exists
            if os.path.exists(full_path):
                logger.info(f"QR code already exists: {full_path}")
                self._update_qr_tracking(vin, dealership_name, full_path, True)
                return {
                    'success': True,
                    'qr_file_path': full_path,
                    'vin': vin,
                    'stock': stock,
                    'dealership': dealership_name,
                    'existed': True
                }
            
            # Generate QR code via API (matching Apps Script endpoint)
            qr_data = vin  # QR contains VIN
            params = {
                'size': self.default_size,
                'data': qr_data
            }
            
            logger.info(f"Generating QR code for VIN: {vin}, Stock: {stock}")
            response = requests.get(self.api_endpoint, params=params, timeout=10)
            
            if response.status_code == 200:
                # Save QR code image
                with open(full_path, 'wb') as f:
                    f.write(response.content)
                
                # Update tracking in database
                self._update_qr_tracking(vin, dealership_name, full_path, True)
                
                logger.info(f"QR code saved: {full_path}")
                return {
                    'success': True,
                    'qr_file_path': full_path,
                    'vin': vin,
                    'stock': stock,
                    'dealership': dealership_name,
                    'existed': False
                }
            else:
                logger.error(f"Failed to generate QR code: HTTP {response.status_code}")
                return {
                    'success': False,
                    'error': f"API error: HTTP {response.status_code}",
                    'vin': vin,
                    'dealership': dealership_name
                }
                
        except Exception as e:
            logger.error(f"Error generating QR code for {vin}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'vin': vin,
                'dealership': dealership_name
            }
    
    def _update_qr_tracking(self, vin: str, dealership_name: str, 
                           file_path: str, exists: bool) -> None:
        """Update QR file tracking in database"""
        try:
            file_size = os.path.getsize(file_path) if exists else None
            
            self.db.execute_non_query(
                """
                INSERT INTO qr_file_tracking 
                    (vin, dealership_name, qr_file_path, file_exists, file_size)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (vin, dealership_name) DO UPDATE SET
                    qr_file_path = EXCLUDED.qr_file_path,
                    file_exists = EXCLUDED.file_exists,
                    file_size = EXCLUDED.file_size,
                    last_verified = CURRENT_TIMESTAMP
                """,
                (vin, dealership_name, file_path, exists, file_size)
            )
        except Exception as e:
            logger.error(f"Failed to update QR tracking: {e}")
    
    def verify_qr_file_exists(self, vin: str, dealership_name: str) -> bool:
        """Check if QR file exists for a specific VIN and dealership"""
        try:
            result = self.db.execute_query(
                """
                SELECT qr_file_path, file_exists 
                FROM qr_file_tracking 
                WHERE vin = %s AND dealership_name = %s
                """,
                (vin, dealership_name),
                fetch='one'
            )
            
            if result and result['file_exists'] and os.path.exists(result['qr_file_path']):
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error verifying QR file for {vin}: {e}")
            return False
    
    def generate_batch_qr_codes(self, dealership_name: str, 
                               limit: Optional[int] = None) -> Dict:
        """Generate QR codes for all vehicles at a dealership"""
        results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        # Get vehicles that need QR codes
        query = """
            SELECT DISTINCT n.vin, n.stock, n.location
            FROM normalized_vehicle_data n
            LEFT JOIN qr_file_tracking q 
                ON n.vin = q.vin AND n.location = q.dealership_name
            WHERE n.location = %s
                AND n.stock IS NOT NULL
                AND n.last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
                AND (q.file_exists IS NULL OR q.file_exists = false)
            ORDER BY n.stock
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        vehicles = self.db.execute_query(query, (dealership_name,))
        results['total'] = len(vehicles)
        
        logger.info(f"Generating QR codes for {len(vehicles)} vehicles at {dealership_name}")
        
        for vehicle in vehicles:
            success, message = self.generate_qr_code(
                vehicle['vin'], 
                vehicle['stock'], 
                vehicle['location']
            )
            
            if success:
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'vin': vehicle['vin'],
                    'stock': vehicle['stock'],
                    'error': message
                })
        
        return results
    
    def verify_qr_files(self, dealership_name: str) -> Dict:
        """Verify existence of QR files for a dealership"""
        results = {
            'total': 0,
            'exists': 0,
            'missing': 0,
            'missing_files': []
        }
        
        # Get all tracked QR files for dealership
        qr_files = self.db.execute_query(
            """
            SELECT vin, qr_file_path, file_exists
            FROM qr_file_tracking
            WHERE dealership_name = %s
            """,
            (dealership_name,)
        )
        
        results['total'] = len(qr_files)
        
        for qr in qr_files:
            exists = os.path.exists(qr['qr_file_path'])
            
            if exists:
                results['exists'] += 1
                # Update if status changed
                if not qr['file_exists']:
                    self._update_qr_tracking(
                        qr['vin'], 
                        dealership_name, 
                        qr['qr_file_path'], 
                        True
                    )
            else:
                results['missing'] += 1
                results['missing_files'].append({
                    'vin': qr['vin'],
                    'path': qr['qr_file_path']
                })
                # Update if status changed
                if qr['file_exists']:
                    self._update_qr_tracking(
                        qr['vin'], 
                        dealership_name, 
                        qr['qr_file_path'], 
                        False
                    )
        
        return results
    
    def get_qr_generation_status(self) -> List[Dict]:
        """Get QR generation status for all dealerships"""
        query = """
            SELECT 
                dc.name as dealership_name,
                dc.qr_output_path,
                COUNT(DISTINCT nvd.vin) as total_vehicles,
                COUNT(DISTINCT qft.vin) FILTER (WHERE qft.file_exists = true) as qr_exists,
                COUNT(DISTINCT nvd.vin) - COUNT(DISTINCT qft.vin) FILTER (WHERE qft.file_exists = true) as qr_missing,
                ROUND(
                    (COUNT(DISTINCT qft.vin) FILTER (WHERE qft.file_exists = true)::DECIMAL / 
                     NULLIF(COUNT(DISTINCT nvd.vin), 0)) * 100, 2
                ) as completion_percentage
            FROM dealership_configs dc
            LEFT JOIN normalized_vehicle_data nvd 
                ON dc.name = nvd.location 
                AND nvd.last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
                AND nvd.stock IS NOT NULL
            LEFT JOIN qr_file_tracking qft 
                ON nvd.vin = qft.vin 
                AND nvd.location = qft.dealership_name
            WHERE dc.is_active = true
            GROUP BY dc.name, dc.qr_output_path
            ORDER BY completion_percentage DESC
        """
        
        return self.db.execute_query(query)
    
    def cleanup_orphaned_qr_files(self, dealership_name: str, dry_run: bool = True) -> Dict:
        """Remove QR files for vehicles no longer in inventory"""
        results = {
            'checked': 0,
            'orphaned': 0,
            'removed': 0,
            'errors': []
        }
        
        # Get QR files that exist but vehicle is no longer in recent inventory
        orphaned = self.db.execute_query(
            """
            SELECT q.vin, q.qr_file_path
            FROM qr_file_tracking q
            LEFT JOIN normalized_vehicle_data n 
                ON q.vin = n.vin 
                AND q.dealership_name = n.location
                AND n.last_seen_date >= CURRENT_DATE - INTERVAL '30 days'
            WHERE q.dealership_name = %s
                AND q.file_exists = true
                AND n.vin IS NULL
            """,
            (dealership_name,)
        )
        
        results['checked'] = len(orphaned)
        
        for qr in orphaned:
            if os.path.exists(qr['qr_file_path']):
                results['orphaned'] += 1
                
                if not dry_run:
                    try:
                        os.remove(qr['qr_file_path'])
                        results['removed'] += 1
                        
                        # Update tracking
                        self._update_qr_tracking(
                            qr['vin'], 
                            dealership_name, 
                            qr['qr_file_path'], 
                            False
                        )
                    except Exception as e:
                        results['errors'].append({
                            'vin': qr['vin'],
                            'path': qr['qr_file_path'],
                            'error': str(e)
                        })
        
        return results

def main():
    """Command-line interface for QR code generation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate QR codes for vehicle inventory')
    parser.add_argument('dealership', help='Dealership name')
    parser.add_argument('--vin', help='Generate QR for specific VIN')
    parser.add_argument('--stock', help='Stock number (required with --vin)')
    parser.add_argument('--batch', action='store_true', help='Generate all missing QR codes')
    parser.add_argument('--limit', type=int, help='Limit batch generation')
    parser.add_argument('--verify', action='store_true', help='Verify existing QR files')
    parser.add_argument('--status', action='store_true', help='Show QR generation status')
    parser.add_argument('--cleanup', action='store_true', help='Remove orphaned QR files')
    parser.add_argument('--execute', action='store_true', help='Execute cleanup (default is dry run)')
    
    args = parser.parse_args()
    
    generator = QRCodeGenerator()
    
    try:
        if args.status:
            status = generator.get_qr_generation_status()
            print("\nQR Code Generation Status:")
            print("-" * 80)
            for dealer in status:
                print(f"{dealer['dealership_name']:40} "
                      f"Total: {dealer['total_vehicles']:5} "
                      f"QR Exists: {dealer['qr_exists']:5} "
                      f"Missing: {dealer['qr_missing']:5} "
                      f"Complete: {dealer['completion_percentage']:6.2f}%")
        
        elif args.vin and args.stock:
            success, message = generator.generate_qr_code(
                args.vin, args.stock, args.dealership
            )
            print(f"QR Generation: {'Success' if success else 'Failed'}")
            print(f"Message: {message}")
        
        elif args.batch:
            results = generator.generate_batch_qr_codes(args.dealership, args.limit)
            print(f"\nBatch QR Generation Results for {args.dealership}:")
            print(f"Total vehicles: {results['total']}")
            print(f"Successfully generated: {results['success']}")
            print(f"Failed: {results['failed']}")
            if results['errors']:
                print("\nErrors:")
                for error in results['errors'][:10]:
                    print(f"  - {error['vin']} ({error['stock']}): {error['error']}")
        
        elif args.verify:
            results = generator.verify_qr_files(args.dealership)
            print(f"\nQR File Verification for {args.dealership}:")
            print(f"Total tracked: {results['total']}")
            print(f"Files exist: {results['exists']}")
            print(f"Files missing: {results['missing']}")
        
        elif args.cleanup:
            results = generator.cleanup_orphaned_qr_files(
                args.dealership, 
                dry_run=not args.execute
            )
            print(f"\nOrphaned QR Cleanup for {args.dealership}:")
            print(f"Files checked: {results['checked']}")
            print(f"Orphaned files: {results['orphaned']}")
            if args.execute:
                print(f"Files removed: {results['removed']}")
            else:
                print("(Dry run - use --execute to remove files)")
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()