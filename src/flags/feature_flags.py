from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class FeatureFlagStore:
    def __init__(self, path: str | None = None):
        if path is None:
            path = str(Path(os.getenv("EDSPIKE_DATA_DIR", "~/.edspike")).expanduser() / "flags.json")
        self._path = path
        self._flags: dict[str, bool] = {}
        self._load()

    def _load(self) -> None:
        p = Path(self._path)
        if p.exists():
            try:
                self._flags = json.loads(p.read_text())
            except (json.JSONDecodeError, OSError):
                self._flags = {}
        else:
            self._flags = {}

    def _save(self) -> None:
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        Path(self._path).write_text(json.dumps(self._flags, indent=2))

    def is_enabled(self, flag: str) -> bool:
        return self._flags.get(flag, False)

    def enable(self, flag: str) -> None:
        self._flags[flag] = True
        self._save()

    def disable(self, flag: str) -> None:
        self._flags[flag] = False
        self._save()

    def set(self, flag: str, value: bool) -> None:
        self._flags[flag] = value
        self._save()

    def all(self) -> dict[str, bool]:
        return dict(self._flags)

    def reset(self) -> None:
        self._flags = {}
        self._save()
