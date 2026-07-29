from __future__ import annotations

import difflib
import hashlib
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class MutationType:
    CREATED = "created"
    EDITED = "edited"
    DELETED = "deleted"
    RENAMED = "renamed"


@dataclass
class FileMutation:
    type: str
    path: str
    old_path: str = ""
    old_hash: str = ""
    new_hash: str = ""
    old_content: str = ""
    new_content: str = ""
    diff: str = ""
    timestamp: str = ""
    session_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class FileMutationTracker:
    def __init__(self, base_dir: str = "."):
        self._base = Path(base_dir).resolve()
        self._history: list[FileMutation] = []
        self._snapshots: dict[str, str] = {}  # path → hash

    def snapshot(self) -> None:
        self._snapshots = {}
        for p in self._base.rglob("*"):
            if p.is_file():
                try:
                    rel = str(p.relative_to(self._base))
                    self._snapshots[rel] = {
                        "hash": self._hash_file(p),
                        "content": self._read_file(p),
                    }
                except (ValueError, OSError):
                    pass

    def _hash_file(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:16]

    def _current_snapshot(self) -> dict[str, dict]:
        snap: dict[str, dict] = {}
        for p in self._base.rglob("*"):
            if p.is_file():
                try:
                    rel = str(p.relative_to(self._base))
                    snap[rel] = {
                        "hash": self._hash_file(p),
                        "content": self._read_file(p),
                    }
                except (ValueError, OSError):
                    pass
        return snap

    def detect_changes(self, session_id: str = "") -> list[FileMutation]:
        mutations: list[FileMutation] = []
        current = self._current_snapshot()

        current_set = set(current)
        previous_set = set(self._snapshots)

        # Created files
        for path in sorted(current_set - previous_set):
            mutations.append(FileMutation(
                type=MutationType.CREATED, path=path,
                new_hash=current[path]["hash"], new_content=current[path]["content"],
                timestamp=self._now(), session_id=session_id,
            ))

        # Deleted files
        for path in sorted(previous_set - current_set):
            mutations.append(FileMutation(
                type=MutationType.DELETED, path=path,
                old_hash=self._snapshots[path]["hash"],
                old_content=self._snapshots[path]["content"],
                timestamp=self._now(), session_id=session_id,
            ))

        # Modified files
        for path in sorted(current_set & previous_set):
            if current[path]["hash"] != self._snapshots[path]["hash"]:
                old_content = self._snapshots[path]["content"]
                new_content = current[path]["content"]
                diff = self._make_diff(path, old_content, new_content)
                mutations.append(FileMutation(
                    type=MutationType.EDITED, path=path,
                    old_hash=self._snapshots[path]["hash"], new_hash=current[path]["hash"],
                    old_content=old_content, new_content=new_content,
                    diff=diff, timestamp=self._now(), session_id=session_id,
                ))

        self._history.extend(mutations)
        self._snapshots = current
        return mutations

    def _read_file(self, path: Path) -> str:
        try:
            return path.read_text()
        except (OSError, UnicodeDecodeError):
            return ""

    def _make_diff(self, path: str, old: str, new: str) -> str:
        return "\n".join(difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"a/{path}", tofile=f"b/{path}",
        ))

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def get_history(self, limit: int = 50) -> list[FileMutation]:
        return self._history[-limit:]

    def undo_last(self) -> FileMutation | None:
        if not self._history:
            return None
        last = self._history.pop()
        if last.type == MutationType.CREATED:
            path = self._base / last.path
            if path.exists():
                path.unlink()
        elif last.type == MutationType.EDITED:
            path = self._base / last.path
            if last.old_content:
                path.write_text(last.old_content)
        elif last.type == MutationType.DELETED:
            path = self._base / last.path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(last.new_content)
        return last

    def clear(self) -> None:
        self._history.clear()
