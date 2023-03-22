import random
import time

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.proxy import *

from fastapi import HTTPException
from bs4 import BeautifulSoup

from app.utils.scrape import avito_scraper
from seleniumwire import webdriver
from app.utils.colors import color_end, color_green, color_red, color_yellow


# Selenium configurations

prefs = {'profile.default_content_setting_values': {
    'cookies': 2, 'images': 2, 'javascript': 2,
    'plugins': 2, 'popups': 2, 'geolocation': 2,
    'notifications': 2, 'auto_select_certificate': 2, 'fullscreen': 2,
    'mouselock': 2, 'mixed_script': 2, 'media_stream': 2,
    'media_stream_mic': 2, 'media_stream_camera': 2, 'protocol_handlers': 2,
    'ppapi_broker': 2, 'automatic_downloads': 2, 'midi_sysex': 2,
    'push_messaging': 2, 'ssl_cert_decisions': 2, 'metro_switch_to_desktop': 2,
    'protected_media_identifier': 2, 'app_banner': 2, 'site_engagement': 2,
    'durable_storage': 2
}}

options = Options()
options.add_argument("--headless=new")
options.add_argument("disable-infobars")
options.add_argument("--disable-extensions")
options.add_argument('--blink-settings=imagesEnabled=false')
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage") # overcome limited resource problems
options.add_argument('--disable-gpu')
options.add_experimental_option('prefs', prefs)

# Adding argument to disable the AutomationControlled flag
options.add_argument("--disable-blink-features=AutomationControlled")
# Exclude the collection of enable-automation switches
options.add_experimental_option("excludeSwitches", ["enable-automation"])
# Turn-off userAutomationExtension
options.add_experimental_option("useAutomationExtension", False)

#####
user_agent = 'Mozilla/5.0 CK={} (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'

options.add_argument("user-agent=" + user_agent)
#####

srv = Service(ChromeDriverManager().install())


def get_driver_requests(driver_requests, url):
    # Access requests via the `requests` attribute
    for request in driver_requests:
        if request.response and request.url == url:
            # print('Headers', request.response.headers['Content-Type'])
            return request.response.status_code


def check_ip(driver):
    time.sleep(random.randint(3, 5))
    driver.get('https://www.expressvpn.com/what-is-my-ip')
    ip_page = driver.page_source
    soup = BeautifulSoup(ip_page, 'html.parser')
    try:
        my_ip = soup.find('h4', attrs={'class': 'ip-address'}).text
        print(f'{color_green}My ip: {my_ip.strip()}{color_end}')
    except:
        error = soup.find('h1').text
        print(f'{color_red}Error - {error.strip()}{color_end}')


def check_status_code(driver, url):
    status_code = get_driver_requests(
        driver_requests=driver.requests, url=url)
    return status_code


def proxy_generator():
    '''
    Get a list of proxy ip and ports
    and return then as generator
    '''

    driver = webdriver.Chrome(service=srv, options=options)
    while True:
        print('Getting proxy page')
        driver.get("https://sslproxies.org/")  # Get a page with proxy ips
        proxy_page = driver.page_source

        proxy_soup = BeautifulSoup(proxy_page, 'html.parser')
        table_body_elements = proxy_soup.find(
            'table', attrs={'class': 'table table-striped table-bordered'})\
            .find('tbody')\
            .find_all('tr')  # Find element that has proxy ip and port
        print(f'{color_green}Proxy found{color_end}')

        proxies = []
        for element in table_body_elements:  # Extract ip and port and combine them
            proxies.append({
                'ip': element.contents[0].text, 
                'port': element.contents[1].text})

        while len(proxies) != 0:
            yield proxies.pop()
    


def prepare_data(product_name, address, data):
    result = []
    [element.insert(0, product_name) for element in data]
    [element.append(address) for element in data]

    # Append scraped data to 'result' list
    [result.append(tuple(element))
        for element in data]
    result.append(data)
    return result


def get_product_main_page(driver, address):
    '''
    Use address and get the main page source,
    check if the IP is blocked, if yes then return empty list [],
    if IP is not blocked from page source find product name and link to comments section,
    then return product name and link
    '''
    print('Getting product page')
    driver.get(address)  # Get avito product page
    avito_page = driver.page_source
    avito_soup = BeautifulSoup(avito_page, 'html.parser')

    # Check if IP was blocked, if it is return false to try another proxy
    if avito_soup.title.text == 'Доступ ограничен: проблема с IP':
        print(f'{color_red}IP blocked{color_end}')
        return False

    product_name = avito_soup.find(
        'span', attrs={'class': 'title-info-title-text'}).text  # Find product name
    comments_link = avito_soup.find(
        'a', attrs={'class': 'link-link-MbQDP link-design-default-_nSbv'})['href']  # Find the link to comments

    if product_name == None or comments_link == None:
        print(f'{color_red}Comments not found{color_end}')
        return False

    time.sleep(random.randint(2, 5))
    print(f'{color_green}Found comments page and slept, returning{color_end}')
    return {'name': product_name, 'link': comments_link}


def get_comments(driver, page_num, proxy_status, comments_link):
    '''
    Iterate over comment on a page and collect them.
    When there is no more comment pages return everything
    '''
    base_url = 'https://www.avito.ru/'
    page_end_url = '&reviewsPage='
    print(f'Getting page num {page_num}')

    url = base_url + \
        comments_link + page_end_url + str(page_num)

    driver.get(url)
    page = driver.page_source

    # AssistTools().check_status_code(url=url)

    soup = BeautifulSoup(page, 'html.parser')

    # Check if IP was blocked, if it is return false to try another proxy
    if soup.title.text == 'Доступ ограничен: проблема с IP':
        print(f'{color_red}IP blocked, selecting new proxy{color_end}')
        proxy_status = False
        return proxy_status

    # Scrape data from the page
    data = avito_scraper(soup=soup)

    if data == []:  # If data is empty then try again with a new proxy
        print(f'{color_red}Empty data, selecting new proxy{color_end}')
        proxy_status = False
        return proxy_status
    if data is False:  # No more comments, stop the loop
        return True

    print(f'{color_green}OK, sleeping and going to the next page{color_end}')
    time.sleep(random.randint(2, 5))  # Sleep from 2 to 5 seconds

    return data
