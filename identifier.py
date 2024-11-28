import json
import platform
import random
import webbrowser
import sys
from enum import Enum
from time import sleep
from datetime import datetime
from os import path, getenv, system
from dotenv import load_dotenv
from urllib.request import Request, urlopen
from requests import Session
from twilio.rest import Client
from plyer import notification

# Load environment variables

load_dotenv()
# Constants
WIN_PLT = "Windows"
LIN_PLT = "Linux"
ALERT_DELAY = int(getenv('ALERT_DELAY', 5))
MIN_DELAY = int(getenv('MIN_DELAY', 1))
MAX_DELAY = int(getenv('MAX_DELAY', 3))
USE_SELENIUM = getenv('WEBDRIVER_PATH') is not None
OPEN_WEB_BROWSER = getenv('OPEN_WEB_BROWSER', 'false').lower() == 'true'
USE_TWILIO = getenv('TWILIO_SID') and getenv('TWILIO_AUTH') and getenv('TWILIO_TO_NUM') and getenv('TWILIO_FROM_NUM')



# Enum for methods
class Methods(str, Enum):
    GET_SELENIUM = "GET_SELENIUM"
    GET_URLLIB = "GET_URLLIB"

# Setup WebDriver if Selenium is enabled
if USE_SELENIUM:
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.firefox.service import Service

    WEBDRIVER_PATH = path.normpath(getenv('WEBDRIVER_PATH'))
    Service = Service(executable_path=WEBDRIVER_PATH)
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options, service=Service)

# Twilio Setup
if USE_TWILIO:
    client = Client(getenv('TWILIO_SID'), getenv('TWILIO_AUTH'))

# Helper function for random user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/92.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.67",
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

# Load websites
with open('websites.json', 'r') as f:
    sites = json.load(f)

# Notification system
def os_notification(title, text):
    try:
        notification.notify(title=title, message=text, timeout=10)
    except Exception as e:
        print(f"Error sending notification: {e}")

# Web scraping logic
def get_page_source(method, url):
    if method == Methods.GET_SELENIUM and USE_SELENIUM:
        return selenium_get(url)
    return urllib_get(url)

def selenium_get(url):
    driver.get(url)
    return driver.page_source

def urllib_get(url):
    headers = {'User-Agent': get_random_user_agent()}
    request = Request(url, headers=headers)
    with urlopen(request) as page:
        return page.read().decode("utf-8")

# Alert the user when the keyword is found
def alert(site):
    product = site['name']
    print(f"{product} IN STOCK")
    print(site['url'])
    if OPEN_WEB_BROWSER:
        webbrowser.open(site['url'], new=1)
    os_notification(f"{product} IN STOCK", site['url'])
    sleep(ALERT_DELAY)

# Send SMS using Twilio
def send_sms(url, name):
    if USE_TWILIO:
        message = client.messages.create(
            to=getenv('TWILIO_TO_NUM'),
            from_=getenv('TWILIO_FROM_NUM'),
            body=f"{name} is in stock: {url}"
        )
        print(f"Twilio log: {message.sid}")

# Main function
def main():
    search_count = 0
    while True:
        now = datetime.now()
        print(f"Search starting {search_count} at {now.strftime('%H:%M:%S')}")
        search_count += 1
        for site in sites:
            if site.get("enabled"):
                print(f"\tChecking {site['name']} ...")
                try:
                    html = get_page_source(Methods[site['method']], site['url'])
                    keyword = site['keyword']
                    alert_on_found = site['alert']
                    index = html.upper().find(keyword.upper())
                    if (alert_on_found and index != -1) or (not alert_on_found and index == -1):
                        alert(site)
                except Exception as e:
                    print(f"\t\tConnection failed: {e}")
                    continue

                # Random delay between checks
                sleep(random.uniform(MIN_DELAY, MAX_DELAY))

if __name__ == '__main__':
    main()
