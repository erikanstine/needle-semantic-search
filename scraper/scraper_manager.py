from ingest import ingest_chunks
from model import PageFormatNotImplementedException
from scraper import Scraper
from storage import load_scraped_urls, update_url_cache, write_url_error_result

from typing import List, Optional, Tuple


def run_scraper_manager(
    crawled_urls: List[str],
) -> Tuple[Optional[List[str]], Optional[List[str]]]:
    already_scraped = load_scraped_urls()
    new_urls = set([url for url in crawled_urls if url not in already_scraped])
    ingested_urls = {}

    # TODO: Use asyncio
    while new_urls:
        url = new_urls.pop()
        try:
            scraper = Scraper(url)
            chunks = scraper.scrape()
            url_metadata = ingest_chunks(chunks)
            ingested_urls[url] = url_metadata
        except PageFormatNotImplementedException as e:
            write_url_error_result(url, str(e))

    update_url_cache(ingested_urls)


if __name__ == "__main__":
    urls = [
        "https://www.fool.com/earnings/call-transcripts/2019/10/30/apple-inc-aapl-q4-2019-earnings-call-transcript.aspx",
        "https://www.fool.com/earnings/call-transcripts/2024/11/20/nvidia-nvda-q3-2025-earnings-call-transcript/",
        "https://www.fool.com/earnings/call-transcripts/2023/01/26/tesla-tsla-q4-2022-earnings-call-transcript/",
    ]

    run_scraper_manager(urls)
