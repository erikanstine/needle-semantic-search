import json
import os

from .time_util import now_utc_iso

from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=".env", override=False)
load_dotenv(dotenv_path=".env.local", override=True)


def load_url_store():
    fn = os.getenv("DEFAULT_STORE_PATH")
    path = Path(fn)
    data = None
    if path.exists():
        with open(fn, "r") as f:
            data = json.load(f)
    return data or {}


def write_url_store(store):
    fn = os.getenv("DEFAULT_STORE_PATH")
    with open(fn, "w+") as f:
        json.dump(store, f, indent=2)


def record_url_metadata(url: str, metadata: dict):
    store = load_url_store()
    entry = store.get(url, {})
    entry.update(metadata)
    store[url] = entry
    write_url_store(store)


def mark_url_as_scraped(url: str):
    record_url_metadata(url, {"status": "scraped", "scraped_at": now_utc_iso()})
