-- Fix VIN History Table Schema Conflicts
-- This script resolves the schema mismatch between different table definitions

-- Step 1: Check current table structure and fix column name issue
DO $$ 
DECLARE
    has_scan_date BOOLEAN;
    has_order_date BOOLEAN;
    has_unique_constraint BOOLEAN;
BEGIN
    -- Check if scan_date column exists
    SELECT EXISTS (
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='vin_history' AND column_name='scan_date'
    ) INTO has_scan_date;
    
    -- Check if order_date column exists
    SELECT EXISTS (
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='vin_history' AND column_name='order_date'
    ) INTO has_order_date;
    
    -- Check if unique constraint exists
    SELECT EXISTS (
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_name='vin_history' 
        AND constraint_type='UNIQUE'
    ) INTO has_unique_constraint;
    
    RAISE NOTICE 'VIN History Schema Status:';
    RAISE NOTICE '  has_scan_date: %', has_scan_date;
    RAISE NOTICE '  has_order_date: %', has_order_date;
    RAISE NOTICE '  has_unique_constraint: %', has_unique_constraint;
    
    -- Fix 1: If we have scan_date but not order_date, rename the column
    IF has_scan_date AND NOT has_order_date THEN
        RAISE NOTICE 'Renaming scan_date to order_date...';
        ALTER TABLE vin_history RENAME COLUMN scan_date TO order_date;
        
        -- Update the index name as well
        DROP INDEX IF EXISTS idx_history_scan_date;
        CREATE INDEX IF NOT EXISTS idx_history_order_date ON vin_history(order_date);
        
        RAISE NOTICE 'Successfully renamed scan_date to order_date';
    END IF;
    
    -- Fix 2: Add missing columns if needed
    IF NOT has_order_date AND NOT has_scan_date THEN
        RAISE NOTICE 'Adding missing order_date column...';
        ALTER TABLE vin_history ADD COLUMN order_date DATE DEFAULT CURRENT_DATE;
        CREATE INDEX IF NOT EXISTS idx_history_order_date ON vin_history(order_date);
        RAISE NOTICE 'Added order_date column';
    END IF;
    
    -- Fix 3: Add missing unique constraint
    IF NOT has_unique_constraint THEN
        RAISE NOTICE 'Adding unique constraint...';
        -- First remove any exact duplicates
        DELETE FROM vin_history v1 
        WHERE v1.id NOT IN (
            SELECT MIN(v2.id) 
            FROM vin_history v2 
            WHERE v2.dealership_name = v1.dealership_name 
            AND v2.vin = v1.vin 
            AND v2.order_date = v1.order_date
        );
        
        -- Add the unique constraint
        ALTER TABLE vin_history 
        ADD CONSTRAINT vin_history_unique 
        UNIQUE(dealership_name, vin, order_date);
        
        RAISE NOTICE 'Added unique constraint vin_history_unique';
    END IF;
    
    -- Fix 4: Add missing vehicle_type column for enhanced logic
    IF NOT EXISTS (
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='vin_history' AND column_name='vehicle_type'
    ) THEN
        RAISE NOTICE 'Adding vehicle_type column for enhanced VIN logic...';
        ALTER TABLE vin_history ADD COLUMN vehicle_type VARCHAR(50);
        CREATE INDEX IF NOT EXISTS idx_history_vehicle_type ON vin_history(vehicle_type);
        RAISE NOTICE 'Added vehicle_type column';
    END IF;
    
    -- Fix 5: Add missing source column for tracking order types
    IF NOT EXISTS (
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='vin_history' AND column_name='source'
    ) THEN
        RAISE NOTICE 'Adding source column for order type tracking...';
        ALTER TABLE vin_history ADD COLUMN source VARCHAR(50) DEFAULT 'LEGACY';
        CREATE INDEX IF NOT EXISTS idx_history_source ON vin_history(source);
        RAISE NOTICE 'Added source column';
    END IF;
    
    RAISE NOTICE 'VIN History schema fixes completed successfully';
    
END $$;

-- Step 2: Update any existing records that might have NULL order_date
UPDATE vin_history 
SET order_date = CURRENT_DATE 
WHERE order_date IS NULL;

-- Step 3: Ensure proper indexes exist
CREATE INDEX IF NOT EXISTS idx_vin_history_dealership_date ON vin_history(dealership_name, order_date DESC);
CREATE INDEX IF NOT EXISTS idx_vin_history_vin ON vin_history(vin);
CREATE INDEX IF NOT EXISTS idx_vin_history_enhanced_lookup ON vin_history(vin, dealership_name, order_date DESC);

-- Step 4: Grant permissions
GRANT ALL ON vin_history TO postgres;
GRANT ALL ON vin_history TO minisforum_user;

-- Step 5: Display final table structure
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'vin_history' 
ORDER BY ordinal_position;