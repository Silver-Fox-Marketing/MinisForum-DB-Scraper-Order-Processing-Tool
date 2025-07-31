-- PostgreSQL performance settings optimized for local single-user setup
-- MinisForum PC: AMD Ryzen 7 6800H, 16GB RAM
-- These settings should be added to postgresql.conf after installation

/*
Add these settings to your postgresql.conf file:

# Memory Settings (16GB total system RAM)
shared_buffers = 4GB                    # 25% of system RAM
effective_cache_size = 8GB              # 50% of system RAM
work_mem = 256MB                        # For complex queries
maintenance_work_mem = 1GB              # For VACUUM, CREATE INDEX, etc.

# Checkpoint Settings (for bulk imports)
checkpoint_segments = 32                # Increase for bulk operations
checkpoint_completion_target = 0.9      # Spread out checkpoint I/O
wal_buffers = 16MB                      # WAL buffer size

# Query Planner
random_page_cost = 1.1                  # SSD optimization (default is 4.0)
effective_io_concurrency = 200          # For SSD

# Logging (optional, for debugging)
log_statement = 'none'                  # Change to 'all' for debugging
log_duration = off                      # Change to 'on' to log query times
log_min_duration_statement = 1000       # Log queries taking > 1 second

# Connection Settings (single user)
max_connections = 20                    # Reduced for single user
*/

-- Create indexes for optimal performance
-- Run this after tables are created and have some data

-- Additional performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_raw_vehicle_composite 
    ON raw_vehicle_data(location, import_date, vin);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_normalized_composite 
    ON normalized_vehicle_data(location, vehicle_condition, last_seen_date);

-- Create partial indexes for common queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_normalized_active_inventory 
    ON normalized_vehicle_data(location, vin) 
    WHERE vehicle_condition IN ('new', 'po', 'cpo', 'onlot') 
    AND last_seen_date >= CURRENT_DATE - INTERVAL '7 days';

-- Statistics for better query planning
ALTER TABLE raw_vehicle_data SET (autovacuum_analyze_scale_factor = 0.02);
ALTER TABLE normalized_vehicle_data SET (autovacuum_analyze_scale_factor = 0.02);

-- Table partitioning setup for raw_vehicle_data (optional, for very large datasets)
-- Uncomment if you expect millions of records
/*
-- Convert to partitioned table by import_date
ALTER TABLE raw_vehicle_data RENAME TO raw_vehicle_data_old;

CREATE TABLE raw_vehicle_data (
    LIKE raw_vehicle_data_old INCLUDING ALL
) PARTITION BY RANGE (import_date);

-- Create monthly partitions
CREATE TABLE raw_vehicle_data_2024_01 PARTITION OF raw_vehicle_data
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
    
-- Continue creating partitions as needed...
*/