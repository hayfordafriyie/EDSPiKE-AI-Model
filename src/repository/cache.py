from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RepositoryEntry:
    url: str
    local_path: str
    branch: str = "main"
    last_fetch: float = 0.0
    last_commit: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


class RepositoryCache:
    def __init__(self, data_dir: str):
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, RepositoryEntry] = {}
        self._load()

    def _path(self) -> Path:
        return self._data_dir / "repos.json"

    def _load(self) -> None:
        path = self._path()
        if path.exists():
            data = json.loads(path.read_text())
            for item in data:
                entry = RepositoryEntry(**item)
                self._entries[entry.url] = entry

    def _save(self) -> None:
        data = [entry.__dict__ for entry in self._entries.values()]
        self._path().write_text(json.dumps(data, indent=2))

    def add(self, url: str, local_path: str, branch: str = "main", meta: dict | None = None) -> RepositoryEntry:
        entry = RepositoryEntry(
            url=url, local_path=local_path, branch=branch, meta=meta or {}
        )
        self._entries[url] = entry
        self._save()
        return entry

    def get(self, url: str) -> RepositoryEntry | None:
        return self._entries.get(url)

    def remove(self, url: str) -> bool:
        if url in self._entries:
            del self._entries[url]
            self._save()
            return True
        return False

    def list(self) -> list[RepositoryEntry]:
        return list(self._entries.values())

    def update_fetch(self, url: str, last_commit: str = "") -> None:
        entry = self.get(url)
        if entry:
            entry.last_fetch = time.time()
            if last_commit:
                entry.last_commit = last_commit
            self._save()

    def exists_at(self, local_path: str) -> RepositoryEntry | None:
        for entry in self._entries.values():
            if entry.local_path == local_path:
                return entry
        return None

    def clear(self) -> None:
        self._entries.clear()
        self._save()
