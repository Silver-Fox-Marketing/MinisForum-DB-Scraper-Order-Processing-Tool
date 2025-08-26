#!/usr/bin/env python3
"""
Scraper Data Normalizer
=======================
Normalizes raw scraper data into standardized categories:
- Vehicle types: cpo, po, new  
- Lot status: onlot, offlot

Based on normalization mapping CSV file.
"""

import os
import sys
import csv
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)

class ScraperDataNormalizer:
    """Normalizes raw scraper data using predefined mapping rules"""
    
    def __init__(self, mapping_file_path: str = None):
        self.vehicle_type_mapping = {}
        self.lot_status_mapping = {}
        
        # Default mapping file path
        if not mapping_file_path:
            mapping_file_path = r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\shared_resources\Scraper Data Normalization Map - Sheet1 (1).csv"
        
        self.load_normalization_mapping(mapping_file_path)
    
    def load_normalization_mapping(self, file_path: str):
        """Load normalization mapping from CSV file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    raw_value = row['Raw'].strip()
                    normalized_value = row['Normalized'].strip()
                    
                    # Determine if this is a vehicle type or lot status mapping
                    if normalized_value in ['cpo', 'po', 'new']:
                        self.vehicle_type_mapping[raw_value.lower()] = normalized_value
                    elif normalized_value in ['onlot', 'offlot']:
                        self.lot_status_mapping[raw_value.lower()] = normalized_value
                    
                logger.info(f"Loaded {len(self.vehicle_type_mapping)} vehicle type mappings")
                logger.info(f"Loaded {len(self.lot_status_mapping)} lot status mappings")
                
        except Exception as e:
            logger.error(f"Error loading normalization mapping: {e}")
            # Fallback to basic mappings
            self._load_fallback_mappings()
    
    def _load_fallback_mappings(self):
        """Load basic fallback mappings if CSV fails"""
        logger.warning("Using fallback normalization mappings")
        
        # Vehicle type mappings
        self.vehicle_type_mapping = {
            'certified used': 'cpo',
            'certified pre-owned': 'cpo', 
            'certified': 'cpo',
            'used': 'po',
            'pre-owned': 'po',
            'new': 'new'
        }
        
        # Lot status mappings - CRITICAL: Use 'on lot' format for database compatibility
        self.lot_status_mapping = {
            'instock': 'on lot',
            'in stock': 'on lot',
            'available': 'on lot',
            'on lot': 'on lot',
            'on-lot': 'on lot',
            'in-transit': 'off lot',
            'in transit': 'off lot',
            'allocated': 'off lot',
            'courtesy vehicle': 'off lot',
            'in-service': 'off lot'
        }
    
    def normalize_vehicle_type(self, raw_type: str) -> str:
        """Normalize vehicle type to cpo, po, or new"""
        if not raw_type:
            return 'unknown'
            
        raw_type_lower = raw_type.lower().strip()
        
        # Direct lookup first
        if raw_type_lower in self.vehicle_type_mapping:
            return self.vehicle_type_mapping[raw_type_lower]
        
        # Fuzzy matching for partial matches
        for key, value in self.vehicle_type_mapping.items():
            if key in raw_type_lower or raw_type_lower in key:
                return value
        
        # Default fallback based on common patterns
        if 'certified' in raw_type_lower or 'cpo' in raw_type_lower:
            return 'cpo'
        elif 'used' in raw_type_lower or 'pre-owned' in raw_type_lower:
            return 'po'
        elif 'new' in raw_type_lower:
            return 'new'
        
        return 'unknown'
    
    def normalize_lot_status(self, raw_status: str) -> str:
        """Normalize status to onlot or offlot"""
        if not raw_status:
            return 'unknown'
            
        raw_status_lower = raw_status.lower().strip()
        
        # Direct lookup first
        if raw_status_lower in self.lot_status_mapping:
            return self.lot_status_mapping[raw_status_lower]
        
        # Fuzzy matching for partial matches
        for key, value in self.lot_status_mapping.items():
            if key in raw_status_lower or raw_status_lower in key:
                return value
        
        # Default fallback patterns - CRITICAL: Use 'on lot' format for database compatibility
        if any(word in raw_status_lower for word in ['stock', 'available', 'lot']):
            return 'on lot'
        elif any(word in raw_status_lower for word in ['transit', 'allocated', 'courtesy', 'service', 'build', 'production']):
            return 'off lot'
        
        # Conservative default - assume on lot if unsure
        return 'on lot'
    
    def normalize_vehicle_data(self, vehicle_data: Dict) -> Tuple[str, str]:
        """
        Normalize a vehicle record and return (normalized_type, lot_status)
        
        Args:
            vehicle_data: Dictionary containing vehicle information
            
        Returns:
            Tuple of (normalized_vehicle_type, on_lot_status)
        """
        raw_type = vehicle_data.get('type', '')
        raw_status = vehicle_data.get('status', '')
        
        normalized_type = self.normalize_vehicle_type(raw_type)
        lot_status = self.normalize_lot_status(raw_status)
        
        return normalized_type, lot_status
    
    def get_mapping_stats(self) -> Dict:
        """Get statistics about the loaded mappings"""
        return {
            'vehicle_type_mappings': len(self.vehicle_type_mapping),
            'lot_status_mappings': len(self.lot_status_mapping),
            'vehicle_types': list(set(self.vehicle_type_mapping.values())),
            'lot_statuses': list(set(self.lot_status_mapping.values()))
        }

# Global normalizer instance
normalizer = ScraperDataNormalizer()

if __name__ == "__main__":
    # Test the normalizer
    test_data = [
        {'type': 'Certified Pre-Owned', 'status': 'InStock'},
        {'type': 'Used', 'status': 'Available'},
        {'type': 'New', 'status': 'In-Transit'},
        {'type': 'Certified Used', 'status': 'Courtesy Vehicle'}
    ]
    
    print("Testing Scraper Data Normalizer:")
    print("=" * 50)
    
    for i, vehicle in enumerate(test_data, 1):
        norm_type, lot_status = normalizer.normalize_vehicle_data(vehicle)
        print(f"{i}. {vehicle['type']:20} | {vehicle['status']:15} -> {norm_type:5} | {lot_status}")
    
    print("\nMapping Statistics:")
    stats = normalizer.get_mapping_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")