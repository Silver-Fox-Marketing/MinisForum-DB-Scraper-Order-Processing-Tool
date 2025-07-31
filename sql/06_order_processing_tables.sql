-- Order Processing Integration Tables
-- Extends the database schema to support order processing, QR tracking, and export management

-- 1. Order Processing Jobs Table
-- Tracks all order processing jobs with their status and results
CREATE TABLE IF NOT EXISTS order_processing_jobs (
    id SERIAL PRIMARY KEY,
    dealership_name VARCHAR(100) NOT NULL,
    job_type VARCHAR(50) NOT NULL DEFAULT 'standard',
    vehicle_count INTEGER DEFAULT 0,
    final_vehicle_count INTEGER,
    export_file TEXT,
    status VARCHAR(20) DEFAULT 'created',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    notes TEXT,
    created_by VARCHAR(100) DEFAULT 'system'
);

-- Create indexes for order_processing_jobs
CREATE INDEX IF NOT EXISTS idx_order_jobs_dealership ON order_processing_jobs(dealership_name);
CREATE INDEX IF NOT EXISTS idx_order_jobs_status ON order_processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_order_jobs_created ON order_processing_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_order_jobs_type ON order_processing_jobs(job_type);

-- 2. QR File Tracking Table
-- Tracks QR code files for each vehicle and their status
CREATE TABLE IF NOT EXISTS qr_file_tracking (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    dealership_name VARCHAR(100) NOT NULL,
    qr_file_path TEXT NOT NULL,
    file_exists BOOLEAN DEFAULT false,
    file_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    job_id INTEGER REFERENCES order_processing_jobs(id) ON DELETE SET NULL,
    
    -- Ensure unique combination of VIN and dealership
    UNIQUE(vin, dealership_name)
);

-- Create indexes for qr_file_tracking
CREATE INDEX IF NOT EXISTS idx_qr_tracking_vin ON qr_file_tracking(vin);
CREATE INDEX IF NOT EXISTS idx_qr_tracking_dealership ON qr_file_tracking(dealership_name);
CREATE INDEX IF NOT EXISTS idx_qr_tracking_exists ON qr_file_tracking(file_exists);
CREATE INDEX IF NOT EXISTS idx_qr_tracking_verified ON qr_file_tracking(last_verified);
CREATE INDEX IF NOT EXISTS idx_qr_tracking_job ON qr_file_tracking(job_id);

-- 3. Export History Table
-- Tracks all data exports for auditing and management
CREATE TABLE IF NOT EXISTS export_history (
    id SERIAL PRIMARY KEY,
    export_type VARCHAR(50) NOT NULL,
    dealership_name VARCHAR(100),
    file_path TEXT NOT NULL,
    record_count INTEGER DEFAULT 0,
    file_size INTEGER,
    export_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    job_id INTEGER REFERENCES order_processing_jobs(id) ON DELETE SET NULL,
    exported_by VARCHAR(100) DEFAULT 'system',
    notes TEXT
);

-- Create indexes for export_history
CREATE INDEX IF NOT EXISTS idx_export_history_type ON export_history(export_type);
CREATE INDEX IF NOT EXISTS idx_export_history_dealership ON export_history(dealership_name);
CREATE INDEX IF NOT EXISTS idx_export_history_date ON export_history(export_date);
CREATE INDEX IF NOT EXISTS idx_export_history_job ON export_history(job_id);

-- 4. Order Processing Configuration Table
-- Stores configuration for different types of order processing jobs
CREATE TABLE IF NOT EXISTS order_processing_config (
    id SERIAL PRIMARY KEY,
    config_name VARCHAR(100) UNIQUE NOT NULL,
    job_type VARCHAR(50) NOT NULL,
    template_settings JSONB DEFAULT '{}',
    output_format VARCHAR(50) DEFAULT 'csv',
    qr_settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for order_processing_config
CREATE INDEX IF NOT EXISTS idx_order_config_name ON order_processing_config(config_name);
CREATE INDEX IF NOT EXISTS idx_order_config_type ON order_processing_config(job_type);
CREATE INDEX IF NOT EXISTS idx_order_config_active ON order_processing_config(is_active);

-- 5. Create useful views for order processing

-- View: Current Job Status Summary
CREATE OR REPLACE VIEW current_job_status AS
SELECT 
    opj.id,
    opj.dealership_name,
    opj.job_type,
    opj.status,
    opj.vehicle_count,
    opj.final_vehicle_count,
    opj.created_at,
    opj.completed_at,
    CASE 
        WHEN opj.completed_at IS NOT NULL THEN 
            EXTRACT(EPOCH FROM (opj.completed_at - opj.created_at))/60
        ELSE 
            EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - opj.created_at))/60
    END as duration_minutes,
    COUNT(qft.id) as qr_files_tracked,
    SUM(CASE WHEN qft.file_exists THEN 1 ELSE 0 END) as qr_files_exist
FROM order_processing_jobs opj
LEFT JOIN qr_file_tracking qft ON opj.id = qft.job_id
GROUP BY opj.id, opj.dealership_name, opj.job_type, opj.status, 
         opj.vehicle_count, opj.final_vehicle_count, opj.created_at, opj.completed_at
ORDER BY opj.created_at DESC;

