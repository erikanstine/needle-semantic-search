import json

from tqdm import tqdm
from typing import Dict, List

from crawler import Crawler
from status_tracker import StatusTracker
from storage import load_scraped_urls, store_crawled_urls
from utils.io import read_last_crawled, store_last_crawled
from utils.report import save_problematic_urls
from utils.storage import TranscriptKey
from utils.time_util import is_older_than_a_week, now_utc


def get_eligible_tickers() -> dict[str, str]:
    fortune_50_tickers = load_ticker_list()
    ticker_dates = read_last_crawled()
    eligible = {}
    for ticker, exchange in fortune_50_tickers.items():
        if any(
            [
                ticker not in ticker_dates,
                ticker in ticker_dates and is_older_than_a_week(ticker_dates[ticker]),
            ]
        ):
            eligible[ticker] = exchange
        else:
            print(
                f"Not crawling {ticker}, last crawled {str(ticker_dates[ticker].date())}"
            )
    return eligible


def get_new_transcript_urls(dry_run: bool = False, force: bool = False) -> List[str]:
    urls_per_request = 50
    crawled_urls = []
    eligible_tickers = get_eligible_tickers()
    scraped = load_scraped_urls()
    max_run = len(eligible_tickers)
    problematic_urls = []
    print(f"Crawling for URLs from {max_run} companies")
    with tqdm(total=max_run, desc="🐛 Crawling companies for URLs...") as pbar:
        for ticker, exchange in eligible_tickers.items():
            urls = []
            if max_run < 1:
                break
            try:
                crawler = Crawler(ticker, exchange)
                found_urls = crawler.crawl(urls_per_request)
                urls = (
                    [url for url in found_urls if url not in scraped]
                    if not force
                    else found_urls
                )
            except Exception as e:
                print(f"Crawler Exception for {ticker}\n{e}")

            if urls:
                print(f"Found {len(urls)} URLs for {ticker}")
                st = StatusTracker()
                for url in urls:
                    try:
                        st.add(TranscriptKey.from_url(url), url)
                    except ValueError as e:
                        print(f"⚠️ Skipping problematic URL: {url}\nReason: {e}")
                        problematic_urls.append(url)
                crawled_urls.extend([u for u in urls if u not in problematic_urls])
                pbar.update(1)
                max_run -= 1
            else:
                print(f"No new URLs found for {ticker}")
                store_last_crawled(ticker, now_utc())
    save_problematic_urls(problematic_urls)
    return crawled_urls


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
