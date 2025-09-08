from . helper_class import *
from . interface_class import *

class PAPPASTOYOTA():

	def __init__(self, data_folder, output_file):

		self.helper = Helper()

		self.interface = INTERFACING()
		
		self.data_folder = data_folder
		self.output_file = output_file
		self.log_folder = self.helper.checking_folder_existence(f'{self.data_folder}log/')

		self.cookie = ''
	
	def processing_each_vehicle(self, json_data, vehicle_url, mode):

		vin = json_data['vin']
		try:
			stock = json_data['stockNumber']
		except:
			stock = json_data.get('stockNum', '')

		v_type = mode.title()
		year = json_data['year']
		make = json_data['brand']

		try:
			model = json_data['model']['modelDescription']
		except:
			model = json_data['model']['marketingName']

		trim = ''
		try:
			ext_color = json_data['extColor']['marketingName'].replace('[extra_cost_color]', '').strip()
		except:
			ext_color = ''

		ispresold = json_data['isPreSold']
		istempvin = json_data['isTempVin']

		status = 'In-Stock'

		if ispresold:
			input('presold')

		if istempvin:
			status = 'Transit'
		
		price = json_data['price']['sellingPrice']
		body = json_data.get('bodyStyle', '')
		try:
			fuel_type = json_data['engine']['fuelType']
		except:
			fuel_type = ''

		if 'unknown' == fuel_type.lower():
			fuel_type = ''

		msrp = int(json_data['price']['totalMsrp'])

		if not msrp:
			msrp = ''

		date_in_stock = json_data.get('acquiredDate', '')
		street_addr = '10011 Spencer Road'
		locality = 'St Peters'
		postal_code = '63376'
		region = 'MO'
		country = 'US'
		location = 'Pappas Toyota'

		soup = self.interface.get_selenium_response(vehicle_url)

		count = 0
		trim = ''

		# while 1:

		# 	soup = self.interface.make_soup()

		# 	try:
		# 		trim = soup.find('input', {'name':'gform_field_values'})['value'].split('&trim=')[1].split('&')[0]
		# 		break
		# 	except Exception as error:
		# 		print('trim not yet loaded...')

		# 	if "We’re working to keep your website experience safe and secure" not in soup.text.strip():
		# 		count += 1

		# 	# print(self.interface.current_url())
		# 	if self.interface.current_url() == 'https://www.pappastoyota.com/':
		# 		return True

		# 	try:
		# 		name = soup.find('div', class_='vdp-title__vehicle-info').h1.text.strip()
		# 		break
		# 	except:
		# 		pass

		# 	if count >= 10:
		# 		break

		# 	time.sleep(1)

		# trim = trim.replace('+', ' ').strip()
		
		if trim:
			model = model.lower().replace(f' {trim}'.lower(), '').strip().title()

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
		headers = {
			'accept': 'application/json, text/plain, */*',
			'accept-language': 'en-US,en;q=0.9',
			'cookie': self.cookie,
			'priority': 'u=1, i',
			'referer': 'https://smartpath.pappastoyota.com/inventory/search?dealerCd=24036&source=t3&zipcode=63376&type=used',
			'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
			'sec-ch-ua-mobile': '?0',
			'sec-ch-ua-platform': '"Linux"',
			'sec-fetch-dest': 'empty',
			'sec-fetch-mode': 'cors',
			'sec-fetch-site': 'same-origin',
			'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
		}

		while 1:
			try:
				response = requests.request("GET", url, headers=headers, data=payload)
				return response.json()

			except Exception as error:
				print('error in getting vehicles: ', error)

			time.sleep(1)

	def get_cookie(self, mode):

		self.interface.get_selenium_response('https://smartpath.pappastoyota.com/inventory/search?dealerCd=24036&source=t3&zipcode=%5B%5D&type=used')

		if 0:

			logs = self.interface.process_browser_logs_for_network_events()

			self.cookie = logs['cookie']

		else:

			cookies = self.interface.driver.get_cookies()
			cookie = []

			for _cookie in cookies:

				_key = _cookie['name']
				_value = _cookie['value']

				if _key == '_dd_s':
					_value = _value.split('&created=')[0]

				cookie.append(f'{_key}={_value}')

			cookie = '; '.join(cookie)

			self.cookie = cookie
			
	def start_scraping_pappastoyota(self):

		processed_json_file = self.log_folder + 'vehicles_processed.json'
		processed_json_data = self.helper.json_exist_data(processed_json_file)

		for mode in ['new', 'used']:

			page_num = 1

			while 1:

				self.get_cookie(mode)

				if mode == 'used':
					url = f'https://smartpath.pappastoyota.com/consumerapi/retail/inventory?dealer[]=24036&zipCode=63376&region=23&pageNo='
					url += f'{page_num}&pageSize=15&leadid=0461a12a-7c1c-4a5e-a5f1-3b25379bf204&includeInvPooling=true&brand=T&type=used'
				else:
					url = f'https://smartpath.pappastoyota.com/consumerapi/retail/inventory?dealer[]=24036&zipCode=63376&region=23&pageNo='
					url += f'{page_num}&pageSize=15&leadid=0461a12a-7c1c-4a5e-a5f1-3b25379bf204&includeInvPooling=true&brand=T&type=new&sort[]=dealerCategory%20desc,price.sellingPrice%20asc,vin%20desc'

				json_data = self.get_all_vehicles(url)

				# self.helper.write_json_file(json_data, 'json_data.json')

				total_vehicles = json_data['pagination']['totalRecords']
				total_pages = json_data['pagination']['totalPages']
				all_vehicles = json_data['vehicleSummary']

				print(page_num, ' : ', len(all_vehicles), ' : ', total_vehicles, ' : ', total_pages)

				for index, vehicle in enumerate(all_vehicles):

					vehicle_vin = vehicle['vin'].lower()

					# vehicle_url = f'https://smartpath.pappastoyota.com/inventory/details?dealerCd=24036&vin={vehicle_vin}&source=t3&zipcode=63376&type={mode}'
					vehicle_url = f'https://www.pappastoyota.com/inventory/{vehicle_vin}/'

					print(page_num, ' : ', len(all_vehicles), ' : ', vehicle_url)


					if vehicle_url not in processed_json_data:

						self.processing_each_vehicle(vehicle, vehicle_url, mode)

						processed_json_data.append(vehicle_url)
						self.helper.write_json_file(processed_json_data, processed_json_file)
						
					else:
						print('Vehicle Already Processed...')

					print('-'*50)
					print()

				if page_num >= total_pages or len(all_vehicles) < 15:
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