-- View: Dealership QR Status Summary
CREATE OR REPLACE VIEW dealership_qr_status AS
SELECT 
    dc.name as dealership_name,
    dc.qr_output_path,
    COUNT(nvd.id) as total_vehicles,
    COUNT(qft.id) as tracked_qr_files,
    SUM(CASE WHEN qft.file_exists THEN 1 ELSE 0 END) as existing_qr_files,
    SUM(CASE WHEN qft.file_exists THEN 0 ELSE 1 END) as missing_qr_files,
    ROUND(
        (SUM(CASE WHEN qft.file_exists THEN 1 ELSE 0 END)::DECIMAL / 
         NULLIF(COUNT(nvd.id), 0)) * 100, 2
    ) as qr_completion_percentage,
    MAX(qft.last_verified) as last_qr_verification
FROM dealership_configs dc
LEFT JOIN normalized_vehicle_data nvd ON dc.name = nvd.location 
    AND nvd.last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
LEFT JOIN qr_file_tracking qft ON nvd.vin = qft.vin 
    AND nvd.location = qft.dealership_name
WHERE dc.is_active = true
GROUP BY dc.name, dc.qr_output_path
ORDER BY qr_completion_percentage DESC;

-- View: Recent Export Activity
CREATE OR REPLACE VIEW recent_export_activity AS
SELECT 
    eh.export_type,
    eh.dealership_name,
    eh.record_count,
    eh.export_date,
    eh.created_at,
    opj.job_type,
    opj.status as job_status,
    eh.exported_by
FROM export_history eh
LEFT JOIN order_processing_jobs opj ON eh.job_id = opj.id
WHERE eh.export_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY eh.created_at DESC;

-- 6. Insert default order processing configurations
INSERT INTO order_processing_config (config_name, job_type, template_settings, qr_settings) VALUES
('Standard Order Processing', 'standard', 
    '{"fields": ["vin", "stock", "year", "make", "model", "trim", "price", "condition"], "sort_by": ["make", "model", "year"]}',
    '{"format": "png", "size": "256x256", "error_correction": "M"}'),
    
('Premium Order Processing', 'premium',
    '{"fields": ["vin", "stock", "year", "make", "model", "trim", "price", "msrp", "condition", "last_seen_date"], "sort_by": ["price", "year"], "min_price": 25000}',
    '{"format": "png", "size": "512x512", "error_correction": "H"}'),
    
('Quick Export', 'quick',
    '{"fields": ["vin", "stock", "make", "model", "price"], "sort_by": ["make", "model"]}',
    '{"format": "png", "size": "128x128", "error_correction": "L"}'),
    
('Custom Order Processing', 'custom',
    '{"fields": ["vin", "stock", "year", "make", "model", "trim", "price", "msrp", "condition", "exterior_color", "fuel_type"], "sort_by": ["dealership", "make", "model"]}',
    '{"format": "png", "size": "256x256", "error_correction": "M"}')

ON CONFLICT (config_name) DO UPDATE SET
    template_settings = EXCLUDED.template_settings,
    qr_settings = EXCLUDED.qr_settings,
    updated_at = CURRENT_TIMESTAMP;

-- 7. Create trigger for updating order_processing_config.updated_at
CREATE OR REPLACE FUNCTION update_order_config_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_order_config_updated_at_trigger
    BEFORE UPDATE ON order_processing_config
    FOR EACH ROW
    EXECUTE FUNCTION update_order_config_updated_at();

-- 8. Create function to automatically track QR files when vehicles are imported
CREATE OR REPLACE FUNCTION auto_track_qr_files()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert QR tracking record for new vehicle
    INSERT INTO qr_file_tracking (vin, dealership_name, qr_file_path, file_exists)
    SELECT 
        NEW.vin,
        NEW.location,
        dc.qr_output_path || NEW.vin || '.png',
        false  -- Assume doesn't exist until verified
    FROM dealership_configs dc
    WHERE dc.name = NEW.location
    ON CONFLICT (vin, dealership_name) DO UPDATE SET
        qr_file_path = EXCLUDED.qr_file_path,
        last_verified = CURRENT_TIMESTAMP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-track QR files for new vehicles
CREATE TRIGGER auto_track_qr_files_trigger
    AFTER INSERT OR UPDATE ON normalized_vehicle_data
    FOR EACH ROW
    EXECUTE FUNCTION auto_track_qr_files();

-- Grant permissions
GRANT ALL ON order_processing_jobs TO postgres;
GRANT ALL ON qr_file_tracking TO postgres;
GRANT ALL ON export_history TO postgres;
GRANT ALL ON order_processing_config TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Create summary function for order processing status
CREATE OR REPLACE FUNCTION get_order_processing_summary()
RETURNS TABLE (
    metric_name TEXT,
    metric_value TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 'Active Dealerships'::TEXT, COUNT(*)::TEXT FROM dealership_configs WHERE is_active = true
    UNION ALL
    SELECT 'Total Vehicles (Last 7 Days)'::TEXT, COUNT(*)::TEXT FROM normalized_vehicle_data 
        WHERE last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
    UNION ALL
    SELECT 'Order Processing Jobs (Last 30 Days)'::TEXT, COUNT(*)::TEXT FROM order_processing_jobs 
        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
    UNION ALL
    SELECT 'QR Files Tracked'::TEXT, COUNT(*)::TEXT FROM qr_file_tracking
    UNION ALL
    SELECT 'QR Files Existing'::TEXT, COUNT(*)::TEXT FROM qr_file_tracking WHERE file_exists = true
    UNION ALL
    SELECT 'Recent Exports (Last 7 Days)'::TEXT, COUNT(*)::TEXT FROM export_history 
        WHERE export_date >= CURRENT_DATE - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;