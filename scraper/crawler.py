import re
import requests

from urllib.parse import urljoin
from bs4 import BeautifulSoup
from typing import List, Optional
from utils.time_util import time_block


class Crawler:
    def __init__(self, ticker: str, exchange: str):
        self.ticker = ticker
        self.exchange = exchange
        self.soup = None
        self.instrument_id = ""
        self.init()

    def init(self):
        resp = requests.get(
            f"https://www.fool.com/quote/{self.exchange.lower()}/{self.ticker.lower()}/"
        )
        self.soup = BeautifulSoup(resp.text, "html.parser")

    @staticmethod
    def parse_raw_slugs(slugs: List[str]) -> List[str]:
        return [s.strip().replace('\\"', "").replace("\\n", "") for s in slugs]

    @staticmethod
    def join_and_validate(slugs: List[str]) -> List[str]:
        base_url = "https://www.fool.com"
        joined_urls = [urljoin(base_url, slug.lstrip()) for slug in slugs]
        r = re.compile(r"^https://www\.fool\.com/earnings/call-transcripts/[\w\-/]+/$")
        return [url for url in joined_urls if r.match(url)]

    def parse_a_elements(self):
        raw_slugs = [a.attrs["href"] for a in self.soup.find_all("a")]
        return self.parse_raw_slugs(raw_slugs)

    @time_block("Crawling for URLs")
    def crawl(self) -> Optional[List[str]]:
        try:
            instrument_id = self.soup.find(
                "meta", attrs={"name": "instrument_ids"}
            ).attrs["content"]
        except Exception as e:
            print(e)
        self.instrument_id = instrument_id

        params = {"page": 1, "per_page": 10}
        resp = requests.get(
            f"https://www.fool.com/dubs/ajax/quote/articles_by_page/{self.instrument_id}/earnings_transcripts",
            params=params,
        )
        self.soup = BeautifulSoup(resp.text, "html.parser")
        clean_slugs = self.parse_a_elements()

        final_urls = self.join_and_validate(clean_slugs)

        return final_urls


if __name__ == "__main__":
    c = Crawler("V", "nyse")
    urls = c.crawl()
    print(urls)
