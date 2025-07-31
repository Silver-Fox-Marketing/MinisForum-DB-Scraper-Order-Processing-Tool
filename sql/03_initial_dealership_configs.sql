-- Initial dealership configurations for Silver Fox Marketing
-- Complete configuration for all 40 dealerships in the scraper system

INSERT INTO dealership_configs (name, filtering_rules, output_rules, qr_output_path) VALUES
-- BMW Dealerships
('BMW of West St. Louis', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0, "year_min": 2020}',
    '{"include_qr": true, "format": "standard", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\bmw_west_stl\\'),
    
('Columbia BMW', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0, "year_min": 2020}',
    '{"include_qr": true, "format": "standard", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\columbia_bmw\\'),

-- Audi Dealerships
('Audi Ranch Mirage', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0, "year_min": 2019}',
    '{"include_qr": true, "format": "standard", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\audi_ranch_mirage\\'),

-- Jaguar & Land Rover
('Jaguar Ranch Mirage', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0, "year_min": 2020}',
    '{"include_qr": true, "format": "premium", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\jaguar_ranch_mirage\\'),
    
('Land Rover Ranch Mirage', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0, "year_min": 2020}',
    '{"include_qr": true, "format": "premium", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\landrover_ranch_mirage\\'),

-- Hyundai Dealerships
('Auffenberg Hyundai', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["model", "price"]}',
    'C:\\qr_codes\\auffenberg_hyundai\\'),
    
('Joe Machens Hyundai', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["model", "price"]}',
    'C:\\qr_codes\\joe_machens_hyundai\\'),

-- Honda Dealerships
('Columbia Honda', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\columbia_honda\\'),
    
('Honda of Frontenac', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\honda_frontenac\\'),
    
('Frank Leta Honda', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\frank_leta_honda\\'),
    
('Serra Honda of O''Fallon', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\serra_honda_ofallon\\'),

-- Toyota Dealerships
('Joe Machens Toyota', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\joe_machens_toyota\\'),
    
('Pappas Toyota', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\pappas_toyota\\'),
    
('Twin City Toyota', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\twin_city_toyota\\'),

-- Nissan Dealerships
('Joe Machens Nissan', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\joe_machens_nissan\\'),

-- Kia Dealerships
('Kia of Columbia', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["model", "price"]}',
    'C:\\qr_codes\\kia_columbia\\'),
    
('Suntrup Kia South', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["model", "price"]}',
    'C:\\qr_codes\\suntrup_kia_south\\'),
    
('H&W Kia', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["model", "price"]}',
    'C:\\qr_codes\\hw_kia\\'),

-- Chrysler/Dodge/Jeep/Ram Dealerships
('Joe Machens Chrysler Dodge Jeep Ram', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["make", "model"]}',
    'C:\\qr_codes\\joe_machens_cdjr\\'),
    
('Glendale Chrysler Jeep', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["make", "model"]}',
    'C:\\qr_codes\\glendale_chrysler_jeep\\'),

-- Lincoln Dealerships
('Dave Sinclair Lincoln South', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0, "year_min": 2020}',
    '{"include_qr": true, "format": "premium", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\dave_sinclair_lincoln_south\\'),
    
('Dave Sinclair Lincoln St. Peters', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0, "year_min": 2020}',
    '{"include_qr": true, "format": "premium", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\dave_sinclair_lincoln_stpeters\\'),

-- Ford Dealerships
('Suntrup Ford West', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\suntrup_ford_west\\'),
    
('Suntrup Ford Kirkwood', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\suntrup_ford_kirkwood\\'),
    
('Pundmann Ford', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\pundmann_ford\\'),
    
('Thoroughbred Ford', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\thoroughbred_ford\\'),

-- Chevrolet/Buick/GMC Dealerships
('Rusty Drewing Chevrolet Buick GMC', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["make", "model"]}',
    'C:\\qr_codes\\rusty_drewing_cbg\\'),
    
('Weber Chevrolet', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\weber_chevrolet\\'),
    
('Suntrup Buick GMC', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["make", "model"]}',
    'C:\\qr_codes\\suntrup_buick_gmc\\'),

-- Cadillac Dealerships
('Bommarito Cadillac', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0, "year_min": 2020}',
    '{"include_qr": true, "format": "premium", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\bommarito_cadillac\\'),
    
('Rusty Drewing Cadillac', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0, "year_min": 2020}',
    '{"include_qr": true, "format": "premium", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\rusty_drewing_cadillac\\'),
    
('Bommarito West County', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0, "year_min": 2020}',
    '{"include_qr": true, "format": "premium", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\bommarito_west_county\\'),

-- Additional Hyundai
('Suntrup Hyundai South', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["model", "price"]}',
    'C:\\qr_codes\\suntrup_hyundai_south\\'),

-- Premium Brands
('MINI of St. Louis', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0, "year_min": 2020}',
    '{"include_qr": true, "format": "premium", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\mini_stlouis\\'),
    
('Porsche St. Louis', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0, "year_min": 2019}',
    '{"include_qr": true, "format": "premium", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\porsche_stlouis\\'),
    
('Spirit Lexus', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0, "year_min": 2020}',
    '{"include_qr": true, "format": "premium", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\spirit_lexus\\'),
    
('West County Volvo Cars', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0, "year_min": 2020}',
    '{"include_qr": true, "format": "premium", "sort_by": ["model", "year"]}',
    'C:\\qr_codes\\west_county_volvo\\'),

-- Independent Dealers
('Indigo Auto Group', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["make", "year"]}',
    'C:\\qr_codes\\indigo_auto_group\\'),
    
('South County Autos', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["make", "year"]}',
    'C:\\qr_codes\\south_county_autos\\'),

-- Final dealership to reach 40 total
('Premier Auto Plaza', 
    '{"exclude_conditions": ["offlot"], "require_stock": true, "min_price": 0}',
    '{"include_qr": true, "format": "standard", "sort_by": ["make", "model"]}',
    'C:\\qr_codes\\premier_auto_plaza\\')

ON CONFLICT (name) DO UPDATE SET
    filtering_rules = EXCLUDED.filtering_rules,
    output_rules = EXCLUDED.output_rules,
    qr_output_path = EXCLUDED.qr_output_path,
    updated_at = CURRENT_TIMESTAMP;

-- Example of filtering rules JSON structure:
/*
{
    "exclude_conditions": ["offlot"],  -- Exclude off-lot vehicles
    "require_stock": true,              -- Must have stock number
    "min_price": 0,                     -- Minimum price filter
    "max_price": 100000,                -- Maximum price filter
    "exclude_makes": [],                -- List of makes to exclude
    "include_only_makes": [],           -- If set, only include these makes
    "exclude_models": [],               -- List of models to exclude
    "year_min": 2020,                   -- Minimum year
    "year_max": 2025                    -- Maximum year
}
*/

-- Example of output rules JSON structure:
/*
{
    "include_qr": true,                 -- Include QR code path in output
    "format": "standard",               -- Output format type
    "fields": [                         -- Custom field selection
        "vin", "stock", "year", "make", 
        "model", "trim", "price"
    ],
    "sort_by": ["make", "model"],      -- Sort order for output
    "group_by": "vehicle_condition"     -- Grouping for output
}
*/