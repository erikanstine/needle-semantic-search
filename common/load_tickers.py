import json
from pathlib import Path


def load_ticker_metadata() -> dict[str, dict[str, str]]:
    """
    Load ticker metadata from common/tickers.json.

    Returns:
        A dictionary mapping ticker symbols (e.g., 'AAPL') to their metadata,
        e.g. { 'exchange': 'NASDAQ', 'name': 'Apple Inc.' }.
    """
    # Determine path to common/tickers.json based on project root
    repo_root = Path(__file__).resolve().parents[1]
    json_path = repo_root / "common" / "tickers.json"

    if not json_path.is_file():
        raise FileNotFoundError(f"Ticker metadata file not found at {json_path}")

    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return data
