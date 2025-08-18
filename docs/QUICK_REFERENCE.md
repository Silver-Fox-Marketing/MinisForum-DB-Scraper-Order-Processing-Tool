# Quick Reference Card

## Daily Operations

### Start Web Interface
```cmd
cd web_gui
python app.py
# Access: http://127.0.0.1:5000
```

### CSV Import Testing (v2.1)
```
1. Navigate to Order Queue Management tab
2. Use CSV Import section
3. ✅ Check "Keep data" for testing (skips VIN logging)
4. ❌ Uncheck "Keep data" for production (logs VINs)
5. Process and validate results
```

### Process CAO Order
```cmd
python order_processing_cli.py --cao "BMW of West St. Louis" --template shortcut_pack
```

### Process LIST Order  
```cmd
python order_processing_cli.py --list "Columbia Honda" --vins "VIN1,VIN2,VIN3"
```

### Check VIN Log Status
```sql
-- Check recent VIN activity for dealership
SELECT COUNT(*) FROM vin_log_bmw_of_west_st_louis WHERE order_date = CURRENT_DATE;
```

## Emergency Recovery

### Rebuild Database
1. Run `INSTALL.bat` again
2. Re-import latest complete_data.csv
3. Verify dealership configs: `SELECT COUNT(*) FROM dealership_configs;`

### Performance Optimization
```sql
VACUUM ANALYZE normalized_vehicle_data;
REINDEX DATABASE minisforum_dealership_db;
```
