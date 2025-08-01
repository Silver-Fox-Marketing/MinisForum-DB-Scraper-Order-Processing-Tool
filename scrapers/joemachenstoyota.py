from enhanced_helper_class import *
import traceback
import sys
import os
import json
import datetime
import requests
import time
from bs4 import BeautifulSoup
from interface_class import *

# Database configuration for bulletproof system
DB_CONFIG = {
    'host': 'localhost', 
    'database': 'vehicle_inventory',
    'user': 'postgres',
    'password': 'password'
}

class JOEMACHENSTOYOTA():

	def __init__(self, data_folder, output_file):

		self.helper = EnhancedHelper(DB_CONFIG)
		
		self.data_folder = data_folder
		self.output_file = output_file
		self.log_folder = self.helper.checking_folder_existence(f'{self.data_folder}log/')

		self.interface = INTERFACING()

	
	def processing_each_vehicle(self, vehicle_url, status):

		# soup = self.get_all_vehicles(vehicle_url)
		soup = self.interface.get_selenium_response(vehicle_url)

		# print(soup)

		json_data = soup.find('script', string=re.compile('shift_digital_session_id')).text.strip()
		json_data = ' '.join(json_data.split()).split('page:')[1].split(', shift_digital_session_id')[0].strip()
		json_data = json.loads(json_data)

		# print(vehicle_data)

		vin = json_data['vehicle_vin'][0]
		stock = json_data['vehicle_stock'][0]
		year = json_data['vehicle_year'][0]
		make = json_data['vehicle_make'][0]
		model = json_data['vehicle_model'][0]
		try:
			ext_color = json_data['vehicle_color_ext'][0]
		except:
			ext_color = ''

		try:
			vehicle_location_id = str(json_data['vehicle_location_id'][0])
		except:
			vehicle_location_id = ''

		if not vehicle_location_id or vehicle_location_id != '8692':
			return True

		status = status.replace('_', '-').title()

		v_type = json_data['vehicle_type']

		if 'certified' in v_type:
			v_type = 'Certified'

		else:
			v_type = v_type[0].title()

		body = json_data['vehicle_body_style'][0]
		fuel_type = json_data['vehicle_engine_fuel'][0]

		date_in_stock = json_data['vehicle_date_instock'][0].split()[0]
		street_addr = '1180 Vandiver Dr'
		locality = 'Columbia'
		postal_code = '65202'
		region = 'MO'
		country = 'US'
		location = 'Joe Machens Toyota'

		trim = json_data['vehicle_trim'][0]
		try:
			price = json_data['vehicle_price'][0]
		except:
			price = ''

		msrp = ''

		if not msrp or msrp == price:
			msrp = ''

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

	def get_all_vehicles(self, url, is_json=False):

		print('Processing URL: ', url)

		payload = {}
		headers = {
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
			'Accept-Language': 'en-US,en;q=0.9',
			'Cache-Control': 'max-age=0',
			'Cookie': 'TID=eda18f7d-f7ea-4b05-97c0-b464670ee4f3; Detection=CfDJ8NP4lA7dvFtKoeevvMarc%2FOdSlws03CnyWqpqYrWrblhmtt2flY3FuyOR9%2FP955qyTmb4Mb%2F9GnKmv%2FIivw9ukVdCHDzpR1tfrvmG00XuVrKmj8oq131HiD7aoTfNM97bwjFkigLPQuhFz6Cu8ZElRgSq%2BwMo7qvSVKTbOMMKOIB; _gid=GA1.2.894012436.1721710996; _gcl_au=1.1.56984312.1721710996; _hjSession_2865343=eyJpZCI6ImFkMjVhM2ViLWVhZmUtNDY4MC1iYTUwLWMyYmMwYmRiZjgyMCIsImMiOjE3MjE3MTA5OTcxNTMsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjoxLCJzcCI6MH0=; _fbp=fb.1.1721710997171.957579351587050092; _edwpv=6998672d-9480-4b90-89d2-95090d40df8d; _edwps=074789695999607158; edmunds=0580fbe2-cd3a-46c5-baef-dbd0f858f05a; edw=706407887819097345; _edwvts=706407887819097345; adsol_nv=1; adsol_session=true; AMCVS_5288FC7C5A0DB1AD0A495DAA%40AdobeOrg=1; s_cc=true; AMCV_5288FC7C5A0DB1AD0A495DAA%40AdobeOrg=1176715910%7CMCIDTS%7C19928%7CMCMID%7C13071349527502173343669021158905392855%7CMCAAMLH-1722315799%7C7%7CMCAAMB-1722315799%7C6G1ynYcLPuiQxYZrsz_pkqfLG9yMXBpb2zX5dvJdYQJzPXImdj0y%7CMCOPTOUT-1721718199s%7CNONE%7CMCSYNCSOP%7C411-19935%7CvVersion%7C5.4.0; _sda:kia:T3:user=719a6870-67f7-4f0f-88e3-d8d84ba70bf6%3A4.0%3A1721710998330%3AX!7d978490d89fe56aa0c89a9d351478ce!wm72iwrctpmo!%3A66245!66245!66245!; _hjSessionUser_2865343=eyJpZCI6Ijg5MGJjMjg1LTYwNGQtNTE4ZC1iOTJmLTNjZTIyMzkwMDE5MiIsImNyZWF0ZWQiOjE3MjE3MTA5OTcxNTEsImV4aXN0aW5nIjp0cnVlfQ==; s_sq=%5B%5BB%5D%5D; .AspNetCore.Antiforgery.JyRgIBeLjWA=CfDJ8NP4lA7dvFtKoeevvMarc_O30hMUzC4UrkWN4sNjdykm6K1asXxoy-hjUrz7GHmDeU6iQGVPahMnDTq1p6LhqpKx4sqpeLAYuDCrLdasgirv5MqBKNHMVBJaklsqG1YVp-6e8Vru8TjAbC73J-8Fs3c; _ga_26SHJRWFVN=GS1.1.1721710996.1.1.1721711950.0.0.0; _ga=GA1.1.595666044.1721710996; _ga_R86HMFVNVP=GS1.1.1721710995.1.1.1721711951.59.0.0; _ga_PCE0F8P6RD=GS1.1.1721710995.1.1.1721711951.0.0.0; _ga_LTTNMPN8G8=GS1.1.1721710996.1.1.1721711951.0.0.0; _ga_P4MTFJCPWL=GS1.1.1721710995.1.1.1721711951.0.0.0; _uetsid=df618a1048b011efa09e259069583907; _uetvid=df62052048b011ef8aed81ccc5e60318; _ga_PB44JM1FPY=GS1.1.1721710999.1.1.1721711953.60.0.0; _ga_RCTCH4F5WQ=GS1.1.1721710999.1.1.1721711953.0.0.0; _ga_N8Y23D5XT5=GS1.2.1721710997.1.1.1721711954.58.0.0; _ga_V8441MN46V=GS1.2.1721710997.1.1.1721711954.0.0.0; cgpd=%7B%22es%22%3A%5B%22318-3%3Acm.lotlinx.com%3A%22%2C%22318-3%3Acalls.mymarketingreports.com%3A%22%2C%22318-3%3Acalls.mymarketingreports.com%3A%22%5D%7D; _sda:kia:T3:session=f37d5120-d414-436b-bb22-274c2c995995%3AN%3A1721713756685%3A%3AX!7d978490d89fe56aa0c89a9d351478ce!wm72iwrctpmo!%3A1721710998335%3AN%3A%3AKIA%3ATEAMVELOCITY%3AMO035%3AN%3A; Detection=CfDJ8NP4lA7dvFtKoeevvMarc%2FOZKPcG33GsSOjcfGbxTsle6j1wIkpTungJ8%2BTGsE0dFY77%2Byj80fXbJE63%2B1g3lqz9JGS%2FS71a95f5icTRGKZrthG5ApFhTbP%2FenMeVfFp1XujXzZXqQd1sAdSg%2FixwTqkvRrXRv1Zx4siQuc2AXq8; TID=0fa35f04-02ba-417a-8825-7a326550f8c7',
			'Priority': 'u=0, i',
			'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
			'Sec-Ch-Ua-Mobile': '?0',
			'Sec-Ch-Ua-Platform': '"Windows"',
			'Sec-Fetch-Dest': 'document',
			'Sec-Fetch-Mode': 'navigate',
			'Sec-Fetch-Site': 'none',
			'Sec-Fetch-User': '?1',
			'Upgrade-Insecure-Requests': '1',
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
			}


		while 1:
			try:
				response = requests.request("GET", url, headers=headers, data=payload)

				if is_json:
					return response.json()

				return BeautifulSoup(response.text, 'html.parser')

			except Exception as error:
				print('error in getting vehicles: ', error)

			time.sleep(1)

			
	def start_scraping_joemachenstoyota(self):

		processed_json_file = self.log_folder + 'vehicles_processed.json'
		processed_json_data = self.helper.json_exist_data(processed_json_file)

		for status in ['allocated', 'in_stock', 'in_transit']:

			page_num = 1

			while 1:

				soup = self.interface.get_selenium_response(f'https://www.joemachenstoyota.com/search/joe-machens-toyota/?av={status}&cy=65201&lc=8692&p={page_num}')

				while 1:

					soup = self.interface.make_soup()

					try:
						all_vehicles = soup.find('div', class_='srp_results carbon').find('div', class_=re.compile('srp_results_vehicles_wrapper')).find_all('h2', class_='vehicle_title')
						break
					except Exception as error:
						print('Page not yet loaded: ', error)

					time.sleep(1)

				total_pages = int(soup.find('span', class_='pagination_settings__page_count').text.strip())

				for index, vehicle in enumerate(all_vehicles):

					vehicle_url = 'https://www.joemachenstoyota.com' + vehicle.a['href']

					print(page_num, ' : ', total_pages, ' : ', len(all_vehicles), ' / ', index + 1, ' : ', vehicle_url)

					if vehicle_url not in processed_json_data:

						self.processing_each_vehicle(vehicle_url, status)

						processed_json_data.append(vehicle_url)
						self.helper.write_json_file(processed_json_data, processed_json_file)
						
					else:
						print('Vehicle Already Processed...')

					print('-'*50)
					print()

				if len(all_vehicles) < 12 or page_num >= total_pages:
					break

				page_num += 1

		self.interface.close_driver()


if __name__ == "__main__":
	handle = MAINCLASS()
	handle.start_scraping()

	print()
	print('*'*50)
	print('ALL DONE, YOU CAN CLOSE THIS CONSOLE AND CHECK THE DATA IN THE OUTPUT_DATA FOLDER.')
	print('*'*50)
	print()