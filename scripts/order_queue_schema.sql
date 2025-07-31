-- Order Queue Management Database Schema
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

-- Insert default template configurations
INSERT INTO template_configurations (template_name, template_type, csv_headers, field_mappings, formatting_rules, qr_column_mapping) VALUES
('Shortcut', 'shortcut', 
 ARRAY['QRYEARMODEL', 'QRSTOCK', '@QR2'], 
 '{"QRYEARMODEL": "year_make_model", "QRSTOCK": "stock_vin_status", "@QR2": "qr_path"}',
 '{"combine_year_make_model": true, "combine_stock_vin_status": true}',
 '@QR2'),

('Shortcut Pack', 'shortcut_pack',
 ARRAY['YEARMAKE', 'MODEL', 'TRIM', 'STOCK', 'VIN', '@QR', 'QRYEARMODEL', 'QRSTOCK', '@QR2', 'MISC'],
 '{"YEARMAKE": "year_make", "MODEL": "model", "TRIM": "trim", "STOCK": "stock_description", "VIN": "vin_status", "@QR": "qr_path", "QRYEARMODEL": "year_make_model", "QRSTOCK": "stock_vin_status", "@QR2": "qr_path", "MISC": "combined_info"}',
 '{"add_new_prefix": true, "combine_fields": true}',
 '@QR2'),

('Flyout', 'flyout',
 ARRAY['Vin', 'Stock', 'Type', 'Year', 'Make', 'Model', 'Trim', 'Ext Color', 'Status', 'Price', 'Body Style', 'Fuel Type', 'MSRP', 'Date In Stock', 'Street Address', 'Locality', 'Postal Code', 'Region', 'Country', 'Location', 'Vehicle URL', 'QR_Code_Path'],
 '{"Vin": "vin", "Stock": "stock", "Type": "type", "Year": "year", "Make": "make", "Model": "model", "Trim": "trim", "Ext Color": "ext_color", "Status": "status", "Price": "price", "Body Style": "body_style", "Fuel Type": "fuel_type", "MSRP": "msrp", "Date In Stock": "date_in_stock", "Street Address": "street_address", "Locality": "locality", "Postal Code": "postal_code", "Region": "region", "Country": "country", "Location": "location", "Vehicle URL": "vehicle_url", "QR_Code_Path": "qr_path"}',
 '{}',
 'QR_Code_Path')
