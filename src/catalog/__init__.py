from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CatalogEntry:
    key: str
    name: str
    type: str  # tool, agent, skill, template, prompt
    description: str = ""
    version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


class CatalogSystem:
    def __init__(self, data_dir: str):
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, CatalogEntry] = {}
        self._load()

    def _path(self) -> Path:
        return self._data_dir / "catalog.json"

    def _load(self) -> None:
        path = self._path()
        if path.exists():
            data = json.loads(path.read_text())
            for item in data:
                entry = CatalogEntry(**item)
                self._entries[entry.key] = entry

    def _save(self) -> None:
        data = [e.__dict__ for e in self._entries.values()]
        self._path().write_text(json.dumps(data, indent=2))

    def register(self, key: str, name: str, type_: str, description: str = "", version: str = "1.0.0", tags: list[str] | None = None, config: dict | None = None) -> CatalogEntry:
        entry = CatalogEntry(
            key=key, name=name, type=type_, description=description,
            version=version, tags=tags or [], config=config or {},
        )
        self._entries[key] = entry
        self._save()
        return entry

    def get(self, key: str) -> CatalogEntry | None:
        return self._entries.get(key)

    def find(self, type_: str | None = None, tag: str | None = None, query: str | None = None) -> list[CatalogEntry]:
        results = list(self._entries.values())
        if type_:
            results = [e for e in results if e.type == type_]
        if tag:
            results = [e for e in results if tag in e.tags]
        if query:
            q = query.lower()
            results = [e for e in results if q in e.name.lower() or q in e.description.lower()]
        return results

    def enable(self, key: str) -> bool:
        entry = self.get(key)
        if not entry:
            return False
        entry.enabled = True
        self._save()
        return True

    def disable(self, key: str) -> bool:
        entry = self.get(key)
        if not entry:
            return False
        entry.enabled = False
        self._save()
        return True

    def remove(self, key: str) -> bool:
        if key in self._entries:
            del self._entries[key]
            self._save()
            return True
        return False

    def list_types(self) -> list[str]:
        return list({e.type for e in self._entries.values()})

    def count(self) -> int:
        return len(self._entries)
