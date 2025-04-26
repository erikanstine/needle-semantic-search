import json
import os
import random

from .time_util import now_utc_iso

from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional

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
    if entry.get("error") and not metadata.get("error"):
        # URL with error status has been updated
        del entry["error"]
    entry.update(metadata)
    store[url] = entry
    write_url_store(store)


def mark_url_as_scraped(url: str):
    record_url_metadata(url, {"status": "fetched", "fetched_at": now_utc_iso()})


def get_cached_instrument_id(ticker: str) -> Optional[str]:
    fn = os.getenv("INSTRUMENT_ID_PATH")
    path = Path(fn)
    data = {}
    if path.exists():
        with open(fn, "r") as f:
            data = json.load(f)
        return data.get(ticker, "")


def store_instrument_id(ticker: str, instrument_id: str):
    fn = os.getenv("INSTRUMENT_ID_PATH")
    path = Path(fn)
    data = {}
    if path.exists():
        with open(fn, "r") as f:
            data = json.load(f)
    if data.get(ticker) == instrument_id:
        return
    data[ticker] = instrument_id
    with open(fn, "w+") as f:
        json.dump(data, f, indent=2)


def pick_useragent() -> Optional[str]:
    fn = os.getenv("USERAGENT_PATH")
    path = Path(fn)
    data = []
    if path.exists():
        with open(fn, "r") as f:
            data = json.load(f)
    return random.choice(data)


def read_last_crawled() -> dict[str, datetime]:
    fn = os.getenv("RECENCY_PATH")
    path = Path(fn)
    data = {}
    if path.exists():
        with open(fn, "r") as f:
            j = json.load(f)
        data = {k: datetime.fromisoformat(v) for k, v in j.items()}
    return data


def store_last_crawled(ticker: str, dt: datetime):
    fn = os.getenv("RECENCY_PATH")
    path = Path(fn)
    data = {}
    if path.exists():
        with open(fn, "r") as f:
            data = json.load(f)
    data[ticker] = dt.isoformat()
    with open(fn, "w+") as f:
        json.dump(data, f, indent=2)
