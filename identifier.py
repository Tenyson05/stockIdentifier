import json
import platform
import random
import webbrowser
import sys
from enum import Enum
from time import sleep
from datetime import datetime, time
from os import path, getenv, system
from dotenv import load_dotenv
from urllib.request import urlopen, Request


platform = platform.system()
WIN_PLT = "Windows"
WIN_LIN = "Linux"

class Methods(str, Enum):
	GET_SELENIUM = "GET_SELENIUM"
	GET_URLLIB = "GET_URLLIB"
	GET_API = "GET_API"

load_dotenv()
USE_SELENIUM = False
WEBDRIVER_PATH = path.normpath(getenv('WEBDRIVER_PATH'))
ALERT_DELAY = int(getenv('ALERT_DELAY'))
MIN_DELAY = int(getenv('MIN_DELAY'))
MAX_DELAY = int(getenv('MAX_DELAY'))
OPEN_WEB_BROWSER = getenv('OPEN_WEB_BROWSER') == 'true'

#get the links from a json file
with open('websites.json', 'r') as f:
	sites = json.load(f)


#Setup selenium
if WEBDRIVER_PATH:
	USE_SELENIUM = True
	print("Starting Selenium... ")
	from selenium import webdriver
	from selenium.webdriver.firefox.options import Options

	options = Options()
	options.headless = True
	driver = webdriver.Firefox(options=options, executable_path=WEBDRIVER_PATH)
	reload_count = 0
	print("Done!")


#Windows settings
print("Running on {}".format(platform))
if platform == WIN_PLT:
	from win10toast import ToastNotifier

	toast = ToastNotifier()

def alert(site):
	product = site.get('name')
	print("{} IN STOCK".format(product))
	print(site.get('url'))
	if OPEN_WEB_BROWSER:
		webbrowser.open(site.get('url'), new=1)
	os_notification("{} IN STOCK".format(product), site.get('url'))
	sleep(ALERT_DELAY)

def os_notification(title, text):
	if platform == WIN_PLT:
		toast.show_toast(title, text, duration=5)
	elif platform == WIN_LIN:
		try:
			system('notify-send "{}" "{}" -i {}'.format(title, text))
		except:
			#no sound on linux
			pass

def selenium_get(url):
	global driver
	global reload_count

	driver.get(url)
	http = driver.page_source

	reload_count += 1
	if reload_count == 10:
		reload_count = 0
		driver.close()
		driver.quit()
		driver = webdriver.Firefox(options=options, executable_path=WEBDRIVER_PATH)
	return http

def urllib_get(url):
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    page = urlopen(request, timeout=30)
    html_bytes = page.read()
    html = html_bytes.decode("utf-8")
    return html

# use to do a test 
def test():
	try:
		if sys.argv[1] == 'test':
			alert(sites[0])
			print("Test complete, if you got this bro")
			return True
	except:
		return False

def main():
	search_count = 0

	exit() if test() else False

	while True:
		now  = datetime.now()
		current_time = now.strftime("%H:%M:%S")
		print("Search starting {} at {}".format(search_count, current_time))
		search_count += 1
		for site in sites:
			if site.get("enabled"):
				print("\tCHecking {} ...".format(site.get('name')))

				try:
					if site.get('method') == Methods.GET_SELENIUM:
						if not USE_SELENIUM:
							continue
						html = selenium_get(site.get('url'))
					else:
						html = urllib_get(site.get('url'))
				except Exception as e:
					print("\t\tConnection failed...")
					print("\t\t{}".format(e))
					continue
				keyword = site.get('keyword')
				alert_on_found = site.get('alert')
				index = html.upper().find(keyword.upper())
				if alert_on_found and index != -1:
					alert(site)
				elif not alert_on_found and index == -1:
					alert(site)
				
				base_sleep = 1
				total_sleep = base_sleep + random.uniform(MIN_DELAY, MAX_DELAY)
				sleep(total_sleep)

if __name__ == '__main__':
	main()