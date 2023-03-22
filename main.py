import os
from bs4 import BeautifulSoup, SoupStrainer
from dotenv import find_dotenv, load_dotenv
import csv
import asyncio
import aiohttp
import time
import coloredlogs
import logging
import re
import unicodedata
from aiohttp_retry import RetryClient, ExponentialRetry

load_dotenv(find_dotenv())
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG')


class Parser:
    def __init__(self):
        self.URL = os.getenv('URL')
        if self.URL is None:
            raise EnvironmentError('URL not specified.')
        self.data = {}
        self.done = set()
        self.session = None

    async def get_categories(self):
        """Get category links from main page."""
        response_text = await self.fetch(self.URL)
        menu = SoupStrainer('div', id='mainmenu')
        soup = BeautifulSoup(response_text, 'lxml', parse_only=menu)
        links = [category.get('href') for category in soup.find_all(href=True)]
        await self.add_tasks(links)

    async def fetch(self, url: str):
        retry_options = ExponentialRetry(attempts=5)
        retry_client = RetryClient(client_session=self.session, retry_options=retry_options)
        async with retry_client.get(url, ssl=False) as response:
            logger.debug(f'>>> Fetching page {url}')
            return await response.text()

    async def scrape(self, category: str):
        if category in self.done:
            return
        page = f'{self.URL}{category}?product_all=1'
        response_text = await self.fetch(page)
        logger.debug(f'<<< Fetched page {page}')
        self.done.add(category)
        soup = BeautifulSoup(response_text, 'lxml')
        cards = soup.find_all('div', attrs={'class': 'pad'})
        cats = soup.find_all('div', attrs={'class': 'category'})
        if cats:
            new_links = [i.a['href'] for i in cats]
            add_links = [i for i in new_links if 'category' in i]
            await self.add_tasks(add_links)
        else:
            title = soup.title.string.split(' - ')[0]
            title = unicodedata.normalize('NFKC', title)
            cat_data = {title: {}}
            for card in cards:
                article = card.find('div', attrs={'class': 'art'}).get_text().split(' ', 1)[1]
                article = unicodedata.normalize('NFKC', article)
                price = card.find('div', attrs={'class': re.compile(r'^price')}).get_text()
                price = unicodedata.normalize('NFKC', price).replace(' ', '')
                cat_data[title][article] = float(price)
            self.data.update(cat_data)
            logger.info(f'Parsed {category}')

    async def add_tasks(self, links: list[str]):
        links = {cat for cat in links if cat not in self.done}
        tasks = [self.scrape(link) for link in links]
        if tasks:
            await asyncio.gather(*tasks)
            logger.debug(f'Added links: {links}')

    async def main(self):
        async with aiohttp.ClientSession() as session:
            self.session = session
            await self.get_categories()

        # wait for tasks to finish
        all_tasks = asyncio.all_tasks()
        current_task = asyncio.current_task()
        all_tasks.remove(current_task)
        if all_tasks:
            await asyncio.wait(all_tasks)
        else:
            await self.session.close()
            self.export()

    def export(self):
        with open('output.csv', 'w', newline='', encoding='utf-8') as csv_file:
            csvwriter = csv.writer(csv_file)
            csvwriter.writerow(['category', 'article', 'price'])
            for cat in self.data:
                for item in self.data[cat]:
                    csvwriter.writerow([cat, item, self.data[cat][item]])

        print('Total pages parsed:', len(self.done))
        print('Categories:', len(self.data))
        print('Time:', time.time() - start_time)


if __name__ == '__main__':
    start_time = time.time()
    asyncio.run(Parser().main())
