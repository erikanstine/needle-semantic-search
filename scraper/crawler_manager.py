import json

from typing import Dict, List

from crawler import Crawler
from storage import load_scraped_urls, store_crawled_urls


def get_new_transcript_urls(force: bool = False) -> List[str]:
    all_discovered = []
    fortune_50_tickers = load_ticker_list()
    for ticker, exchange in fortune_50_tickers.items():
        crawler = Crawler(ticker, exchange)
        found_urls = crawler.crawl()
        all_discovered.extend(found_urls)
        break

    if force:
        return all_discovered
    scraped = load_scraped_urls()
    return [url for url in all_discovered if url not in scraped]


def get_urls_and_store(force: bool = False) -> List[str]:
    new_urls = get_new_transcript_urls(force)
    store_crawled_urls(new_urls)
    return new_urls


def load_ticker_list() -> Dict[str, str]:
    with open("data/fortune_50_tickers.json", "r") as f:
        data = json.load(f)
    return data


if __name__ == "__main__":
    _ = get_new_transcript_urls()
