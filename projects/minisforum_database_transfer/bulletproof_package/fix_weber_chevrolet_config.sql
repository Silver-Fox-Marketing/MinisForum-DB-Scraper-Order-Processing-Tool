-- Fix Weber Chevrolet Configuration
-- Add missing exclude_missing_stock_number filter to match South County DCJR

UPDATE dealership_configs
SET filtering_rules = '{"notes": "Standardized configuration based on Porsche St. Louis template", "order_type": "cao", "days_on_lot": {"max": 999, "min": 0}, "price_range": {"max": 999999, "min": 0}, "require_stock": true, "vehicle_types": ["new", "used"], "exclude_status": ["In-Transit", "Sold", "Allocated"], "exclude_in_transit": true, "allowed_vehicle_types": ["new", "cpo", "po", "certified", "pre-owned"], "exclude_missing_stock_number": true}'
WHERE name = 'Weber Chevrolet';

-- Verify the update
SELECT name, filtering_rules FROM dealership_configs WHERE name = 'Weber Chevrolet';