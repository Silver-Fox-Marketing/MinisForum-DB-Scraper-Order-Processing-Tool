from enhanced_helper_class import *
import traceback
import sys
import os
import json
import datetime
import requests
import time

# Database configuration for bulletproof system
DB_CONFIG = {
    'host': 'localhost', 
    'database': 'vehicle_inventory',
    'user': 'postgres',
    'password': 'password'
}

class DAVESINCLAIRLINCOLNSTPETERS():

	def __init__(self, data_folder, output_file):

		self.helper = EnhancedHelper(DB_CONFIG)
		
		self.data_folder = data_folder
		self.output_file = output_file
		self.log_folder = self.helper.checking_folder_existence(f'{self.data_folder}log/')

	
	def processing_each_vehicle(self, json_data):

		vin = json_data['VehicleVin']
		stock = json_data['VehicleStockNumber']
		v_type = json_data['VehicleCondition'].title()
		year = json_data['VehicleYear']
		make = json_data['VehicleMake']
		model = json_data['VehicleModel']
		trim = json_data['VehicleTrim']
		ext_color = json_data['ExteriorColorLabel']

		status = ''

		if json_data['VehicleInStock']:
			status = 'In-stock'

		elif json_data['VehicleInTransit']:
			status = 'In-transit'

		try:
			price = int(json_data['VehicleMsrp'])
		except:
			price = ''

		body = json_data['VehicleBodyStyle']
		fuel_type = json_data['VehicleFuelType']
		msrp = int(json_data['VehicleMsrp'])

		if not price or price is None:
			price =  json_data.get('VehicleInternetPrice', '')

		if not msrp:
			msrp = ''

		if not price:
			price = ''

		date_in_stock = json_data['VehicleTaggingInventoryDate']
		street_addr = '4760 North Service Road'
		locality = 'Saint Peters'
		postal_code = '63376'
		region = 'MO'
		country = 'US'
		location = 'Dave Sinclair Lincoln St. Peters'
		vehicle_url = json_data['VehicleDetailUrl']

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

	def get_all_vehicles(self, url):

		print('Processing URL: ', url)

		payload = {}

		headers = {'Content-Type': 'application/json' }

		while 1:
			try:
				response = requests.request("GET", url, headers=headers, data=payload)
				return response.json()

			except Exception as error:
				print('error in getting vehicles: ', error)

			time.sleep(1)

			
	def start_scraping_davesinclairlincolnstpeters(self):

		processed_json_file = self.log_folder + 'vehicles_processed.json'
		processed_json_data = self.helper.json_exist_data(processed_json_file)

		soup = self.helper.make_soup_url('https://www.davesinclairlincolnstpeters.com/searchall.aspx?pt=1')
		json_data = soup.find('script', id='dealeron_tagging_data').string.strip()
		json_data = json.loads(' '.join(json_data.split()))

		dealer_id = json_data['dealerId']
		page_id = json_data['pageId']

		page_num = 1
		display_cards = 0

		while 1:

			url = f'https://www.davesinclairlincolnstpeters.com/api/vhcliaa/vehicle-pages/cosmos/srp/vehicles/{dealer_id}/{page_id}?Dealership=Dave%20Sinclair%20Lincoln%20St.%20Peters&host=www.davesinclairlincolnstpeters.com&pt={page_num}'
			url += f'&pn=12&displayCardsShown={display_cards}'

			json_data = self.get_all_vehicles(url)

			# self.helper.write_json_file(json_data, 'json_data.json')

			total_vehicles = json_data['Paging']['PaginationDataModel']['TotalCount']
			total_pages = json_data['Paging']['PaginationDataModel']['TotalPages']
			all_vehicles = json_data['DisplayCards']
			display_cards = json_data['Paging']['PaginationDataModel']['PageEnd']

			print(page_num, ' : ', len(all_vehicles), ' : ', total_vehicles, ' : ', total_pages)

			for index, vehicle in enumerate(all_vehicles):

				vehicle = vehicle['VehicleCard']

				name = vehicle['VehicleName']
				vehicle_url = vehicle['VehicleDetailUrl']

				print(page_num, ' : ', len(all_vehicles), ' : ', name, ' : ', vehicle_url)


				if vehicle_url not in processed_json_data:

					self.processing_each_vehicle(vehicle)

					processed_json_data.append(vehicle_url)
					self.helper.write_json_file(processed_json_data, processed_json_file)
					
				else:
					print('Vehicle Already Processed...')

				print('-'*50)
				print()

			if page_num >= total_pages or len(all_vehicles) < 12:
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