import json
from datetime import datetime, timezone
from scraper.utils.io import (
    load_url_store,
    write_url_store,
    record_url_metadata,
    mark_url_as_scraped,
    get_cached_instrument_id,
    store_instrument_id,
    pick_useragent,
    read_last_crawled,
    store_last_crawled,
)


def test_record_and_mark_url(tmp_path, monkeypatch):
    store_path = tmp_path / "store.json"
    monkeypatch.setenv("DEFAULT_STORE_PATH", str(store_path))

    record_url_metadata("http://example.com", {"foo": "bar"})
    data = json.loads(store_path.read_text())
    assert data["http://example.com"]["foo"] == "bar"

    mark_url_as_scraped("http://example.com")
    data = json.loads(store_path.read_text())
    assert data["http://example.com"]["status"] == "fetched"
    assert "fetched_at" in data["http://example.com"]


def test_instrument_id_cache(tmp_path, monkeypatch):
    path = tmp_path / "ids.json"
    monkeypatch.setenv("INSTRUMENT_ID_PATH", str(path))

    assert get_cached_instrument_id("AAPL") == ""
    store_instrument_id("AAPL", "123")
    assert get_cached_instrument_id("AAPL") == "123"


def test_pick_useragent(tmp_path, monkeypatch):
    path = tmp_path / "ua.json"
    json.dump(["UA1", "UA2"], path.open("w"))
    monkeypatch.setenv("USERAGENT_PATH", str(path))
    assert pick_useragent() in ["UA1", "UA2"]


def test_last_crawled(tmp_path, monkeypatch):
    path = tmp_path / "recency.json"
    monkeypatch.setenv("RECENCY_PATH", str(path))

    now = datetime.now(timezone.utc)
    store_last_crawled("AAPL", now)
    data = read_last_crawled()
    assert "AAPL" in data
    delta = abs((data["AAPL"] - now).total_seconds())
    assert delta < 1
