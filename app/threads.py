import os
import gc
import csv

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
        proxy_status = False # False - proxy need's to change, True - proxy is good
        temp_file_path = f'app/static/temp/Temp-{current_thread().name}.csv' 

        writer = csv.writer(tempFile)  # Create a writer
        with open(temp_file_path, 'w', encoding='UTF8') as tempFile:

            while True:
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
                    del result # Mark for cleaning
                    gc.collect() # Clear memory
                    break

                result = prepare_data(self.main_page['name'], self.main_page['link'], data)
                writer.writerow(result) # Write data into the temp file
                print(f'{color_yellow}{page_num} written into the temp file{color_end}')
                page_num += self.step
                tempFile.flush() # Flush the internal buffer
                os.fsync(tempFile.fileno()) # Sync internal buffer and file, and force data to be written to hard drive

        with self.lock:
            write_to_csv(main_file=self.fileLocation, temp_file=temp_file_path)
        print(f'{color_green}{current_thread().name} finished on page {page_num - self.step}{color_end}')

        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print(f'{color_green}{current_thread().name} temp file cleared{color_end}')