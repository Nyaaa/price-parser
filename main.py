import os
import requests
from bs4 import BeautifulSoup, SoupStrainer
from dotenv import find_dotenv, load_dotenv
import re
import csv

load_dotenv(find_dotenv())
URL = os.getenv('URL')


def get_categories():
    """Get category links from main page."""
    r = requests.get(URL)
    r.raise_for_status()
    links = []
    menu = SoupStrainer('div', id='mainmenu')
    soup = BeautifulSoup(r.content, features='lxml', parse_only=menu)
    for category in soup.find_all(href=True):
        links.append(category.get('href'))
    return links


def scrape(page):
    print(page)
    r = requests.get(page)
    soup = BeautifulSoup(r.content, features='lxml')
    cards = soup.find_all('div', attrs={'class': 'pad'})
    print(cards)


def traverse():
    categories = get_categories()
    for cat in categories[:10]:
        if bool(re.search(r'\d', cat)):
            scrape(f'{URL}{cat}?product_all=1')
        else:
            print(cat)


if __name__ == '__main__':
    traverse()
