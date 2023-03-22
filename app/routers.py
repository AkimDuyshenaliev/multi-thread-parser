from fastapi import APIRouter
from .threads import ParsingWithProxy
from app.utils.parse import proxy_generator
from threading import Lock


router = APIRouter(
    tags=["AvitoScraper"],
    prefix="/avito-scraper",
)


@router.post('/address', status_code=201)
def get_avito_product_link(threads, address):
    main_file = 'app/static/stars_and_comments.csv'

    lock = Lock() # Initialize lock object
    proxies = proxy_generator()  # Get proxies
    num_of_threads = int(threads)
    th = [ParsingWithProxy(
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