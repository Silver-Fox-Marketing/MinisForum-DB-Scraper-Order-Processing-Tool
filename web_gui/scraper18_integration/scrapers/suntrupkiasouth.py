from . helper_class import *

class SUNTRUPKIASOUTH():

	def __init__(self, data_folder, output_file):

		self.helper = Helper()
		
		self.data_folder = data_folder
		self.output_file = output_file
		self.log_folder = self.helper.checking_folder_existence(f'{self.data_folder}log/')

	
	def processing_each_vehicle(self, json_data):

		vin = json_data['objectID']
		stock = json_data['stock']
		v_type = json_data['type']
		year = json_data['year']
		make = json_data['make']
		model = json_data['model']
		trim = json_data['trim']
		ext_color = json_data['ext_color']
		status = ''
		price = json_data['our_price']
		body = json_data['body']
		fuel_type = json_data.get('fueltype', '')
		msrp = int(json_data['msrp'])

		if 'please call for price' in str(price).lower():
			price = 'Please call for price'


		if not msrp:
			msrp = ''

		date_in_stock = json_data['date_in_stock']
		street_addr = '6263 S Lindbergh Blvd'
		locality = 'St. Louis'
		postal_code = '63123'
		region = 'MO'
		country = 'US'
		location = 'Suntrup Kia South'
		vehicle_url = json_data['link']

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

	def get_all_vehicles(self, page_num, mode):

		print('Getting Vehicles: ', page_num)

		url = "https://sewjn80htn-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.9.1)%3B%20Browser%20(lite)%3B%20JS%20Helper%20(3.22.4)&x-algolia-api-key=179608f32563367799314290254e3e44&x-algolia-application-id=SEWJN80HTN"


		if mode == 'used':
			payload = json.dumps({
			"requests": [
			{
				"indexName": "suntrupkiasouth_production_inventory_specials_oem_price",
				"params": f"facetFilters=%5B%5B%22Location%3ASuntrup%20Kia%20South%22%5D%2C%5B%22loaner_hide%3Atrue%22%5D%2C%5B%22type%3ACertified%20Pre-Owned%22%2C%22type%3APre-Owned%22%5D%5D&facets=%5B%22Location%22%2C%22algolia_sort_order%22%2C%22api_id%22%2C%22bedtype%22%2C%22body%22%2C%22cap_one%22%2C%22certified%22%2C%22city_mpg%22%2C%22custom_body%22%2C%22custom_loaner_feed_value%22%2C%22cylinders%22%2C%22date_in_stock%22%2C%22date_modified%22%2C%22days_in_stock%22%2C%22doors%22%2C%22drivetrain%22%2C%22engine_description%22%2C%22ext_color%22%2C%22ext_color_generic%22%2C%22ext_options%22%2C%22features%22%2C%22features%22%2C%22finance_details%22%2C%22ford_SpecialVehicle%22%2C%22fueltype%22%2C%22hash%22%2C%22hw_mpg%22%2C%22in_transit_filter%22%2C%22int_color%22%2C%22int_options%22%2C%22lease_details%22%2C%22lightning%22%2C%22lightning.class%22%2C%22lightning.finance_monthly_payment%22%2C%22lightning.isPolice%22%2C%22lightning.isSpecial%22%2C%22lightning.lease_monthly_payment%22%2C%22lightning.locations%22%2C%22lightning.locations.meta_location%22%2C%22lightning.status%22%2C%22link%22%2C%22loaner_hide%22%2C%22location%22%2C%22make%22%2C%22metal_flags%22%2C%22miles%22%2C%22model%22%2C%22model_number%22%2C%22msrp%22%2C%22objectID%22%2C%22our_price%22%2C%22our_price_label%22%2C%22special_field_1%22%2C%22stock%22%2C%22thumbnail%22%2C%22title_vrp%22%2C%22transmission_description%22%2C%22trim%22%2C%22type%22%2C%22vin%22%2C%22year%22%5D&hitsPerPage=20&maxValuesPerFacet=250&page={page_num}"
			}, {
				"indexName": "suntrupkiasouth_production_inventory_specials_oem_price",
				"params": "analytics=false&clickAnalytics=false&facetFilters=%5B%5B%22loaner_hide%3Atrue%22%5D%2C%5B%22type%3ACertified%20Pre-Owned%22%2C%22type%3APre-Owned%22%5D%5D&facets=Location&hitsPerPage=0&maxValuesPerFacet=250&page=0"
			}, {
				"indexName": "suntrupkiasouth_production_inventory_specials_oem_price",
				"params": "analytics=false&clickAnalytics=false&facetFilters=%5B%5B%22Location%3ASuntrup%20Kia%20South%22%5D%2C%5B%22type%3ACertified%20Pre-Owned%22%2C%22type%3APre-Owned%22%5D%5D&facets=loaner_hide&hitsPerPage=0&maxValuesPerFacet=250&page=0"
			}, {
				"indexName": "suntrupkiasouth_production_inventory_specials_oem_price",
				"params": "analytics=false&clickAnalytics=false&facetFilters=%5B%5B%22Location%3ASuntrup%20Kia%20South%22%5D%2C%5B%22loaner_hide%3Atrue%22%5D%5D&facets=type&hitsPerPage=0&maxValuesPerFacet=250&page=0"
			} ] })

		else:

			payload = json.dumps({
			"requests": [
			{
				"indexName": "suntrupkiasouth_production_inventory_specials_oem_price",
				"params": f"facetFilters=%5B%5B%22type%3ANew%22%5D%5D&facets=%5B%22Location%22%2C%22algolia_sort_order%22%2C%22api_id%22%2C%22bedtype%22%2C%22body%22%2C%22cap_one%22%2C%22certified%22%2C%22city_mpg%22%2C%22custom_body%22%2C%22custom_loaner_feed_value%22%2C%22cylinders%22%2C%22date_in_stock%22%2C%22date_modified%22%2C%22days_in_stock%22%2C%22doors%22%2C%22drivetrain%22%2C%22engine_description%22%2C%22ext_color%22%2C%22ext_color_generic%22%2C%22ext_options%22%2C%22features%22%2C%22features%22%2C%22finance_details%22%2C%22ford_SpecialVehicle%22%2C%22fueltype%22%2C%22hash%22%2C%22hw_mpg%22%2C%22in_transit_filter%22%2C%22int_color%22%2C%22int_options%22%2C%22lease_details%22%2C%22lightning%22%2C%22lightning.class%22%2C%22lightning.finance_monthly_payment%22%2C%22lightning.isPolice%22%2C%22lightning.isSpecial%22%2C%22lightning.lease_monthly_payment%22%2C%22lightning.locations%22%2C%22lightning.locations.meta_location%22%2C%22lightning.status%22%2C%22link%22%2C%22loaner_hide%22%2C%22location%22%2C%22make%22%2C%22metal_flags%22%2C%22miles%22%2C%22model%22%2C%22model_number%22%2C%22msrp%22%2C%22objectID%22%2C%22our_price%22%2C%22our_price_label%22%2C%22special_field_1%22%2C%22stock%22%2C%22thumbnail%22%2C%22title_vrp%22%2C%22transmission_description%22%2C%22trim%22%2C%22type%22%2C%22vin%22%2C%22year%22%5D&hitsPerPage=20&maxValuesPerFacet=250&page={page_num}"
			}, {
				"indexName": "suntrupkiasouth_production_inventory_specials_oem_price",
				"params": "analytics=false&clickAnalytics=false&facets=type&hitsPerPage=0&maxValuesPerFacet=250&page=0"
			} ] })

		headers = {
			'Content-Type': 'application/json'
		}

		while 1:
			try:
				response = requests.request("POST", url, headers=headers, data=payload)
				return response.json()

			except Exception as error:
				print('error in getting vehicles: ', error)

			time.sleep(1)

			
	def start_scraping_suntrupkiasouth(self):

		processed_json_file = self.log_folder + 'vehicles_processed.json'
		processed_json_data = self.helper.json_exist_data(processed_json_file)

		for mode in ['used', 'new']:

			page_num = 0

			while 1:

				json_data = self.get_all_vehicles(page_num, mode)['results'][0]

				total_vehicles = json_data['nbHits']
				total_pages = json_data['nbPages']
				all_vehicles = json_data['hits']

				print(page_num, ' : ', len(all_vehicles), ' : ', total_vehicles, ' : ', total_pages)

				for index, vehicle in enumerate(all_vehicles):

					name = vehicle['title_vrp']
					vehicle_url = vehicle['link']

					print(page_num, ' : ', len(all_vehicles), ' : ', name, ' : ', vehicle_url)

					vehicle_unique = f'{vehicle_url}_kiasouth'


					if vehicle_unique not in processed_json_data:

						self.processing_each_vehicle(vehicle)

						processed_json_data.append(vehicle_unique)
						self.helper.write_json_file(processed_json_data, processed_json_file)
						
					else:
						print('Vehicle Already Processed...')

					print('-'*50)
					print()

				if page_num >= total_pages:
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