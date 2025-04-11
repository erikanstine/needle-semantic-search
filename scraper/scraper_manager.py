from chunk_processor import ChunkProcessor
from ingest import ingest_chunks
from utils.io import mark_url_as_scraped, record_url_metadata
from utils.time_util import now_utc_iso
from model import PageFormatNotImplementedException
from scraper import Scraper
from storage import (
    clear_urls_to_scrape,
    load_scraped_urls,
    write_url_error_result,
)

from datetime import datetime
from tqdm import tqdm
from typing import Any, List, Optional, Tuple


def url_already_scraped(url: str) -> bool:
    already_scraped = load_scraped_urls()
    return url in already_scraped


def update_report(report, url, result, e=""):
    if result not in ["scraped", "skipped", "failed"]:
        print(f"Check unhandled report status: {result}")
        return report

    if result == "failed":
        report["failed"][url] = e
    else:
        report[result].append(url)

    report["total_urls"] += 1
    return report


def run_scraper_manager(
    crawled_urls: List[str], force: bool = False, batch: bool = False
) -> dict[str, Any]:
    report = {
        "started_at": now_utc_iso(),
        "scraped": [],
        "skipped": [],
        "failed": {},
        "total_urls": 0,
    }
    if batch:
        all_chunks = []
        for url in tqdm(crawled_urls, desc="📄 Scraping transcripts...", leave=False):
            if not force and url_already_scraped(url):
                print(f"Skipping already scraped url: {url}")
                update_report(report, url, "skipped")
                continue
            try:
                scraper = Scraper(url)
                chunks, call_metadata = scraper.scrape()
                record_url_metadata(
                    url,
                    metadata={
                        "status": "pending",
                        "discovered_at": now_utc_iso(),
                        "num_chunks": len(chunks),
                        "company": call_metadata["company"],
                        "quarter": call_metadata["quarter"],
                    },
                )
                all_chunks.extend(chunks)
                mark_url_as_scraped(url)
                update_report(report, url, "scraped")
            except Exception as e:
                record_url_metadata(url, {"status": "failed", "error": str(e)})
                report["failed"][url] = str(e)
                update_report(report, url, "failed", str(e))
        processor = ChunkProcessor(chunks)
        processor.embed()
        processor.upsert()
    else:
        for url in crawled_urls:
            if not force and url_already_scraped(url):
                print(f"Skipping already scraped url: {url}")
                update_report(report, url, "skipped")
                continue
            try:
                scraper = Scraper(url)
                chunks, call_metadata = scraper.scrape()
                # Write URLs here, pending status
                record_url_metadata(
                    url,
                    metadata={
                        "status": "pending",
                        "discovered_at": now_utc_iso(),
                        "num_chunks": len(chunks),
                        "company": call_metadata["company"],
                        "quarter": call_metadata["quarter"],
                    },
                )
                ingest_chunks(chunks)
                mark_url_as_scraped(url)
                update_report(report, url, "scraped")
            except Exception as e:
                record_url_metadata(url, {"status": "failed", "error": str(e)})
                report["failed"][url] = str(e)
                update_report(report, url, "failed", str(e))

    report["ended_at"] = now_utc_iso()
    report["runtime_seconds"] = (
        datetime.fromisoformat(report["ended_at"])
        - datetime.fromisoformat(report["started_at"])
    ).total_seconds()

    clear_urls_to_scrape()
    return report


if __name__ == "__main__":
    urls = [
        "https://www.fool.com/earnings/call-transcripts/2019/10/30/apple-inc-aapl-q4-2019-earnings-call-transcript.aspx",
        "https://www.fool.com/earnings/call-transcripts/2024/11/20/nvidia-nvda-q3-2025-earnings-call-transcript/",
        "https://www.fool.com/earnings/call-transcripts/2023/01/26/tesla-tsla-q4-2022-earnings-call-transcript/",
    ]

    run_scraper_manager(urls)
