import os
import requests
from bs4 import BeautifulSoup, SoupStrainer
from dotenv import find_dotenv, load_dotenv
import csv

load_dotenv(find_dotenv())
URL = os.getenv('URL')
links = set()
data = {}


def get_categories():
    """Get category links from main page."""
    r = requests.get(URL)
    r.raise_for_status()
    menu = SoupStrainer('div', id='mainmenu')
    soup = BeautifulSoup(r.content, features='lxml', parse_only=menu)
    for category in soup.find_all(href=True):
        links.add(category.get('href'))


def scrape(category):
    page = f'{URL}{category}?product_all=1'
    print(page)
    r = requests.get(page)
    soup = BeautifulSoup(r.content, features='lxml')
    cards = soup.find_all('div', attrs={'class': 'pad'})
    cats = soup.find_all('div', attrs={'class': 'category'})
    if cats:
        links.update([i.a['href'] for i in cats])
    else:
        links.remove(category)
        title = soup.title.string.split(' - ')[0]
        data[title] = {}
        for card in cards:
            article = card.find('div', attrs={'class': 'art'}).get_text().split(' ', 1)[1]
            price = card.find('div', attrs={'class': 'price'}).get_text().encode('ascii', 'ignore')
            data[title][article] = price


def traverse():
    get_categories()
    for cat in set(links):
        scrape(cat)
        # print(data)
        # break

    with open('output.csv', 'w', encoding='utf-8') as csv_file:
        csvwriter = csv.writer(csv_file, delimiter='\t')
        for cat in data:
            for item in data[cat]:
                csvwriter.writerow([cat, item, data[cat][item]])


if __name__ == '__main__':
    traverse()
