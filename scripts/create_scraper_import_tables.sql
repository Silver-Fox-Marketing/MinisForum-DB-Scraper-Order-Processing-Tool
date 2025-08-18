-- Create tables for tracking scraper imports and archiving data
-- This schema supports the new scraper import management system

-- Table to track all scraper import sessions
CREATE TABLE IF NOT EXISTS scraper_imports (
    import_id SERIAL PRIMARY KEY,
    import_date DATE NOT NULL,
    import_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_vehicles INTEGER NOT NULL DEFAULT 0,
    dealerships_count INTEGER NOT NULL DEFAULT 0,
    dealerships_list TEXT[], -- Array of dealership names included
    import_source VARCHAR(100), -- 'manual_csv', 'automated_scrape', 'api', etc.
    file_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'archived', 'failed'
    archived_at TIMESTAMP,
    notes TEXT,
    created_by VARCHAR(100),
    UNIQUE(import_date, status) -- Only one active import per date
);

-- Create index for faster queries
CREATE INDEX idx_scraper_imports_date ON scraper_imports(import_date DESC);
CREATE INDEX idx_scraper_imports_status ON scraper_imports(status);

-- Modified raw_vehicle_data table to include import_id reference
ALTER TABLE raw_vehicle_data 
ADD COLUMN IF NOT EXISTS import_id INTEGER REFERENCES scraper_imports(import_id),
ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE;

-- Create indexes for the new columns
CREATE INDEX IF NOT EXISTS idx_raw_vehicle_import_id ON raw_vehicle_data(import_id);
CREATE INDEX IF NOT EXISTS idx_raw_vehicle_archived ON raw_vehicle_data(is_archived);

-- Function to archive previous imports when new data arrives
CREATE OR REPLACE FUNCTION archive_previous_imports()
RETURNS VOID AS $$
BEGIN
    -- Archive all currently active imports
    UPDATE scraper_imports 
    SET status = 'archived', 
        archived_at = CURRENT_TIMESTAMP
    WHERE status = 'active';
    
    -- Mark all non-archived vehicle data as archived
    UPDATE raw_vehicle_data 
    SET is_archived = TRUE 
    WHERE is_archived = FALSE;
END;
$$ LANGUAGE plpgsql;

-- View to get only current active vehicle data
CREATE OR REPLACE VIEW current_vehicle_inventory AS
SELECT * FROM raw_vehicle_data 
WHERE is_archived = FALSE;

-- View to get summary of all imports
CREATE OR REPLACE VIEW scraper_import_summary AS
SELECT 
    si.import_id,
    si.import_date,
    si.import_timestamp,
    si.total_vehicles,
    si.dealerships_count,
    si.import_source,
    si.status,
    si.file_name,
    COUNT(DISTINCT rvd.location) as actual_dealerships,
    COUNT(rvd.vin) as actual_vehicles
FROM scraper_imports si
LEFT JOIN raw_vehicle_data rvd ON si.import_id = rvd.import_id
GROUP BY si.import_id
ORDER BY si.import_timestamp DESC;

-- Create a unified VIN log view for all dealerships
CREATE OR REPLACE VIEW all_dealership_vin_logs AS
SELECT 
    table_name,
    REPLACE(REPLACE(table_name, '_vin_log', ''), '_', ' ') as dealership_name,
    (SELECT COUNT(*) FROM information_schema.columns 
     WHERE table_name = t.table_name AND table_schema = 'public') as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
AND table_name LIKE '%_vin_log'
ORDER BY table_name;