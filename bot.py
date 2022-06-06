#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup

import time
import socket
import re
import sys

####################
# -- Parameters -- #
DEBUG = False

REFRESH_RATE = 120

TELEGRAM_TOKEN_ID = ""
TELEGRAM_CHAT_ID = ""

KVALSTER_ROOMS = [2, 3]
KVALSTER_MIN_SQM = 60
KVALSTER_LOCATION = "Stockholm"
KVALSTER_MAX_DAYS_LISTED = 3
KVALSTER_SOURCE = "blocket.se"

MAX_BUDGET = 16000
##################

URL = "https://kvalster.se/" + KVALSTER_LOCATION + "/Uthyres/L%C3%A4genheter?" + "Rum=" + ",".join([str(room_num) for room_num in KVALSTER_ROOMS]) + "&maxHyra=" + str(MAX_BUDGET) + "&minYta=" + str(KVALSTER_MIN_SQM) + "&maxListad=" + str(KVALSTER_MAX_DAYS_LISTED)

def send_telegram_notification(text):
	url_req = "https://api.telegram.org/bot" + TELEGRAM_TOKEN_ID + "/sendMessage" + "?chat_id=" + TELEGRAM_CHAT_ID + "&text=" + text
	request = requests.get(url_req)

def retrieve_apartments():

	apartments = {}

	req_ret = requests.get(URL)
	req_ret = req_ret.text.replace("<br />", " ")
	soup_ret = BeautifulSoup(req_ret, "html.parser")
	soup_res = soup_ret.find("table", attrs={"class":"o"})
	table_rows = soup_res.find_all("tr")

	num = 1
	for row in table_rows:
		num = num +1
		data = []
		spanList = []
		linkList = []
		for col in row.find_all("td"):
			# Get a list of spans
			spans = col.find_all("span")
			spanList.append([span.getText() for span in spans])
			for item in spanList:
				for line in item:
					data.append(line)
			spanList = []

			# Get a list of "a" and find the apartment's ID in order to generate a final URL
			links = col.find_all("a")
			linkList.append([link.get("href") for link in links])
			for linkItem in linkList:
				for line in linkItem:
					data.append(line)

		address = str(data[3])
		domain = re.search("(?:[a-z09.]*?)([a-zA-Z0-9-]*\.se)", address)
		address = re.sub("(?:[a-z09.]*?)([a-zA-Z0-9-]*\.se)", "", address)
		link = str(data[2])
		apartmentID = re.search("\d+", link).group(0)
		# Address | Listing Source | URL to listing | Number of rooms | Monthly cost | sqm
		apartment_info = [ address, domain.group(1), link, data[1], data[4], data[8] ]
		if (not apartmentID in apartments):
			apartments[apartmentID] = []

		apartments[apartmentID].append(apartment_info)

		if DEBUG is True:
			print("Request URL: " + URL)
			print("-- Found the following apartments -- ")
			print("Rooms: " + data[1])
			print("Address: " + address)
			print("Cost: " + data[4])
			print("Sqm: " + data[8])
			print("Listed on: " + domain.group(1))
			print("URL: " + link)
			return apartments
		else:
			return apartments


apartments_req = retrieve_apartments()
initTime = time.time()

while True:
	apartments_res = retrieve_apartments()
	for key in apartments_res.keys():
		if key not in apartments_req.keys():
			apartments_req[key] = apartments_res[key]
			address = apartments_req[key][0][0]
			source = apartments_req[key][0][1]
			url = apartments_req[key][0][2]
			rooms = apartments_req[key][0][3]
			cost = apartments_req[key][0][4]
			sqm = apartments_req[key][0][5]
			msg = "New apartment listed! \n[Rooms]: " + rooms + "\n[SQM]: " + sqm + "\n[Source]: " + source + "\n[Cost]: " + cost + "\n[URL]: " + url
			# IF no source preference, output any source - otherwise output specific source result
			if not KVALSTER_SOURCE:
				send_telegram_notification(msg)
			else:
				if source == KVALSTER_SOURCE:
					send_telegram_notification(msg)

	console_output = "[Uptime: " + str(time.strftime('%H:%M:%S', time.gmtime(round(time.time() - initTime)))) + "]"
	sys.stdout.write("%s   \r" % (console_output) )
	time.sleep(REFRESH_RATE)