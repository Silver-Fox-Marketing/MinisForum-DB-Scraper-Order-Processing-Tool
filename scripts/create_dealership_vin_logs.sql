-- ==========================================
-- DEALERSHIP-SPECIFIC VIN LOGS v2.1
-- Silver Fox Order Processing System
-- Created: 2025-08-08
-- ==========================================

-- This script creates individual VIN log tables for each dealership
-- This replaces the unified vin_history table for better performance
-- and isolated dealership-specific VIN tracking

BEGIN;

-- Drop the old unified vin_history table (backup first if needed)
-- DROP TABLE IF EXISTS vin_history CASCADE;

-- Create dealership-specific VIN log tables
-- Standard structure for all dealership VIN log tables:
-- - id: Primary key
-- - vin: 17-character VIN 
-- - vehicle_type: new/used/certified
-- - order_date: Date when order was processed
-- - created_at: Timestamp when record was created
-- - UNIQUE constraint on (vin, order_date) to prevent duplicates

-- Audi Ranch Mirage
CREATE TABLE IF NOT EXISTS vin_log_audi_ranch_mirage (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Auffenberg Hyundai
CREATE TABLE IF NOT EXISTS vin_log_auffenberg_hyundai (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- BMW of West St. Louis
CREATE TABLE IF NOT EXISTS vin_log_bmw_of_west_st_louis (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Bommarito Cadillac
CREATE TABLE IF NOT EXISTS vin_log_bommarito_cadillac (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Bommarito West County
CREATE TABLE IF NOT EXISTS vin_log_bommarito_west_county (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Columbia BMW
CREATE TABLE IF NOT EXISTS vin_log_columbia_bmw (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Columbia Honda
CREATE TABLE IF NOT EXISTS vin_log_columbia_honda (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Dave Sinclair Lincoln
CREATE TABLE IF NOT EXISTS vin_log_dave_sinclair_lincoln (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Dave Sinclair Lincoln South
CREATE TABLE IF NOT EXISTS vin_log_dave_sinclair_lincoln_south (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Dave Sinclair Lincoln St. Peters
CREATE TABLE IF NOT EXISTS vin_log_dave_sinclair_lincoln_st_peters (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Frank Leta Honda
CREATE TABLE IF NOT EXISTS vin_log_frank_leta_honda (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Glendale Chrysler Jeep
CREATE TABLE IF NOT EXISTS vin_log_glendale_chrysler_jeep (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- H&W Kia
CREATE TABLE IF NOT EXISTS vin_log_handw_kia (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Honda of Frontenac
CREATE TABLE IF NOT EXISTS vin_log_honda_of_frontenac (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Indigo Auto Group
CREATE TABLE IF NOT EXISTS vin_log_indigo_auto_group (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Jaguar Ranch Mirage
CREATE TABLE IF NOT EXISTS vin_log_jaguar_ranch_mirage (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Joe Machens CDJR
CREATE TABLE IF NOT EXISTS vin_log_joe_machens_cdjr (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Joe Machens Hyundai
CREATE TABLE IF NOT EXISTS vin_log_joe_machens_hyundai (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Joe Machens Nissan
CREATE TABLE IF NOT EXISTS vin_log_joe_machens_nissan (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Joe Machens Toyota
CREATE TABLE IF NOT EXISTS vin_log_joe_machens_toyota (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Kia of Columbia
CREATE TABLE IF NOT EXISTS vin_log_kia_of_columbia (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Land Rover Ranch Mirage
CREATE TABLE IF NOT EXISTS vin_log_land_rover_ranch_mirage (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Mini of St. Louis
CREATE TABLE IF NOT EXISTS vin_log_mini_of_st_louis (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Pappas Toyota
CREATE TABLE IF NOT EXISTS vin_log_pappas_toyota (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Porsche St. Louis
CREATE TABLE IF NOT EXISTS vin_log_porsche_st_louis (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Pundmann Ford
CREATE TABLE IF NOT EXISTS vin_log_pundmann_ford (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Rusty Drewing Cadillac
CREATE TABLE IF NOT EXISTS vin_log_rusty_drewing_cadillac (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Rusty Drewing Chevrolet Buick GMC
CREATE TABLE IF NOT EXISTS vin_log_rusty_drewing_chevrolet_buick_gmc (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Serra Honda O'Fallon
CREATE TABLE IF NOT EXISTS vin_log_serra_honda_ofallon (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- South County Autos
CREATE TABLE IF NOT EXISTS vin_log_south_county_autos (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Spirit Lexus
CREATE TABLE IF NOT EXISTS vin_log_spirit_lexus (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Stehouwer Auto
CREATE TABLE IF NOT EXISTS vin_log_stehouwer_auto (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Suntrup Buick GMC
CREATE TABLE IF NOT EXISTS vin_log_suntrup_buick_gmc (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Suntrup Ford Kirkwood
CREATE TABLE IF NOT EXISTS vin_log_suntrup_ford_kirkwood (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Suntrup Ford West
CREATE TABLE IF NOT EXISTS vin_log_suntrup_ford_west (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Suntrup Hyundai South
CREATE TABLE IF NOT EXISTS vin_log_suntrup_hyundai_south (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Suntrup Kia South
CREATE TABLE IF NOT EXISTS vin_log_suntrup_kia_south (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Thoroughbred Ford
CREATE TABLE IF NOT EXISTS vin_log_thoroughbred_ford (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Twin City Toyota
CREATE TABLE IF NOT EXISTS vin_log_twin_city_toyota (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Weber Chevrolet
CREATE TABLE IF NOT EXISTS vin_log_weber_chevrolet (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- West County Volvo Cars
CREATE TABLE IF NOT EXISTS vin_log_west_county_volvo_cars (
    id SERIAL PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    vehicle_type VARCHAR(20),
    order_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vin, order_date)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_vin_log_audi_ranch_mirage_vin ON vin_log_audi_ranch_mirage(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_audi_ranch_mirage_order_date ON vin_log_audi_ranch_mirage(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_auffenberg_hyundai_vin ON vin_log_auffenberg_hyundai(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_auffenberg_hyundai_order_date ON vin_log_auffenberg_hyundai(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_bmw_of_west_st_louis_vin ON vin_log_bmw_of_west_st_louis(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_bmw_of_west_st_louis_order_date ON vin_log_bmw_of_west_st_louis(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_bommarito_cadillac_vin ON vin_log_bommarito_cadillac(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_bommarito_cadillac_order_date ON vin_log_bommarito_cadillac(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_bommarito_west_county_vin ON vin_log_bommarito_west_county(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_bommarito_west_county_order_date ON vin_log_bommarito_west_county(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_columbia_bmw_vin ON vin_log_columbia_bmw(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_columbia_bmw_order_date ON vin_log_columbia_bmw(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_columbia_honda_vin ON vin_log_columbia_honda(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_columbia_honda_order_date ON vin_log_columbia_honda(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_dave_sinclair_lincoln_vin ON vin_log_dave_sinclair_lincoln(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_dave_sinclair_lincoln_order_date ON vin_log_dave_sinclair_lincoln(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_dave_sinclair_lincoln_south_vin ON vin_log_dave_sinclair_lincoln_south(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_dave_sinclair_lincoln_south_order_date ON vin_log_dave_sinclair_lincoln_south(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_dave_sinclair_lincoln_st_peters_vin ON vin_log_dave_sinclair_lincoln_st_peters(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_dave_sinclair_lincoln_st_peters_order_date ON vin_log_dave_sinclair_lincoln_st_peters(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_frank_leta_honda_vin ON vin_log_frank_leta_honda(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_frank_leta_honda_order_date ON vin_log_frank_leta_honda(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_glendale_chrysler_jeep_vin ON vin_log_glendale_chrysler_jeep(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_glendale_chrysler_jeep_order_date ON vin_log_glendale_chrysler_jeep(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_handw_kia_vin ON vin_log_handw_kia(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_handw_kia_order_date ON vin_log_handw_kia(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_honda_of_frontenac_vin ON vin_log_honda_of_frontenac(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_honda_of_frontenac_order_date ON vin_log_honda_of_frontenac(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_indigo_auto_group_vin ON vin_log_indigo_auto_group(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_indigo_auto_group_order_date ON vin_log_indigo_auto_group(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_jaguar_ranch_mirage_vin ON vin_log_jaguar_ranch_mirage(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_jaguar_ranch_mirage_order_date ON vin_log_jaguar_ranch_mirage(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_joe_machens_cdjr_vin ON vin_log_joe_machens_cdjr(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_joe_machens_cdjr_order_date ON vin_log_joe_machens_cdjr(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_joe_machens_hyundai_vin ON vin_log_joe_machens_hyundai(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_joe_machens_hyundai_order_date ON vin_log_joe_machens_hyundai(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_joe_machens_nissan_vin ON vin_log_joe_machens_nissan(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_joe_machens_nissan_order_date ON vin_log_joe_machens_nissan(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_joe_machens_toyota_vin ON vin_log_joe_machens_toyota(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_joe_machens_toyota_order_date ON vin_log_joe_machens_toyota(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_kia_of_columbia_vin ON vin_log_kia_of_columbia(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_kia_of_columbia_order_date ON vin_log_kia_of_columbia(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_land_rover_ranch_mirage_vin ON vin_log_land_rover_ranch_mirage(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_land_rover_ranch_mirage_order_date ON vin_log_land_rover_ranch_mirage(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_mini_of_st_louis_vin ON vin_log_mini_of_st_louis(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_mini_of_st_louis_order_date ON vin_log_mini_of_st_louis(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_pappas_toyota_vin ON vin_log_pappas_toyota(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_pappas_toyota_order_date ON vin_log_pappas_toyota(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_porsche_st_louis_vin ON vin_log_porsche_st_louis(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_porsche_st_louis_order_date ON vin_log_porsche_st_louis(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_pundmann_ford_vin ON vin_log_pundmann_ford(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_pundmann_ford_order_date ON vin_log_pundmann_ford(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_rusty_drewing_cadillac_vin ON vin_log_rusty_drewing_cadillac(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_rusty_drewing_cadillac_order_date ON vin_log_rusty_drewing_cadillac(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_rusty_drewing_chevrolet_buick_gmc_vin ON vin_log_rusty_drewing_chevrolet_buick_gmc(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_rusty_drewing_chevrolet_buick_gmc_order_date ON vin_log_rusty_drewing_chevrolet_buick_gmc(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_serra_honda_ofallon_vin ON vin_log_serra_honda_ofallon(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_serra_honda_ofallon_order_date ON vin_log_serra_honda_ofallon(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_south_county_autos_vin ON vin_log_south_county_autos(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_south_county_autos_order_date ON vin_log_south_county_autos(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_spirit_lexus_vin ON vin_log_spirit_lexus(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_spirit_lexus_order_date ON vin_log_spirit_lexus(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_stehouwer_auto_vin ON vin_log_stehouwer_auto(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_stehouwer_auto_order_date ON vin_log_stehouwer_auto(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_suntrup_buick_gmc_vin ON vin_log_suntrup_buick_gmc(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_suntrup_buick_gmc_order_date ON vin_log_suntrup_buick_gmc(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_suntrup_ford_kirkwood_vin ON vin_log_suntrup_ford_kirkwood(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_suntrup_ford_kirkwood_order_date ON vin_log_suntrup_ford_kirkwood(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_suntrup_ford_west_vin ON vin_log_suntrup_ford_west(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_suntrup_ford_west_order_date ON vin_log_suntrup_ford_west(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_suntrup_hyundai_south_vin ON vin_log_suntrup_hyundai_south(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_suntrup_hyundai_south_order_date ON vin_log_suntrup_hyundai_south(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_suntrup_kia_south_vin ON vin_log_suntrup_kia_south(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_suntrup_kia_south_order_date ON vin_log_suntrup_kia_south(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_thoroughbred_ford_vin ON vin_log_thoroughbred_ford(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_thoroughbred_ford_order_date ON vin_log_thoroughbred_ford(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_twin_city_toyota_vin ON vin_log_twin_city_toyota(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_twin_city_toyota_order_date ON vin_log_twin_city_toyota(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_weber_chevrolet_vin ON vin_log_weber_chevrolet(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_weber_chevrolet_order_date ON vin_log_weber_chevrolet(order_date);

CREATE INDEX IF NOT EXISTS idx_vin_log_west_county_volvo_cars_vin ON vin_log_west_county_volvo_cars(vin);
CREATE INDEX IF NOT EXISTS idx_vin_log_west_county_volvo_cars_order_date ON vin_log_west_county_volvo_cars(order_date);

COMMIT;

-- ==========================================
-- DEALERSHIP-SPECIFIC VIN LOGS COMPLETED
-- Total tables created: 41
-- ==========================================