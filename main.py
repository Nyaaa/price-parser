import os
from bs4 import BeautifulSoup, SoupStrainer
from dotenv import find_dotenv, load_dotenv
import csv
import asyncio
import aiohttp
import time

load_dotenv(find_dotenv())


class Parser:
    def __init__(self):
        self.URL = os.getenv('URL')
        self.data = {}
        self.done = []
        self.session = None

    async def get_categories(self):
        """Get category links from main page."""
        links = set()
        async with self.session.get(url=self.URL) as response:
            response_text = await response.text()
            menu = SoupStrainer('div', id='mainmenu')
            soup = BeautifulSoup(response_text, 'lxml', parse_only=menu)
            for category in soup.find_all(href=True):
                links.add(category.get('href'))
            return links

    async def scrape(self, category):
        if category in self.done:
            return
        page = f'{self.URL}{category}?product_all=1'
        self.done.append(category)

        async with self.session.get(url=page) as response:
            response_text = await response.text()
            soup = BeautifulSoup(response_text, 'lxml')

            cards = soup.find_all('div', attrs={'class': 'pad'})
            cats = soup.find_all('div', attrs={'class': 'category'})
            if cats:
                new_links = [i.a['href'] for i in cats]
                add_links = [i for i in new_links if 'category' in i]
                await self.add_tasks(add_links)
            else:
                # self.done.append(category)
                title = soup.title.string.split(' - ')[0]
                cat_data = {title: {}}
                for card in cards:
                    article = card.find('div', attrs={'class': 'art'}).get_text().split(' ', 1)[1]
                    price = card.find('div', attrs={'class': 'price'}).get_text().encode('ascii', 'ignore')
                    cat_data[title][article] = float(price)
                self.data.update(cat_data)
                print(category)

    async def add_tasks(self, links):
        async with asyncio.TaskGroup() as tg:
            for cat in links:
                if cat not in self.done:
                    tg.create_task(self.scrape(cat))

    async def main(self):
        async with aiohttp.ClientSession() as session:
            self.session = session
            links = await self.get_categories()
            await self.add_tasks(links)

        # wait for tasks to finish
        all_tasks = asyncio.all_tasks()
        current_task = asyncio.current_task()
        all_tasks.remove(current_task)
        if all_tasks:
            await asyncio.wait(all_tasks)
        else:
            self.export()

    def export(self):
        with open('output.csv', 'w', newline='', encoding='utf-8') as csv_file:
            csvwriter = csv.writer(csv_file)
            for cat in self.data:
                for item in self.data[cat]:
                    csvwriter.writerow([cat, item, self.data[cat][item]])

        print('Total pages parsed:', len(self.done))
        print('Categories:', len(self.data))
        print('Time:', time.time() - start_time)


if __name__ == '__main__':
    start_time = time.time()
    asyncio.run(Parser().main())
