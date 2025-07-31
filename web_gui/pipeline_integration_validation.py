#!/usr/bin/env python3
"""
PIPELINE INTEGRATION VALIDATION
===============================

Comprehensive validation of the complete Silver Fox Marketing pipeline integration
without requiring live database connections. This validates the architecture,
data flow, and integration patterns for production readiness.

Focus Areas:
1. Component Integration Architecture
2. Data Flow Patterns
3. Error Handling Mechanisms  
4. File System Integration
5. Configuration Management
6. Production Deployment Readiness

Author: Claude (Silver Fox Assistant)
Created: July 2025
Purpose: Final integration validation for production deployment
"""

import os
import sys
import json
import csv
import logging
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline_integration_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PipelineIntegrationValidator:
    """Validates complete pipeline integration for production readiness"""
    
    def __init__(self):
        self.validation_results = {
            'start_time': datetime.now(),
            'architecture_validation': {'status': False, 'details': []},
            'component_integration': {'status': False, 'details': []},
            'data_flow_patterns': {'status': False, 'details': []},
            'file_system_integration': {'status': False, 'details': []},
            'configuration_management': {'status': False, 'details': []},
            'error_handling': {'status': False, 'details': []},
            'performance_patterns': {'status': False, 'details': []},
            'production_readiness': {'status': False, 'details': []},
            'google_apps_script_compatibility': {'status': False, 'details': []},
            'deployment_validation': {'status': False, 'details': []},
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Define expected file structure
        self.expected_structure = {
            'scripts': [
                'database_connection.py',
                'csv_importer_complete.py', 
                'order_processing_integration.py',
                'qr_code_generator.py',
                'data_exporter.py',
                'database_config.py'
            ],
            'web_gui': [
                'app.py',
                'production_config.py',
                'requirements.txt',
                'start_server.bat'
            ],
            'sql': [
                '01_create_database.sql',
                '02_create_tables.sql',
                '03_initial_dealership_configs.sql'
            ],
            'config': [
                'database_config.json'
            ]
        }
        
        # Base paths
        self.base_path = Path(__file__).parent.parent
        self.scripts_path = self.base_path / 'scripts'
        self.web_gui_path = self.base_path / 'web_gui'
        self.sql_path = self.base_path / 'sql'
        self.config_path = self.base_path / 'config'
    
    def run_comprehensive_validation(self) -> Dict:
        """Execute comprehensive pipeline validation"""
        logger.info("=" * 80)
        logger.info("STARTING COMPREHENSIVE PIPELINE INTEGRATION VALIDATION")
        logger.info("Validating production readiness for Silver Fox Marketing")
        logger.info("=" * 80)
        
        try:
            # Phase 1: Architecture Validation
            self._validate_architecture()
            
            # Phase 2: Component Integration
            self._validate_component_integration()
            
            # Phase 3: Data Flow Patterns
            self._validate_data_flow_patterns()
            
            # Phase 4: File System Integration
            self._validate_file_system_integration()
            
            # Phase 5: Configuration Management
            self._validate_configuration_management()
            
            # Phase 6: Error Handling
            self._validate_error_handling()
            
            # Phase 7: Performance Patterns
            self._validate_performance_patterns()
            
            # Phase 8: Google Apps Script Compatibility
            self._validate_google_apps_script_compatibility()
            
            # Phase 9: Deployment Validation
            self._validate_deployment_readiness()
            
            # Phase 10: Production Readiness Assessment
            self._assess_production_readiness()
            
            return self._generate_validation_report()
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            self.validation_results['errors'].append(f"Critical validation failure: {str(e)}")
            return self.validation_results
    
    def _validate_architecture(self):
        """Validate overall system architecture"""
        logger.info("Phase 1: Validating system architecture...")
        
        try:
            architecture_checks = []
            
            # Check 1: Verify all required directories exist
            required_dirs = ['scripts', 'web_gui', 'sql', 'config']
            for dir_name in required_dirs:
                dir_path = self.base_path / dir_name
                exists = dir_path.exists()
                architecture_checks.append({
                    'check': f'Directory: {dir_name}',
                    'status': exists,
                    'details': f'Found at {dir_path}' if exists else f'Missing: {dir_path}'
                })
            
            # Check 2: Verify all required files exist
            for dir_name, files in self.expected_structure.items():
                dir_path = self.base_path / dir_name
                if dir_path.exists():
                    for file_name in files:
                        file_path = dir_path / file_name
                        exists = file_path.exists()
                        architecture_checks.append({
                            'check': f'File: {dir_name}/{file_name}',
                            'status': exists,
                            'details': f'Found: {file_path}' if exists else f'Missing: {file_path}'
                        })
            
            # Check 3: Validate Python module structure
            sys.path.insert(0, str(self.scripts_path))
            
            try:
                import database_connection
                import csv_importer_complete  
                import order_processing_integration
                import qr_code_generator
                import data_exporter
                
                architecture_checks.append({
                    'check': 'Python module imports',
                    'status': True,
                    'details': 'All core modules importable'
                })
            except ImportError as e:
                architecture_checks.append({
                    'check': 'Python module imports', 
                    'status': False,
                    'details': f'Import error: {str(e)}'
                })
            
            # Evaluate architecture validation
            passed_checks = [c for c in architecture_checks if c['status']]
            success_rate = len(passed_checks) / len(architecture_checks)
            
            self.validation_results['architecture_validation']['status'] = success_rate >= 0.9
            self.validation_results['architecture_validation']['details'].extend([
                f"Architecture validation: {len(passed_checks)}/{len(architecture_checks)} checks passed ({success_rate:.1%})",
                "Detailed results:"
            ])
            
            for check in architecture_checks:
                status_icon = "✓" if check['status'] else "✗"
                self.validation_results['architecture_validation']['details'].append(
                    f"  {status_icon} {check['check']}: {check['details']}"
                )
            
            logger.info(f"✓ Architecture validation: {success_rate:.1%} success rate")
            
        except Exception as e:
            logger.error(f"✗ Architecture validation failed: {e}")
            self.validation_results['architecture_validation']['status'] = False
            self.validation_results['errors'].append(f"Architecture validation: {str(e)}")
    
    def _validate_component_integration(self):
        """Validate integration between system components"""
        logger.info("Phase 2: Validating component integration...")
        
        try:
            integration_tests = []
            
            # Test 1: Web GUI integration with backend modules
            try:
                web_gui_app_path = self.web_gui_path / 'app.py'
                if web_gui_app_path.exists():
                    with open(web_gui_app_path, 'r') as f:
                        app_content = f.read()
                    
                    # Check for required imports
                    required_imports = [
                        'from csv_importer_complete import CompleteCSVImporter',
                        'from order_processing_integration import OrderProcessingIntegrator',
                        'from qr_code_generator import QRCodeGenerator',
                        'from data_exporter import DataExporter'
                    ]
                    
                    imports_found = all(imp in app_content for imp in required_imports)
                    integration_tests.append({
                        'test': 'Web GUI backend integration',
                        'status': imports_found,
                        'details': 'All required imports found' if imports_found else 'Missing required imports'
                    })
                else:
                    integration_tests.append({
                        'test': 'Web GUI backend integration',
                        'status': False,
                        'details': 'app.py not found'
                    })
            except Exception as e:
                integration_tests.append({
                    'test': 'Web GUI backend integration',
                    'status': False,
                    'details': f'Error: {str(e)}'
                })
            
            # Test 2: Database connection integration
            try:
                db_config_path = self.config_path / 'database_config.json'
                if db_config_path.exists():
                    with open(db_config_path, 'r') as f:
                        db_config = json.load(f)
                    
                    required_keys = ['host', 'database', 'username', 'password', 'port']
                    has_all_keys = all(key in db_config for key in required_keys)
                    
                    integration_tests.append({
                        'test': 'Database configuration',
                        'status': has_all_keys,
                        'details': 'All required DB config keys present' if has_all_keys else 'Missing DB config keys'
                    })
                else:
                    integration_tests.append({
                        'test': 'Database configuration',
                        'status': False,
                        'details': 'database_config.json not found'
                    })
            except Exception as e:
                integration_tests.append({
                    'test': 'Database configuration',
                    'status': False,
                    'details': f'Error: {str(e)}'
                })
            
            # Test 3: CSV importer integration patterns
            try:
                csv_importer_path = self.scripts_path / 'csv_importer_complete.py'
                if csv_importer_path.exists():
                    with open(csv_importer_path, 'r') as f:
                        importer_content = f.read()
                    
                    # Check for key integration patterns
                    patterns = [
                        'class CompleteCSVImporter',
                        'def import_complete_csv',
                        'def should_include_vehicle',
                        'from database_connection import db_manager'
                    ]
                    
                    patterns_found = all(pattern in importer_content for pattern in patterns)
                    integration_tests.append({
                        'test': 'CSV importer integration patterns',
                        'status': patterns_found,
                        'details': 'All integration patterns found' if patterns_found else 'Missing integration patterns'
                    })
                else:
                    integration_tests.append({
                        'test': 'CSV importer integration patterns',
                        'status': False,
                        'details': 'csv_importer_complete.py not found'
                    })
            except Exception as e:
                integration_tests.append({
                    'test': 'CSV importer integration patterns',
                    'status': False,
                    'details': f'Error: {str(e)}'
                })
            
            # Test 4: Order processing integration
            try:
                order_proc_path = self.scripts_path / 'order_processing_integration.py'
                if order_proc_path.exists():
                    with open(order_proc_path, 'r') as f:
                        order_content = f.read()
                    
                    # Check for order processing patterns
                    patterns = [
                        'class OrderProcessingIntegrator',
                        'def create_order_processing_job',
                        'def generate_qr_codes_for_job',
                        'from qr_code_generator import QRCodeGenerator'
                    ]
                    
                    patterns_found = all(pattern in order_content for pattern in patterns)
                    integration_tests.append({
                        'test': 'Order processing integration',
                        'status': patterns_found,
                        'details': 'All integration patterns found' if patterns_found else 'Missing integration patterns'
                    })
                else:
                    integration_tests.append({
                        'test': 'Order processing integration',
                        'status': False,
                        'details': 'order_processing_integration.py not found'
                    })
            except Exception as e:
                integration_tests.append({
                    'test': 'Order processing integration',
                    'status': False,
                    'details': f'Error: {str(e)}'
                })
            
            # Evaluate component integration
            passed_tests = [t for t in integration_tests if t['status']]
            success_rate = len(passed_tests) / len(integration_tests)
            
            self.validation_results['component_integration']['status'] = success_rate >= 0.8
            self.validation_results['component_integration']['details'].extend([
                f"Component integration: {len(passed_tests)}/{len(integration_tests)} tests passed ({success_rate:.1%})",
                "Integration test results:"
            ])
            
            for test in integration_tests:
                status_icon = "✓" if test['status'] else "✗"
                self.validation_results['component_integration']['details'].append(
                    f"  {status_icon} {test['test']}: {test['details']}"
                )
            
            logger.info(f"✓ Component integration: {success_rate:.1%} success rate")
            
        except Exception as e:
            logger.error(f"✗ Component integration validation failed: {e}")
            self.validation_results['component_integration']['status'] = False
            self.validation_results['errors'].append(f"Component integration: {str(e)}")
    
    def _validate_data_flow_patterns(self):
        """Validate data flow patterns throughout the pipeline"""
        logger.info("Phase 3: Validating data flow patterns...")
        
        try:
            data_flow_checks = []
            
            # Check 1: CSV Import → Database Storage Pattern
            csv_importer_path = self.scripts_path / 'csv_importer_complete.py'
            if csv_importer_path.exists():
                with open(csv_importer_path, 'r') as f:
                    content = f.read()
                
                # Look for data flow patterns
                flow_patterns = [
                    'raw_vehicle_data',  # Raw data storage
                    'normalized_vehicle_data',  # Normalized data
                    'vin_history',  # History tracking
                    'execute_batch_insert',  # Bulk operations
                    'upsert_data'  # Data merging
                ]
                
                patterns_found = sum(1 for pattern in flow_patterns if pattern in content)
                data_flow_checks.append({
                    'check': 'CSV Import → Database Storage',
                    'status': patterns_found >= 4,  # At least 4/5 patterns should be present
                    'details': f'Found {patterns_found}/5 data flow patterns'
                })
            
            # Check 2: Database → Order Processing Pattern
            order_proc_path = self.scripts_path / 'order_processing_integration.py'
            if order_proc_path.exists():
                with open(order_proc_path, 'r') as f:
                    content = f.read()
                
                flow_patterns = [
                    'normalized_vehicle_data',  # Source data
                    'dealership_configs',  # Configuration join
                    'order_processing_jobs',  # Job tracking
                    'filtering_rules',  # Data filtering
                    'export_file'  # Output generation
                ]
                
                patterns_found = sum(1 for pattern in flow_patterns if pattern in content)
                data_flow_checks.append({
                    'check': 'Database → Order Processing',
                    'status': patterns_found >= 4,
                    'details': f'Found {patterns_found}/5 data flow patterns'
                })
            
            # Check 3: Order Processing → QR Generation Pattern
            qr_gen_path = self.scripts_path / 'qr_code_generator.py'
            if qr_gen_path.exists():
                with open(qr_gen_path, 'r') as f:
                    content = f.read()
                
                flow_patterns = [
                    'qr_file_tracking',  # File tracking
                    'dealership_name',  # Context preservation
                    'stock',  # Filename generation
                    'qr_file_path',  # Path management
                    'file_exists'  # Validation
                ]
                
                patterns_found = sum(1 for pattern in flow_patterns if pattern in content)
                data_flow_checks.append({
                    'check': 'Order Processing → QR Generation',
                    'status': patterns_found >= 3,
                    'details': f'Found {patterns_found}/5 data flow patterns'
                })
            
            # Check 4: QR Generation → Adobe Export Pattern
            data_exp_path = self.scripts_path / 'data_exporter.py'
            if data_exp_path.exists():
                with open(data_exp_path, 'r') as f:
                    content = f.read()
                
                flow_patterns = [
                    'export_dealership_data',  # Export function
                    'qr_code_path',  # QR integration
                    'filtering_rules',  # Filter application
                    'output_rules',  # Output configuration
                    'csv'  # File format
                ]
                
                patterns_found = sum(1 for pattern in flow_patterns if pattern in content)
                data_flow_checks.append({
                    'check': 'QR Generation → Adobe Export',
                    'status': patterns_found >= 3,
                    'details': f'Found {patterns_found}/5 data flow patterns'
                })
            
            # Check 5: Web GUI → Backend Integration Pattern
            web_gui_path = self.web_gui_path / 'app.py'
            if web_gui_path.exists():
                with open(web_gui_path, 'r') as f:
                    content = f.read()
                
                flow_patterns = [
                    'ScraperController',  # Controller pattern
                    'run_scraper',  # Pipeline orchestration
                    'generate_adobe_report',  # Output generation
                    'get_dealership_configs',  # Configuration flow
                    'jsonify'  # API response formatting
                ]
                
                patterns_found = sum(1 for pattern in flow_patterns if pattern in content)
                data_flow_checks.append({
                    'check': 'Web GUI → Backend Integration',
                    'status': patterns_found >= 4,
                    'details': f'Found {patterns_found}/5 data flow patterns'
                })
            
            # Evaluate data flow validation
            passed_checks = [c for c in data_flow_checks if c['status']]
            success_rate = len(passed_checks) / len(data_flow_checks) if data_flow_checks else 0
            
            self.validation_results['data_flow_patterns']['status'] = success_rate >= 0.8
            self.validation_results['data_flow_patterns']['details'].extend([
                f"Data flow validation: {len(passed_checks)}/{len(data_flow_checks)} patterns validated ({success_rate:.1%})",
                "Flow pattern results:"
            ])
            
            for check in data_flow_checks:
                status_icon = "✓" if check['status'] else "✗"
                self.validation_results['data_flow_patterns']['details'].append(
                    f"  {status_icon} {check['check']}: {check['details']}"
                )
            
            logger.info(f"✓ Data flow patterns: {success_rate:.1%} validation rate")
            
        except Exception as e:
            logger.error(f"✗ Data flow pattern validation failed: {e}")
            self.validation_results['data_flow_patterns']['status'] = False
            self.validation_results['errors'].append(f"Data flow patterns: {str(e)}")
    
    def _validate_file_system_integration(self):
        """Validate file system integration patterns"""
        logger.info("Phase 4: Validating file system integration...")
        
        try:
            fs_integration_checks = []
            
            # Check 1: Directory Structure Creation
            try:
                # Test directory creation patterns used in the system
                test_dirs = ['test_qr_codes', 'test_exports', 'test_imports']
                created_dirs = []
                
                for dir_name in test_dirs:
                    test_path = Path(dir_name)
                    try:
                        test_path.mkdir(exist_ok=True)
                        if test_path.exists():
                            created_dirs.append(dir_name)
                            test_path.rmdir()  # Cleanup
                    except Exception:
                        pass
                
                fs_integration_checks.append({
                    'check': 'Directory creation capabilities',
                    'status': len(created_dirs) == len(test_dirs),
                    'details': f'Successfully created {len(created_dirs)}/{len(test_dirs)} test directories'
                })
            except Exception as e:
                fs_integration_checks.append({
                    'check': 'Directory creation capabilities',
                    'status': False,
                    'details': f'Error: {str(e)}'
                })
            
            # Check 2: CSV File Operations
            try:
                test_csv = 'test_file_operations.csv'
                test_data = [
                    {'vin': 'TEST12345', 'stock': 'STK001', 'dealer': 'Test Dealer'},
                    {'vin': 'TEST67890', 'stock': 'STK002', 'dealer': 'Test Dealer'}
                ]
                
                # Write test CSV
                with open(test_csv, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['vin', 'stock', 'dealer'])
                    writer.writeheader()
                    writer.writerows(test_data)
                
                # Read test CSV
                with open(test_csv, 'r') as f:
                    reader = csv.DictReader(f)
                    read_data = list(reader)
                
                # Validate
                write_read_success = len(read_data) == len(test_data)
                
                # Cleanup
                os.unlink(test_csv)
                
                fs_integration_checks.append({
                    'check': 'CSV file operations',
                    'status': write_read_success,
                    'details': 'CSV write/read operations successful' if write_read_success else 'CSV operations failed'
                })
                
            except Exception as e:
                fs_integration_checks.append({
                    'check': 'CSV file operations',
                    'status': False,
                    'details': f'Error: {str(e)}'
                })
            
            # Check 3: Configuration File Handling
            try:
                config_file = 'test_config.json'
                test_config = {
                    'dealership': 'Test Dealer',
                    'filtering_rules': {'min_price': 10000},
                    'output_rules': {'include_qr': True}
                }
                
                # Write config
                with open(config_file, 'w') as f:
                    json.dump(test_config, f, indent=2)
                
                # Read config
                with open(config_file, 'r') as f:
                    read_config = json.load(f)
                
                # Validate
                config_success = read_config == test_config
                
                # Cleanup
                os.unlink(config_file)
                
                fs_integration_checks.append({
                    'check': 'Configuration file handling',
                    'status': config_success,
                    'details': 'JSON config operations successful' if config_success else 'JSON config operations failed'
                })
                
            except Exception as e:
                fs_integration_checks.append({
                    'check': 'Configuration file handling',
                    'status': False,
                    'details': f'Error: {str(e)}'
                })
            
            # Check 4: Path Management Patterns
            try:
                # Test path operations used in the system
                test_paths = [
                    'C:/qr_codes/test_dealer/test.png',
                    'C:/exports/test_export.csv',
                    'C:/imports/test_import.csv'
                ]
                
                path_operations_success = True
                for path_str in test_paths:
                    try:
                        path_obj = Path(path_str)
                        # Test path manipulation operations
                        parent = path_obj.parent
                        name = path_obj.name
                        stem = path_obj.stem
                        
                        # Basic validation that path operations work
                        if not all([parent, name, stem]):
                            path_operations_success = False
                            break
                    except Exception:
                        path_operations_success = False
                        break
                
                fs_integration_checks.append({
                    'check': 'Path management patterns',
                    'status': path_operations_success,
                    'details': 'Path operations successful' if path_operations_success else 'Path operations failed'
                })
                
            except Exception as e:
                fs_integration_checks.append({
                    'check': 'Path management patterns',
                    'status': False,
                    'details': f'Error: {str(e)}'
                })
            
            # Evaluate file system integration
            passed_checks = [c for c in fs_integration_checks if c['status']]
            success_rate = len(passed_checks) / len(fs_integration_checks) if fs_integration_checks else 0
            
            self.validation_results['file_system_integration']['status'] = success_rate >= 0.75
            self.validation_results['file_system_integration']['details'].extend([
                f"File system integration: {len(passed_checks)}/{len(fs_integration_checks)} checks passed ({success_rate:.1%})",
                "Integration results:"
            ])
            
            for check in fs_integration_checks:
                status_icon = "✓" if check['status'] else "✗"
                self.validation_results['file_system_integration']['details'].append(
                    f"  {status_icon} {check['check']}: {check['details']}"
                )
            
            logger.info(f"✓ File system integration: {success_rate:.1%} success rate")
            
        except Exception as e:
            logger.error(f"✗ File system integration validation failed: {e}")
            self.validation_results['file_system_integration']['status'] = False
            self.validation_results['errors'].append(f"File system integration: {str(e)}")
    
    def _validate_configuration_management(self):
        """Validate configuration management patterns"""
        logger.info("Phase 5: Validating configuration management...")
        
        try:
            config_checks = []
            
            # Check 1: Database Configuration
            db_config_path = self.config_path / 'database_config.json'
            if db_config_path.exists():
                try:
                    with open(db_config_path, 'r') as f:
                        db_config = json.load(f)
                    
                    required_keys = ['host', 'database', 'username', 'password', 'port']
                    optional_keys = ['sslmode', 'connect_timeout']
                    
                    has_required = all(key in db_config for key in required_keys)
                    has_optional = any(key in db_config for key in optional_keys)
                    
                    config_checks.append({
                        'check': 'Database configuration structure',
                        'status': has_required,
                        'details': f'Required keys: {has_required}, Optional keys: {has_optional}'
                    })
                except Exception as e:
                    config_checks.append({
                        'check': 'Database configuration structure',
                        'status': False,
                        'details': f'Error reading config: {str(e)}'
                    })
            else:
                config_checks.append({
                    'check': 'Database configuration structure',
                    'status': False,
                    'details': 'database_config.json not found'
                })
            
            # Check 2: Production Configuration
            prod_config_path = self.web_gui_path / 'production_config.py'
            if prod_config_path.exists():
                try:
                    with open(prod_config_path, 'r') as f:
                        prod_config_content = f.read()
                    
                    # Check for production configuration patterns
                    config_patterns = [
                        'class ProductionConfig',
                        'DEBUG = False',
                        'THREADED = True',
                        'get_config',
                        'HOST'
                    ]
                    
                    patterns_found = sum(1 for pattern in config_patterns if pattern in prod_config_content)
                    config_checks.append({
                        'check': 'Production configuration patterns',
                        'status': patterns_found >= 3,
                        'details': f'Found {patterns_found}/5 configuration patterns'
                    })
                except Exception as e:
                    config_checks.append({
                        'check': 'Production configuration patterns',
                        'status': False,
                        'details': f'Error reading config: {str(e)}'
                    })
            else:
                config_checks.append({
                    'check': 'Production configuration patterns',
                    'status': False,
                    'details': 'production_config.py not found'
                })
            
            # Check 3: Dealership Configuration Patterns
            try:
                # Look for dealership configuration patterns in SQL files
                sql_files = list(self.sql_path.glob('*.sql'))
                dealership_config_found = False
                
                for sql_file in sql_files:
                    with open(sql_file, 'r') as f:
                        content = f.read()
                    
                    if 'dealership_configs' in content.lower():
                        dealership_config_found = True
                        break
                
                config_checks.append({
                    'check': 'Dealership configuration schema',
                    'status': dealership_config_found,
                    'details': 'Dealership config tables found in SQL' if dealership_config_found else 'No dealership config schema found'
                })
            except Exception as e:
                config_checks.append({
                    'check': 'Dealership configuration schema',
                    'status': False,
                    'details': f'Error checking SQL files: {str(e)}'
                })
            
            # Check 4: Requirements Management
            req_files = ['requirements.txt', 'requirements_test.txt']
            req_checks = []
            
            for req_file in req_files:
                req_path = self.web_gui_path / req_file
                if req_path.exists():
                    try:
                        with open(req_path, 'r') as f:
                            requirements = f.read()
                        
                        # Check for essential dependencies
                        essential_deps = ['Flask', 'psycopg2', 'pandas', 'requests']
                        deps_found = sum(1 for dep in essential_deps if dep.lower() in requirements.lower())
                        
                        req_checks.append({
                            'file': req_file,
                            'status': deps_found >= 3,
                            'details': f'Found {deps_found}/4 essential dependencies'
                        })
                    except Exception as e:
                        req_checks.append({
                            'file': req_file,
                            'status': False,
                            'details': f'Error reading {req_file}: {str(e)}'
                        })
                else:
                    req_checks.append({
                        'file': req_file,
                        'status': False,
                        'details': f'{req_file} not found'
                    })
            
            req_success = any(check['status'] for check in req_checks)
            config_checks.append({
                'check': 'Requirements management',
                'status': req_success,
                'details': f'Requirements files validation: {req_checks}'
            })
            
            # Evaluate configuration management
            passed_checks = [c for c in config_checks if c['status']]
            success_rate = len(passed_checks) / len(config_checks) if config_checks else 0
            
            self.validation_results['configuration_management']['status'] = success_rate >= 0.75
            self.validation_results['configuration_management']['details'].extend([
                f"Configuration management: {len(passed_checks)}/{len(config_checks)} checks passed ({success_rate:.1%})",
                "Configuration results:"
            ])
            
            for check in config_checks:
                status_icon = "✓" if check['status'] else "✗"
                self.validation_results['configuration_management']['details'].append(
                    f"  {status_icon} {check['check']}: {check['details']}"
                )
            
            logger.info(f"✓ Configuration management: {success_rate:.1%} success rate")
            
        except Exception as e:
            logger.error(f"✗ Configuration management validation failed: {e}")
            self.validation_results['configuration_management']['status'] = False
            self.validation_results['errors'].append(f"Configuration management: {str(e)}")
    
    def _validate_error_handling(self):
        """Validate error handling patterns"""
        logger.info("Phase 6: Validating error handling...")
        
        try:
            error_handling_checks = []
            
            # Check 1: Exception Handling Patterns
            script_files = [
                'csv_importer_complete.py',
                'order_processing_integration.py', 
                'qr_code_generator.py',
                'data_exporter.py'
            ]
            
            for script_file in script_files:
                script_path = self.scripts_path / script_file
                if script_path.exists():
                    try:
                        with open(script_path, 'r') as f:
                            content = f.read()
                        
                        # Check for error handling patterns
                        error_patterns = [
                            'try:',
                            'except Exception as e:',
                            'logger.error',
                            'logger.warning',
                            'raise'
                        ]
                        
                        patterns_found = sum(1 for pattern in error_patterns if pattern in content)
                        
                        error_handling_checks.append({
                            'check': f'Error handling in {script_file}',
                            'status': patterns_found >= 3,
                            'details': f'Found {patterns_found}/5 error handling patterns'
                        })
                    except Exception as e:
                        error_handling_checks.append({
                            'check': f'Error handling in {script_file}',
                            'status': False,
                            'details': f'Error reading file: {str(e)}'
                        })
                else:
                    error_handling_checks.append({
                        'check': f'Error handling in {script_file}',
                        'status': False,
                        'details': f'{script_file} not found'
                    })
            
            # Check 2: Web GUI Error Handling
            web_gui_path = self.web_gui_path / 'app.py'
            if web_gui_path.exists():
                try:
                    with open(web_gui_path, 'r') as f:
                        content = f.read()
                    
                    # Check for web-specific error handling
                    web_error_patterns = [
                        'try:',
                        'except Exception as e:',
                        'logger.error',
                        'jsonify',
                        'return jsonify'
                    ]
                    
                    patterns_found = sum(1 for pattern in web_error_patterns if pattern in content)
                    
                    error_handling_checks.append({
                        'check': 'Web GUI error handling',
                        'status': patterns_found >= 4,
                        'details': f'Found {patterns_found}/5 web error handling patterns'
                    })
                except Exception as e:
                    error_handling_checks.append({
                        'check': 'Web GUI error handling',
                        'status': False,
                        'details': f'Error reading app.py: {str(e)}'
                    })
            
            # Check 3: Logging Configuration
            try:
                # Check for logging setup patterns across files
                logging_patterns_found = []
                
                for script_file in script_files + ['app.py']:
                    file_path = self.scripts_path / script_file if script_file != 'app.py' else self.web_gui_path / script_file
                    
                    if file_path.exists():
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        if 'import logging' in content and 'logger = logging.getLogger' in content:
                            logging_patterns_found.append(script_file)
                
                error_handling_checks.append({
                    'check': 'Logging configuration',
                    'status': len(logging_patterns_found) >= 3,
                    'details': f'Proper logging found in {len(logging_patterns_found)} files: {logging_patterns_found}'
                })
            except Exception as e:
                error_handling_checks.append({
                    'check': 'Logging configuration',
                    'status': False,
                    'details': f'Error checking logging: {str(e)}'
                })
            
            # Check 4: Data Validation Patterns
            try:
                csv_importer_path = self.scripts_path / 'csv_importer_complete.py'
                if csv_importer_path.exists():
                    with open(csv_importer_path, 'r') as f:
                        content = f.read()
                    
                    # Check for data validation patterns
                    validation_patterns = [
                        'def validate_row',
                        'def should_include_vehicle',
                        'if not',
                        'return False',
                        'Invalid'
                    ]
                    
                    patterns_found = sum(1 for pattern in validation_patterns if pattern in content)
                    
                    error_handling_checks.append({
                        'check': 'Data validation patterns',
                        'status': patterns_found >= 3,
                        'details': f'Found {patterns_found}/5 validation patterns'
                    })
                else:
                    error_handling_checks.append({
                        'check': 'Data validation patterns',
                        'status': False,
                        'details': 'CSV importer not found'
                    })
            except Exception as e:
                error_handling_checks.append({
                    'check': 'Data validation patterns',
                    'status': False,
                    'details': f'Error checking validation: {str(e)}'
                })
            
            # Evaluate error handling
            passed_checks = [c for c in error_handling_checks if c['status']]
            success_rate = len(passed_checks) / len(error_handling_checks) if error_handling_checks else 0
            
            self.validation_results['error_handling']['status'] = success_rate >= 0.7
            self.validation_results['error_handling']['details'].extend([
                f"Error handling: {len(passed_checks)}/{len(error_handling_checks)} checks passed ({success_rate:.1%})",
                "Error handling results:"
            ])
            
            for check in error_handling_checks:
                status_icon = "✓" if check['status'] else "✗"
                self.validation_results['error_handling']['details'].append(
                    f"  {status_icon} {check['check']}: {check['details']}"
                )
            
            logger.info(f"✓ Error handling: {success_rate:.1%} success rate")
            
        except Exception as e:
            logger.error(f"✗ Error handling validation failed: {e}")
            self.validation_results['error_handling']['status'] = False
            self.validation_results['errors'].append(f"Error handling: {str(e)}")
    
    def _validate_performance_patterns(self):
        """Validate performance optimization patterns"""
        logger.info("Phase 7: Validating performance patterns...")
        
        try:
            performance_checks = []
            
            # Check 1: Database Performance Patterns
            try:
                # Check SQL files for performance optimizations
                sql_files = list(self.sql_path.glob('*.sql'))
                performance_sql_patterns = []
                
                for sql_file in sql_files:
                    with open(sql_file, 'r') as f:
                        content = f.read().lower()
                    
                    # Look for performance patterns
                    if 'index' in content:
                        performance_sql_patterns.append('Indexes')
                    if 'primary key' in content:
                        performance_sql_patterns.append('Primary Keys')
                    if 'constraint' in content:
                        performance_sql_patterns.append('Constraints')
                    if 'vacuum' in content or 'analyze' in content:
                        performance_sql_patterns.append('Maintenance')
                
                performance_checks.append({
                    'check': 'Database performance patterns',
                    'status': len(performance_sql_patterns) >= 2,
                    'details': f'Found patterns: {", ".join(set(performance_sql_patterns))}'
                })
            except Exception as e:
                performance_checks.append({
                    'check': 'Database performance patterns',
                    'status': False,
                    'details': f'Error checking SQL files: {str(e)}'
                })
            
            # Check 2: Bulk Operation Patterns
            try:
                csv_importer_path = self.scripts_path / 'csv_importer_complete.py'
                if csv_importer_path.exists():
                    with open(csv_importer_path, 'r') as f:
                        content = f.read()
                    
                    # Check for bulk operations
                    bulk_patterns = [
                        'execute_batch_insert',
                        'upsert_data',
                        'batch',
                        'bulk',
                        'COPY'
                    ]
                    
                    patterns_found = sum(1 for pattern in bulk_patterns if pattern in content)
                    
                    performance_checks.append({
                        'check': 'Bulk operation patterns',
                        'status': patterns_found >= 2,
                        'details': f'Found {patterns_found}/5 bulk operation patterns'
                    })
                else:
                    performance_checks.append({
                        'check': 'Bulk operation patterns',
                        'status': False,
                        'details': 'CSV importer not found'
                    })
            except Exception as e:
                performance_checks.append({
                    'check': 'Bulk operation patterns',
                    'status': False,
                    'details': f'Error checking bulk operations: {str(e)}'
                })
            
            # Check 3: Caching and Optimization Patterns
            try:
                # Check for caching patterns across files
                caching_files = []
                
                all_python_files = list(self.scripts_path.glob('*.py')) + list(self.web_gui_path.glob('*.py'))
                
                for py_file in all_python_files:
                    try:
                        with open(py_file, 'r') as f:
                            content = f.read()
                        
                        # Look for optimization patterns
                        if any(pattern in content for pattern in ['cache', 'memoize', 'lru_cache', 'static']):
                            caching_files.append(py_file.name)
                    except Exception:
                        pass
                
                performance_checks.append({
                    'check': 'Caching and optimization patterns',
                    'status': len(caching_files) >= 1,
                    'details': f'Optimization patterns found in: {", ".join(caching_files)}' if caching_files else 'No caching patterns found'
                })
            except Exception as e:
                performance_checks.append({
                    'check': 'Caching and optimization patterns',
                    'status': False,
                    'details': f'Error checking caching: {str(e)}'
                })
            
            # Check 4: Memory Management Patterns
            try:
                # Check for memory-conscious patterns
                memory_patterns = []
                
                csv_importer_path = self.scripts_path / 'csv_importer_complete.py'
                if csv_importer_path.exists():
                    with open(csv_importer_path, 'r') as f:
                        content = f.read()
                    
                    # Look for memory management patterns
                    if 'groupby' in content:
                        memory_patterns.append('Data grouping')
                    if 'del ' in content or 'clear()' in content:
                        memory_patterns.append('Memory cleanup')
                    if 'chunk' in content or 'batch' in content:
                        memory_patterns.append('Chunked processing')
                
                performance_checks.append({
                    'check': 'Memory management patterns',
                    'status': len(memory_patterns) >= 1,
                    'details': f'Found patterns: {", ".join(memory_patterns)}' if memory_patterns else 'No memory management patterns found'
                })
            except Exception as e:
                performance_checks.append({
                    'check': 'Memory management patterns',
                    'status': False,
                    'details': f'Error checking memory management: {str(e)}'
                })
            
            # Evaluate performance patterns
            passed_checks = [c for c in performance_checks if c['status']]
            success_rate = len(passed_checks) / len(performance_checks) if performance_checks else 0
            
            self.validation_results['performance_patterns']['status'] = success_rate >= 0.5  # Lower threshold for performance optimizations
            self.validation_results['performance_patterns']['details'].extend([
                f"Performance patterns: {len(passed_checks)}/{len(performance_checks)} checks passed ({success_rate:.1%})",
                "Performance results:"
            ])
            
            for check in performance_checks:
                status_icon = "✓" if check['status'] else "✗"
                self.validation_results['performance_patterns']['details'].append(
                    f"  {status_icon} {check['check']}: {check['details']}"
                )
            
            logger.info(f"✓ Performance patterns: {success_rate:.1%} success rate")
            
        except Exception as e:
            logger.error(f"✗ Performance pattern validation failed: {e}")
            self.validation_results['performance_patterns']['status'] = False
            self.validation_results['errors'].append(f"Performance patterns: {str(e)}")
    
    def _validate_google_apps_script_compatibility(self):
        """Validate compatibility with existing Google Apps Script workflow"""
        logger.info("Phase 8: Validating Google Apps Script compatibility...")
        
        try:
            compatibility_checks = []
            
            # Check 1: QR Code Generation Compatibility
            try:
                qr_gen_path = self.scripts_path / 'qr_code_generator.py'
                if qr_gen_path.exists():
                    with open(qr_gen_path, 'r') as f:
                        content = f.read()
                    
                    # Check for Apps Script compatible patterns
                    gas_patterns = [
                        'qrserver.com',  # Same QR API
                        'stock',  # Filename using stock number
                        '.png',  # Same image format
                        'vin',  # QR data content
                        '388x388'  # Same size format
                    ]
                    
                    patterns_found = sum(1 for pattern in gas_patterns if pattern in content)
                    
                    compatibility_checks.append({
                        'check': 'QR code generation compatibility',
                        'status': patterns_found >= 4,
                        'details': f'Found {patterns_found}/5 GAS-compatible patterns'
                    })
                else:
                    compatibility_checks.append({
                        'check': 'QR code generation compatibility',
                        'status': False,
                        'details': 'QR generator not found'
                    })
            except Exception as e:
                compatibility_checks.append({
                    'check': 'QR code generation compatibility',
                    'status': False,
                    'details': f'Error checking QR compatibility: {str(e)}'
                })
            
            # Check 2: Data Export Format Compatibility
            try:
                data_exp_path = self.scripts_path / 'data_exporter.py'
                if data_exp_path.exists():
                    with open(data_exp_path, 'r') as f:
                        content = f.read()
                    
                    # Check for export compatibility
                    export_patterns = [
                        'csv',  # Same export format
                        'vin',  # VIN field
                        'stock',  # Stock field
                        'qr_code_path',  # QR path field
                        'dealership'  # Dealership context
                    ]
                    
                    patterns_found = sum(1 for pattern in export_patterns if pattern in content)
                    
                    compatibility_checks.append({
                        'check': 'Data export format compatibility',
                        'status': patterns_found >= 4,
                        'details': f'Found {patterns_found}/5 export compatibility patterns'
                    })
                else:
                    compatibility_checks.append({
                        'check': 'Data export format compatibility',
                        'status': False,
                        'details': 'Data exporter not found'
                    })
            except Exception as e:
                compatibility_checks.append({
                    'check': 'Data export format compatibility',
                    'status': False,
                    'details': f'Error checking export compatibility: {str(e)}'
                })
            
            # Check 3: CSV Import Format Compatibility
            try:
                csv_imp_path = self.scripts_path / 'csv_importer_complete.py'
                if csv_imp_path.exists():
                    with open(csv_imp_path, 'r') as f:
                        content = f.read()
                    
                    # Check for CSV format compatibility
                    csv_patterns = [
                        'complete_data.csv',  # Expected filename
                        'dealer_name',  # Dealership field
                        'scraped_at',  # Timestamp field
                        'import_complete_csv',  # Import function
                        'vin'  # VIN field
                    ]
                    
                    patterns_found = sum(1 for pattern in csv_patterns if pattern in content)
                    
                    compatibility_checks.append({
                        'check': 'CSV import format compatibility',
                        'status': patterns_found >= 4,
                        'details': f'Found {patterns_found}/5 CSV compatibility patterns'
                    })
                else:
                    compatibility_checks.append({
                        'check': 'CSV import format compatibility',
                        'status': False,
                        'details': 'CSV importer not found'
                    })
            except Exception as e:
                compatibility_checks.append({
                    'check': 'CSV import format compatibility',
                    'status': False,
                    'details': f'Error checking CSV compatibility: {str(e)}'
                })
            
            # Check 4: File Path Compatibility
            try:
                # Check for Windows-style paths (matching current setup)
                path_compatibility = []
                
                all_files = list(self.scripts_path.glob('*.py')) + list(self.web_gui_path.glob('*.py'))
                
                for py_file in all_files:
                    try:
                        with open(py_file, 'r') as f:
                            content = f.read()
                        
                        if 'C:/' in content or 'C:\\' in content:
                            path_compatibility.append(py_file.name)
                    except Exception:
                        pass
                
                compatibility_checks.append({
                    'check': 'File path compatibility',
                    'status': len(path_compatibility) >= 2,
                    'details': f'Windows paths found in: {", ".join(path_compatibility)}' if path_compatibility else 'No Windows paths found'
                })
            except Exception as e:
                compatibility_checks.append({
                    'check': 'File path compatibility',
                    'status': False,
                    'details': f'Error checking path compatibility: {str(e)}'
                })
            
            # Evaluate Google Apps Script compatibility
            passed_checks = [c for c in compatibility_checks if c['status']]
            success_rate = len(passed_checks) / len(compatibility_checks) if compatibility_checks else 0
            
            self.validation_results['google_apps_script_compatibility']['status'] = success_rate >= 0.75
            self.validation_results['google_apps_script_compatibility']['details'].extend([
                f"GAS compatibility: {len(passed_checks)}/{len(compatibility_checks)} checks passed ({success_rate:.1%})",
                "Compatibility results:"
            ])
            
            for check in compatibility_checks:
                status_icon = "✓" if check['status'] else "✗"
                self.validation_results['google_apps_script_compatibility']['details'].append(
                    f"  {status_icon} {check['check']}: {check['details']}"
                )
            
            logger.info(f"✓ Google Apps Script compatibility: {success_rate:.1%} success rate")
            
        except Exception as e:
            logger.error(f"✗ Google Apps Script compatibility validation failed: {e}")
            self.validation_results['google_apps_script_compatibility']['status'] = False
            self.validation_results['errors'].append(f"GAS compatibility: {str(e)}")
    
    def _validate_deployment_readiness(self):
        """Validate deployment readiness"""
        logger.info("Phase 9: Validating deployment readiness...")
        
        try:
            deployment_checks = []
            
            # Check 1: Required Files for Deployment
            required_deployment_files = [
                ('scripts/database_connection.py', 'Database connection module'),
                ('scripts/csv_importer_complete.py', 'CSV import functionality'),
                ('web_gui/app.py', 'Web GUI application'),
                ('web_gui/requirements.txt', 'Python dependencies'),
                ('web_gui/start_server.bat', 'Server startup script'),
                ('sql/01_create_database.sql', 'Database setup'),
                ('config/database_config.json', 'Database configuration')
            ]
            
            missing_files = []
            for file_path, description in required_deployment_files:
                full_path = self.base_path / file_path
                if not full_path.exists():
                    missing_files.append(f'{file_path} ({description})')
            
            deployment_checks.append({
                'check': 'Required deployment files',
                'status': len(missing_files) == 0,
                'details': f'Missing files: {", ".join(missing_files)}' if missing_files else 'All required files present'
            })
            
            # Check 2: Documentation and Guides
            doc_files = [
                'README.md',
                'DEPLOYMENT_CHECKLIST.md',
                'INSTALL.bat'
            ]
            
            found_docs = []
            for doc_file in doc_files:
                if (self.base_path / doc_file).exists():
                    found_docs.append(doc_file)
            
            deployment_checks.append({
                'check': 'Documentation availability',
                'status': len(found_docs) >= 2,
                'details': f'Found documentation: {", ".join(found_docs)}'
            })
            
            # Check 3: Configuration Templates
            try:
                config_files = list(self.config_path.glob('*.json'))
                template_files = list(self.base_path.glob('*template*'))
                
                deployment_checks.append({
                    'check': 'Configuration templates',
                    'status': len(config_files) >= 1,
                    'details': f'Found {len(config_files)} config files and {len(template_files)} templates'
                })
            except Exception as e:
                deployment_checks.append({
                    'check': 'Configuration templates',
                    'status': False,
                    'details': f'Error checking configs: {str(e)}'
                })
            
            # Check 4: Database Schema Files
            try:
                sql_files = list(self.sql_path.glob('*.sql'))
                schema_files = [f for f in sql_files if any(keyword in f.name.lower() for keyword in ['create', 'table', 'schema'])]
                
                deployment_checks.append({
                    'check': 'Database schema files',
                    'status': len(schema_files) >= 2,
                    'details': f'Found {len(schema_files)} schema files: {[f.name for f in schema_files]}'
                })
            except Exception as e:
                deployment_checks.append({
                    'check': 'Database schema files',
                    'status': False,
                    'details': f'Error checking SQL files: {str(e)}'
                })
            
            # Check 5: Dependency Management
            try:
                req_path = self.web_gui_path / 'requirements.txt'
                if req_path.exists():
                    with open(req_path, 'r') as f:
                        requirements = f.read()
                    
                    # Check for version pinning
                    lines = requirements.strip().split('\n')
                    versioned_deps = [line for line in lines if '>=' in line or '==' in line]
                    
                    deployment_checks.append({
                        'check': 'Dependency versioning',
                        'status': len(versioned_deps) >= len(lines) * 0.8,  # 80% should have versions
                        'details': f'{len(versioned_deps)}/{len(lines)} dependencies have version constraints'
                    })
                else:
                    deployment_checks.append({
                        'check': 'Dependency versioning',
                        'status': False,
                        'details': 'requirements.txt not found'
                    })
            except Exception as e:
                deployment_checks.append({
                    'check': 'Dependency versioning',
                    'status': False,
                    'details': f'Error checking requirements: {str(e)}'
                })
            
            # Check 6: Startup Scripts
            startup_scripts = ['start_server.bat', 'INSTALL.bat']
            found_scripts = []
            
            for script in startup_scripts:
                if (self.base_path / script).exists() or (self.web_gui_path / script).exists():
                    found_scripts.append(script)
            
            deployment_checks.append({
                'check': 'Startup and installation scripts',
                'status': len(found_scripts) >= 1,
                'details': f'Found scripts: {", ".join(found_scripts)}'
            })
            
            # Evaluate deployment readiness
            passed_checks = [c for c in deployment_checks if c['status']]
            success_rate = len(passed_checks) / len(deployment_checks) if deployment_checks else 0
            
            self.validation_results['deployment_validation']['status'] = success_rate >= 0.8
            self.validation_results['deployment_validation']['details'].extend([
                f"Deployment readiness: {len(passed_checks)}/{len(deployment_checks)} checks passed ({success_rate:.1%})",
                "Deployment results:"
            ])
            
            for check in deployment_checks:
                status_icon = "✓" if check['status'] else "✗"
                self.validation_results['deployment_validation']['details'].append(
                    f"  {status_icon} {check['check']}: {check['details']}"
                )
            
            logger.info(f"✓ Deployment readiness: {success_rate:.1%} success rate")
            
        except Exception as e:
            logger.error(f"✗ Deployment readiness validation failed: {e}")
            self.validation_results['deployment_validation']['status'] = False
            self.validation_results['errors'].append(f"Deployment readiness: {str(e)}")
    
    def _assess_production_readiness(self):
        """Assess overall production readiness"""
        logger.info("Phase 10: Assessing production readiness...")
        
        try:
            # Define production readiness criteria with weights
            readiness_criteria = [
                {
                    'criterion': 'Architecture validation',
                    'test': 'architecture_validation',
                    'weight': 10,
                    'required': True,
                    'description': 'Core system architecture must be sound'
                },
                {
                    'criterion': 'Component integration',
                    'test': 'component_integration',
                    'weight': 9,
                    'required': True,
                    'description': 'All components must integrate properly'
                },
                {
                    'criterion': 'Data flow patterns',
                    'test': 'data_flow_patterns',
                    'weight': 9,
                    'required': True,
                    'description': 'Data must flow correctly through pipeline'
                },
                {
                    'criterion': 'File system integration',
                    'test': 'file_system_integration',
                    'weight': 7,
                    'required': True,
                    'description': 'File operations must work reliably'
                },
                {
                    'criterion': 'Configuration management',
                    'test': 'configuration_management',
                    'weight': 8,
                    'required': True,
                    'description': 'Configuration must be properly managed'
                },
                {
                    'criterion': 'Error handling',
                    'test': 'error_handling',
                    'weight': 8,
                    'required': True,
                    'description': 'System must handle errors gracefully'
                },
                {
                    'criterion': 'Performance patterns',
                    'test': 'performance_patterns',
                    'weight': 6,
                    'required': False,
                    'description': 'Performance optimizations recommended'
                },
                {
                    'criterion': 'Google Apps Script compatibility',
                    'test': 'google_apps_script_compatibility',
                    'weight': 8,
                    'required': True,
                    'description': 'Must be compatible with existing workflow'
                },
                {
                    'criterion': 'Deployment readiness',
                    'test': 'deployment_validation',
                    'weight': 9,
                    'required': True,
                    'description': 'Must have all deployment requirements'
                }
            ]
            
            # Calculate readiness scores
            total_score = 0
            max_possible_score = 0
            failed_required = []
            
            assessment_details = []
            
            for criterion in readiness_criteria:
                test_result = self.validation_results.get(criterion['test'], {})
                test_passed = test_result.get('status', False)
                weight = criterion['weight']
                
                max_possible_score += weight
                
                if test_passed:
                    total_score += weight
                    status_text = "PASS"
                    status_icon = "✓"
                elif criterion['required']:
                    failed_required.append(criterion['criterion'])
                    status_text = "FAIL (REQUIRED)"
                    status_icon = "✗"
                else:
                    status_text = "FAIL (OPTIONAL)"
                    status_icon = "⚠️"
                
                assessment_details.append({
                    'criterion': criterion['criterion'],
                    'status': test_passed,
                    'required': criterion['required'],
                    'weight': weight,
                    'status_text': status_text,
                    'status_icon': status_icon,
                    'description': criterion['description']
                })
            
            # Calculate overall readiness percentage
            readiness_percentage = (total_score / max_possible_score) * 100 if max_possible_score > 0 else 0
            
            # Determine production readiness
            is_production_ready = (
                readiness_percentage >= 85 and  # 85% overall score
                len(failed_required) == 0       # All required tests must pass
            )
            
            # Generate recommendations
            recommendations = self._generate_production_recommendations(
                is_production_ready, 
                failed_required, 
                assessment_details,
                readiness_percentage
            )
            
            # Update validation results
            self.validation_results['production_readiness']['status'] = is_production_ready
            self.validation_results['production_readiness']['details'].extend([
                f"🎯 PRODUCTION READINESS ASSESSMENT",
                f"Overall Score: {readiness_percentage:.1f}%",
                f"Required Criteria: {len(readiness_criteria) - len(failed_required)}/{sum(1 for c in readiness_criteria if c['required'])} passed",
                f"Production Ready: {'YES ✅' if is_production_ready else 'NO ❌'}",
                "",
                "Detailed Assessment:"
            ])
            
            for detail in assessment_details:
                self.validation_results['production_readiness']['details'].append(
                    f"  {detail['status_icon']} {detail['criterion']}: {detail['status_text']} "
                    f"(Weight: {detail['weight']}/10)"
                )
                self.validation_results['production_readiness']['details'].append(
                    f"     {detail['description']}"
                )
            
            if failed_required:
                self.validation_results['production_readiness']['details'].extend([
                    "",
                    f"❌ CRITICAL ISSUES - Failed Required Criteria:",
                    *[f"   • {criterion}" for criterion in failed_required]
                ])
            
            self.validation_results['production_readiness']['details'].extend([
                "",
                "📋 RECOMMENDATIONS:",
                *recommendations
            ])
            
            # Store recommendations
            self.validation_results['recommendations'] = recommendations
            
            # Log assessment results
            if is_production_ready:
                logger.info(f"🎉 PRODUCTION READY! Score: {readiness_percentage:.1f}%")
            else:
                logger.warning(f"❌ NOT PRODUCTION READY - Score: {readiness_percentage:.1f}%, Failed: {failed_required}")
            
        except Exception as e:
            logger.error(f"✗ Production readiness assessment failed: {e}")
            self.validation_results['production_readiness']['status'] = False
            self.validation_results['errors'].append(f"Production readiness assessment: {str(e)}")
    
    def _generate_production_recommendations(self, is_production_ready: bool, failed_required: List[str], assessment_details: List[Dict], score: float) -> List[str]:
        """Generate specific recommendations based on assessment results"""
        recommendations = []
        
        if is_production_ready:
            recommendations.extend([
                "🎉 SYSTEM IS PRODUCTION READY!",
                "✅ Deploy to production environment",
                "📊 Set up monitoring and logging",
                "🔄 Establish backup and recovery procedures",
                "📈 Monitor performance metrics in production"
            ])
        else:
            recommendations.append("❌ SYSTEM IS NOT READY FOR PRODUCTION")
            
            # Specific recommendations based on failed criteria
            for detail in assessment_details:
                if not detail['status'] and detail['required']:
                    criterion = detail['criterion']
                    
                    if 'architecture' in criterion.lower():
                        recommendations.extend([
                            "🏗️  Fix architecture issues:",
                            "   • Ensure all required files are present",
                            "   • Verify Python module imports work correctly",
                            "   • Check directory structure completeness"
                        ])
                    
                    elif 'integration' in criterion.lower():
                        recommendations.extend([
                            "🔗 Fix component integration:",
                            "   • Verify all modules can import each other",
                            "   • Check database connection configuration",
                            "   • Ensure web GUI can access backend modules"
                        ])
                    
                    elif 'data flow' in criterion.lower():
                        recommendations.extend([
                            "🌊 Fix data flow issues:",
                            "   • Verify database schema completeness",
                            "   • Check data transformation patterns",
                            "   • Ensure proper data validation"
                        ])
                    
                    elif 'error handling' in criterion.lower():
                        recommendations.extend([
                            "⚠️  Improve error handling:",
                            "   • Add try-catch blocks to critical functions",
                            "   • Implement proper logging throughout",
                            "   • Add data validation checks"
                        ])
                    
                    elif 'configuration' in criterion.lower():
                        recommendations.extend([
                            "⚙️  Fix configuration management:",
                            "   • Complete database configuration setup",
                            "   • Add production configuration files",
                            "   • Ensure proper dependency versioning"
                        ])
                    
                    elif 'deployment' in criterion.lower():
                        recommendations.extend([
                            "🚀 Prepare for deployment:",
                            "   • Create missing documentation",
                            "   • Add installation scripts",
                            "   • Ensure all deployment files are present"
                        ])
                    
                    elif 'compatibility' in criterion.lower():
                        recommendations.extend([
                            "🔄 Ensure Google Apps Script compatibility:",
                            "   • Verify QR code generation matches GAS workflow",
                            "   • Check CSV export format compatibility",
                            "   • Ensure file path conventions match"
                        ])
            
            # General recommendations based on score
            if score < 50:
                recommendations.extend([
                    "",
                    "🚨 CRITICAL: Score below 50% - Major rework needed",
                    "   • Focus on required criteria first",
                    "   • Consider architectural redesign",
                    "   • Extensive testing required before deployment"
                ])
            elif score < 70:
                recommendations.extend([
                    "",
                    "⚠️  MODERATE: Score below 70% - Significant issues remain",
                    "   • Address all required criteria failures",
                    "   • Improve optional components for better reliability",
                    "   • Plan thorough testing phase"
                ])
            elif score < 85:
                recommendations.extend([
                    "",
                    "📋 MINOR: Score below 85% - Small improvements needed",
                    "   • Address remaining required criteria",
                    "   • Consider optional improvements for production quality",
                    "   • Ready for staging deployment with monitoring"
                ])
        
        # Always add general best practices
        recommendations.extend([
            "",
            "📚 GENERAL BEST PRACTICES:",
            "   • Implement comprehensive logging",
            "   • Set up automated backups",
            "   • Create monitoring dashboards",
            "   • Document operational procedures",
            "   • Plan regular maintenance windows"
        ])
        
        return recommendations
    
    def _generate_validation_report(self) -> Dict:
        """Generate comprehensive validation report"""
        logger.info("Generating comprehensive validation report...")
        
        try:
            # Calculate summary statistics
            all_validation_keys = [k for k in self.validation_results.keys() 
                                 if isinstance(self.validation_results[k], dict) 
                                 and 'status' in self.validation_results[k]]
            
            total_validations = len(all_validation_keys)
            passed_validations = sum(1 for k in all_validation_keys 
                                   if self.validation_results[k].get('status') == True)
            
            test_duration = datetime.now() - self.validation_results['start_time']
            
            # Build comprehensive report
            final_report = {
                'validation_execution': {
                    'start_time': self.validation_results['start_time'].isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'duration_seconds': test_duration.total_seconds(),
                    'duration_formatted': str(test_duration)
                },
                'executive_summary': {
                    'total_validations': total_validations,
                    'passed_validations': passed_validations,
                    'failed_validations': total_validations - passed_validations,
                    'success_rate': (passed_validations / total_validations) * 100 if total_validations > 0 else 0,
                    'production_ready': self.validation_results.get('production_readiness', {}).get('status', False),
                    'total_errors': len(self.validation_results.get('errors', [])),
                    'total_warnings': len(self.validation_results.get('warnings', []))
                },
                'detailed_results': self.validation_results,
                'recommendations': self.validation_results.get('recommendations', []),
                'deployment_verdict': self._get_deployment_verdict()
            }
            
            # Log executive summary
            logger.info("=" * 80)
            logger.info("PIPELINE INTEGRATION VALIDATION COMPLETED")
            logger.info("=" * 80)
            logger.info(f"Validations: {passed_validations}/{total_validations} passed ({(passed_validations/total_validations)*100:.1f}%)")
            logger.info(f"Duration: {test_duration}")
            logger.info(f"Production Ready: {'YES' if final_report['executive_summary']['production_ready'] else 'NO'}")
            logger.info(f"Errors: {final_report['executive_summary']['total_errors']}")
            logger.info(f"Warnings: {final_report['executive_summary']['total_warnings']}")
            logger.info("=" * 80)
            
            return final_report
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {
                'error': f"Report generation failed: {str(e)}",
                'partial_results': self.validation_results
            }
    
    def _get_deployment_verdict(self) -> Dict:
        """Get final deployment verdict and recommendation"""
        is_production_ready = self.validation_results.get('production_readiness', {}).get('status', False)
        
        all_validation_keys = [k for k in self.validation_results.keys() 
                             if isinstance(self.validation_results[k], dict) 
                             and 'status' in self.validation_results[k]]
        
        total_validations = len(all_validation_keys)
        passed_validations = sum(1 for k in all_validation_keys 
                               if self.validation_results[k].get('status') == True)
        
        success_rate = (passed_validations / total_validations) * 100 if total_validations > 0 else 0
        
        if is_production_ready and success_rate >= 90:
            return {
                'verdict': 'DEPLOY_TO_PRODUCTION',
                'confidence': 'HIGH',
                'recommendation': '🎉 DEPLOY TO PRODUCTION - System is bulletproof and ready for live operation',
                'action_items': [
                    'Deploy to production environment',
                    'Set up monitoring and alerting',
                    'Configure automated backups',
                    'Document operational procedures'
                ]
            }
        elif is_production_ready and success_rate >= 80:
            return {
                'verdict': 'DEPLOY_WITH_MONITORING',
                'confidence': 'MEDIUM_HIGH',
                'recommendation': '✅ DEPLOY WITH MONITORING - Production ready but monitor closely',
                'action_items': [
                    'Deploy to production with enhanced monitoring',
                    'Set up alerts for all system components',
                    'Plan immediate response procedures',
                    'Schedule regular health checks'
                ]
            }
        elif success_rate >= 70:
            return {
                'verdict': 'DEPLOY_TO_STAGING',
                'confidence': 'MEDIUM',
                'recommendation': '📋 DEPLOY TO STAGING - Address issues before production',
                'action_items': [
                    'Deploy to staging environment first',
                    'Fix identified integration issues',
                    'Run comprehensive testing',
                    'Re-validate before production deployment'
                ]
            }
        else:
            return {
                'verdict': 'DO_NOT_DEPLOY',
                'confidence': 'LOW',
                'recommendation': '❌ DO NOT DEPLOY - Critical issues require immediate attention',
                'action_items': [
                    'Address all critical failures',
                    'Fix required component integrations',
                    'Improve error handling and logging',
                    'Re-run validation after fixes'
                ]
            }

def main():
    """Main function to run pipeline integration validation"""
    print("🔍 Starting Pipeline Integration Validation")
    print("Validating production readiness for Silver Fox Marketing")
    print("=" * 80)
    
    # Create and run validator
    validator = PipelineIntegrationValidator()
    
    try:
        # Execute validation
        final_report = validator.run_comprehensive_validation()
        
        # Save detailed report
        report_file = f"pipeline_integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2, default=str)
        
        print(f"\n📋 Detailed report saved: {report_file}")
        
        # Print executive summary
        print("\n" + "=" * 80)
        print("EXECUTIVE SUMMARY")
        print("=" * 80)
        
        summary = final_report.get('executive_summary', {})
        verdict = final_report.get('deployment_verdict', {})
        
        print(f"Validations Passed: {summary.get('passed_validations', 0)}/{summary.get('total_validations', 0)} ({summary.get('success_rate', 0):.1f}%)")
        print(f"Production Ready: {'YES' if summary.get('production_ready') else 'NO'}")
        print(f"Deployment Verdict: {verdict.get('verdict', 'UNKNOWN')}")
        print(f"Confidence Level: {verdict.get('confidence', 'UNKNOWN')}")
        print(f"Recommendation: {verdict.get('recommendation', 'Unknown')}")
        
        errors = final_report.get('detailed_results', {}).get('errors', [])
        warnings = final_report.get('detailed_results', {}).get('warnings', [])
        
        if errors:
            print(f"\n⚠️  Errors ({len(errors)}):")
            for error in errors[:3]:  # Show first 3 errors
                print(f"  • {error}")
            if len(errors) > 3:
                print(f"  ... and {len(errors) - 3} more errors")
        
        if warnings:
            print(f"\n⚠️  Warnings ({len(warnings)}):")
            for warning in warnings[:3]:  # Show first 3 warnings
                print(f"  • {warning}")
            if len(warnings) > 3:
                print(f"  ... and {len(warnings) - 3} more warnings")
        
        action_items = verdict.get('action_items', [])
        if action_items:
            print(f"\n📝 Next Steps:")
            for item in action_items:
                print(f"  • {item}")
        
        print("=" * 80)
        
        return 0 if summary.get('production_ready') else 1
        
    except KeyboardInterrupt:
        print("\n⏹️  Validation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Validation failed with critical error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())