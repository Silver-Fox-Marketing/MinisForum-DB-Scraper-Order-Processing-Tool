-- Additional Constraints and Optimizations
-- Run this after dealership_configs table is populated (after 03_initial_dealership_configs.sql)

-- Add foreign key constraint to ensure location matches dealership configs
ALTER TABLE normalized_vehicle_data
ADD CONSTRAINT fk_location_dealership
FOREIGN KEY (location) REFERENCES dealership_configs(name) ON DELETE CASCADE;

-- Add validation constraints for data integrity
ALTER TABLE normalized_vehicle_data
ADD CONSTRAINT check_price_positive CHECK (price >= 0);

ALTER TABLE normalized_vehicle_data
ADD CONSTRAINT check_msrp_positive CHECK (msrp >= 0 OR msrp IS NULL);

ALTER TABLE normalized_vehicle_data
ADD CONSTRAINT check_year_reasonable CHECK (year >= 1900 AND year <= 2030);

-- Add VIN format validation (basic 17-character alphanumeric check)
ALTER TABLE normalized_vehicle_data
ADD CONSTRAINT check_vin_format CHECK (
    vin ~ '^[A-HJ-NPR-Z0-9]{17}$' OR vin IS NULL
);

-- Ensure stock numbers are not empty when provided
ALTER TABLE normalized_vehicle_data
ADD CONSTRAINT check_stock_not_empty CHECK (
    stock IS NULL OR LENGTH(TRIM(stock)) > 0
);

-- Add constraint for dealership_configs to ensure QR paths are not empty
ALTER TABLE dealership_configs
ADD CONSTRAINT check_qr_path_not_empty CHECK (
    qr_output_path IS NULL OR LENGTH(TRIM(qr_output_path)) > 0
);

-- Create additional indexes for common query patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_normalized_make_model 
    ON normalized_vehicle_data(make, model);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_normalized_year_condition 
    ON normalized_vehicle_data(year, vehicle_condition);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_normalized_price_range 
    ON normalized_vehicle_data(price) WHERE price > 0;

-- Note: QR file tracking indexes are created in 06_order_processing_tables.sql

-- Add comment to document the execution order
COMMENT ON CONSTRAINT fk_location_dealership ON normalized_vehicle_data IS 
'Ensures all vehicle locations reference valid dealership configurations';

-- Grant permissions for new constraints
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;