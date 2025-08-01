from . helper_class import *
from . interface_class import *

class TWINCITYTOYOTA():

	def __init__(self, data_folder, output_file):

		self.helper = Helper()

		self.interface = INTERFACING()
		
		self.data_folder = data_folder
		self.output_file = output_file
		self.log_folder = self.helper.checking_folder_existence(f'{self.data_folder}log/')

		self.cookie = ''

	def click_buttons(self):

		try:
			self.interface.clicking('//button[@aria-label="Allow all cookies"]')
		except:
			pass

		try:
			self.interface.clicking('//div[@data-testid="close-modal"]')
		except:
			pass

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
			ext_color = json_data['extColor']['marketingName']
		except:
			ext_color = ''

		status = ''
		try:
			price = int(json_data['price']['sellingPrice'])
		except:
			price = ''

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
		street_addr = '301 Autumn Ridge Drive'
		locality = 'Herculaneum'
		postal_code = '63048'
		region = 'MO'
		country = 'US'
		location = 'Twin City Toyota'

		self.interface.get_selenium_response('https://www.twincitytoyota.com/')

		while 1:
			try:
				self.interface.entering_values('//*[@id="s_search"]', vin)
				break
			except Exception as error:
				print('Error in entering VIN: ', error)

			self.click_buttons()
			time.sleep(1)

		count = 0

		while 1:

			soup = self.interface.make_soup()

			try:
				vehicle_url = 'https://www.twincitytoyota.com' + soup.find('div', id=re.compile('result_type_i_')).find('li', class_=re.compile('result')).a['href']
				break
			except Exception as error:
				# print('Vehicle URL not yet loaded: ', error)
				pass

			self.click_buttons()

			count += 1

			if count >= 3:
				return True

			time.sleep(2)

		soup = self.interface.get_selenium_response(vehicle_url)

		try:
			trim = soup.find('div', string='Trim').find_next_sibling('div').text.strip()
		except:
			trim = ''

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

	def get_cookie(self):

		self.interface.get_selenium_response('https://smartpath.twincitytoyota.com/inventory/search?dealerCd=24067&source=t3&zipcode=63048&type=used')

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
			
	def start_scraping_twincitytoyota(self):

		processed_json_file = self.log_folder + 'vehicles_processed.json'
		processed_json_data = self.helper.json_exist_data(processed_json_file)

		for mode in ['used', 'new']:

			page_num = 1

			while 1:

				self.get_cookie()

				if mode == 'used':
					url = f'https://smartpath.twincitytoyota.com/consumerapi/retail/inventory?dealer[]=24067&zipCode=63048&region=23&pageNo='
					url += f'{page_num}&pageSize=15&leadid=6b4c4c09-4d21-449d-9380-a5de9e565fc0&includeInvPooling=true&brand=T&type=used'
				else:
					url = 'https://smartpath.twincitytoyota.com/consumerapi/retail/inventory?dealer[]=24067&zipCode=63048&region=23&pageNo='
					url += f'{page_num}&pageSize=15&leadid=6b4c4c09-4d21-449d-9380-a5de9e565fc0&includeInvPooling=true&brand=T&type=new&sort[]=dealerCategory%20desc,price.sellingPrice%20asc,vin%20desc'

				json_data = self.get_all_vehicles(url)

				# self.helper.write_json_file(json_data, 'json_data.json')

				total_vehicles = json_data['pagination']['totalRecords']
				total_pages = json_data['pagination']['totalPages']
				all_vehicles = json_data['vehicleSummary']

				print(page_num, ' : ', len(all_vehicles), ' : ', total_vehicles, ' : ', total_pages)

				for index, vehicle in enumerate(all_vehicles):

					vehicle_vin = vehicle['vin']

					vehicle_url = f'https://smartpath.twincitytoyota.com/inventory/details?dealerCd=24067&vin={vehicle_vin}&source=t3&zipcode=63048&type={mode}'
					# vehicle_url = f'https://www.twincitytoyota.com/inventory/{vehicle_vin}/'

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