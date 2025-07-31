-- Order Processing Tables for Silver Fox Marketing
-- ================================================

-- VIN History table for tracking vehicle changes
CREATE TABLE IF NOT EXISTS vin_history (
    id SERIAL PRIMARY KEY,
    dealership_name VARCHAR(255) NOT NULL,
    vin VARCHAR(17) NOT NULL,
    order_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dealership_name, vin, order_date)
);

-- Index for faster lookups
CREATE INDEX idx_vin_history_dealership_date ON vin_history(dealership_name, order_date DESC);
CREATE INDEX idx_vin_history_vin ON vin_history(vin);

-- Order Schedule table for tracking weekly schedule
CREATE TABLE IF NOT EXISTS order_schedule (
    id SERIAL PRIMARY KEY,
    day_of_week VARCHAR(10) NOT NULL,
    order_type VARCHAR(20) NOT NULL, -- 'CAO' or 'As Ordered'
    dealership_name VARCHAR(255) NOT NULL,
    template_type VARCHAR(50),
    vehicle_types TEXT[], -- Array of types: new, used, cpo, etc
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dealership filter configurations
CREATE TABLE IF NOT EXISTS dealership_filters (
    id SERIAL PRIMARY KEY,
    dealership_name VARCHAR(255) UNIQUE NOT NULL,
    exclude_conditions TEXT[], -- e.g., ['In-Transit', 'Missing Stock #']
    include_types TEXT[], -- e.g., ['New', 'Used', 'CPO']
    min_price DECIMAL(10, 2),
    max_price DECIMAL(10, 2),
    exclude_missing_stock BOOLEAN DEFAULT TRUE,
    exclude_missing_price BOOLEAN DEFAULT FALSE,
    exclude_in_transit BOOLEAN DEFAULT FALSE,
    custom_filters JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order processing results
CREATE TABLE IF NOT EXISTS order_results (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES order_processing_jobs(job_id),
    dealership_name VARCHAR(255) NOT NULL,
    order_type VARCHAR(20) NOT NULL,
    order_date DATE NOT NULL,
    total_vehicles INTEGER DEFAULT 0,
    new_vehicles INTEGER DEFAULT 0,
    removed_vehicles INTEGER DEFAULT 0,
    qr_codes_generated INTEGER DEFAULT 0,
    qr_folder_path TEXT,
    csv_file_path TEXT,
    processing_time_seconds DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- QR Code tracking
CREATE TABLE IF NOT EXISTS qr_codes (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES order_processing_jobs(job_id),
    dealership_name VARCHAR(255) NOT NULL,
    vin VARCHAR(17) NOT NULL,
    vehicle_url TEXT NOT NULL,
    qr_file_path TEXT NOT NULL,
    qr_file_name VARCHAR(255) NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily scrape logs
CREATE TABLE IF NOT EXISTS daily_scrape_logs (
    id SERIAL PRIMARY KEY,
    scrape_date DATE NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    total_dealerships INTEGER DEFAULT 0,
    successful_dealerships INTEGER DEFAULT 0,
    failed_dealerships INTEGER DEFAULT 0,
    total_vehicles INTEGER DEFAULT 0,
    real_data_vehicles INTEGER DEFAULT 0,
    fallback_data_vehicles INTEGER DEFAULT 0,
    error_messages JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add new columns to existing tables if they don't exist
DO $$ 
BEGIN
    -- Add last_cao_date to dealership_configs if not exists
    IF NOT EXISTS (
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='dealership_configs' AND column_name='last_cao_date'
    ) THEN
        ALTER TABLE dealership_configs ADD COLUMN last_cao_date DATE;
    END IF;
    
    -- Add last_list_order_date to dealership_configs if not exists
    IF NOT EXISTS (
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='dealership_configs' AND column_name='last_list_order_date'
    ) THEN
        ALTER TABLE dealership_configs ADD COLUMN last_list_order_date DATE;
    END IF;
    
    -- Add last_scrape_timestamp to dealership_configs if not exists
    IF NOT EXISTS (
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='dealership_configs' AND column_name='last_scrape_timestamp'
    ) THEN
        ALTER TABLE dealership_configs ADD COLUMN last_scrape_timestamp TIMESTAMP;
    END IF;
    
    -- Add order_form_id to dealership_configs
    IF NOT EXISTS (
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='dealership_configs' AND column_name='order_form_id'
    ) THEN
        ALTER TABLE dealership_configs ADD COLUMN order_form_id VARCHAR(255);
    END IF;
    
    -- Add vin_log_id to dealership_configs
    IF NOT EXISTS (
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='dealership_configs' AND column_name='vin_log_id'
    ) THEN
        ALTER TABLE dealership_configs ADD COLUMN vin_log_id VARCHAR(255);
    END IF;
    
    -- Add pipedrive_org_id to dealership_configs
    IF NOT EXISTS (
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='dealership_configs' AND column_name='pipedrive_org_id'
    ) THEN
        ALTER TABLE dealership_configs ADD COLUMN pipedrive_org_id VARCHAR(100);
    END IF;
END $$;

-- Insert sample order schedule data based on the CSV
INSERT INTO order_schedule (day_of_week, order_type, dealership_name, template_type, vehicle_types) VALUES
-- Monday CAO
('Monday', 'CAO', 'Porsche STL - New & Used', 'Shortcut', ARRAY['new', 'used']),
('Monday', 'CAO', 'South County DCJR - New & Used', 'Shortcut Pack', ARRAY['new', 'used']),
('Monday', 'CAO', 'Frank Leta Honda', 'Flyout', ARRAY['new', 'used']),
-- Monday As Ordered
('Monday', 'As Ordered', 'Dave Sinclair Lincoln SOCO', 'Shortcut Pack', ARRAY['new', 'used']),
('Monday', 'As Ordered', 'Dave Sinclair Manchester', 'Flyout', ARRAY['new', 'used']),
('Monday', 'As Ordered', 'Dave Sinclair Lincoln St. Peters', 'Shortcut Pack', ARRAY['new', 'used']),
('Monday', 'As Ordered', 'Suntrup Hyundai', 'Shortcut Pack', ARRAY['new', 'used']),
('Monday', 'As Ordered', 'Suntrup Kia', 'Shortcut Pack', ARRAY['new', 'used']),
-- Tuesday CAO
('Tuesday', 'CAO', 'Spirit Lexus', 'Flyout', ARRAY['new', 'used']),
('Tuesday', 'CAO', 'Suntrup Ford Kirkwood', 'Flyout', ARRAY['new', 'used']),
('Tuesday', 'CAO', 'Suntrup Ford Westport', 'Flyout', ARRAY['new', 'used']),
('Tuesday', 'CAO', 'Weber Chevy', 'Custom', ARRAY['new', 'used']),
('Tuesday', 'CAO', 'HW KIA - Used', 'Flyout', ARRAY['used']),
-- Wednesday CAO
('Wednesday', 'CAO', 'Pappas Toyota - New & Loaner', 'Shortcut Pack', ARRAY['new']),
('Wednesday', 'CAO', 'Porsche STL - New & Used', 'Shortcut', ARRAY['new', 'used']),
('Wednesday', 'CAO', 'Serra New & Used', 'Shortcut Pack', ARRAY['new', 'used']),
('Wednesday', 'CAO', 'Auffenberg Used', 'Shortcut Pack', ARRAY['used']),
-- Thursday CAO
('Thursday', 'CAO', 'Spirit Lexus', 'Flyout', ARRAY['new', 'used']),
('Thursday', 'CAO', 'Suntrup Ford Kirkwood', 'Flyout', ARRAY['new', 'used']),
('Thursday', 'CAO', 'Suntrup Ford Westport', 'Flyout', ARRAY['new', 'used'])
ON CONFLICT DO NOTHING;

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO minisforum_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO minisforum_user;