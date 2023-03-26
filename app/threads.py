import gc

from seleniumwire import webdriver
from app.utils.parse import (
            get_comments, 
            check_ip, 
            prepare_data)
from app.utils.scrape import write_to_csv
from seleniumwire import webdriver
from threading import Thread, current_thread
from app.utils.colors import color_end, color_green, color_red, color_yellow


class ParsingWithProxy(Thread):
    def __init__(self, srv, options, main_page, fileLocation, page_num, step, proxies, lock):
        super().__init__()
        self.driver = webdriver.Chrome(service=srv, options=options)
        self.main_page = main_page
        self.fileLocation = fileLocation
        self.page_num = page_num
        self.step = step
        self.proxies = proxies
        self.lock = lock

    def run(self):
        driver = self.driver
        page_num = self.page_num
        saved_pages = 0
        proxy_status = False # False - proxy need's to change, True - proxy is good
        result = []

        while True:
            if saved_pages == 3:
                with self.lock:
                    write_to_csv(scraper_result=result, main_file=self.fileLocation)

                print(f'{color_green}Saved pages on {current_thread().name} = {saved_pages}, dumping and clearing memory{color_end}')
                del result # Mark for cleaning
                gc.collect() # Clear memory
                saved_pages = 0
                result = []

            if proxy_status is False:
                with self.lock:
                    proxy = next(self.proxies)
                driver.proxy = {'http':'http://%s:%s' % (proxy['ip'], proxy['port'])}
                print(f'{color_yellow}Page: {page_num}, selected proxy {driver.proxy}{color_end}')
                proxy_status = True
               
            try:
                if self.main_page is False: # If an error occurred then try another proxy
                    proxy_status = False
                    continue

                data = get_comments(
                    driver=driver,
                    page_num=page_num,
                    proxy_status=proxy_status,
                    comments_link=self.main_page['link'])
            except:
                print(f'{color_red}Exception on page {page_num}, choosing another proxy and trying again{color_end}')
                proxy_status = False
                continue
            
            if data is False:  # If parser returns False then select another parser and restart
                proxy_status = False
                continue
            if data is True:  # If parser returns True then there is no more comments
                with self.lock:
                    write_to_csv(scraper_result=result, main_file=self.fileLocation)

                print(f'{color_green}{current_thread().name} finished on page {page_num - self.step}{color_end}')
                del result # Mark for cleaning
                gc.collect() # Clear memory
                break

            saved_pages += 1
            result += prepare_data(self.main_page['name'], self.main_page['link'], data)
            page_num += self.step
