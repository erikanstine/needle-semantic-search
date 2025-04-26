import json
from pathlib import Path
from typing import Dict
from utils.storage import TranscriptKey
from utils.time_util import now_utc_iso


class StatusTracker:
    def __init__(self, path: str = "data/status/manifest.json", autosave: bool = True):
        self.path = Path(path)
        self.data = self._load()
        self.autosave = autosave
        self._dirty = False

    def _load(self) -> Dict[str, dict]:
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save(self):
        if not self._dirty:
            return
        temp_path = self.path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)
        temp_path.replace(self.path)
        self._dirty = False

    def add(self, key: TranscriptKey, url: str):
        slug = key.slug()
        if slug not in self.data:
            self.data[slug] = {
                "url": url,
                "discovered_at": now_utc_iso(),
                "html_saved": False,
                "parsed": False,
                "embedded": False,
                "failed_at_step": None,
                "last_attempt": None,
            }
            self._dirty = True
            if self.autosave:
                self._save()

    def update(self, slug: str, field: str, value):
        if slug not in self.data:
            raise ValueError(f"Slug not found: {slug}")
        self.data[slug][field] = value
        self.data[slug]["last_attempt"] = now_utc_iso()
        self._dirty = True
        if self.autosave:
            self._save()

    def mark_success(self, slug: str, step: str):
        self.update(slug, step, True)
        self.data[slug]["failed_at_step"] = None  # clear any past failure
        self._dirty = True
        if self.autosave:
            self._save()

    def mark_failure(self, slug: str, step: str, error: str):
        self.update(slug, step, False)
        self.data[slug]["failed_at_step"] = f"{step}: {error}"
        self._dirty = True
        if self.autosave:
            self._save()

    def filter_for(self, step: str, status: bool = False) -> list:
        return [
            slug for slug, fields in self.data.items() if fields.get(step) == status
        ]

    def get_url(self, slug: str) -> str:
        return self.data[slug]["url"]

    def save(self):
        self._save()
