from . helper_class import *
from . interface_class import *

class COLUMBIABMW():

	def __init__(self, data_folder, output_file):

		self.helper = Helper()

		self.interface = INTERFACING()
		
		self.data_folder = data_folder
		self.output_file = output_file
		self.log_folder = self.helper.checking_folder_existence(f'{self.data_folder}log/')

		self.cookie = ''
	
	def processing_each_vehicle(self, json_data, vehicle_url, mode):

		# self.helper.write_json_file(json_data, 'json_data.json')

		address_to_check = json_data['address']['accountName'].lower()

		if 'bmw of columbia' not in address_to_check:
			return False

		vin = json_data['vin']
		stock = json_data.get('stockNumber', '')
		v_type = json_data.get('inventoryType', '').title()
		year = json_data['year']
		make = json_data['make']
		model = json_data.get('model', '')
		trim = json_data.get('trim', '')
		ext_color = json_data.get('exteriorColor', '')
		body = json_data.get('bodyStyle', '')
		fuel_type = json_data.get('fuelType', '')

		try:
			msrp = int(json_data['pricing']['msrp'].replace('$', '').replace(',', '').split('.')[0])
		except:
			msrp = ''

		try:
			price = int(json_data['pricing']['finalPrice'].replace('$', '').replace(',', '').split('.')[0])
		except:
			price = ''

		status = json_data.get('status', '')

		if status == 'live':
			status = 'On-Lot'
		elif status in ['in_transit', 'in_transit_at_factory']:
			status = 'In Transit'
		else:
			status = ''


		date_in_stock = json_data.get('inventoryDate', '')
		street_addr = '1900 I-70 Drive Southwest'
		locality = 'Columbia'
		postal_code = '65203'
		region = 'MO'
		country = 'US'
		location = 'BMW of Columbia'

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
			'accept': '*/*',
			'accept-language': 'en-US,en;q=0.9',
			'cookie' : 'DDC.postalCode=; locale=en_US; ddc_diag_akam_clientIP=211.192.45.144; ddc_diag_akam_ghostIP=23.32.241.73; DDC.postalCityState=SEOUL%2C%20%2C%20KR; DDC.userCoordinates=37.57%2C127.00; activeSession=true; __ssoid=c6388e4540394a92bf8e9efa396e7ad0; optimizelyEndUserId=oeu1727223585617r0.782217936385946; AKA_A2=A; callTrackingSessionId=tyqxib8imvgm1h4bsib; pxa_id=hD1wu26zatynKmnib22080eI; _gid=GA1.2.98685282.1727223587; _gtm_group=false; pxa_ipv4=211.192.45.144; pixall_cookie_sync=true; _ga_last=GA1.1.1612803538.1727223587; fullthrottlelims_t2=3243883256; r=1; __ggtruid=1727223588739.dcb34d0c-dd4c-9fff-54d1-9bf55c258218; __ggtrses=1; ddc_abcg_cache=; ddc_abcamm_cache=; ddc_abcc_cache=; ddc_abc_cache=hD1wu26zatynKmnib22080eI; ak_bmsc=EF4FACCC56749E3C7651CE2F1D7C0F1B~000000000000000000000000000000~YAAQRfEgF8qZ/hCSAQAA+2eMJhlT7U31j18zVAAmy68udzFha7kU+8fZnZQ9PDk9jy8k7qEMrthJFlmorv6PpGcKnyAU8iqlAGxU6B1O698EIEZvDbLS8RxYWrCtJO3bHD42rQQEy6DSIINlCpN9Yra3UsWPeB/+RhjJcnW500h3FEY9j90nhOHHA5sSmpthUSyHBxA0lpUcT4DxYejuuYA0R10Xy6qNZgn9/+BW4gMHsuYrEWRZfBwM1DEbIXsRAW3mcGslUnEs+kjLBRSvIyWUfgdfuNWFzX/WvX7MjAag93ABpIeESH/AcG69GD/H0m4DD+UVr+Pe3GnSYdzkowUDahN9jMIpzlWXQa4cFsfIpQlB4iMP6lzYlr6LuLkaomOCyIQEsblMf1Mg+Npt37sfBqwNo7ob2d8C9d0CkP7UAd52Cttz9tyEPW9bNiS+Q4hTaGMsSZo4vUahl4ZeTIkmPaHp2LpsewoJ; AMCVS_3ECF483F53AB366E0A490D44%40AdobeOrg=1; s_cc=true; AMCV_3ECF483F53AB366E0A490D44%40AdobeOrg=179643557%7CMCIDTS%7C19992%7CMCMID%7C49550426469522434744425719959598255091%7CMCAAMLH-1727828389%7C11%7CMCAAMB-1727828389%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1727230790s%7CNONE%7CMCSYNCSOP%7C411-19999%7CMCAID%7CNONE%7CvVersion%7C5.5.0; __td_signed=true; s_vnc365=1758759590808%26vn%3D1; s_ivc=true; vlVisitCreatedUtc=Wed, 25 Sep 2024 12:19:52 GMT; lmc=15231.1727223592914.4293; _sda:stellantis:T3:user=76f15604-70dd-4310-939b-b75a3468f4e2%3A4.0%3A1727223591038%3Ai88agpppiqbn!090ae554424e743f7b00f344c56420e0!10u8a58ipzrfz!%3A67776!67776!67776!; _aeaid=9f9d80b6-6c63-4ec6-a30f-444789a89247; aelastsite=IllFlU%2B4MdM%2BAOebqJ4ybr8U4%2FCNGO%2BORgLZxdLPqPqVdAGf8JB9TqmFC7dWP34Q; aelreadersettings=%7B%22c_big%22%3A0%2C%22rg%22%3A0%2C%22memph%22%3A0%2C%22contrast_setting%22%3A0%2C%22colorshift_setting%22%3A0%2C%22text_size_setting%22%3A0%2C%22space_setting%22%3A0%2C%22font_setting%22%3A0%2C%22k%22%3A0%2C%22k_disable_default%22%3A0%2C%22hlt%22%3A0%2C%22disable_animations%22%3A0%2C%22display_alt_desc%22%3A0%7D; ddc_diag_akam_currentTime=1727223604; ddc_diag_akam_requestID=c8ec9e4; ddc_diag_akam_fullPath=/akam-sw-policy.json; abc_3rd_party=hD1wu26zatynKmnib22080eI; _ga_JREN7K6BBQ=GS1.1.1727223587.1.1.1727223609.38.0.0; _ga_LL473N0F7N=GS1.1.1727223587.1.1.1727223609.38.0.0; _ga_SB4SCXY874=GS1.1.1727223587.1.1.1727223609.0.0.0; _ga_XMRK861STD=GS1.1.1727223587.1.1.1727223610.0.0.0; nl_v_fst_w3244hmtj=1; _ga_1S7VPWMZVS=GS1.2.1727223588.1.1.1727223612.0.0.0; _ga_9METPJBKZE=GS1.2.1727223588.1.1.1727223612.0.0.0; _ga_Z566R9PNZZ=GS1.2.1727223588.1.1.1727223612.0.0.0; _ga_TZGWT6H2HN=GS1.1.1727223589.1.1.1727223619.30.0.0; _ga_RHDG9N8C8Y=GS1.1.1727223590.1.1.1727223620.0.0.0; caconsentcookie={"version":"1.0","categories":{"functional":true,"general":false,"statistics":true,"targeting":false},"updatedAt":"2024-09-25T00:20:20.602Z","expiresAt":"2025-09-25T00:20:20.602Z","consentMethod":"OPT_IN","hasInteractedWithBanner":false,"limitSensitivePersonalData":null}; bm_sv=DA48EFE17D97E77A21DC386D2090654B~YAAQRfEgF5ib/hCSAQAAMOuMJhk/jYEFjKykEpFRp9HtPqUqvkpwDGT+lkXhZMujfgDV/8KWH4R8D0ibg/8YIUaxjJ/6ixXk0soREgJKBOS1tIGPR4sV4IFkzFIlHF/s6e12mCMFuu1HJ8fFIkHT6J1U1fuMhgrzLX0tN73cK+v7v0i+4kdkb3R7NYm8JITnSCkHEgqacuUxUum015ddUcJJclPXiRprFDpEfaLpCeVYHYMgic3T/bY3F7Q3lWcaqyXSvCg/pIkSwAD3iFeQ~1; forty_n_user=v2D8JChR2AvRVUs1Qnl6QmRNUk01KzZaeTA3bllwS3FQMjlvSWQ4b2RNa003c0hyM0NtST0~; forty_n_fbuid=2c493eed215c995d91a4e5d2060beb51e47529f594a608fda3535cdc289455e9; forty_n_t=1.37ccbc.1727223590.1.2.1727223590.1727223620.4.0; aeatstartmessage=true; abc=hD1wu26zatynKmnib22080eI; _ga=GA1.2.1612803538.1727223587; _gat_UA-57199785-1=1; _ga_4BZJKD1FGT=GS1.1.1727223589.1.1.1727223784.60.0.0; _ga_MNJHV4SLES=GS1.1.1727223589.1.1.1727223784.0.0.0; _td=5d8a8be2-7229-4bf8-bebc-f276c906a5a1; _ga_Y4BVE7J3Q3=GS1.1.1727223588.1.1.1727223785.0.0.0; _ga_YYYYYYYYYY=GS1.1.1727223591.1.0.1727223785.0.0.0; _ga_730V2YYEMM=GS1.1.1727223588.1.1.1727223785.0.0.0; akaalb_pixall_prod=1727225585~op=ddc_ana_pixall_prod:eng_ana_pixall_prod-pico-us-west-2|~rv=50~m=eng_ana_pixall_prod-pico-us-west-2:0|~os=6aafa3aac97a52a58cd06655a170720e~id=77ce202294019e391e408e72a4ba5448; _ga_B6LVSEVL1T=GS1.2.1727223601.1.0.1727223789.0.0.0; _ga_1RQHBHW17C=GS1.1.1727223587.1.1.1727223789.54.0.0; s_sq=fcanaftafca.dealers.usa%252Cfcaentrp.globalreportsuite%3D%2526c.%2526a.%2526activitymap.%2526page%253Ddealer%25253Aus%25253Asearch-inventory%25253Anew-inventory%2526link%253D2%2526region%253Dinventory-paging1-app-root%2526pageIDType%253D1%2526.activitymap%2526.a%2526.c%2526pid%253Ddealer%25253Aus%25253Asearch-inventory%25253Anew-inventory%2526pidt%253D1%2526oid%253Dhttps%25253A%25252F%25252Fwww.glendalechryslerjeep.net%25252Fnew-inventory%25252Findex.htm%25253Fstart%25253D16%2526ot%253DA; _ga_DRYFC644X2=GS1.1.1727223588.1.1.1727223789.0.0.0; _sda:stellantis:T3:session=8428606c-34a3-43fd-a06d-dcdc6a64a920%3AN%3A1727225559873%3A%3Ai88agpppiqbn!090ae554424e743f7b00f344c56420e0!10u8a58ipzrfz!%3A1727223591040%3AN%3A%3ASTELLANTIS%3ADEALERDOTCOM%3A63515%3AN%3A',
			'priority': 'u=1, i',
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

	def start_scraping_columbiabmw(self):

		processed_json_file = self.log_folder + 'vehicles_processed.json'
		processed_json_data = self.helper.json_exist_data(processed_json_file)

		for mode in ['new', 'used']:

			page_num = 0

			while 1:

				if mode == 'used':
					url = f'https://www.columbiabmw.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_USED:inventory-data-bus1/getInventory?start={page_num}'
				else:
					url = f'https://www.columbiabmw.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?start={page_num}'

				json_data = self.get_all_vehicles(url)

				# self.helper.write_json_file(json_data, 'json_data.json')

				total_vehicles = json_data['pageInfo']['totalCount']
				all_vehicles = json_data['pageInfo']['trackingData']

				print(page_num, ' : ', len(all_vehicles), ' : ', total_vehicles)

				for index, vehicle in enumerate(all_vehicles):

					vehicle_url = f'https://www.columbiabmw.com' + vehicle['link']

					print(page_num, ' : ', len(all_vehicles), ' : ', vehicle_url)


					if vehicle_url not in processed_json_data:

						self.processing_each_vehicle(vehicle, vehicle_url, mode)

						processed_json_data.append(vehicle_url)
						self.helper.write_json_file(processed_json_data, processed_json_file)
						
					else:
						print('Vehicle Already Processed...')

					print('-'*50)
					print()

				if len(all_vehicles) < 18 or page_num >= total_vehicles:
					break

				page_num += 18

		self.interface.close_driver()


if __name__ == "__main__":
	handle = MAINCLASS()
	handle.start_scraping()

	print()
	print('*'*50)
	print('ALL DONE, YOU CAN CLOSE THIS CONSOLE AND CHECK THE DATA IN THE OUTPUT_DATA FOLDER.')
	print('*'*50)
	print()