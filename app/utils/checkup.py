import random
import time
import os
from bs4 import BeautifulSoup


def check_if_empty(fileName):
    """ Проверить что файл пустой,
    пустой - True
    не пустой - False"""

    # check if size of file is 0
    if os.stat(fileName).st_size == 0:
        return True
    return False