import json
import os

from dotenv import load_dotenv
from pathlib import Path
from typing import Any, Dict, List

load_dotenv(dotenv_path=".env", override=False)
load_dotenv(dotenv_path=".env.local", override=True)


def load_scraped_urls() -> set[str]:
    fn = os.getenv("JSON_DATA_STORE_LOCATION")
    path = Path(fn)
    if path.exists():
        with open(fn, "r") as f:
            data = json.load(f)
        # Support JSON as dict
        return set(data.keys()) if isinstance(data, dict) else set(data)
    return set()


def write_url_error_result(url: str, error: str):
    fn = os.getenv("JSON_ERROR_DATA_STORE_LOCATION")
    path = Path(fn)
    if path.exists():
        with open(fn, "r") as f:
            data = json.load(f)
    else:
        data = {}

    data[url] = {"error": error}
    with open(fn, "w+") as f:
        json.dump(data, f, indent=2)


def update_url_cache(urls: Dict[str, Dict[str, Any]]):
    fn = os.getenv("JSON_DATA_STORE_LOCATION")
    path = Path(fn)
    if path.exists():
        with open(fn, "r") as f:
            data = json.load(f)
    else:
        data = {}

    data.update(urls)

    with open(fn, "w+") as f:
        json.dump(data, f, indent=2)


def store_crawled_urls(urls: List[str]):
    fn = os.getenv("JSON_URLS_TO_SCRAPE")
    Path(fn).parent.mkdir(parents=True, exist_ok=True)
    with open(fn, "w") as f:
        json.dump(urls, f, indent=2)


def clear_urls_to_scrape():
    fn = os.getenv("JSON_URLS_TO_SCRAPE")
    with open(fn, "w") as f:
        json.dump([], f)
    print(f"Scrape queue cleared (empty file): {fn}")
