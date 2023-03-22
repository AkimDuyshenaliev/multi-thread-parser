from seleniumwire import webdriver
from app.utils.parse import (
            get_product_main_page, 
            get_comments, 
            check_ip, 
            prepare_data,
            options,
            srv)
from app.utils.scrape import write_to_csv
from seleniumwire import webdriver
from threading import Thread
from app.utils.colors import color_end, color_green, color_red, color_yellow


class ParsingWithProxy(Thread):
    def __init__(self, page_num, step, address, main_file, proxies, lock):
        super().__init__()
        self.driver = webdriver.Chrome(service=srv, options=options)
        self.page_num = page_num
        self.step = step
        self.address = address
        self.main_file = main_file
        self.proxies = proxies
        self.lock = lock

    def run(self):
        driver = self.driver
        page_num = self.page_num
        proxy_status = False
        main_page = None
        result = []

        while True:
            if proxy_status is False:
                with self.lock:
                    proxy = next(self.proxies)
                driver.proxy = {'http':'http://%s:%s' % (proxy['ip'], proxy['port'])}
                print(f'{color_yellow}Page: {page_num}\nSelected proxy {driver.proxy}{color_end}')
                proxy_status = True
               
            try:
                # check_ip(driver=driver)
                if main_page is None: # If there is no product name and comments link then get them
                    main_page = get_product_main_page(driver=driver, address=self.address)
                if main_page is False: # If an error occurred then try another proxy
                    proxy_status = False
                    continue

                data = get_comments(
                    driver=driver,
                    page_num=page_num,
                    proxy_status=proxy_status,
                    comments_link=main_page['link'])
            except:
                print(f'{color_red}Exception on page {page_num}, choosing another proxy and trying again{color_end}')
                proxy_status = False
                continue
            

            if data is False:  # If parser returns False then select another parser and restart
                proxy_status = False
                continue
            if data is True:  # If parser returns True then there is no more comments
                break

            print(f'Data for page {page_num} {data}')
            result = prepare_data(main_page['name'], self.address, data)
            page_num += self.step

        with self.lock:
            write_to_csv(scraper_result=result, main_file=self.main_file)