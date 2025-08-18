-- Enhanced VIN Log Schema for Order Tracking
-- Adds order_number and order_date columns to all dealership VIN log tables

-- First, let's get all dealership VIN log tables
DO $$
DECLARE
    table_record RECORD;
    sql_statement TEXT;
BEGIN
    -- Loop through all VIN log tables
    FOR table_record IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%_vin_log'
    LOOP
        -- Add order_number column if it doesn't exist
        sql_statement := 'ALTER TABLE ' || table_record.table_name || ' ADD COLUMN IF NOT EXISTS order_number VARCHAR(50)';
        EXECUTE sql_statement;
        RAISE NOTICE 'Added order_number column to %', table_record.table_name;
        
        -- Add order_date column if it doesn't exist (separate from processed_date)
        sql_statement := 'ALTER TABLE ' || table_record.table_name || ' ADD COLUMN IF NOT EXISTS order_date DATE';
        EXECUTE sql_statement;
        RAISE NOTICE 'Added order_date column to %', table_record.table_name;
        
        -- Add index for faster order_number lookups
        sql_statement := 'CREATE INDEX IF NOT EXISTS idx_' || table_record.table_name || '_order_number ON ' || table_record.table_name || '(order_number)';
        EXECUTE sql_statement;
        RAISE NOTICE 'Added order_number index to %', table_record.table_name;
        
        -- Add index for order_date
        sql_statement := 'CREATE INDEX IF NOT EXISTS idx_' || table_record.table_name || '_order_date ON ' || table_record.table_name || '(order_date)';
        EXECUTE sql_statement;
        RAISE NOTICE 'Added order_date index to %', table_record.table_name;
    END LOOP;
END $$;

-- Create a view to show VIN log summary with order tracking
CREATE OR REPLACE VIEW vin_log_summary AS
WITH vin_log_stats AS (
    -- BMW of West St. Louis
    SELECT 
        'BMW of West St. Louis' as dealership_name,
        'bmw_of_west_st_louis_vin_log' as table_name,
        COUNT(*) as total_vins,
        COUNT(DISTINCT order_number) as total_orders,
        MIN(order_date) as first_order_date,
        MAX(order_date) as last_order_date,
        MIN(processed_date) as first_processed_date,
        MAX(processed_date) as last_processed_date
    FROM bmw_of_west_st_louis_vin_log
    WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'bmw_of_west_st_louis_vin_log')
    
    UNION ALL
    
    -- Bommarito West County
    SELECT 
        'Bommarito West County' as dealership_name,
        'bommarito_west_county_vin_log' as table_name,
        COUNT(*) as total_vins,
        COUNT(DISTINCT order_number) as total_orders,
        MIN(order_date) as first_order_date,
        MAX(order_date) as last_order_date,
        MIN(processed_date) as first_processed_date,
        MAX(processed_date) as last_processed_date
    FROM bommarito_west_county_vin_log
    WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'bommarito_west_county_vin_log')
    
    -- Add more dealership unions as needed
)
SELECT * FROM vin_log_stats WHERE total_vins > 0
ORDER BY dealership_name;

-- Create a standardized order number generation function
CREATE OR REPLACE FUNCTION generate_order_number(dealership_slug TEXT, order_type TEXT DEFAULT 'CAO')
RETURNS TEXT AS $$
DECLARE
    order_date TEXT;
    sequence_num INTEGER;
    order_number TEXT;
BEGIN
    -- Get current date in YYYYMMDD format
    order_date := to_char(CURRENT_DATE, 'YYYYMMDD');
    
    -- Get next sequence number for this dealership and date
    -- This ensures unique order numbers per dealership per day
    SELECT COALESCE(MAX(
        CASE 
            WHEN order_number ~ (dealership_slug || '_' || order_type || '_' || order_date || '_[0-9]+')
            THEN CAST(split_part(order_number, '_', -1) AS INTEGER)
            ELSE 0
        END
    ), 0) + 1
    INTO sequence_num
    FROM information_schema.tables t
    WHERE t.table_name = dealership_slug || '_vin_log';
    
    -- Format: DEALERSHIP_ORDERTYPE_YYYYMMDD_001
    order_number := UPPER(dealership_slug) || '_' || UPPER(order_type) || '_' || order_date || '_' || LPAD(sequence_num::TEXT, 3, '0');
    
    RETURN order_number;
END;
$$ LANGUAGE plpgsql;

-- Example: SELECT generate_order_number('bmw_of_west_st_louis', 'CAO');
-- Returns: BMW_OF_WEST_ST_LOUIS_CAO_20250818_001

COMMENT ON FUNCTION generate_order_number(TEXT, TEXT) IS 'Generates unique order numbers for VIN log entries in format: DEALERSHIP_TYPE_DATE_SEQUENCE';

-- Create example order numbers for any existing VIN log entries that don't have them
-- This is optional and can be run to backfill historical data with generated order numbers
/*
DO $$
DECLARE
    table_record RECORD;
    sql_statement TEXT;
BEGIN
    FOR table_record IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%_vin_log'
    LOOP
        -- Update existing records without order numbers
        sql_statement := 
            'UPDATE ' || table_record.table_name || ' 
             SET order_number = ''HISTORICAL_'' || UPPER(REPLACE(''' || table_record.table_name || ''', ''_vin_log'', '''')) || ''_'' || to_char(processed_date, ''YYYYMMDD'') || ''_001'',
                 order_date = processed_date
             WHERE order_number IS NULL';
        
        EXECUTE sql_statement;
        
        GET DIAGNOSTICS sql_statement = ROW_COUNT;
        RAISE NOTICE 'Updated % records in %', sql_statement, table_record.table_name;
    END LOOP;
END $$;
*/