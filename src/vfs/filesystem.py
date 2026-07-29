from __future__ import annotations

import hashlib
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class FileEntry:
    path: str
    is_dir: bool
    size: int = 0
    modified_at: float = 0.0
    hash: str = ""


class FsWatcher:
    def __init__(self):
        self._callbacks: list[Callable[[str, str], None]] = []
        self._snapshots: dict[str, dict[str, float]] = {}

    def on_change(self, callback: Callable[[str, str], None]) -> None:
        self._callbacks.append(callback)

    def snapshot(self, root: str) -> dict[str, float]:
        snapshot: dict[str, float] = {}
        root_p = Path(root)
        if not root_p.exists():
            return snapshot
        for p in root_p.rglob("*"):
            if p.is_file():
                try:
                    snapshot[str(p.relative_to(root_p))] = p.stat().st_mtime
                except OSError:
                    pass
        return snapshot

    def poll(self, root: str) -> list[tuple[str, str]]:
        current = self.snapshot(root)
        previous = self._snapshots.get(root, {})
        self._snapshots[root] = current
        changes: list[tuple[str, str]] = []

        all_keys = set(previous) | set(current)
        for key in all_keys:
            if key not in previous:
                changes.append((key, "created"))
            elif key not in current:
                changes.append((key, "deleted"))
            elif previous[key] != current[key]:
                changes.append((key, "modified"))

        for cb in self._callbacks:
            for path, change in changes:
                try:
                    cb(path, change)
                except Exception as exc:
                    logger.error("Watcher callback error: %s", exc)
        return changes


class VirtualFileSystem:
    def __init__(self, allowed_roots: list[str] | None = None):
        self._allowed_roots = [Path(r).resolve() for r in (allowed_roots or ["."])]
        self._watcher = FsWatcher()

    def _resolve(self, path: str) -> Path:
        p = Path(path).resolve()
        allowed = False
        for root in self._allowed_roots:
            try:
                p.relative_to(root)
                allowed = True
                break
            except ValueError:
                continue
        if not allowed:
            raise PermissionError(f"Path {path} is outside allowed roots: {self._allowed_roots}")
        return p

    def read(self, path: str, offset: int = 0, limit: int | None = None) -> str:
        p = self._resolve(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")
        content = p.read_text()
        if offset > 1:
            lines = content.split("\n")
            start = offset - 1
            end = start + limit if limit else None
            content = "\n".join(lines[start:end])
        elif limit:
            content = "\n".join(content.split("\n")[:limit])
        return content

    def write(self, path: str, content: str) -> None:
        p = self._resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)

    def edit(self, path: str, old_string: str, new_string: str) -> bool:
        p = self._resolve(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")
        content = p.read_text()
        if old_string not in content:
            raise ValueError(f"old_string not found in {path}")
        p.write_text(content.replace(old_string, new_string, 1))
        return True

    def list(self, path: str = ".") -> list[FileEntry]:
        p = self._resolve(path)
        if not p.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        entries: list[FileEntry] = []
        for child in sorted(p.iterdir()):
            try:
                stat = child.stat()
                entries.append(FileEntry(
                    path=str(child),
                    is_dir=child.is_dir(),
                    size=stat.st_size if child.is_file() else 0,
                    modified_at=stat.st_mtime,
                ))
            except OSError:
                pass
        return entries

    def hash(self, path: str) -> str:
        p = self._resolve(path)
        if not p.exists() or p.is_dir():
            return ""
        return hashlib.sha256(p.read_bytes()).hexdigest()

    def exists(self, path: str) -> bool:
        try:
            p = self._resolve(path)
            return p.exists()
        except PermissionError:
            return False

    def glob(self, pattern: str, path: str = ".") -> list[str]:
        p = self._resolve(path)
        return [str(f.relative_to(p)) for f in sorted(p.glob(pattern)) if f.is_file()]

    def grep(self, pattern: str, path: str = ".", include: str | None = None) -> list[dict[str, Any]]:
        import re
        p = self._resolve(path)
        matches: list[dict[str, Any]] = []
        regex = re.compile(pattern)
        files_iter = p.rglob(include) if include else p.rglob("*")
        for f in files_iter:
            if not f.is_file():
                continue
            try:
                for i, line in enumerate(f.read_text().split("\n"), 1):
                    if regex.search(line):
                        matches.append({"file": str(f.relative_to(p)), "line": i, "content": line})
            except (OSError, UnicodeDecodeError):
                pass
        return matches

    @property
    def watcher(self) -> FsWatcher:
        return self._watcher

    def get_tool_specs(self) -> list[dict[str, Any]]:
        return [
            {"name": "vfs_read", "description": "Read a file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "offset": {"type": "integer"}, "limit": {"type": "integer"}}}},
            {"name": "vfs_write", "description": "Write a file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
            {"name": "vfs_edit", "description": "Edit a file (search-replace)", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "old_string": {"type": "string"}, "new_string": {"type": "string"}}, "required": ["path", "old_string", "new_string"]}},
            {"name": "vfs_list", "description": "List directory contents", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}},
            {"name": "vfs_glob", "description": "Search files by glob pattern", "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}}, "required": ["pattern"]}},
            {"name": "vfs_grep", "description": "Search file contents by regex", "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}, "include": {"type": "string"}}, "required": ["pattern"]}},
        ]
