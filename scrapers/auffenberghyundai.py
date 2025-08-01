from enhanced_helper_class import *
import traceback
import sys
import os
import json
import datetime
import requests

# Database configuration for bulletproof system
DB_CONFIG = {
    'host': 'localhost', 
    'database': 'vehicle_inventory',
    'user': 'postgres',
    'password': 'password'
}

class AUFFENBERGHYUNDAI():

	def __init__(self, data_folder, output_file):

		self.helper = EnhancedHelper(DB_CONFIG)
		
		self.data_folder = data_folder
		self.output_file = output_file
		self.log_folder = self.helper.checking_folder_existence(f'{self.data_folder}log/')

	
	def processing_each_vehicle(self, json_data):


		vin = ''
		stock = ''
		ext_color = ''

		for attr in json_data['attributes']:

			attr_title = attr['name']
			attr_value = attr['value']

			if attr_title == 'vin':
				vin = attr_value

			elif attr_title == 'stockNumber':
				stock = attr_value

			elif attr_title == 'exteriorColor':
				ext_color = attr_value

		v_type = json_data['condition'].title().split()[0].strip()
		year = json_data['year']
		make = json_data['make']
		model = json_data.get('model', '')
		try:
			trim = json_data['trim']
		except:
			trim = json_data['title'][1].split(model)[1].strip()

		status = json_data['status'].lower()

		if status == 'live':
			status = 'On The Lot'

		else:
			status = 'In Transit'


		try:
			price = int(json_data['trackingPricing']['salePrice'])
		except:
			try:
				price = int(str((json_data['trackingPricing']['salePrice']).replace('$', '').replace(',', '')))
			except:
				price = ''

		body = json_data.get('bodyStyle', '')
		fuel_type = json_data.get('fuelType', '')
		try:
			msrp = int(json_data['trackingPricing']['msrp'].replace(',', '').replace('$', ''))
		except:
			msrp = ''
		if not msrp or msrp == price:
			msrp = ''
		
		if not price:
			price = 'Please Call'

		date_in_stock = ''
		street_addr = ' 1050 Berg Blvd'
		locality = "Shiloh"
		postal_code = '62269'
		region = 'IL'
		country = 'US'
		location = 'Auffenberg Hyundai'
		vehicle_url = 'https://www.auffenberghyundai.com' + json_data['link']

		# if vehicle_url == 'https://www.auffenberghyundai.com/new/Hyundai/2025-Hyundai-Elantra-3d935d3dac181eee66c9e910d8ef7fd2.htm':
		# 	input('wait here')

		self.helper.writing_output_file([
			vin,
			stock,
			v_type,
			year,
			make,
			model,
			trim,
			ext_color,
			status,
			price,
			body,
			fuel_type,
			msrp,
			date_in_stock,
			street_addr,
			locality,
			postal_code,
			region,
			country,
			location,
			vehicle_url
		], self.output_file)

	def get_all_vehicles(self, page_num):

		offset = 18 * (page_num - 1)

		print('Getting Vehicles: ', page_num, ' : ', offset)

		url = "https://www.auffenberghyundai.com/api/widget/ws-inv-data/getInventory"

		payload = json.dumps({
			"siteId": "auffenberghyundaishiloh",
			"locale": "en_US",
			"device": "DESKTOP",
			"pageAlias": "INVENTORY_LISTING_DEFAULT_AUTO_ALL",
			"pageId": "v9_INVENTORY_SEARCH_RESULTS_AUTO_ALL_V1_1",
			"windowId": "inventory-data-bus1",
			"widgetName": "ws-inv-data",
			"inventoryParameters": {"start": [str(offset) ] }, "includePricing": True,
			"flags": {
			"vcda-js-environment": "live",
			"ws-scripts-concurrency-limits-concurrency": 16,
			"ws-scripts-concurrency-limits-queue": 16,
			"ws-scripts-concurrency-limits-enabled": True,
			"ws-itemlist-service-version": "v5",
			"ws-itemlist-model-version": "v1",
			"ws-scripts-inline-css": True,
			"ws-inv-data-fetch-timeout": 5000,
			"ws-inv-data-fetch-retries": 2,
			"ws-inv-data-use-wis": True,
			"ws-inv-data-wis-fetch-timeout": 5000,
			"srp-track-fetch-resource-timing": True,
			"srp-test-package-data": 0,
			"ws-inv-data-preload-inventory": True,
			"ws-inv-data-location-service-fetch-timeout": 3000,
			"ws-inv-data-location-service-fetch-retries": 2,
			"wsm-account-data-distributor-timeout": 50,
			"wsm-account-data-distributor-retries": 2,
			"enable-client-side-geolocation-ws-inv-data": False,
			"enable-account-data-distributor-fetch-ws-inv-data": True,
			"ws-inv-data-spellcheck-proxy-timeout": 5000,
			"ws-inv-data-spellcheck-server-timeout": 1500,
			"ws-inv-data-spellcheck-server-retries": 0,
			"srp-toggle-databus-editor": True,
			"srp-send-ws-inv-data-prefs-to-wis": False
		} })

		headers = {
		'Content-Type': 'application/json',
		'Cookie': 'ak_bmsc=245D920A5CC0F2BBFBE9905AAC960F90~000000000000000000000000000000~YAAQRbxBF3B+UVqWAQAAvs9Jaxu+U3QrnXMWIrhC/QZrk/02vmWaVFWS/PFbjafVpHmFCyzXmdrNP+P6IKkLjNesc3stXyuFWTzmUQIHknQHD9LvSe6nsqTol5O8N+9vQrJ4OTz1CBeCBBZq4iQpJWx/ZRZsbPB9EYjOg0QjrgvTweUxFLn5ZlrWpSpTJF/aGhsbxNzAbR2Okb9byCCWCr6Fx9whvOT3vUYX+Ydzf/aXN0HZ92JTz0e9XpSs7kYoKbp2S6ldLWcGaqR2YacdJ2LzA74beUYnDh+k2LXliBgTwlcnqwgX/yQq00LixmHU1BjxRxn5hYYGuoteDTU8zhCaLDFKTppupHiDa22lBbMtmpnITVeO; bm_sv=0CBFFEE15C6EE3E69590E6318EE128BD~YAAQP7xBF0QMa1iWAQAA6t5JaxtC1oj1wn7JpP/wZH+PlRRKX0e4MsQR1yvu70yagQvDi9szsPbcfjL/IegZKfka3zz47r4n8YvnAHiYEJ2eWL8o4U4Y8LiMpupWTkZLHhs+v5NAmriYg5ubJvq8Srad1XlSkwvu2KldPs+TSkc/IO5cNKkm9tTH3pP3d+RyrfRZmH3Xy+uD5revMBbcbiMP/EX7d6KYNdzTA4tNJjzp2TZLNH34BFvmKoyY+Zzi+wvxsiVEirl3kXs=~1'
		}

		response = requests.request("POST", url, headers=headers, data=payload)

		return response.json()
	
	def start_scraping_auffenberghyundai(self):

		processed_json_file = self.log_folder + 'vehicles_processed.json'
		processed_json_data = self.helper.json_exist_data(processed_json_file)

		page_num = 1

		while 1:

			json_data = self.get_all_vehicles(page_num)

			total_vehicles = json_data['pageInfo']['totalCount']
			total_pages = (total_vehicles // 18) + 1
			all_vehicles = json_data['inventory']

			# self.helper.write_json_file(json_data, 'json_data.json')

			print(page_num, ' : ', len(all_vehicles), ' : ', total_vehicles, ' : ', total_pages)

			for index, vehicle in enumerate(all_vehicles):

				name = vehicle['title'][0]
				vehicle_url = 'https://www.auffenberghyundai.com' + vehicle['link']

				print(page_num, ' : ', len(all_vehicles), ' : ', name, ' : ', vehicle_url)

				if vehicle_url not in processed_json_data:

					self.processing_each_vehicle(vehicle)

					processed_json_data.append(vehicle_url)
					self.helper.write_json_file(processed_json_data, processed_json_file)
					
				else:
					print('Vehicle Already Processed...')

				print('-'*50)
				print()

			if page_num >= total_pages or len(all_vehicles) < 18:
				break

			page_num += 1


if __name__ == "__main__":
	handle = MAINCLASS()
	handle.start_scraping()

	print()
	print('*'*50)
	print('ALL DONE, YOU CAN CLOSE THIS CONSOLE AND CHECK THE DATA IN THE OUTPUT_DATA FOLDER.')
	print('*'*50)
	print()