import os
import time
from fastapi import APIRouter
from starlette.responses import FileResponse
from .threads import ParsingWithProxy
from app.utils.parse import get_product_main_page, proxy_generator, srv, options
from threading import Lock


router = APIRouter(
    tags=["AvitoScraper"],
    prefix="/avito-scraper",
)


@router.post('/avito-product', status_code=201)
def get_avito_product_link(addresses: list, threads: int | None = None):
    fileLocation = 'app/static/stars_and_comments.csv'
    
    lock = Lock() # Initialize lock object
    proxies = proxy_generator()  # Get proxies
    num_of_threads = threads if threads else 5
    os.mkdir('app/static/temp') # Create a temporary directory

    for address in addresses:
        main_page = get_product_main_page(address=address)
        th = [ParsingWithProxy(
            srv=srv,
            options=options,
            main_page=main_page,
            fileLocation=fileLocation,
            page_num=i, 
            step=num_of_threads, 
            proxies=proxies,
            lock=lock) for i in range(1, num_of_threads+1)]

        for proxy in th:
            proxy.start()
            time.sleep(1)

        for proxy in th:
            proxy.join()

    os.rmdir('app/static/temp') # Delete temporary directory
    return FileResponse("app/static/stars_and_comments.csv")