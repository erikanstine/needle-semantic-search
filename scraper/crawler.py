from typing import List, Optional

from storage import store_crawled_urls


def get_new_transcript_urls() -> List[str]:
    urls = [
        "https://www.fool.com/earnings/call-transcripts/2022/01/28/visa-v-q1-2022-earnings-call-transcript/"
    ]
    store_crawled_urls(urls)
    return urls


def load_ticker_list() -> List[str]:
    with open("data/fortune_50_tickers.txt", "r") as f:
        data = [l.strip() for l in f.readlines()]
    return data


if __name__ == "__main__":
    get_new_transcript_urls()
