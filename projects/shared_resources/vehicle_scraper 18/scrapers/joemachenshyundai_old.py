from . helper_class import *
from urllib.parse import unquote

class JOEMACHENSHYUNDAI():

	def __init__(self, data_folder, output_file):

		self.helper = Helper()
		
		self.data_folder = data_folder
		self.output_file = output_file
		self.log_folder = self.helper.checking_folder_existence(f'{self.data_folder}log/')

	
	def processing_each_vehicle(self, vehicle_data):

		json_data = vehicle_data['data-params']
		json_data = unquote(json_data)

		vin = json_data.split('vin:')[1].split(';')[0]
		stock = json_data.split('stockNumber:')[1].split(';')[0]
		v_type = json_data.split('category:')[1].split(';')[0].title()
		year = json_data.split('year:')[1].split(';')[0]
		make = json_data.split('make:')[1].split(';')[0]
		model = json_data.split('model:')[1].split(';')[0]
		trim = json_data.split('trim:')[1].split(';')[0]
		ext_color = json_data.split('exteriorColor:')[1].split(';')[0]
		status = json_data.split('inventoryStatus:')[1].split(';')[0]

		try:
			price = int(json_data.split('salePrice:')[1].split(';')[0].replace('%24', '').replace('%2C', ''))
		except:
			price = ''

		body = json_data.split('bodyType:')[1].split(';')[0]
		fuel_type = json_data.split('fuelType:')[1].split(';')[0]

		try:
			msrp = int(json_data.split('msrp:')[1].split(';')[0].replace('%24', '').replace('%2C', ''))
		except:
			try:
				msrp = int(json_data.split('featuredPrice:')[1].split(';')[0].replace('%24', '').replace('%2C', ''))
			except:
				msrp = ''

		if not msrp or msrp == price:
			msrp = ''


		date_in_stock = ''
		street_addr = '1300 Vandiver Dr'
		locality = 'Columbia'
		postal_code = '65202'
		region = 'MO'
		country = 'US'
		location = 'Joe Machens Hyundai'
		vehicle_url = vehicle_data.h3.a['href']

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

		offset = 100 * (page_num - 1)

		print('Getting Vehicles: ', page_num, ' : ', offset)

		url = "https://www.joemachenshyundai.com/VehicleSearchResults?configCtx=%7B%22webId%22%3A%22hyun-joemachens%22%2C%22locale%22%3A%22en_US%22%2C%22version%22%3A%22LIVE%22%2C%22page%22%3A%22VehicleSearchResults%22%2C%22secureSiteId%22%3Anull%7D&fragmentId=view%2Fcard%2Fce07e0af-cf8e-4a7e-942a-5fcc70a17b87&search=new%2Cpreowned%2Ccertified&location=hyun-joemachens&"
		url += f"limit=100&offset={offset}&page={page_num}&forceOrigin=true"

		payload = {}
		headers = {}

		while 1:
			try:
				response = requests.request("GET", url, headers=headers, data=payload)
				return BeautifulSoup(response.text, 'html.parser')

			except Exception as error:
				print('error in getting vehicles: ', error)

			time.sleep(1)

			
	def start_scraping_joemachenshyundai(self):

		processed_json_file = self.log_folder + 'vehicles_processed.json'
		processed_json_data = self.helper.json_exist_data(processed_json_file)

		page_num = 1

		while 1:

			soup = self.get_all_vehicles(page_num)

			total_vehicles = int(soup.find('span', class_='total-result-count').text.strip().split()[0])
			total_pages = int(soup.find('wc-pagination')['totalpages'])
			all_vehicles = soup.find('div', {'if':'cards'}).find_all('wc-vehicle-card', {'data-origin-name':'VehicleProductItem'})

			print(page_num, ' : ', len(all_vehicles), ' : ', total_vehicles, ' : ', total_pages)

			for index, vehicle in enumerate(all_vehicles):

				name = vehicle.find('img', class_='product-image')['alt']
				vehicle_url = vehicle.h3.a['href']

				print(page_num, ' : ', len(all_vehicles), ' : ', name, ' : ', vehicle_url)

				if vehicle_url not in processed_json_data:

					self.processing_each_vehicle(vehicle)

					processed_json_data.append(vehicle_url)
					self.helper.write_json_file(processed_json_data, processed_json_file)
					
				else:
					print('Vehicle Already Processed...')

				print('-'*50)
				print()

			if page_num >= total_pages or len(all_vehicles) < 100:
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