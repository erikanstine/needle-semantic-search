from scraper.utils.storage import TranscriptKey, LocalStorage


def test_transcriptkey_conversions():
    tk = TranscriptKey("AAPL", "Q1", 2024)
    slug = tk.slug()
    assert slug == "aapl-q1-2024"
    path = tk.to_path("data")
    assert path.endswith("data/html/aapl/q1-2024.html")
    assert TranscriptKey.from_slug(slug).slug() == slug
    assert TranscriptKey.from_path(path).slug() == slug
    url = "https://example.com/foo-aapl-q1-2024-bar"
    assert TranscriptKey.from_url(url).slug() == slug


def test_localstorage_roundtrip(tmp_path):
    tk = TranscriptKey("MSFT", "Q2", 2023)
    store = LocalStorage(data_root=str(tmp_path))
    store.write_html(tk, "hello")
    assert store.read_html(tk) == "hello"
    saved = tmp_path / "html" / "msft" / "q2-2023.html"
    assert saved.exists() and saved.read_text(encoding="utf-8") == "hello"
