import json
import os

from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from typing import Any, Dict, List

load_dotenv(dotenv_path=".env", override=False)
load_dotenv(dotenv_path=".env.local", override=True)


def load_scraped_urls() -> set[str]:
    fn = os.getenv("DEFAULT_STORE_PATH")
    path = Path(fn)
    if path.exists():
        with open(fn, "r") as f:
            data = json.load(f)
        # Support JSON as dict
        return (
            set(u for u, m in data.items() if m.get("status", "") == "fetched")
            if isinstance(data, dict)
            else set(data)
        )
    return set()


def update_url_cache(urls: Dict[str, Dict[str, Any]]):
    fn = os.getenv("DEFAULT_STORE_PATH")
    path = Path(fn)
    if path.exists():
        with open(fn, "r") as f:
            data = json.load(f)
    else:
        data = {}

    data.update(urls)

    with open(fn, "w+") as f:
        json.dump(data, f, indent=2)


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


def store_crawled_urls(urls: List[str]):
    fn = os.getenv("JSON_URLS_TO_SCRAPE")
    path = Path(fn)
    if path.exists():
        with open(fn, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.extend(urls)

    with open(fn, "w") as f:
        json.dump(data, f, indent=2)


def clear_urls_to_scrape():
    fn = os.getenv("JSON_URLS_TO_SCRAPE")
    with open(fn, "w") as f:
        json.dump([], f)
    print(f"Scrape queue cleared (empty file): {fn}")


def save_unhandled_title(title: str, output_path: str = "data/unhandled_titles.txt"):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing titles if the file exists
    existing_titles = set()
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                clean_line = line.strip().split(" | ")[0]  # Only look at title part
                existing_titles.add(clean_line)

    # Check if this title is already logged
    title = title.strip()
    if title not in existing_titles:
        timestamp = datetime.utcnow().isoformat()
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{title} | first_seen: {timestamp}\n")
