from . helper_class import *

class JOEMACHENSNISSAN():

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
		status = json_data.get('intransit_filter', '')
		price = json_data['our_price']
		body = json_data['body']
		fuel_type = json_data['fueltype']
		msrp = int(json_data['msrp'])

		if not msrp:
			msrp = ''

		date_in_stock = json_data['date_in_stock']
		street_addr = '201 Nebraska Ave'
		locality = 'Columbia'
		postal_code = '65203'
		region = 'MO'
		country = 'US'
		location = 'Joe Machens Nissan'
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

	def get_all_vehicles(self, page_num, mode, filter_mode):

		print('Getting Vehicles: ', page_num)

		url = "https://2591j46p8g-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.9.1)%3B%20Browser%20(lite)%3B%20JS%20Helper%20(3.4.4)&x-algolia-api-key=78311e75e16dd6273d6b00cd6c21db3c&x-algolia-application-id=2591J46P8G"

		if mode == 'used':
			payload = json.dumps({"requests": [{
				"indexName": "joemachensnissan-winback1023_production_inventory_days_in_stock_high_to_low",
				"params": f"maxValuesPerFacet=250&hitsPerPage=20&page={page_num}&facets=%5B%22features%22%2C%22our_price%22%2C%22lightning.lease_monthly_payment%22%2C%22lightning.finance_monthly_payment%22%2C%22type%22%2C%22api_id%22%2C%22year%22%2C%22make%22%2C%22model%22%2C%22model_number%22%2C%22trim%22%2C%22body%22%2C%22doors%22%2C%22miles%22%2C%22ext_color_generic%22%2C%22features%22%2C%22lightning.isSpecial%22%2C%22lightning.locations%22%2C%22Location%22%2C%22in_transit_filter%22%2C%22lightning.status%22%2C%22lightning.class%22%2C%22fueltype%22%2C%22bedtype%22%2C%22engine_description%22%2C%22transmission_description%22%2C%22metal_flags%22%2C%22city_mpg%22%2C%22hw_mpg%22%2C%22days_in_stock%22%2C%22date_in_stock%22%2C%22ford_SpecialVehicle%22%2C%22lightning.locations.meta_location%22%2C%22intransit_filter%22%2C%22location%22%2C%22special_field_1%22%2C%22title_vrp%22%2C%22ext_color%22%2C%22int_color%22%2C%22certified%22%2C%22lightning%22%2C%22drivetrain%22%2C%22int_options%22%2C%22ext_options%22%2C%22cylinders%22%2C%22vin%22%2C%22stock%22%2C%22msrp%22%2C%22our_price_label%22%2C%22finance_details%22%2C%22lease_details%22%2C%22thumbnail%22%2C%22link%22%2C%22objectID%22%2C%22algolia_sort_order%22%2C%22date_modified%22%2C%22hash%22%2C%22monroneyLabel%22%5D&tagFilters=&facetFilters=%5B%5B%22location%3AJoe%20Machens%20Nissan%22%5D%2C%5B%22type%3ANew%22%2C%22type%3ACertified%20Used%22%2C%22type%3AUsed%22%5D%5D"
			}, {
			"indexName": "joemachensnissan-winback1023_production_inventory_days_in_stock_high_to_low",
			"params": "maxValuesPerFacet=250&hitsPerPage=1&page=0&attributesToRetrieve=%5B%5D&attributesToHighlight=%5B%5D&attributesToSnippet=%5B%5D&tagFilters=&analytics=false&clickAnalytics=false&facets=location&facetFilters=%5B%5B%22type%3ANew%22%2C%22type%3ACertified%20Used%22%2C%22type%3AUsed%22%5D%5D"
			}, {
			"indexName": "joemachensnissan-winback1023_production_inventory_days_in_stock_high_to_low",
			"params": "maxValuesPerFacet=250&hitsPerPage=1&page=0&attributesToRetrieve=%5B%5D&attributesToHighlight=%5B%5D&attributesToSnippet=%5B%5D&tagFilters=&analytics=false&clickAnalytics=false&facets=type&facetFilters=%5B%5B%22location%3AJoe%20Machens%20Nissan%22%5D%5D"
			} ] })

		else:
			payload = json.dumps({
				"requests": [
			{
				"indexName": "joemachensnissan-winback1023_production_inventory_days_in_stock_high_to_low",
				"params": f"maxValuesPerFacet=250&hitsPerPage=20&page={page_num}&facets=%5B%22features%22%2C%22our_price%22%2C%22lightning.lease_monthly_payment%22%2C%22lightning.finance_monthly_payment%22%2C%22type%22%2C%22api_id%22%2C%22year%22%2C%22make%22%2C%22model%22%2C%22model_number%22%2C%22trim%22%2C%22body%22%2C%22doors%22%2C%22miles%22%2C%22ext_color_generic%22%2C%22features%22%2C%22lightning.isSpecial%22%2C%22lightning.locations%22%2C%22Location%22%2C%22in_transit_filter%22%2C%22lightning.status%22%2C%22lightning.class%22%2C%22fueltype%22%2C%22bedtype%22%2C%22engine_description%22%2C%22transmission_description%22%2C%22metal_flags%22%2C%22city_mpg%22%2C%22hw_mpg%22%2C%22days_in_stock%22%2C%22date_in_stock%22%2C%22ford_SpecialVehicle%22%2C%22lightning.isPolice%22%2C%22lightning.locations.meta_location%22%2C%22intransit_filter%22%2C%22location%22%2C%22special_field_1%22%2C%22title_vrp%22%2C%22ext_color%22%2C%22int_color%22%2C%22certified%22%2C%22lightning%22%2C%22drivetrain%22%2C%22int_options%22%2C%22ext_options%22%2C%22cylinders%22%2C%22vin%22%2C%22stock%22%2C%22msrp%22%2C%22our_price_label%22%2C%22finance_details%22%2C%22lease_details%22%2C%22thumbnail%22%2C%22link%22%2C%22objectID%22%2C%22algolia_sort_order%22%2C%22date_modified%22%2C%22hash%22%2C%22monroneyLabel%22%5D&tagFilters=&facetFilters=%5B%5B%22type%3ANew%22%5D%2C%5B%22intransit_filter%3A{filter_mode}%22%5D%5D"
			},
			{
				"indexName": "joemachensnissan-winback1023_production_inventory_days_in_stock_high_to_low",
				"params": f"maxValuesPerFacet=250&hitsPerPage=1&page=0&attributesToRetrieve=%5B%5D&attributesToHighlight=%5B%5D&attributesToSnippet=%5B%5D&tagFilters=&analytics=false&clickAnalytics=false&facets=type&facetFilters=%5B%5B%22intransit_filter%3A{filter_mode}%22%5D%5D"
			},
			{
				"indexName": "joemachensnissan-winback1023_production_inventory_days_in_stock_high_to_low",
				"params": "maxValuesPerFacet=250&hitsPerPage=1&page=0&attributesToRetrieve=%5B%5D&attributesToHighlight=%5B%5D&attributesToSnippet=%5B%5D&tagFilters=&analytics=false&clickAnalytics=false&facets=intransit_filter&facetFilters=%5B%5B%22type%3ANew%22%5D%5D"
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

			
	def start_scraping_joemachensnissan(self):

		processed_json_file = self.log_folder + 'vehicles_processed.json'
		processed_json_data = self.helper.json_exist_data(processed_json_file)

		for mode in ['used', 'new']:

			for filter_mode in ['On-Lot', 'In-Transit']:

				if mode == 'used' and filter_mode == 'In-Transit':
					continue

				page_num = 0

				while 1:

					json_data = self.get_all_vehicles(page_num, mode, filter_mode)['results'][0]

					# self.helper.write_json_file(json_data, 'json_data.json')

					total_vehicles = json_data['nbHits']
					total_pages = json_data['nbPages']
					all_vehicles = json_data['hits']

					print(page_num, ' : ', len(all_vehicles), ' : ', total_vehicles, ' : ', total_pages)


					for index, vehicle in enumerate(all_vehicles):

						name = vehicle['title_vrp']
						vehicle_url = vehicle['link']

						print(page_num, ' : ', len(all_vehicles), ' : ', name, ' : ', vehicle_url)


						if vehicle_url not in processed_json_data:

							self.processing_each_vehicle(vehicle)

							processed_json_data.append(vehicle_url)
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