-- Order Queue Management Database Schema (Simplified)
-- Silver Fox Marketing - Order Processing Queue System
-- Created: 2025-07-29

-- Order Queue Table - Tracks daily order processing queue
CREATE TABLE IF NOT EXISTS order_queue (
    queue_id SERIAL PRIMARY KEY,
    dealership_name VARCHAR(255) NOT NULL,
    order_type VARCHAR(50) NOT NULL, -- 'CAO' or 'As Ordered'
    template_type VARCHAR(50) NOT NULL, -- 'Shortcut', 'Shortcut Pack', 'Flyout', 'Custom'
    vehicle_types TEXT[], -- Array of vehicle types: ['new', 'used', 'cpo']
    scheduled_date DATE NOT NULL,
    day_of_week VARCHAR(20) NOT NULL,
    priority INTEGER DEFAULT 1, -- 1=high, 2=medium, 3=low
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'failed'
    assigned_to VARCHAR(100), -- Who is processing this order
    notes TEXT,
    
    -- Completion tracking
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    processing_duration INTEGER, -- seconds
    
    -- Order results
    vehicles_processed INTEGER DEFAULT 0,
    qr_codes_generated INTEGER DEFAULT 0,
    csv_output_path VARCHAR(500),
    qr_output_path VARCHAR(500),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(dealership_name, scheduled_date, order_type)
);

-- Template Configuration Table
CREATE TABLE IF NOT EXISTS template_configurations (
    template_id SERIAL PRIMARY KEY,
    template_name VARCHAR(100) NOT NULL UNIQUE,
    template_type VARCHAR(50) NOT NULL, -- 'shortcut', 'shortcut_pack', 'flyout', 'custom'
    csv_headers TEXT[], -- Array of CSV column headers
    field_mappings JSONB, -- Maps database fields to CSV columns
    formatting_rules JSONB, -- Special formatting rules (like NEW prefix)
    qr_column_mapping VARCHAR(100), -- Which column contains QR paths
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily Queue Summary Table
CREATE TABLE IF NOT EXISTS daily_queue_summary (
    summary_id SERIAL PRIMARY KEY,
    queue_date DATE NOT NULL UNIQUE,
    total_orders INTEGER DEFAULT 0,
    completed_orders INTEGER DEFAULT 0,
    pending_orders INTEGER DEFAULT 0,
    failed_orders INTEGER DEFAULT 0,
    total_vehicles INTEGER DEFAULT 0,
    total_qr_codes INTEGER DEFAULT 0,
    completion_percentage DECIMAL(5,2) DEFAULT 0.0,
    average_processing_time INTEGER DEFAULT 0, -- seconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_order_queue_date ON order_queue(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_order_queue_status ON order_queue(status);
CREATE INDEX IF NOT EXISTS idx_order_queue_dealership ON order_queue(dealership_name);
CREATE INDEX IF NOT EXISTS idx_order_queue_day ON order_queue(day_of_week);