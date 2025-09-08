import json
import os
import re
import requests
import sys
import random
import csv
import time
from bs4 import BeautifulSoup
import datetime

class Helper():

	def __init__(self):
		pass

	def read_txt_file(self,filename):
		with open(filename) as infile:
			ids = [row.replace('\n', '').replace('\r', '') for row in infile]
		return ids

	def writing_output_file(self, sub_list, output_file):

		if self.is_file_exist(output_file):
			csv_data = self.reading_csv(output_file)
		else:
			csv_data = [self.read_json_file('./input_data/headers.json')]
			
		csv_data.append(sub_list)
		self.writing_csv(csv_data, output_file)

		# print("Writing Output File Done...")

	def get_url_response(self, url, is_json=False):
 
		print("Processing URL: ", url)

		count = 0

		headers = {'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'}
		while 1:

			try:
				if not is_json:
					return requests.get(url, headers=headers, timeout=30).text

				return requests.get(url, headers=headers, timeout=30).json()
			except Exception as error:
				print('Error in getting URL response: ', error)

			count += 1

			if count > 3:
				return False

			time.sleep(3)


	def make_soup_url(self, url):
		return BeautifulSoup(self.get_url_response(url), 'html.parser')

	def reading_csv(self,csv_filename):
		f = open(csv_filename,'r', encoding='utf-8', errors='replace')
		csv_data = []
		reader = csv.reader(f)
		for row in reader:
			csv_data.append(row)

		f.close()
		return csv_data 

	def writing_csv(self,data,csv_filename):

		myFile = open(csv_filename, 'w', newline='',encoding='utf-8',errors='replace')
		with myFile:
			writer = csv.writer(myFile,quoting=csv.QUOTE_ALL)
			writer.writerows(data)

		return csv_filename

	def checking_folder_existence(self,dest_dir):

		if not os.path.exists(dest_dir):
			os.mkdir(dest_dir)
			print("Directory " , dest_dir ,  " Created ")

		return dest_dir
		
	def write_json_file(self,data,filename):

		while 1:
			try:
				with open(filename, 'w',encoding='utf-8') as outfile:
					json.dump(data, outfile,indent=4)
				break
			except Exception as error:
				print("Error in writing Json file: ",error)
				time.sleep(1)

	def read_json_file(self,filename):
		data = {}
		with open(filename,encoding='utf-8') as json_data:
			data = json.load(json_data)
		return data

	def is_file_exist(self,filename):
		if os.path.exists(filename):
			return True
		else:
			return False

	def json_exist_data(self,fileName):
		json_data = []
		if self.is_file_exist(fileName):
			json_data = self.read_json_file(fileName)
		return json_data

	def downloading_image_file(self, image_url, image_filename):

		if self.is_file_exist(image_filename):
			return True

		print('Downloading File: ', image_filename, ' : ', image_url)

		headers = {
			'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
		}

		response = requests.request("GET", image_url, headers=headers, data={}).content

		with open(image_filename, 'wb') as handler:
			handler.write(response)

	def write_random_file(self,text,file_name):
		file= open(file_name,"w",encoding='utf-8')
		file.write(str(text))
		file.close()

	def read_random_file(self,file_name):
		f = open(file_name, "r",encoding='utf-8')
		return f.read()