import pytest

from pathlib import Path
from .utils.storage import LocalStorage, TranscriptKey


@pytest.fixture
def sample_html():
    return "<html><body><h1>Test Transcript</h1><p>This is a test.</p></body></html>"


@pytest.fixture
def sample_key():
    return TranscriptKey(company="AAPL", quarter="q1", year=2022)


@pytest.fixture
def local_storage(tmp_path):
    return LocalStorage(data_root=str(tmp_path))


def test_write_and_read_html(local_storage, sample_key, sample_html):
    # Write HTML to storage
    local_storage.write_html(sample_key, sample_html)

    # Read HTML back
    result = local_storage.read_html(sample_key)

    assert result == sample_html

    # Verify file exists on disk
    path = Path(sample_key.to_path(local_storage.data_root))
    assert path.exists()
    assert path.read_text(encoding="utf-8") == sample_html
