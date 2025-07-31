-- Fix Database Schema Issues
-- ===========================
-- Fix missing columns identified in stress test

-- Fix vin_history table - add order_date column if missing
DO $$ 
BEGIN
    -- Check if order_date column exists in vin_history
    IF NOT EXISTS (
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='vin_history' AND column_name='order_date'
    ) THEN
        -- Add order_date column
        ALTER TABLE vin_history ADD COLUMN order_date DATE DEFAULT CURRENT_DATE;
        RAISE NOTICE 'Added order_date column to vin_history table';
    ELSE
        RAISE NOTICE 'order_date column already exists in vin_history table';
    END IF;
    
    -- Check if qr_count column exists in order_processing_jobs
    IF NOT EXISTS (
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='order_processing_jobs' AND column_name='qr_count'
    ) THEN
        -- Add qr_count column
        ALTER TABLE order_processing_jobs ADD COLUMN qr_count INTEGER DEFAULT 0;
        RAISE NOTICE 'Added qr_count column to order_processing_jobs table';
    ELSE
        RAISE NOTICE 'qr_count column already exists in order_processing_jobs table';
    END IF;
    
    -- Update existing vin_history records to have order_date
    UPDATE vin_history 
    SET order_date = created_at::date 
    WHERE order_date IS NULL;
    RAISE NOTICE 'Updated existing vin_history records with order_date';
    
    -- Update existing order_processing_jobs records to have qr_count
    UPDATE order_processing_jobs 
    SET qr_count = 0 
    WHERE qr_count IS NULL;
    RAISE NOTICE 'Updated existing order_processing_jobs records with qr_count';
    
END $$;