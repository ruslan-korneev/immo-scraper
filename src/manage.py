import os

from dotenv import load_dotenv

from scraper import Scraper


load_dotenv()

proxies = os.environ.get('PROXIES', None)
if proxies:
    PROXIES = [{"https": proxy} for proxy in proxies.split(',')]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/99.0.4844.84 Safari/537.36"
    )
}

if __name__ == '__main__':
    scraper = Scraper(HEADERS, PROXIES)
    scraper.start_scraper()
