import re
import requests

from urllib.parse import urljoin
from bs4 import BeautifulSoup
from typing import List, Optional
from utils.constants import URL_REGEX
from utils.io import get_cached_instrument_id, store_instrument_id, pick_useragent
from utils.time_util import polite_sleep, time_block


class Crawler:
    def __init__(self, ticker: str, exchange: str):
        self.ticker = ticker.lower()
        self.exchange = exchange
        self.soup = None
        self.instrument_id = ""
        self.session = requests.Session()
        # self.session.headers = {
        #     "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        #     "accept-encoding": "gzip, deflate, br, zstd",
        #     "accept-language": "en-US,en;q=0.9,de;q=0.8",
        #     "connection": "keep-alive",
        #     "dnt": "1",
        #     "referer": "https://www.fool.com/earnings-call-transcripts/",
        #     "user-agent": pick_useragent(),
        # }
        resp = self.session.get("https://www.fool.com")

    @staticmethod
    def parse_raw_slugs(slugs: List[str]) -> List[str]:
        return [s.strip().replace('\\"', "").replace("\\n", "") for s in slugs]

    @staticmethod
    def join_and_validate(slugs: List[str]) -> List[str]:
        base_url = "https://www.fool.com"
        joined_urls = [urljoin(base_url, slug.lstrip()) for slug in slugs]
        r = re.compile(URL_REGEX)
        return [url for url in joined_urls if r.match(url)]

    def write_error_page(self, resp: str):
        with open(f"error-log-{self.ticker}.html", "w+") as f:
            f.write(str(self.soup))

    def parse_a_elements(self):
        raw_slugs = [a.attrs["href"] for a in self.soup.find_all("a")]
        return self.parse_raw_slugs(raw_slugs)

    @polite_sleep()
    def fetch_instrument_id(self) -> str:
        try:
            # breakpoint()
            resp = self.session.get(
                f"https://www.fool.com/quote/{self.exchange.lower()}/{self.ticker.lower()}/",
            )
            self.soup = BeautifulSoup(resp.text, "html.parser")
            meta_tag = self.soup.find("meta", attrs={"name": "instrument_ids"})
            if not meta_tag:
                raise Exception("Could not find instrument_id <meta> tag")
            instrument_id = meta_tag.attrs["content"]
            if not instrument_id:
                raise Exception("<meta> tag did not have instrument_id")
            return instrument_id
        except Exception as e:
            self.write_error_page(self.soup)
            print(f"fetch_instrument_id exception: {e}")

    @polite_sleep()
    def fetch_url_slugs(self, n: int = 50) -> List[str]:
        params = {"page": 1, "per_page": n}
        resp = self.session.get(
            f"https://www.fool.com/dubs/ajax/quote/articles_by_page/{self.instrument_id}/earnings_transcripts",
            params=params,
        )
        self.soup = BeautifulSoup(resp.text, "html.parser")
        return self.parse_a_elements()

    @time_block("Crawling for URLs")
    def crawl(self, n: int = 50) -> Optional[List[str]]:
        instrument_id = get_cached_instrument_id(self.ticker)
        if not instrument_id:
            instrument_id = self.fetch_instrument_id()
            store_instrument_id(self.ticker, instrument_id)
        self.instrument_id = instrument_id

        slugs = self.fetch_url_slugs(n)
        final_urls = self.join_and_validate(slugs)

        return final_urls


if __name__ == "__main__":
    c = Crawler("WMT", "nyse")
    urls = c.crawl()
    print(urls)
