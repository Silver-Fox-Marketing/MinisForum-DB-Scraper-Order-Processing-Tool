# -*- coding: utf-8 -*-
from . helper_class import *
import undetected_chromedriver as uc
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

class INTERFACING():

    def __init__(self):
        self.driver_initialized = False
        self.driver = ''
        self.MAX_TRIALS = 2

    def make_soup(self):
        return BeautifulSoup(self.driver.page_source, 'html.parser')

    def current_url(self):
        return self.driver.current_url

    def get_driver(self):

        capabilities = DesiredCapabilities.CHROME
        capabilities["goog:loggingPrefs"] = {"performance": "ALL"}
        
        if 1:
            self.driver = uc.Chrome(driver_executable_path='./chromedriver', desired_capabilities=capabilities)

        else:
            
            self.driver = webdriver.Chrome("./chromedriver", desired_capabilities=capabilities)

        self.driver_initialized = True
        self.driver.maximize_window()

    def process_browser_logs_for_network_events(self):

        logs = self.driver.get_log("performance")

        # Helper().write_json_file(logs, 'logs.json')

        for entry in logs:

            try:
                log = json.loads(entry["message"])["message"]['params']['headers']
                _auth = log.get('Cookie', '')

                if not _auth:
                    _auth = log['cookie']

                if '_gid=GA' not in _auth:
                    what

            except Exception as error:
                # print('error: ', error)
                continue

            return log

    def close_driver(self):

        if self.driver_initialized:
            self.driver.quit()
            print("Closed the driver")
            self.driver_initialized = False

    def get_selenium_response(self,url):
        page_src = None
        try:
            if not self.driver_initialized:
                self.get_driver()
            else:
                pass
            print("Processing URL: ", url)
            self.driver.get(url)
            sleep_time = 3
            time.sleep(sleep_time)
            
        except Exception as error:
            print('Error in getting selenium response: ',error)

        return self.make_soup()

    def get_page_source(self):
        return self.driver.page_source

    def refresh_page(self):
        self.driver.refresh()

    def get_url_response(self, url, is_json=False):
 
        print("Processing URL: ", url)

        headers = {'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,  like Gecko) Chrome/92.0.4515.107 Safari/537.36'}

        if not is_json:
            return requests.get(url, headers=headers, timeout=30).text

        return requests.get(url, headers=headers, timeout=30).json()


    def make_soup_url(self, url):
        return BeautifulSoup(self.get_url_response(url), 'html.parser')

    def clicking(self,xpath):
        elem = self.driver.find_element('xpath', xpath)
        elem.click()
        time.sleep(random.randint(2,3))

    def entering_values(self,xpath,value):
        elem = self.driver.find_element('xpath', xpath)
        elem.clear()
        elem.send_keys(value)
        # time.sleep(random.randint(2,4))
