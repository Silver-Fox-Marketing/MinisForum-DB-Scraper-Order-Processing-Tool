"""
Database configuration for the dealership database system
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str = "localhost"
    port: int = 5432
    database: str = "dealership_db"
    user: str = "postgres"
    password: str = ""  # Set via environment variable
    
    # Connection pool settings
    min_connections: int = 1
    max_connections: int = 5
    
    # Paths
    base_path: str = r"C:\dealership_database"
    backup_path: str = r"C:\dealership_database\backups"
    import_path: str = r"C:\dealership_database\imports"
    export_path: str = r"C:\dealership_database\exports"
    
    def __post_init__(self):
        # Get password from environment variable for security
        self.password = os.environ.get('DEALERSHIP_DB_PASSWORD', '')
        
        # Create directories if they don't exist (password will be set via environment)
        
        # Create directories if they don't exist
        for path in [self.base_path, self.backup_path, self.import_path, self.export_path]:
            os.makedirs(path, exist_ok=True)
    
    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def connection_dict(self) -> dict:
        """Get connection parameters as dictionary"""
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password
        }

# Vehicle condition normalization rules
CONDITION_MAPPING = {
    # CPO mappings
    'certified used': 'cpo',
    'certified pre-owned': 'cpo',
    'certified': 'cpo',
    'cpo': 'cpo',
    
    # Pre-owned mappings
    'used': 'po',
    'pre-owned': 'po',
    'preowned': 'po',
    'po': 'po',
    
    # New mappings
    'new': 'new',
    
    # Off-lot mappings
    'in-transit': 'offlot',
    'in transit': 'offlot',
    'intransit': 'offlot',
    'arriving soon': 'offlot',
    'arriving': 'offlot',
    'offlot': 'offlot',
    
    # On-lot mappings
    'on-lot': 'onlot',
    'on lot': 'onlot',
    'onlot': 'onlot',
    'in-lot': 'onlot',
    'in lot': 'onlot',
    'inlot': 'onlot',
    'instock': 'onlot',
    'in stock': 'onlot',
    'available': 'onlot'
}

# CSV column mappings
CSV_COLUMNS = [
    'vin', 'stock', 'type', 'year', 'make', 'model', 'trim',
    'ext_color', 'status', 'price', 'body_style', 'fuel_type',
    'msrp', 'date_in_stock', 'street_address', 'locality',
    'postal_code', 'region', 'country', 'location', 'vehicle_url'
]

# Required columns that must have values
REQUIRED_COLUMNS = ['vin', 'stock']

# Numeric columns that need type conversion
NUMERIC_COLUMNS = ['year', 'price', 'msrp']

# Date columns that need parsing
DATE_COLUMNS = ['date_in_stock']

# Default configuration instance
config = DatabaseConfig()