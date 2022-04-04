import json
import random
from time import sleep
from typing import Literal

import requests as request
from bs4 import BeautifulSoup as BS

from parser import parse_product


class Scraper:
    def __init__(
        self, HEADERS: dict[Literal["User-Agent"], str],
        PROXIES: list[dict[Literal["https"], str]]
    ) -> None:
        self.HEADERS = HEADERS
        self.PROXIES = PROXIES
        self.DOMAIN = "https://www.immobiliare.it"
        self.CATALOG_URL = f"{self.DOMAIN}/vendita-appartamenti/roma/"
        self.TIME_SLEEP = 15
        self.products = []

    def start_scraper(self) -> None:
        print("START SCRAPING")
        self.catalog_pages = self.get_pages()
        self.scrape_product_urls()
        self.scrape_products()

    def get_soup(self, url: str) -> BS:
        """
        get html page using response from request to `url`
        if not response -> request again
        if response with code 404 ->
            shuffle urls and request to another url,
            change proxies, sleep `self.TIME_SLEEP * 5`
        """
        response = None
        while not response:
            try:
                print(f"Get html from {url}")
                sleep(self.TIME_SLEEP)
                response = request.get(
                    url, headers=self.HEADERS,
                    proxies=random.choice(self.PROXIES)
                )
            except Exception as e:
                print(f"{e}\nTry Again...")
                continue
            else:
                print(response.status_code)
                if response.status_code == 404:
                    print(
                        f"Error: {response.status_code}\n"
                        "refresh urls, change proxy"
                        f" and sleep {self.TIME_SLEEP*5}"
                    )
                    random.shuffle(self.product_urls)
                    url = self.product_urls[0]
                    sleep(self.TIME_SLEEP*4)
                else:
                    print(f"Successful: {response.status_code}")
        return BS(response.text, 'lxml')

    def get_pages(self) -> list[str]:
        """ return all pages links of catalog web-page """
        print('get pages')
        soup = self.get_soup(self.CATALOG_URL)
        pages_from_soup = soup.find(
            'div', class_="in-pagination__list"
        ).find_all('div', class_="in-pagination__item")
        last_page_number = int(pages_from_soup[-1].text)
        return [self.CATALOG_URL] + [
            f"{self.CATALOG_URL}?pag={page}"
            for page in range(last_page_number+1) if page > 1
        ]

    def get_urls_from_file(self) -> list[str]:
        print("try to get urls from file")
        try:
            with open("product_urls.json", "r") as file:
                product_urls = json.load(file)
            print("Success")
        except FileNotFoundError:
            print("Failed, try to scrape")
            product_urls = []
        return product_urls

    def scrape_product_urls(self) -> list[dict[Literal["url"], str]]:
        """ scrape urls """
        print("scrape urls")
        self.product_urls = self.get_urls_from_file()
        if self.product_urls:
            return self.product_urls

        for counter, page in enumerate(self.catalog_pages, start=1):
            print(f"page {counter}/{len(self.catalog_pages)}")
            soup = self.get_soup(page)
            for card in soup.find_all('div', class_="in-card"):
                url = card.find('a', class_="in-card__title").get('href')
                self.product_urls.append({"url": url})
                self.save("product_urls")
        return self.product_urls

    def get_products_from_file(self) -> list:
        """ get products if already exists """
        try:
            with open('products.json', 'r') as file:
                products = json.load(file)
        except FileNotFoundError:
            products = []
        return products

    def scrape_products(self) -> list:
        """ scrape products """
        print("Scrape products")
        self.products = self.get_products_from_file()
        self.product_urls = list(map(
            lambda url: url['url'], self.product_urls))
        random.shuffle(self.product_urls)
        while self.product_urls:
            url = self.product_urls[0]
            try:
                soup = self.get_soup(url)
                product = parse_product(soup, url)
            except Exception as e:
                print(e)
                self.product_urls.pop(0)
                continue
            self.products.append(product)
            self.save("products")
            self.product_urls.pop(0)
        return self.products

    def save(self, filename: str) -> None:
        """ save file in root of project """
        with open(f"{filename}.json", 'w') as file:
            json.dump(self.products, file, indent=4, ensure_ascii=False)