ON CONFLICT (template_name) DO NOTHING;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_order_queue_date ON order_queue(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_order_queue_status ON order_queue(status);
CREATE INDEX IF NOT EXISTS idx_order_queue_dealership ON order_queue(dealership_name);
CREATE INDEX IF NOT EXISTS idx_order_queue_day ON order_queue(day_of_week);

-- Create trigger to update daily summary
CREATE OR REPLACE FUNCTION update_daily_queue_summary()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO daily_queue_summary (
        queue_date, 
        total_orders, 
        completed_orders, 
        pending_orders, 
        failed_orders,
        total_vehicles,
        total_qr_codes,
        completion_percentage,
        average_processing_time,
        updated_at
    )
    SELECT 
        scheduled_date,
        COUNT(*) as total_orders,
        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders,
        COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_orders,
        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_orders,
        COALESCE(SUM(vehicles_processed), 0) as total_vehicles,
        COALESCE(SUM(qr_codes_generated), 0) as total_qr_codes,
        CASE 
            WHEN COUNT(*) > 0 THEN 
                ROUND((COUNT(CASE WHEN status = 'completed' THEN 1 END)::DECIMAL / COUNT(*)) * 100, 2)
            ELSE 0 
        END as completion_percentage,
        COALESCE(AVG(processing_duration), 0)::INTEGER as average_processing_time,
        CURRENT_TIMESTAMP
    FROM order_queue 
    WHERE scheduled_date = COALESCE(NEW.scheduled_date, OLD.scheduled_date)
    GROUP BY scheduled_date
    ON CONFLICT (queue_date) 
    DO UPDATE SET
        total_orders = EXCLUDED.total_orders,
        completed_orders = EXCLUDED.completed_orders,
        pending_orders = EXCLUDED.pending_orders,
        failed_orders = EXCLUDED.failed_orders,
        total_vehicles = EXCLUDED.total_vehicles,
        total_qr_codes = EXCLUDED.total_qr_codes,
        completion_percentage = EXCLUDED.completion_percentage,
        average_processing_time = EXCLUDED.average_processing_time,
        updated_at = EXCLUDED.updated_at;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_daily_summary
    AFTER INSERT OR UPDATE OR DELETE ON order_queue
    FOR EACH ROW
    EXECUTE FUNCTION update_daily_queue_summary();

-- Create function to populate weekly schedule
CREATE OR REPLACE FUNCTION populate_weekly_schedule(start_date DATE DEFAULT CURRENT_DATE)
RETURNS INTEGER AS $$
DECLARE
    schedule_count INTEGER := 0;
    current_date DATE;
    day_name TEXT;
BEGIN
    -- Clear existing pending orders for the week
    DELETE FROM order_queue 
    WHERE scheduled_date BETWEEN start_date AND start_date + INTERVAL '6 days'
    AND status = 'pending';
    
    -- Loop through 7 days starting from start_date
    FOR i IN 0..6 LOOP
        current_date := start_date + i;
        day_name := TO_CHAR(current_date, 'Day');
        day_name := TRIM(day_name);
        
        -- Monday CAO orders
        IF day_name = 'Monday' THEN
            INSERT INTO order_queue (dealership_name, order_type, template_type, vehicle_types, scheduled_date, day_of_week) VALUES
            ('Porsche STL - New & Used', 'CAO', 'Shortcut', ARRAY['new', 'used'], current_date, day_name),
            ('South County DCJR - New & Used', 'CAO', 'Shortcut Pack', ARRAY['new', 'used'], current_date, day_name),
            ('Frank Leta Honda', 'CAO', 'Flyout', ARRAY['new', 'used'], current_date, day_name);
            schedule_count := schedule_count + 3;
        END IF;
        
        -- Tuesday CAO orders
        IF day_name = 'Tuesday' THEN
            INSERT INTO order_queue (dealership_name, order_type, template_type, vehicle_types, scheduled_date, day_of_week) VALUES
            ('Spirit Lexus', 'CAO', 'Flyout', ARRAY['new', 'used'], current_date, day_name),
            ('Suntrup Ford Kirkwood', 'CAO', 'Flyout', ARRAY['new', 'used'], current_date, day_name),
            ('Suntrup Ford Westport', 'CAO', 'Flyout', ARRAY['new', 'used'], current_date, day_name),
            ('Weber Chevy', 'CAO', 'Custom', ARRAY['new', 'used'], current_date, day_name),
            ('HW KIA - Used', 'CAO', 'Flyout', ARRAY['used'], current_date, day_name),
            ('Volvo Cars West County - New', 'CAO', 'Shortcut', ARRAY['new'], current_date, day_name),
            ('Bommarito West County - Used', 'CAO', 'Flyout', ARRAY['used'], current_date, day_name),
            ('Glendale CDJR - Used', 'CAO', 'Shortcut Pack', ARRAY['used'], current_date, day_name),
            ('Honda of Frontenac - Used', 'CAO', 'Shortcut Pack', ARRAY['used'], current_date, day_name);
            schedule_count := schedule_count + 9;
        END IF;
        
        -- Wednesday CAO orders
        IF day_name = 'Wednesday' THEN
            INSERT INTO order_queue (dealership_name, order_type, template_type, vehicle_types, scheduled_date, day_of_week) VALUES
            ('Pappas Toyota - New & Loaner', 'CAO', 'Shortcut Pack', ARRAY['new'], current_date, day_name),
            ('Porsche STL - New & Used', 'CAO', 'Shortcut', ARRAY['new', 'used'], current_date, day_name),
            ('Serra New & Used', 'CAO', 'Shortcut Pack', ARRAY['new', 'used'], current_date, day_name),
            ('Auffenberg Used', 'CAO', 'Shortcut Pack', ARRAY['used'], current_date, day_name),
            ('Frank Leta Honda', 'CAO', 'Flyout', ARRAY['new', 'used'], current_date, day_name),
            ('Suntrup Buick GMC', 'CAO', 'Shortcut', ARRAY['new', 'used'], current_date, day_name);
            schedule_count := schedule_count + 6;
        END IF;
        
        -- Thursday CAO orders
        IF day_name = 'Thursday' THEN
            INSERT INTO order_queue (dealership_name, order_type, template_type, vehicle_types, scheduled_date, day_of_week) VALUES
            ('Spirit Lexus', 'CAO', 'Flyout', ARRAY['new', 'used'], current_date, day_name),
            ('Suntrup Ford Kirkwood', 'CAO', 'Flyout', ARRAY['new', 'used'], current_date, day_name),
            ('Suntrup Ford Westport', 'CAO', 'Flyout', ARRAY['new', 'used'], current_date, day_name),
            ('Weber Chevy', 'CAO', 'Custom', ARRAY['new', 'used'], current_date, day_name),
            ('HW KIA - Used', 'CAO', 'Flyout', ARRAY['used'], current_date, day_name),
            ('Volvo Cars West County - New', 'CAO', 'Shortcut', ARRAY['new'], current_date, day_name),
            ('Bommarito West County - Used', 'CAO', 'Flyout', ARRAY['used'], current_date, day_name),
            ('Glendale CDJR - Used', 'CAO', 'Shortcut Pack', ARRAY['used'], current_date, day_name),
            ('Honda of Frontenac - New & Used', 'CAO', 'Shortcut Pack', ARRAY['new', 'used'], current_date, day_name),
            ('South County DCJR - New & Used', 'CAO', 'Shortcut Pack', ARRAY['new', 'used'], current_date, day_name),
            ('Thoroughbred - Used', 'CAO', 'Shortcut Pack', ARRAY['used'], current_date, day_name);
            schedule_count := schedule_count + 11;
        END IF;
    END LOOP;
    
    RETURN schedule_count;
END;
$$ LANGUAGE plpgsql;