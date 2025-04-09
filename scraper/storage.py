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
