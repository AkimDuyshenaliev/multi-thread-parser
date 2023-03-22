import re
import csv
from bs4 import BeautifulSoup
from app.utils.checkup import check_if_empty


def avito_scraper(soup):
    ''' This function will take a link to comments of a product from "https://www.avito.ru/"
        and parse it to get every comment that has "Дополнительно" in it
        it will also take the number of stars that this comment gave to the product '''

    ### No comments, return False to stop the loop
    if soup.find('div', attrs={'class':'EmptyState-wrapper-_UnmQ'}):
        return False
    
    # Find all "div" of the comment body with class name
    comments_body = soup.find_all(
        'div',
        attrs={'class': 'ReviewModelSnippet-root-kb0P5 sizes-author-avatar-sizes-oVHTX'})

    # Check for errors, if list is empty then proxy needs to change
    if comments_body == []:
        print('--- --- --- Comments not found, list is empty')
        return []
    print('--- --- --- Found comments')

    stars_and_text = []
    search_string = re.compile('Дополнительно[:]?')
    for comment in comments_body:  # Iterate every found element
        review_body = comment.find(
            'div', attrs={'class': 'ReviewBody-body-LG28b'})
        try:
            # In the found comment body find span element with a certain class and text content
            # then look for it's sibling and get it's text
            review_text = review_body.find(
                'span',
                attrs={'class': 'desktop-1exxyw0'},
                text=search_string).next_sibling.contents[0].contents[0].text
            re.sub('[^A-Za-z0-9]+', '', review_text)
            review_text = ' '.join(review_text.split('\n'))
            print('--- --- --- Found "Дополнительно"')
        except:
            continue

        # Find div with stars and iterate over it to find how many yellow stars there are
        stars = review_body.find(
            'div', attrs={'class': 'RatingStars-root-Edhhx'})
        stars_count = len(([1 for star in stars
                            if re.search('yellow', star.contents[0]['class'][1])]))
        stars_and_text.append([stars_count, review_text])
        print('--- --- --- Parsed successfully, returning')
    return stars_and_text


def write_to_csv(scraper_result, main_file):
    header = ['product', 'stars', 'comment', 'productlink']

    with open(main_file, 'a', encoding='UTF8') as base_file:
        writer = csv.writer(base_file)  # Create a writer

        if check_if_empty(main_file) is True:
            writer.writerow(header)  # Create the header
        writer.writerows(scraper_result)  # Write data
