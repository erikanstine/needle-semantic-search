from ingest import ingest_chunks
from model import PageFormatNotImplementedException
from scraper import Scraper


if __name__ == "__main__":
    urls = [
        "https://www.fool.com/earnings/call-transcripts/2019/10/30/apple-inc-aapl-q4-2019-earnings-call-transcript.aspx",
        "https://www.fool.com/earnings/call-transcripts/2024/11/20/nvidia-nvda-q3-2025-earnings-call-transcript/",
        "https://www.fool.com/earnings/call-transcripts/2023/01/26/tesla-tsla-q4-2022-earnings-call-transcript/",
    ]
    seen_urls = set()

    for u in urls:
        if u in seen_urls:
            continue
        seen_urls.add(u)
        try:
            scraper = Scraper(u)
            chunks = scraper.scrape()
            print(f"URL: {u}, \nChunks: {len(chunks)}\n")
            ingest_chunks(chunks)

        except PageFormatNotImplementedException as e:
            print("Invalid URL:", u)
