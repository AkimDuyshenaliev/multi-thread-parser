from fastapi import APIRouter
from .threads import ParsingWithProxy
from app.utils.parse import get_product_main_page, proxy_generator
from threading import Lock

import sys
import errno


router = APIRouter(
    tags=["AvitoScraper"],
    prefix="/avito-scraper",
)


@router.post('/address', status_code=201)
def get_avito_product_link(addresses: list, threads: int | None = None):
    main_file = 'app/static/stars_and_comments.csv'

    lock = Lock() # Initialize lock object
    proxies = proxy_generator()  # Get proxies
    num_of_threads = int(threads) if threads else 5
    for address in addresses:
        try:
            main_page = get_product_main_page(address=address)
            th = [ParsingWithProxy(
                main_page=main_page,
                page_num=i, 
                step=num_of_threads, 
                address=address,
                main_file=main_file,
                proxies=proxies,
                lock=lock) for i in range(1, num_of_threads+1)]

            for proxy in th:
                proxy.start()

            for proxy in th:
                proxy.join()
        except IOError as e:
            if e.errno == errno.EPIPE: # Handling broken pipe error
                pass