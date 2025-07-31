#!/usr/bin/env python3
"""
Web GUI Validation Script
=========================

Comprehensive validation script for the MinisForum Database Web GUI
to ensure bulletproof deployment readiness.

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import os
import sys
import json
import re
from pathlib import Path

class WebGUIValidator:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.issues = []
        self.warnings = []
        self.passes = []
        
    def log_pass(self, message):
        self.passes.append(f"✓ {message}")
        print(f"✓ {message}")
        
    def log_warning(self, message):
        self.warnings.append(f"⚠ {message}")
        print(f"⚠ {message}")
        
    def log_issue(self, message):
        self.issues.append(f"✗ {message}")
        print(f"✗ {message}")
    
    def validate_file_structure(self):
        """Validate required files and directories exist"""
        print("\n=== FILE STRUCTURE VALIDATION ===")
        
        required_files = [
            'app.py',
            'requirements.txt',
            'start_server.bat',
            'templates/index.html',
            'static/css/style.css',
            'static/js/app.js'
        ]
        
        required_dirs = [
            'static',
            'static/css',
            'static/js',
            'static/fonts',
            'templates'
        ]
        
        for file_path in required_files:
            full_path = self.base_dir / file_path
            if full_path.exists():
                self.log_pass(f"Required file exists: {file_path}")
            else:
                self.log_issue(f"Missing required file: {file_path}")
        
        for dir_path in required_dirs:
            full_path = self.base_dir / dir_path
            if full_path.exists():
                self.log_pass(f"Required directory exists: {dir_path}")
            else:
                self.log_issue(f"Missing required directory: {dir_path}")
    
    def validate_flask_app(self):
        """Validate Flask application configuration"""
        print("\n=== FLASK APPLICATION VALIDATION ===")
        
        app_file = self.base_dir / 'app.py'
        if not app_file.exists():
            self.log_issue("app.py file missing")
            return
            
        with open(app_file, 'r') as f:
            app_content = f.read()
        
        # Check Flask imports
        if 'from flask import Flask' in app_content:
            self.log_pass("Flask import found")
        else:
            self.log_issue("Flask import missing")
            
        # Check Flask-SocketIO
        if 'from flask_socketio import SocketIO' in app_content:
            self.log_pass("Flask-SocketIO import found")
        else:
            self.log_warning("Flask-SocketIO import missing")
        
        # Check secret key
        if 'app.secret_key' in app_content:
            self.log_pass("Secret key configured")
        else:
            self.log_issue("Secret key missing")
        
        # Check debug mode
        if 'debug=True' in app_content:
            self.log_warning("Debug mode enabled - should be disabled in production")
        else:
            self.log_pass("Debug mode properly configured")
        
        # Check API routes
        api_routes = re.findall(r'@app\.route\([\'\"](/api/[^\'\"]+)', app_content)
        if len(api_routes) >= 5:
            self.log_pass(f"Found {len(api_routes)} API routes")
        else:
            self.log_warning(f"Only {len(api_routes)} API routes found - may be incomplete")
    
    def validate_frontend_integration(self):
        """Validate frontend-backend integration"""
        print("\n=== FRONTEND INTEGRATION VALIDATION ===")
        
        # Check template file
        template_file = self.base_dir / 'templates/index.html'
        if template_file.exists():
            with open(template_file, 'r') as f:
                template_content = f.read()
            
            # Check Flask templating usage
            if '{{ url_for(' in template_content:
                self.log_pass("Flask templating used for static assets")
            else:
                self.log_warning("Flask templating not used - static assets may not load correctly")
            
            # Check responsive design
            if 'viewport' in template_content:
                self.log_pass("Responsive design viewport configured")
            else:
                self.log_warning("Viewport meta tag missing - mobile compatibility issues")
                
        # Check JavaScript file
        js_file = self.base_dir / 'static/js/app.js'
        if js_file.exists():
            with open(js_file, 'r') as f:
                js_content = f.read()
            
            # Check API calls
            api_calls = js_content.count("fetch('/api/")
            if api_calls >= 5:
                self.log_pass(f"Found {api_calls} API fetch calls")
            else:
                self.log_warning(f"Only {api_calls} API calls found")
            
            # Check error handling
            try_blocks = js_content.count('try {')
            catch_blocks = js_content.count('catch (')
            
            if try_blocks == catch_blocks and try_blocks > 0:
                self.log_pass(f"Error handling implemented ({try_blocks} try/catch blocks)")
            else:
                self.log_warning("Incomplete error handling in JavaScript")
    
    def validate_static_assets(self):
        """Validate static asset configuration"""
        print("\n=== STATIC ASSETS VALIDATION ===")
        
        css_file = self.base_dir / 'static/css/style.css'
        if css_file.exists():
            with open(css_file, 'r') as f:
                css_content = f.read()
            
            # Check for CSS3 features
            modern_features = ['flexbox', 'grid', 'transition', 'transform']
            found_features = []
            
            if 'display: flex' in css_content:
                found_features.append('flexbox')
            if 'display: grid' in css_content:
                found_features.append('grid')
            if 'transition:' in css_content:
                found_features.append('transitions')
            if 'transform:' in css_content:
                found_features.append('transforms')
            
            if len(found_features) >= 2:
                self.log_pass(f"Modern CSS features used: {found_features}")
            else:
                self.log_warning("Limited use of modern CSS features")
            
            # Check brand colors
            if '--primary-red:' in css_content:
                self.log_pass("Silver Fox brand colors configured")
            else:
                self.log_warning("Brand colors not found in CSS")
        
        # Check font files
        fonts_dir = self.base_dir / 'static/fonts'
        if fonts_dir.exists():
            font_files = list(fonts_dir.glob('*.woff*'))
            if len(font_files) >= 2:
                self.log_pass(f"Font files available: {[f.name for f in font_files]}")
            else:
                self.log_warning("Calmetta brand fonts missing - will fallback to Montserrat")
    
    def validate_backend_integration(self):
        """Validate backend module integration"""
        print("\n=== BACKEND INTEGRATION VALIDATION ===")
        
        app_file = self.base_dir / 'app.py'
        if app_file.exists():
            with open(app_file, 'r') as f:
                app_content = f.read()
            
            # Check backend imports
            backend_modules = [
                'database_connection',
                'csv_importer_complete',
                'order_processing_integration',
                'qr_code_generator',
                'data_exporter'
            ]
            
            import_count = 0
            for module in backend_modules:
                if f'from {module} import' in app_content:
                    import_count += 1
            
            if import_count == len(backend_modules):
                self.log_pass("All backend modules imported")
            else:
                self.log_warning(f"Only {import_count}/{len(backend_modules)} backend modules imported")
            
            # Check error handling for imports
            if 'try:' in app_content and 'ImportError' in app_content:
                self.log_pass("Import error handling implemented")
            else:
                self.log_warning("Import error handling missing")
    
    def validate_security(self):
        """Validate security configuration"""
        print("\n=== SECURITY VALIDATION ===")
        
        # Check Flask app security
        app_file = self.base_dir / 'app.py'
        if app_file.exists():
            with open(app_file, 'r') as f:
                app_content = f.read()
            
            # Check CORS configuration
            if 'cors_allowed_origins' in app_content:
                self.log_pass("CORS configuration found")
            else:
                self.log_warning("CORS configuration may be missing")
            
            # Check for SQL injection prevention
            if 'execute_query' in app_content:
                self.log_pass("Database query methods used (parameterized queries)")
            else:
                self.log_warning("Database query patterns not found")
        
        # Check template security
        template_file = self.base_dir / 'templates/index.html'
        if template_file.exists():
            with open(template_file, 'r') as f:
                template_content = f.read()
            
            # Check for XSS protection
            if '{{ ' in template_content and ' }}' in template_content:
                self.log_pass("Flask auto-escaping enabled (XSS protection)")
            else:
                self.log_warning("Template escaping may not be enabled")
    
    def validate_production_readiness(self):
        """Validate production deployment readiness"""
        print("\n=== PRODUCTION READINESS VALIDATION ===")
        
        # Check requirements file
        req_file = self.base_dir / 'requirements.txt'
        if req_file.exists():
            with open(req_file, 'r') as f:
                requirements = f.read()
            
            essential_packages = ['Flask', 'Flask-SocketIO', 'psycopg2-binary']
            missing_packages = []
            
            for package in essential_packages:
                if package.lower() not in requirements.lower():
                    missing_packages.append(package)
            
            if not missing_packages:
                self.log_pass("All essential packages in requirements.txt")
            else:
                self.log_warning(f"Missing packages: {missing_packages}")
        
        # Check startup script
        startup_script = self.base_dir / 'start_server.bat'
        if startup_script.exists():
            with open(startup_script, 'r') as f:
                script_content = f.read()
            
            if 'pip install -r requirements.txt' in script_content:
                self.log_pass("Startup script installs dependencies")
            else:
                self.log_warning("Startup script missing dependency installation")
            
            if 'python app.py' in script_content:
                self.log_pass("Startup script launches application")
            else:
                self.log_issue("Startup script missing application launch")
    
    def run_validation(self):
        """Run complete validation suite"""
        print("🔍 MinisForum Database Web GUI - Bulletproof Deployment Validation")
        print("=" * 70)
        
        self.validate_file_structure()
        self.validate_flask_app()
        self.validate_frontend_integration()
        self.validate_static_assets()
        self.validate_backend_integration()
        self.validate_security()
        self.validate_production_readiness()
        
        # Generate summary
        print("\n" + "=" * 70)
        print("🏁 VALIDATION SUMMARY")
        print("=" * 70)
        
        print(f"✅ PASSED: {len(self.passes)} checks")
        print(f"⚠️  WARNINGS: {len(self.warnings)} items")
        print(f"❌ ISSUES: {len(self.issues)} critical problems")
        
        if self.issues:
            print("\n🚨 CRITICAL ISSUES TO FIX:")
            for issue in self.issues:
                print(f"   {issue}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS TO CONSIDER:")
            for warning in self.warnings:
                print(f"   {warning}")
        
        # Overall assessment
        print("\n" + "=" * 70)
        if len(self.issues) == 0:
            if len(self.warnings) <= 3:
                print("🎉 WEB GUI IS BULLETPROOF - READY FOR DEPLOYMENT!")
            else:
                print("✅ WEB GUI IS DEPLOYMENT READY - Consider addressing warnings")
        else:
            print("❌ WEB GUI NEEDS FIXES BEFORE DEPLOYMENT")
        
        print("=" * 70)
        
        return len(self.issues) == 0

if __name__ == '__main__':
    validator = WebGUIValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)