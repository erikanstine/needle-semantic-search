import os
import re

from pathlib import Path


class TranscriptKey:
    def __init__(self, company: str, quarter: str, year: int):
        self.company = company.lower()
        self.quarter = quarter.lower()
        self.year = year

    def to_path(self, data_root: str) -> str:
        return f"{data_root}/html/{self.company}/{self.quarter}-{self.year}.html"

    def slug(self) -> str:
        return f"{self.company}-{self.quarter}-{self.year}"

    @classmethod
    def from_path(cls, path: str) -> "TranscriptKey":
        match = re.search(r"\/html\/(\w+)\/(q\d{1})-(\d{4})\.html", path.lower())
        if not match:
            raise ValueError(f"Invalid path format: {path}")
        company, quarter, year = match.groups()
        return cls(company, quarter, int(year))

    @classmethod
    def from_slug(cls, slug: str) -> "TranscriptKey":
        match = re.search(r"(\w+)-(q\d{1})-(\d{4})", slug.lower())
        if not match:
            raise ValueError(f"Invalid slug format: {slug}")
        company, quarter, year = match.groups()
        return cls(company, quarter, int(year))

    @classmethod
    def from_url(cls, url: str) -> "TranscriptKey":
        match = re.search(r"-(\w+)-(q\d{1})-(\d{4})-", url.lower())
        if not match:
            raise ValueError(f"Unrecognized url format: {url}")
        company, quarter, year = match.groups()
        return cls(company, quarter, int(year))


class Storage:
    def __init__(self):
        pass

    def write_html(self, tk: TranscriptKey, html: str):
        pass

    def read_html(self, tk: TranscriptKey) -> str:
        pass


class LocalStorage(Storage):
    def __init__(self, data_root: str = "data"):
        super().__init__()
        self.data_root = data_root

    def write_html(self, tk: TranscriptKey, html: str):
        path = Path(tk.to_path(self.data_root))
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

    def read_html(self, tk: TranscriptKey) -> str:
        path = Path(tk.to_path(self.data_root))
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
