-- Simple Order Processing Tables
-- ================================

-- VIN History table for tracking vehicle changes
CREATE TABLE IF NOT EXISTS vin_history (
    id SERIAL PRIMARY KEY,
    dealership_name VARCHAR(255) NOT NULL,
    vin VARCHAR(17) NOT NULL,
    order_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order Schedule table for tracking weekly schedule
CREATE TABLE IF NOT EXISTS order_schedule (
    id SERIAL PRIMARY KEY,
    day_of_week VARCHAR(10) NOT NULL,
    order_type VARCHAR(20) NOT NULL,
    dealership_name VARCHAR(255) NOT NULL,
    template_type VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily scrape logs
CREATE TABLE IF NOT EXISTS daily_scrape_logs (
    id SERIAL PRIMARY KEY,
    scrape_date DATE NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    total_dealerships INTEGER DEFAULT 0,
    successful_dealerships INTEGER DEFAULT 0,
    total_vehicles INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);