import sys
sys.path.append('scripts')
from database_connection import DatabaseManager

def check_configs():
    db = DatabaseManager()
    
    print("=== Honda of Frontenac Config ===")
    result = db.execute_query('SELECT * FROM dealership_configs WHERE dealership_name = %s', ('Honda of Frontenac',))
    for row in result:
        print(f'ID: {row[0]}')
        print(f'Dealership: {row[1]}')
        print(f'Vehicle Types: {row[2]}') 
        print(f'Status: {row[3]}')
        print(f'Price Min: {row[4]}')
        print(f'Price Max: {row[5]}')
        print(f'Days on Lot Min: {row[6]}')
        print(f'Active: {row[7]}')
        print()
    
    print("=== South County DCJR Config (Working) ===")
    result = db.execute_query('SELECT * FROM dealership_configs WHERE dealership_name = %s', ('South County Autos',))
    for row in result:
        print(f'ID: {row[0]}')
        print(f'Dealership: {row[1]}')
        print(f'Vehicle Types: {row[2]}') 
        print(f'Status: {row[3]}')
        print(f'Price Min: {row[4]}')
        print(f'Price Max: {row[5]}')
        print(f'Days on Lot Min: {row[6]}')
        print(f'Active: {row[7]}')

if __name__ == "__main__":
    check_configs()