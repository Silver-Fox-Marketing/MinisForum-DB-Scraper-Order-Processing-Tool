from . helper_class import *
from urllib.parse import unquote

class PORSCHESTLOUIS():

	def __init__(self, data_folder, output_file):

		self.helper = Helper()
		
		self.data_folder = data_folder
		self.output_file = output_file
		self.log_folder = self.helper.checking_folder_existence(f'{self.data_folder}log/')

	
	def processing_each_vehicle(self, vehicle_url):

		soup = self.get_all_vehicles(vehicle_url)

		json_data = soup.find('div', class_='vdp vdp--mod')

		vin = json_data['data-vin']
		stock = json_data['data-dotagging-item-number']
		v_type = json_data['data-vehicletype'].title()

		data_cpo = json_data['data-cpo']

		if v_type == 'Used' and data_cpo == 'True':
			v_type = 'Certified Pre-Owned'
			
		year = json_data['data-year']
		make = json_data['data-make']
		model = json_data['data-model']
		trim = json_data['data-trim']
		ext_color = json_data['data-extcolor']
		status = json_data['data-intransit']

		if status == 'False':
			status = 'In Stock'
		else:
			status = 'In Transit'

		price = json_data['data-price']

		body = json_data['data-bodystyle']
		fuel_type = json_data['data-dotagging-item-fuel-type']

		msrp = ''


		date_in_stock = json_data['data-dotagging-item-inventory-date']
		street_addr = '2970 South Hanley Rd'
		locality = 'St. Louis'
		postal_code = '63143'
		region = 'MO'
		country = 'US'
		location = 'Porsche St. Louis'

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
		headers = {}

		while 1:
			try:
				response = requests.request("GET", url, headers=headers, data=payload)
				return BeautifulSoup(response.text, 'html.parser')

			except Exception as error:
				print('error in getting vehicles: ', error)

			time.sleep(1)

			
	def start_scraping_porschestlouis(self):

		processed_json_file = self.log_folder + 'vehicles_processed.json'
		processed_json_data = self.helper.json_exist_data(processed_json_file)

		for mode in ['searchnew', 'searchused']:

			page_num = 1

			while 1:

				current_url = f'https://www.porschestlouis.com/{mode}.aspx?pt={page_num}'

				soup = self.get_all_vehicles(current_url)

				try:
					json_data = soup.find('script', id='dlron-srp-model').string.strip()
					json_data = json.loads(' '.join(json_data.split()))
				except:
					break
					
				all_vehicles = json.loads(json_data['ItemListJson'])['itemListElement']

				total_vehicles = json_data['SearchResultsListModel']['ResultsCount']
				total_pages = (total_vehicles // 12) + 1
	
				print(page_num, ' : ', len(all_vehicles), ' : ', total_vehicles, ' : ', total_pages)

				for index, vehicle in enumerate(all_vehicles):

					name = vehicle['name']
					vehicle_url = vehicle['url']

					print(page_num, ' : ', len(all_vehicles), ' : ', name, ' : ', vehicle_url)

					if vehicle_url not in processed_json_data:

						count = 0
						while 1:

							try:
								self.processing_each_vehicle(vehicle_url)
								break
							except Exception as error:
								print('Getting New URL: ', error)

							count += 1

							if count >= 3:
								break
								
							time.sleep(3)

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