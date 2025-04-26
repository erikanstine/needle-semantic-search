import requests

from status_tracker import StatusTracker
from utils.io import mark_url_as_scraped, record_url_metadata
from utils.storage import LocalStorage, TranscriptKey
from utils.time_util import now_utc_iso, polite_sleep
from storage import (
    clear_urls_to_scrape,
    load_scraped_urls,
)

from datetime import datetime
from tqdm import tqdm
from typing import Any, List, Optional, Tuple


class HTMLFetcher:
    def __init__(
        self,
        st: StatusTracker,
        crawled_urls,
        data_root: str = "data",
        force: bool = False,
        batch: bool = True,
    ):
        self.st = st
        self.urls = crawled_urls
        self.force = force
        self.batch = batch
        self.already_fetched_urls = load_scraped_urls()
        self.report = {
            "started_at": now_utc_iso(),
            "fetched": [],
            "skipped": [],
            "failed": {},
            "total_urls": 0,
        }
        self.storage = LocalStorage(data_root)

    def already_fetched(self, url: str) -> bool:
        return url in self.already_fetched_urls

    def update_report(self, url, result, e=""):
        if result not in ["fetched", "skipped", "failed"]:
            print(f"Check unhandled report status: {result}")

        if result == "failed":
            self.report["failed"][url] = e
        else:
            self.report[result].append(url)

        self.report["total_urls"] += 1

    @polite_sleep()
    def fetch_html(self, url) -> str:
        resp = requests.get(url)
        return resp.text

    def fetch(self):
        for url in tqdm(self.urls, desc="📄 Fetching transcripts...", leave=False):
            if not self.force and self.already_fetched(url):
                print(f"Skipping already fetched url: {url}")
                self.update_report(url, "skipped")
                continue
            tk = TranscriptKey.from_url(url)
            try:
                html = self.fetch_html(url)
                self.storage.write_html(tk, html)

                self.st.mark_success(tk.slug(), "html_saved")
                record_url_metadata(
                    url,
                    metadata={
                        "status": "fetched",
                        "discovered_at": now_utc_iso(),
                        "company": tk.company,
                        "quarter": f"{tk.quarter.upper()} {tk.year}",
                    },
                )
                mark_url_as_scraped(url)
                self.update_report(url, "fetched")
            except Exception as e:
                self.st.mark_failure(tk.slug(), "html_saved", str(e))
                record_url_metadata(url, {"status": "failed", "error": str(e)})
                self.update_report(url, "failed", str(e))

        self.report["ended_at"] = now_utc_iso()
        self.report["runtime_seconds"] = (
            datetime.fromisoformat(self.report["ended_at"])
            - datetime.fromisoformat(self.report["started_at"])
        ).total_seconds()
        clear_urls_to_scrape()

    def get_report(self):
        return self.report


if __name__ == "__main__":
    urls = [
        "https://www.fool.com/earnings/call-transcripts/2019/10/30/apple-inc-aapl-q4-2019-earnings-call-transcript.aspx",
        "https://www.fool.com/earnings/call-transcripts/2024/11/20/nvidia-nvda-q3-2025-earnings-call-transcript/",
        "https://www.fool.com/earnings/call-transcripts/2023/01/26/tesla-tsla-q4-2022-earnings-call-transcript/",
    ]

    f = HTMLFetcher(urls)
    f.fetch()
