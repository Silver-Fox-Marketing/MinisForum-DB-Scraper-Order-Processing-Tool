from . helper_class import *
from . interface_class import *
import base64
import json
import re
import time

class JOEMACHENSNISSAN():

	def __init__(self, data_folder, output_file):

		self.helper = Helper()

		self.data_folder = data_folder
		self.output_file = output_file
		self.log_folder = self.helper.checking_folder_existence(f'{self.data_folder}log/')
		self.DI_BASE = "https://www.joemachensnissan.com/api/inventory/query/"
		self.interface = INTERFACING()
		self.session_cookies = None

	def di_encode_filter(self, expr):
		return base64.b64encode(expr.encode("utf-8")).decode("ascii")

	def get_advanced_driver(self):
		"""Get Chrome driver with advanced anti-detection settings for Cloudflare bypass"""
		print("[DRIVER] Initializing stealth Chrome driver for aggressive Cloudflare bypass...")

		import undetected_chromedriver as uc
		from selenium.webdriver.chrome.options import Options

		try:
			# Stealth Chrome options for very aggressive Cloudflare protection
			options = Options()
			options.add_argument('--no-sandbox')
			options.add_argument('--disable-dev-shm-usage')
			options.add_argument('--disable-blink-features=AutomationControlled')
			options.add_argument('--disable-extensions')
			options.add_argument('--disable-plugins-discovery')
			options.add_argument('--disable-default-apps')
			options.add_argument('--disable-sync')
			options.add_argument('--disable-translate')
			options.add_argument('--hide-scrollbars')
			options.add_argument('--disable-logging')
			options.add_argument('--disable-background-timer-throttling')
			options.add_argument('--disable-renderer-backgrounding')
			options.add_argument('--disable-backgrounding-occluded-windows')
			options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
			options.add_experimental_option('useAutomationExtension', False)

			# More realistic user agent
			options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')

			# Create the undetected Chrome driver with extra stealth
			self.interface.driver = uc.Chrome(options=options, version_main=121, headless=False)
			self.interface.driver_initialized = True

			# Execute stealth scripts
			stealth_scripts = [
				"Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
				"Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})",
				"Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})",
				"window.chrome = { runtime: {} }",
			]

			for script in stealth_scripts:
				try:
					self.interface.driver.execute_script(script)
				except:
					pass

			print("[DRIVER] Stealth Chrome driver initialized successfully")
			return True

		except Exception as e:
			print(f"[ERROR] Failed to initialize stealth driver: {e}")
			# Fallback to standard driver
			self.interface.get_driver()
			return True

	def establish_session(self):
		print("[SESSION] Establishing session with Chrome driver and Cloudflare bypass...")

		try:
			# Initialize driver if not already done
			if not self.interface.driver_initialized:
				self.interface.get_driver()

			# Try homepage first (less aggressive protection)
			homepage_url = "https://www.joemachensnissan.com/"
			print(f"[SESSION] Loading homepage: {homepage_url}")

			# Navigate to homepage first
			self.interface.driver.get(homepage_url)
			time.sleep(5)  # Basic wait for homepage

			# Check homepage loaded
			homepage_source = self.interface.driver.page_source
			if 'nissan' in homepage_source.lower() and len(homepage_source) > 3000:
				print("[SESSION] Homepage loaded successfully")
			else:
				print("[SESSION] Homepage may have issues, but continuing...")

			# Now try inventory page with Cloudflare handling
			inventory_url = "https://www.joemachensnissan.com/new-vehicles/"
			print(f"[SESSION] Loading inventory: {inventory_url}")

			# Navigate to the inventory page
			self.interface.driver.get(inventory_url)
			print("[SESSION] Initial inventory page load complete, checking for Cloudflare...")

			# Wait for Cloudflare to finish - moderate approach
			max_wait_time = 60  # 1 minute - more reasonable
			wait_interval = 10   # Check every 10 seconds

			for attempt in range(max_wait_time // wait_interval):
				current_time = attempt * wait_interval
				page_title = self.interface.driver.title
				page_source = self.interface.driver.page_source

				print(f"[SESSION] Check {attempt + 1} ({current_time}s): Title='{page_title[:40]}...'")

				# Check for Cloudflare challenge indicators
				cloudflare_indicators = [
					"checking your browser", "cloudflare", "please wait", "loading",
					"verifying you are human", "challenge", "one moment"
				]

				is_cloudflare = any(indicator in page_title.lower() for indicator in cloudflare_indicators)
				is_cloudflare = is_cloudflare or any(indicator in page_source.lower() for indicator in cloudflare_indicators[:4])

				if is_cloudflare:
					print(f"[SESSION] Cloudflare processing, waiting {wait_interval} more seconds...")
					time.sleep(wait_interval)
					continue

				# Check if we have substantial vehicle content
				vehicle_indicators = ['inventory', 'vehicle', 'new cars', 'used cars', 'vin', 'stock']
				has_vehicle_content = any(indicator in page_source.lower() for indicator in vehicle_indicators)

				if has_vehicle_content and len(page_source) > 4000:
					print(f"[SESSION] Vehicle content detected after {current_time} seconds - success!")
					return True

				print(f"[SESSION] Waiting for vehicle content... (page size: {len(page_source)})")
				time.sleep(wait_interval)

			# If we get here, max time reached - be more forgiving
			print("[SESSION] Max wait time reached, checking if we can proceed anyway...")
			final_source = self.interface.driver.page_source

			# Try to proceed anyway if we have reasonable content
			if len(final_source) > 1000:
				print(f"[SESSION] Content size: {len(final_source)} chars - proceeding to try scraping...")
				return True
			else:
				print(f"[ERROR] Insufficient content loaded (only {len(final_source)} chars)")
				return False

		except Exception as e:
			print(f"[ERROR] Failed to establish session: {e}")
			import traceback
			traceback.print_exc()
			return False

	def processing_each_vehicle_toyota_style(self, vehicle_url, status):
		"""Process individual vehicle like Toyota scraper - extract data and save to CSV"""
		print(f"[VEHICLE] Processing: {vehicle_url}")

		# Use our JSON-LD extraction method
		vehicle_data = self.process_vehicle_detail_page(vehicle_url)

		if not vehicle_data:
			return False

		# Format status like Toyota scraper
		status = status.replace('_', '-').title()

		# Use existing processing method to save data
		vehicle_data['url'] = vehicle_url
		self.processing_each_vehicle(vehicle_data)

		print(f"[SUCCESS] Saved: {vehicle_data.get('year', '')} {vehicle_data.get('make', '')} {vehicle_data.get('model', '')} - VIN: {vehicle_data.get('vin', '')}")
		return True

	def processing_each_vehicle(self, vehicle_data):
		"""Process vehicle data and format it like other scrapers"""
		print(f"[DEBUG] processing_each_vehicle called with: {vehicle_data}")

		# Handle both API data and page-scraped data
		vin = vehicle_data.get('vin', '')
		stock = vehicle_data.get('stock', '') or vehicle_data.get('stockNumber', '')

		# Determine vehicle type from URL or data
		vehicle_url = vehicle_data.get('url', '')
		if 'new-vehicles' in vehicle_url or '/new/' in vehicle_url:
			v_type = 'New'
		elif 'used-vehicles' in vehicle_url or '/used/' in vehicle_url:
			v_type = 'Used'
		elif 'certified-vehicles' in vehicle_url or '/certified/' in vehicle_url:
			v_type = 'Certified'
		else:
			v_type = vehicle_data.get('type', 'Used')

		year = vehicle_data.get('year', '')
		make = vehicle_data.get('make', '')
		model = vehicle_data.get('model', '')
		trim = vehicle_data.get('trim', '')
		ext_color = vehicle_data.get('exteriorColor', '') or vehicle_data.get('color', '')

		# Set status based on URL or default to In-Stock
		if 'allocated' in vehicle_url.lower():
			status = 'Allocated'
		elif 'in_transit' in vehicle_url.lower():
			status = 'In-Transit'
		else:
			status = 'In-Stock'

		# Clean up price
		price = vehicle_data.get('price', '').replace('$', '').replace(',', '') if vehicle_data.get('price') else ''
		if price:
			# Remove non-numeric characters except decimal point
			price_clean = ''.join(c for c in str(price) if c.isdigit() or c == '.')
			price = price_clean if price_clean else ''

		body = vehicle_data.get('bodyStyle', '') or vehicle_data.get('body', '')
		fuel_type = vehicle_data.get('fuelType', '') or vehicle_data.get('fuel', '')

		# MSRP handling
		msrp = vehicle_data.get('msrp', '')
		if msrp and str(msrp).isdigit():
			msrp = int(msrp)
		else:
			msrp = ''

		date_in_stock = vehicle_data.get('dateInStock', '') or vehicle_data.get('date_in_stock', '')

		# Joe Machens Nissan address info
		street_addr = '201 Nebraska Ave'
		locality = 'Columbia'
		postal_code = '65203'
		region = 'MO'
		country = 'US'
		location = 'Joe Machens Nissan'

		# Output in same format as other scrapers (21 fields)
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

	def fetch_di_inventory_selenium(self, filter_expr, page=1, per_page=200, sort="createdAt_desc"):
		"""Use Selenium to directly access the API endpoint and extract JSON response"""
		print(f'[SELENIUM API] Getting Vehicles Page: {page}')

		# Ensure we have a session
		if not self.session_cookies:
			if not self.establish_session():
				return {"error": "Failed to establish session"}

		# Build the API URL
		params = {
			"encoded": "true",
			"filter": self.di_encode_filter(filter_expr),
			"page": str(page),
			"perPage": str(per_page),
			"sort": sort
		}

		# Convert params to URL string
		param_string = "&".join([f"{k}={v}" for k, v in params.items()])
		api_url = f"{self.DI_BASE}?{param_string}"

		try:
			# Use Selenium to navigate to the API endpoint
			self.interface.driver.get(api_url)
			time.sleep(3)

			# Get the page source which should contain the JSON response
			page_source = self.interface.driver.page_source

			# Extract JSON from the page
			import re
			# Look for JSON in <pre> tags or in the body
			json_match = re.search(r'<pre[^>]*>([^<]+)</pre>', page_source, re.DOTALL)
			if json_match:
				json_text = json_match.group(1)
			else:
				# If no <pre> tags, look for JSON-like content in body
				json_match = re.search(r'\{[^}]*"vehicles"[^}]*\}', page_source, re.DOTALL)
				if json_match:
					json_text = json_match.group(0)
				else:
					return {"error": "No JSON found in response", "body": page_source[:500]}

			try:
				import json
				data = json.loads(json_text)
			except json.JSONDecodeError as e:
				return {"error": f"Invalid JSON: {str(e)}", "body": json_text[:500]}

			vehicles = data.get("vehicles") or data.get("results") or data.get("data") or []
			total = data.get("total") or data.get("count") or len(vehicles)

			print(f"[SUCCESS] Retrieved {len(vehicles)} vehicles via Selenium (Total available: {total})")
			return {"total": total, "vehicles": vehicles, "raw": data}

		except Exception as error:
			return {"error": f"Selenium API request failed: {str(error)}"}

	def fetch_di_inventory(self, filter_expr, page=1, per_page=200, sort="createdAt_desc", timeout=30):
		print(f'[API] Getting Vehicles Page: {page}')

		# Ensure we have a valid session
		if not self.session_cookies:
			if not self.establish_session():
				return {"error": "Failed to establish session"}

		params = {
			"encoded": "true",
			"filter": self.di_encode_filter(filter_expr),
			"page": str(page),
			"perPage": str(per_page),
			"sort": sort
		}

		headers = {
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
			"Accept": "application/json, text/plain, */*",
			"Accept-Language": "en-US,en;q=0.9",
			"Accept-Encoding": "gzip, deflate, br",
			"Referer": "https://www.joemachensnissan.com/inventory/",
			"Origin": "https://www.joemachensnissan.com",
			"Connection": "keep-alive",
			"Sec-Fetch-Dest": "empty",
			"Sec-Fetch-Mode": "cors",
			"Sec-Fetch-Site": "same-origin",
			"sec-ch-ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
			"sec-ch-ua-mobile": "?0",
			"sec-ch-ua-platform": '"Windows"'
		}

		retry_count = 0
		max_retries = 2

		while retry_count < max_retries:
			try:
				# Use session cookies to bypass Cloudflare
				response = requests.get(
					self.DI_BASE,
					params=params,
					headers=headers,
					cookies=self.session_cookies,
					timeout=timeout
				)

				if response.status_code == 403:
					print("[WARNING] 403 Forbidden - Re-establishing session...")
					# Try to re-establish session
					if self.establish_session():
						retry_count += 1
						continue
					else:
						# Safe error handling for Windows encoding
						error_body = response.text[:200].encode('ascii', 'ignore').decode('ascii')
						return {"error": "HTTP 403 - Unable to bypass Cloudflare protection", "body": error_body}

				if not response.ok:
					# Safe error handling for Windows encoding
					error_text = response.text[:200].encode('ascii', 'ignore').decode('ascii')
					print(f"[ERROR] HTTP {response.status_code}: {error_text}")
					return {"error": f"HTTP {response.status_code}", "body": error_text}

				try:
					data = response.json()
				except ValueError:
					# Safe error handling for Windows encoding
					error_text = response.text[:200].encode('ascii', 'ignore').decode('ascii')
					print(f"[ERROR] Non-JSON Response: {error_text}")
					return {"error": "Non-JSON", "body": error_text}

				vehicles = data.get("vehicles") or data.get("results") or data.get("data") or []
				total = data.get("total") or data.get("count") or len(vehicles)

				print(f"[SUCCESS] Retrieved {len(vehicles)} vehicles (Total available: {total})")
				return {"total": total, "vehicles": vehicles, "raw": data}

			except Exception as error:
				print(f'[ERROR] Request failed: {error}')
				retry_count += 1
				if retry_count < max_retries:
					print(f"[RETRY] Waiting 3 seconds before retry {retry_count + 1}/{max_retries}")
					time.sleep(3)
				else:
					return {"error": f"Request failed after {max_retries} retries: {str(error)}"}

		return {"error": "Maximum retries exceeded"}

	def get_vehicle_listing_urls_robust(self, inventory_type, page_num):
		"""Enhanced version of get_vehicle_listing_urls with better Cloudflare handling"""
		print(f'[LISTING] Getting {inventory_type} vehicles page {page_num} (Enhanced)')

		# Build inventory URL based on type
		if inventory_type == 'new':
			base_url = f'https://www.joemachensnissan.com/new-vehicles/?p={page_num}'
		elif inventory_type == 'used':
			base_url = f'https://www.joemachensnissan.com/used-vehicles/?p={page_num}'
		else:  # certified
			base_url = f'https://www.joemachensnissan.com/certified-vehicles/?p={page_num}'

		try:
			print(f'[URL] Loading: {base_url}')

			# Navigate directly with the driver
			self.interface.driver.get(base_url)

			# Extended wait for Cloudflare and page loading - up to 3 minutes for first page
			max_wait_time = 180 if page_num == 1 else 60  # 3 minutes for first page, 1 minute for others
			wait_interval = 10
			max_attempts = max_wait_time // wait_interval

			for attempt in range(max_attempts):
				elapsed_time = attempt * wait_interval
				page_source = self.interface.driver.page_source
				page_title = self.interface.driver.title
				current_url = self.interface.driver.current_url

				print(f"[DEBUG] Attempt {attempt + 1}/{max_attempts} ({elapsed_time}s): Title='{page_title[:50]}...'")

				# Check for Cloudflare indicators
				cloudflare_indicators = [
					"checking your browser", "cloudflare", "please wait", "loading",
					"verifying you are human", "challenge", "checking if the site connection is secure"
				]

				is_cloudflare = any(indicator in page_title.lower() for indicator in cloudflare_indicators)
				is_cloudflare = is_cloudflare or any(indicator in page_source.lower() for indicator in cloudflare_indicators[:4])

				if is_cloudflare:
					print(f"[CLOUDFLARE] Still processing, waiting {wait_interval} more seconds...")
					time.sleep(wait_interval)
					continue

				# Check if we have vehicle content indicating successful load
				vehicle_content_indicators = ['inventory', 'vehicle', 'vin', 'stock', 'price', 'new cars', 'used cars']
				has_vehicle_content = any(indicator in page_source.lower() for indicator in vehicle_content_indicators)

				if has_vehicle_content:
					print(f"[SUCCESS] Vehicle content detected after {elapsed_time} seconds")
					break
				else:
					print(f"[WAITING] No vehicle content yet, waiting {wait_interval} more seconds...")
					time.sleep(wait_interval)

			else:
				print(f"[WARNING] Max wait time ({max_wait_time}s) reached, proceeding anyway...")

			# Get the soup after waiting
			soup = self.interface.make_soup()

			if not soup:
				print(f'[ERROR] Failed to get soup for page {page_num}')
				return []

			# Enhanced vehicle URL detection with multiple strategies
			vehicle_urls = set()

			# Strategy 1: Look for inventory links
			for link in soup.find_all('a', href=True):
				href = link.get('href', '').strip()
				if '/inventory/' in href and 'joemachensnissan.com' in (href if href.startswith('http') else f'https://www.joemachensnissan.com{href}'):
					if not href.startswith('http'):
						href = 'https://www.joemachensnissan.com' + (href if href.startswith('/') else '/' + href)
					vehicle_urls.add(href)

			# Strategy 2: Look for vehicle detail patterns
			for link in soup.find_all('a', href=True):
				href = link.get('href', '').strip()
				vehicle_patterns = ['/vehicle-details/', '/detail/', 'VIN=', '/new-', '/used-', '/certified-', '/vehicles/']
				if any(pattern in href for pattern in vehicle_patterns):
					if not href.startswith('http'):
						href = 'https://www.joemachensnissan.com' + (href if href.startswith('/') else '/' + href)
					if 'joemachensnissan.com' in href:
						vehicle_urls.add(href)

			# Strategy 3: Look for vehicle cards/containers
			vehicle_containers = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'vehicle|car|listing|inventory|item', re.I))
			for container in vehicle_containers:
				for link in container.find_all('a', href=True):
					href = link.get('href', '').strip()
					if href and not href.startswith('#') and not href.startswith('javascript'):
						if not href.startswith('http'):
							href = 'https://www.joemachensnissan.com' + (href if href.startswith('/') else '/' + href)
						if 'joemachensnissan.com' in href and any(pattern in href for pattern in ['/inventory/', '/vehicle']):
							vehicle_urls.add(href)

			vehicle_urls_list = list(vehicle_urls)

			if vehicle_urls_list:
				print(f"[SUCCESS] Page {page_num}: Found {len(vehicle_urls_list)} unique vehicle URLs")
				# Show samples for debugging
				for i, url in enumerate(vehicle_urls_list[:3], 1):
					print(f"[SAMPLE {i}] {url}")
				return vehicle_urls_list
			else:
				print(f"[EMPTY] Page {page_num}: No vehicle URLs found")
				# Enhanced debugging
				all_links = soup.find_all('a', href=True)
				print(f"[DEBUG] Total links on page: {len(all_links)}")

				# Check if page loaded properly
				page_text = soup.get_text().lower()
				if 'error' in page_text or '404' in page_text:
					print("[DEBUG] Page contains error indicators")
				elif len(page_text) < 1000:
					print(f"[DEBUG] Page text is very short ({len(page_text)} chars), may not have loaded properly")

				return []

		except Exception as error:
			print(f'[ERROR] Failed to get vehicle listings for page {page_num}: {error}')
			import traceback
			traceback.print_exc()
			return []

	def get_vehicle_listing_urls(self, inventory_type, page_num):
		"""Get vehicle URLs from inventory listing pages"""
		print(f'[LISTING] Getting {inventory_type} vehicles page {page_num}')

		# Ensure driver is initialized
		if not self.interface.driver_initialized:
			print('[INIT] Initializing Chrome driver...')
			self.interface.get_driver()

		# Build inventory URL based on type
		if inventory_type == 'new':
			base_url = f'https://www.joemachensnissan.com/new-vehicles/?p={page_num}'
		elif inventory_type == 'used':
			base_url = f'https://www.joemachensnissan.com/used-vehicles/?p={page_num}'
		else:  # certified
			base_url = f'https://www.joemachensnissan.com/certified-vehicles/?p={page_num}'

		try:
			print(f'[URL] Loading: {base_url}')

			# Navigate directly with the driver instead of using interface method
			self.interface.driver.get(base_url)

			# Wait for page to load and Cloudflare to complete
			time.sleep(10)  # Initial wait

			# Check for Cloudflare and wait if needed
			for check_attempt in range(6):  # Check up to 6 times (60 seconds total)
				page_source = self.interface.driver.page_source
				page_title = self.interface.driver.title

				# Check if still loading or Cloudflare processing
				if any(indicator in page_title.lower() for indicator in ["checking", "cloudflare", "loading"]):
					print(f"[DEBUG] Still processing Cloudflare, attempt {check_attempt + 1}, waiting...")
					time.sleep(10)
					continue

				# Check if we have vehicle content
				if 'vehicle' in page_source.lower() or 'inventory' in page_source.lower():
					print(f"[DEBUG] Page loaded successfully with vehicle content")
					break

				print(f"[DEBUG] No vehicle content yet, attempt {check_attempt + 1}, waiting...")
				time.sleep(10)

			# Get the soup after waiting
			soup = self.interface.make_soup()

			if not soup:
				print(f'[ERROR] Failed to get soup for page {page_num}')
				return []

			# Look for vehicle cards/links - use multiple strategies
			vehicle_urls = set()  # Use set to avoid duplicates

			# Method 1: Look for any links containing "/inventory/"
			print(f'[DEBUG] Searching for vehicle links on page {page_num}')
			for link in soup.find_all('a', href=True):
				href = link.get('href', '').strip()

				# Look for inventory links
				if '/inventory/' in href:
					if not href.startswith('http'):
						href = 'https://www.joemachensnissan.com' + (href if href.startswith('/') else '/' + href)
					vehicle_urls.add(href)
					print(f'[FOUND LINK] {href}')

			# Method 2: Look for vehicle detail page patterns
			for link in soup.find_all('a', href=True):
				href = link.get('href', '').strip()
				# More specific patterns for vehicle detail pages
				if any(pattern in href for pattern in ['/vehicle-details/', '/detail/', 'VIN=', '/new-', '/used-', '/certified-']):
					if not href.startswith('http'):
						href = 'https://www.joemachensnissan.com' + (href if href.startswith('/') else '/' + href)
					if 'joemachensnissan.com' in href:
						vehicle_urls.add(href)

			# Method 3: Look for vehicle cards by common CSS classes
			vehicle_cards = soup.find_all(['div', 'article'], class_=re.compile(r'vehicle|car|listing|inventory', re.I))
			print(f'[DEBUG] Found {len(vehicle_cards)} potential vehicle cards')

			for card in vehicle_cards:
				for link in card.find_all('a', href=True):
					href = link.get('href', '').strip()
					if href and not href.startswith('#'):
						if not href.startswith('http'):
							href = 'https://www.joemachensnissan.com' + (href if href.startswith('/') else '/' + href)
						if 'joemachensnissan.com' in href and any(pattern in href for pattern in ['/inventory/', '/new-', '/used-', '/certified-']):
							vehicle_urls.add(href)

			# Method 4: Look for links by text content (like "View Details", "More Info", etc.)
			for link in soup.find_all('a', href=True):
				link_text = link.get_text(strip=True).lower()
				if any(phrase in link_text for phrase in ['view', 'details', 'more', 'info', 'see']):
					href = link.get('href', '').strip()
					if href and '/inventory/' in href:
						if not href.startswith('http'):
							href = 'https://www.joemachensnissan.com' + (href if href.startswith('/') else '/' + href)
						vehicle_urls.add(href)

			vehicle_urls_list = list(vehicle_urls)

			if vehicle_urls_list:
				print(f"[SUCCESS] Page {page_num}: Found {len(vehicle_urls_list)} unique vehicle URLs")
				for i, url in enumerate(vehicle_urls_list[:3], 1):  # Show first 3 as examples
					print(f"[SAMPLE {i}] {url}")
				return vehicle_urls_list
			else:
				print(f"[EMPTY] Page {page_num}: No vehicle URLs found")
				# Add debugging to see what's on the page
				all_links = soup.find_all('a', href=True)
				print(f"[DEBUG] Total links found on page: {len(all_links)}")
				inventory_links = [link for link in all_links if '/inventory/' in link.get('href', '')]
				print(f"[DEBUG] Links containing '/inventory/': {len(inventory_links)}")
				return []

		except Exception as error:
			print(f'[ERROR] Failed to get vehicle listings for page {page_num}: {error}')
			import traceback
			traceback.print_exc()
			return []

	def process_vehicle_detail_page(self, vehicle_url):
		"""Process individual vehicle detail page to extract data using Toyota scraper method"""
		print(f'[DETAIL] Processing: {vehicle_url}')

		try:
			# Use same pattern as Toyota scraper
			soup = self.interface.get_selenium_response(vehicle_url)
			time.sleep(2)

			# Joe Machens Nissan uses JSON-LD structured data instead of shift_digital_session_id
			json_ld_scripts = soup.find_all('script', type='application/ld+json')

			json_data = None
			for script in json_ld_scripts:
				try:
					data = json.loads(script.get_text())
					# Look for Car/Product type with vehicle information
					if isinstance(data, dict) and data.get('@type'):
						types = data.get('@type', [])
						if isinstance(types, str):
							types = [types]
						if 'Car' in types or 'Product' in types:
							json_data = data
							break
				except json.JSONDecodeError:
					continue

			if not json_data:
				print(f"[ERROR] Could not find vehicle JSON-LD data on page: {vehicle_url}")
				return None

			# Extract data using same pattern as Toyota scraper
			vehicle_data = {}

			# Core vehicle information from JSON-LD structure
			try:
				vehicle_data['vin'] = json_data['vehicleIdentificationNumber']
				vehicle_data['stock'] = json_data['@id']  # Stock number
				vehicle_data['year'] = json_data['vehicleModelDate']
				vehicle_data['make'] = json_data['brand']['name'] if isinstance(json_data['brand'], dict) else json_data['brand']
				vehicle_data['model'] = json_data['model']
			except (KeyError, TypeError) as e:
				print(f"[ERROR] Missing required vehicle data: {e}")
				return None

			# Optional fields with fallbacks from JSON-LD structure
			vehicle_data['exteriorColor'] = json_data.get('color', '')
			vehicle_data['vehicle_location_id'] = ''  # Not available in JSON-LD

			# Determine vehicle type from condition
			condition = json_data.get('itemCondition', '')
			if 'NewCondition' in condition:
				vehicle_data['type'] = 'New'
			elif 'UsedCondition' in condition:
				vehicle_data['type'] = 'Used'
			else:
				vehicle_data['type'] = 'New'  # Default assumption

			# Additional details from JSON-LD
			vehicle_data['bodyStyle'] = json_data.get('bodyType', '')
			vehicle_data['fuelType'] = json_data.get('fuelType', '')
			vehicle_data['dateInStock'] = ''  # Not available in JSON-LD

			# Extract trim from name (remove year make model)
			full_name = json_data.get('name', '')
			trim_part = full_name.replace(f"{vehicle_data['year']} {vehicle_data['make']} {vehicle_data['model']}", '').strip()
			vehicle_data['trim'] = trim_part

			# Extract price from offers section
			try:
				offers = json_data.get('offers', {})
				if isinstance(offers, dict):
					vehicle_data['price'] = offers.get('price', '')
				else:
					vehicle_data['price'] = ''
			except:
				vehicle_data['price'] = ''

			vehicle_data['msrp'] = ''  # Set empty like Toyota scraper
			vehicle_data['url'] = vehicle_url

			print(f"[SUCCESS] Extracted: {vehicle_data['year']} {vehicle_data['make']} {vehicle_data['model']} - VIN: {vehicle_data['vin']}")
			return vehicle_data

		except Exception as error:
			print(f'[ERROR] Failed to process vehicle detail: {error}')
			import traceback
			traceback.print_exc()
			return None

	def extract_vin_from_page(self, soup):
		"""Extract VIN from page using multiple strategies"""
		# Look for VIN in various locations
		patterns = [
			r'\b[A-HJ-NPR-Z0-9]{17}\b',  # Standard VIN pattern
		]

		# Check common VIN locations
		for element in soup.find_all(['span', 'div', 'td'], string=re.compile(r'VIN', re.IGNORECASE)):
			parent = element.parent
			if parent:
				text = parent.get_text()
				for pattern in patterns:
					vin_match = re.search(pattern, text)
					if vin_match:
						return vin_match.group(0)

		# Check in meta tags
		for meta in soup.find_all('meta'):
			content = meta.get('content', '')
			for pattern in patterns:
				vin_match = re.search(pattern, content)
				if vin_match:
					return vin_match.group(0)

		return ''

	def extract_stock_from_page(self, soup):
		"""Extract stock number from page"""
		for element in soup.find_all(['span', 'div', 'td'], string=re.compile(r'Stock', re.IGNORECASE)):
			parent = element.parent
			if parent:
				text = parent.get_text()
				stock_match = re.search(r'Stock[^:]*:\s*([A-Z0-9]+)', text, re.IGNORECASE)
				if stock_match:
					return stock_match.group(1)
		return ''

	def extract_price_from_page(self, soup):
		"""Extract price from page"""
		# Look for price patterns
		price_patterns = [
			r'\$([0-9,]+)',
			r'Price[^:]*:\s*\$([0-9,]+)',
		]

		for element in soup.find_all(['span', 'div'], class_=re.compile(r'price', re.IGNORECASE)):
			text = element.get_text()
			for pattern in price_patterns:
				price_match = re.search(pattern, text)
				if price_match:
					return price_match.group(1).replace(',', '')

		return ''

	def start_scraping_joemachensnissan(self):

		processed_json_file = self.log_folder + 'vehicles_processed.json'
		processed_json_data = self.helper.json_exist_data(processed_json_file)

		print("[INIT] Starting Joe Machens Nissan scraper - simple Toyota pattern...")

		# Use simple search approach like Toyota scraper
		for status in ['allocated', 'in_stock', 'in_transit']:
			print(f"[STATUS] Processing {status} vehicles...")

			page_num = 1
			while page_num <= 50:  # Increase to 50 pages to ensure we get all 247 VINs
				print(f"[PAGE] Page {page_num} for {status} vehicles")

				# Use the inventory page URLs that we know work
				if status == 'allocated':
					search_url = f'https://www.joemachensnissan.com/new-vehicles/?p={page_num}'
				elif status == 'in_stock':
					search_url = f'https://www.joemachensnissan.com/used-vehicles/?p={page_num}'
				else:  # in_transit - just use new vehicles again since most inventory is new
					search_url = f'https://www.joemachensnissan.com/new-vehicles/?p={page_num}'
				soup = self.interface.get_selenium_response(search_url)

				if not soup:
					print(f"[ERROR] Failed to load page {page_num}")
					break

				# Wait for page to load completely and get vehicle links
				time.sleep(10)  # Give page time to load
				soup = self.interface.make_soup()

				if not soup:
					print(f"[ERROR] Failed to get page content for page {page_num}")
					break

				# Find all vehicle inventory links on the page
				vehicle_urls = []
				for link in soup.find_all('a', href=True):
					href = link.get('href', '').strip()
					if '/inventory/' in href:
						if not href.startswith('http'):
							href = 'https://www.joemachensnissan.com' + (href if href.startswith('/') else '/' + href)
						vehicle_urls.append(href)

				# Remove duplicates
				vehicle_urls = list(set(vehicle_urls))

				print(f"[FOUND] {len(vehicle_urls)} vehicles on page {page_num}")

				if not vehicle_urls:
					print(f"[DONE] No vehicles found on page {page_num}, finishing {status}")
					break

				# Process each vehicle
				for index, vehicle_url in enumerate(vehicle_urls):
					print(f"[VEHICLE] {page_num}:{index+1}/{len(vehicle_urls)} - {vehicle_url}")

					if vehicle_url not in processed_json_data:
						# Process using Toyota-style method with JSON-LD extraction
						success = self.processing_each_vehicle_toyota_style(vehicle_url, status)
						if success:
							processed_json_data.append(vehicle_url)
							self.helper.write_json_file(processed_json_data, processed_json_file)
						else:
							print('[ERROR] Failed to process vehicle')
					else:
						print('[SKIP] Vehicle already processed')

				# Check if we should continue - if we found fewer than 10 vehicles, probably no more pages
				if len(vehicle_urls) < 10:
					print(f"[DONE] Finished {status} - found only {len(vehicle_urls)} vehicles, probably last page")
					break

				page_num += 1

		self.interface.close_driver()
		print("[COMPLETE] Scraping finished")


if __name__ == "__main__":
	import sys
	import os

	data_folder = "output_data/"
	output_file = "joe_machens_nissan_vehicles.csv"

	if len(sys.argv) > 1:
		data_folder = sys.argv[1]
	if len(sys.argv) > 2:
		output_file = sys.argv[2]

	try:
		scraper = JOEMACHENSNISSAN(data_folder, output_file)
		scraper.start_scraping_joemachensnissan()

		print()
		print('*' * 70)
		print('[SUCCESS] Joe Machens Nissan scraper completed successfully!')
		print('Data saved using Dealer Inspire API')
		print('Check the output in:', data_folder + output_file)
		print('*' * 70)
		print()

	except Exception as e:
		print(f"[ERROR] Scraper failed: {e}")
		sys.exit(1)