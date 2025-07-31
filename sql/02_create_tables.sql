-- Create all tables for the dealership database
-- Run this after creating the database

-- 1. Raw Vehicle Data Table (Audit/Legal Copy)
CREATE TABLE IF NOT EXISTS raw_vehicle_data (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17),
    stock VARCHAR(50),
    type VARCHAR(50),
    year INTEGER,
    make VARCHAR(100),
    model VARCHAR(100),
    trim VARCHAR(200),
    ext_color VARCHAR(100),
    status VARCHAR(50),
    price DECIMAL(10, 2),
    body_style VARCHAR(50),
    fuel_type VARCHAR(50),
    msrp DECIMAL(10, 2),
    date_in_stock DATE,
    street_address VARCHAR(255),
    locality VARCHAR(100),
    postal_code VARCHAR(20),
    region VARCHAR(100),
    country VARCHAR(100),
    location VARCHAR(100), -- dealership identifier
    vehicle_url TEXT,
    import_date DATE DEFAULT CURRENT_DATE,
    import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for raw_vehicle_data
CREATE INDEX IF NOT EXISTS idx_raw_vin ON raw_vehicle_data(vin);
CREATE INDEX IF NOT EXISTS idx_raw_stock ON raw_vehicle_data(stock);
CREATE INDEX IF NOT EXISTS idx_raw_location ON raw_vehicle_data(location);
CREATE INDEX IF NOT EXISTS idx_raw_import_date ON raw_vehicle_data(import_date);

-- 2. Normalized Vehicle Data Table (Processed Data)
CREATE TABLE IF NOT EXISTS normalized_vehicle_data (
    id SERIAL PRIMARY KEY,
    raw_data_id INTEGER REFERENCES raw_vehicle_data(id) ON DELETE CASCADE,
    vin VARCHAR(17) NOT NULL,
    stock VARCHAR(50) NOT NULL,
    vehicle_condition VARCHAR(10) CHECK (vehicle_condition IN ('new', 'po', 'cpo', 'offlot', 'onlot')),
    year INTEGER,
    make VARCHAR(100),
    model VARCHAR(100),
    trim VARCHAR(200),
    status VARCHAR(50),
    price DECIMAL(10, 2),
    msrp DECIMAL(10, 2),
    date_in_stock DATE,
    location VARCHAR(100),
    vehicle_url TEXT,
    vin_scan_count INTEGER DEFAULT 1,
    last_seen_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint to prevent duplicates
    UNIQUE(vin, location)
);

-- Create indexes for normalized_vehicle_data
CREATE INDEX IF NOT EXISTS idx_norm_vin ON normalized_vehicle_data(vin);
CREATE INDEX IF NOT EXISTS idx_norm_stock ON normalized_vehicle_data(stock);
CREATE INDEX IF NOT EXISTS idx_norm_location ON normalized_vehicle_data(location);
CREATE INDEX IF NOT EXISTS idx_norm_condition ON normalized_vehicle_data(vehicle_condition);
CREATE INDEX IF NOT EXISTS idx_norm_last_seen ON normalized_vehicle_data(last_seen_date);

-- 3. VIN History Table (Tracking)
CREATE TABLE IF NOT EXISTS vin_history (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    dealership_name VARCHAR(100) NOT NULL,
    scan_date DATE NOT NULL,
    raw_data_id INTEGER REFERENCES raw_vehicle_data(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for vin_history
CREATE INDEX IF NOT EXISTS idx_history_vin ON vin_history(vin);
CREATE INDEX IF NOT EXISTS idx_history_dealership ON vin_history(dealership_name);
CREATE INDEX IF NOT EXISTS idx_history_scan_date ON vin_history(scan_date);

-- 4. Dealership Configs Table
CREATE TABLE IF NOT EXISTS dealership_configs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    filtering_rules JSONB DEFAULT '{}',
    output_rules JSONB DEFAULT '{}',
    qr_output_path TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for dealership_configs
CREATE INDEX IF NOT EXISTS idx_config_name ON dealership_configs(name);
CREATE INDEX IF NOT EXISTS idx_config_active ON dealership_configs(is_active);

-- Create update trigger for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_normalized_vehicle_data_updated_at 
    BEFORE UPDATE ON normalized_vehicle_data
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dealership_configs_updated_at 
    BEFORE UPDATE ON dealership_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add foreign key constraint to ensure location matches dealership configs
-- Note: This should be run after dealership_configs table is populated
-- ALTER TABLE normalized_vehicle_data
-- ADD CONSTRAINT fk_location_dealership
-- FOREIGN KEY (location) REFERENCES dealership_configs(name) ON DELETE CASCADE;

-- Create view for easy querying of current inventory
CREATE OR REPLACE VIEW current_inventory AS
SELECT 
    n.*,
    d.name as dealership_name,
    d.qr_output_path
FROM normalized_vehicle_data n
JOIN dealership_configs d ON n.location = d.name
WHERE n.last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
    AND d.is_active = true
    AND n.vehicle_condition IN ('new', 'po', 'cpo', 'onlot');

-- Grant permissions (adjust as needed)
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;