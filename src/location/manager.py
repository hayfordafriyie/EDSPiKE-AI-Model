from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Location:
    name: str
    path: str
    description: str = ""
    services: list[str] = field(default_factory=list)
    created_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class LocationManager:
    def __init__(self, data_dir: str | None = None):
        if data_dir is None:
            data_dir = str(Path(os.getenv("EDSPIKE_DATA_DIR", "~/.edspike")).expanduser() / "locations")
        self._dir = Path(data_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self._dir / "_index.json"
        self._locations: dict[str, Location] = {}
        self._load()

    def _load(self) -> None:
        if self._index_path.exists():
            try:
                data = json.loads(self._index_path.read_text())
                for item in data:
                    loc = Location(**item)
                    self._locations[loc.name] = loc
            except (json.JSONDecodeError, OSError, TypeError):
                pass

    def _save(self) -> None:
        data = [
            {
                "name": loc.name,
                "path": loc.path,
                "description": loc.description,
                "services": loc.services,
                "created_at": loc.created_at,
                "metadata": loc.metadata,
            }
            for loc in self._locations.values()
        ]
        self._index_path.write_text(json.dumps(data, indent=2))

    def register(self, name: str, path: str, description: str = "", services: list[str] | None = None, metadata: dict | None = None) -> Location:
        loc = Location(
            name=name,
            path=str(Path(path).resolve()),
            description=description,
            services=services or [],
            created_at=time.time(),
            metadata=metadata or {},
        )
        self._locations[name] = loc
        self._save()
        return loc

    def get(self, name: str) -> Location | None:
        return self._locations.get(name)

    def remove(self, name: str) -> bool:
        if name in self._locations:
            del self._locations[name]
            self._save()
            return True
        return False

    def list(self) -> list[dict[str, Any]]:
        return [
            {
                "name": loc.name,
                "path": loc.path,
                "description": loc.description,
                "services": loc.services,
                "created_at": loc.created_at,
            }
            for loc in sorted(self._locations.values(), key=lambda l: l.name)
        ]

    def add_service(self, name: str, service: str) -> bool:
        loc = self._locations.get(name)
        if not loc:
            return False
        if service not in loc.services:
            loc.services.append(service)
            self._save()
        return True

    def resolve(self, name_or_path: str) -> str | None:
        if name_or_path in self._locations:
            return self._locations[name_or_path].path
        p = Path(name_or_path)
        if p.exists():
            return str(p.resolve())
        return None
