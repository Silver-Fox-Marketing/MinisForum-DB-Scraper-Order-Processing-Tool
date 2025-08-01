import json
import os
import re
import requests
import sys
import random
import csv
import time
from bs4 import BeautifulSoup
import datetime
import psycopg2
from psycopg2 import sql
import traceback

class DatabaseHelper:
    """Database integration helper for scrapers"""
    
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None
        
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            return True
        except Exception as e:
            print(f"Database connection error: {e}")
            return False
            
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            
    def insert_vehicle_data(self, vehicle_data):
        """Insert vehicle data into raw_data table"""
        try:
            if not self.connection:
                if not self.connect():
                    return False
                    
            cursor = self.connection.cursor()
            
            # Insert into raw_data table (matching existing structure)
            insert_query = """
                INSERT INTO raw_data (
                    vin, stock, v_type, year, make, model, trim, ext_color,
                    status, price, body, fuel_type, msrp, date_in_stock,
                    street_addr, locality, postal_code, region, country,
                    location, vehicle_url, import_timestamp
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Add import timestamp
            vehicle_data_with_timestamp = list(vehicle_data) + [datetime.datetime.now()]
            
            cursor.execute(insert_query, vehicle_data_with_timestamp)
            self.connection.commit()
            cursor.close()
            return True
            
        except Exception as e:
            print(f"Database insert error: {e}")
            if self.connection:
                self.connection.rollback()
            return False

class EnhancedHelper:
    """Enhanced helper class combining original functionality with database integration"""
    
    def __init__(self, db_config=None):
        # Initialize database helper if config provided
        if db_config:
            self.db_helper = DatabaseHelper(db_config)
        else:
            self.db_helper = None
            
    def read_txt_file(self, filename):
        with open(filename) as infile:
            ids = [row.replace('\n', '').replace('\r', '') for row in infile]
        return ids

    def writing_output_file(self, sub_list, output_file):
        """Write to both CSV file and database"""
        
        # Original CSV writing functionality (preserved)
        if self.is_file_exist(output_file):
            csv_data = self.reading_csv(output_file)
        else:
            csv_data = [["vin", "stock", "v_type", "year", "make", "model", "trim", "ext_color",
                        "status", "price", "body", "fuel_type", "msrp", "date_in_stock",
                        "street_addr", "locality", "postal_code", "region", "country",
                        "location", "vehicle_url"]]
            
        csv_data.append(sub_list)
        self.writing_csv(csv_data, output_file)
        
        # Database writing functionality (new)
        if self.db_helper:
            success = self.db_helper.insert_vehicle_data(sub_list)
            if success:
                print("SUCCESS: Vehicle data saved to database")
            else:
                print("FAILED: Failed to save vehicle data to database")

    def get_url_response(self, url, is_json=False):
        print("Processing URL: ", url)
        count = 0
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'}
        
        while 1:
            try:
                if not is_json:
                    return requests.get(url, headers=headers, timeout=30).text
                return requests.get(url, headers=headers, timeout=30).json()
            except Exception as error:
                print('Error in getting URL response: ', error)
            
            count += 1
            if count > 3:
                return False
            time.sleep(3)

    def make_soup_url(self, url):
        return BeautifulSoup(self.get_url_response(url), 'html.parser')

    def reading_csv(self, csv_filename):
        f = open(csv_filename, 'r', encoding='utf-8', errors='replace')
        csv_data = []
        reader = csv.reader(f)
        for row in reader:
            csv_data.append(row)
        f.close()
        return csv_data

    def writing_csv(self, data, csv_filename):
        myFile = open(csv_filename, 'w', newline='', encoding='utf-8', errors='replace')
        with myFile:
            writer = csv.writer(myFile, quoting=csv.QUOTE_ALL)
            writer.writerows(data)
        return csv_filename

    def checking_folder_existence(self, dest_dir):
        if not os.path.exists(dest_dir):
            os.mkdir(dest_dir)
            print("Directory", dest_dir, "Created")
        return dest_dir

    def write_json_file(self, data, filename):
        while 1:
            try:
                with open(filename, 'w', encoding='utf-8') as outfile:
                    json.dump(data, outfile, indent=4)
                break
            except Exception as error:
                print("Error in writing Json file: ", error)
                time.sleep(1)

    def read_json_file(self, filename):
        data = {}
        with open(filename, encoding='utf-8') as json_data:
            data = json.load(json_data)
        return data

    def is_file_exist(self, filename):
        if os.path.exists(filename):
            return True
        else:
            return False

    def json_exist_data(self, fileName):
        json_data = []
        if self.is_file_exist(fileName):
            json_data = self.read_json_file(fileName)
        return json_data

    def downloading_image_file(self, image_url, image_filename):
        if self.is_file_exist(image_filename):
            return True
        
        print('Downloading File: ', image_filename, ' : ', image_url)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }
        
        response = requests.request("GET", image_url, headers=headers, data={}).content
        with open(image_filename, 'wb') as handler:
            handler.write(response)

    def write_random_file(self, text, file_name):
        file = open(file_name, "w", encoding='utf-8')
        file.write(str(text))
        file.close()

    def read_random_file(self, file_name):
        f = open(file_name, "r", encoding='utf-8')
        return f.read()

# Backward compatibility - create Helper class that uses EnhancedHelper
class Helper(EnhancedHelper):
    """Backward compatible Helper class"""
    pass