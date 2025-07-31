-- Create the dealership database
-- Run this as postgres superuser

-- Drop existing database if needed (comment out if not desired)
-- DROP DATABASE IF EXISTS dealership_db;

-- Create the database
CREATE DATABASE dealership_db
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'C'
    LC_CTYPE = 'C'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Connect to the new database
\c dealership_db;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For fuzzy text search

-- Grant privileges
GRANT ALL ON DATABASE dealership_db TO postgres;