#!/usr/bin/env python3
"""
Production Configuration for MinisForum Database Web GUI
========================================================

Production-ready Flask configuration with security settings
and performance optimizations.

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import os

class ProductionConfig:
    """Production Flask configuration"""
    
    # Security settings
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'silver_fox_marketing_minisforum_2025')
    DEBUG = False
    TESTING = False
    
    # Server settings
    HOST = os.environ.get('FLASK_HOST', '127.0.0.1')  # Use 0.0.0.0 for external access
    PORT = int(os.environ.get('FLASK_PORT', 5000))
    
    # Performance settings
    THREADED = True
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = 'production_web_gui.log'
    
    # CORS settings
    CORS_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:5000']
    
    # Database settings (from environment for security)
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://localhost/dealership_db')
    
    @staticmethod
    def init_app(app):
        """Initialize app with production settings"""
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Configure logging
        if not app.debug and not app.testing:
            file_handler = RotatingFileHandler(
                ProductionConfig.LOG_FILE,
                maxBytes=10485760,  # 10MB
                backupCount=5
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('MinisForum Web GUI startup (production)')

class DevelopmentConfig:
    """Development Flask configuration"""
    
    DEBUG = True
    SECRET_KEY = 'dev-key-not-for-production'
    HOST = '127.0.0.1'
    PORT = 5000
    THREADED = True
    LOG_LEVEL = 'DEBUG'

def get_config():
    """Get appropriate configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    
    if env == 'production':
        return ProductionConfig
    else:
        return DevelopmentConfig