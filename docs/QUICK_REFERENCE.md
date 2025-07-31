# Quick Reference Card

## Daily Operations

### Import Complete CSV
```cmd
cd C:\minisforum_database_transfer
python scripts\csv_importer_complete.py "C:\data_imports\complete_data.csv"
```

### Export All Data
```cmd
python scripts\data_exporter.py --all --output "C:\exports\all_vehicles_%DATE%.csv"
```

### Export Single Dealership
```cmd
python scripts\data_exporter.py --dealership "BMW of West St. Louis" --output "C:\exports\bmw_west.csv"
```

### Check Database Status
```cmd
psql -d minisforum_dealership_db -c "SELECT COUNT(*) FROM normalized_vehicle_data;"
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
