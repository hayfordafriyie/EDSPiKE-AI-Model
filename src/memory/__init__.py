from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class MemoryEntry:
    id: str
    content: str
    source: str = ""  # conversation, tool_result, user_input
    importance: float = 0.5  # 0.0 to 1.0
    tags: list[str] = field(default_factory=list)
    created_at: float = 0.0
    accessed_at: float = 0.0
    ttl_days: float = 30.0


@dataclass
class MemoryPolicy:
    min_importance: float = 0.3
    max_entries: int = 1000
    auto_expire_days: float = 90.0
    recall_limit: int = 20


class ActiveMemory:
    def __init__(self, data_dir: str = ""):
        self._entries: list[MemoryEntry] = []
        self._policy = MemoryPolicy()
        self._path = Path(data_dir) / "memory.json" if data_dir else None
        if self._path:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._load()

    def _load(self) -> None:
        if self._path and self._path.exists():
            try:
                data = json.loads(self._path.read_text())
                self._entries = [MemoryEntry(**e) for e in data]
            except Exception:
                pass

    def _save(self) -> None:
        if self._path is None:
            return
        data = [
            {
                "id": e.id, "content": e.content, "source": e.source,
                "importance": e.importance, "tags": e.tags,
                "created_at": e.created_at, "accessed_at": e.accessed_at,
                "ttl_days": e.ttl_days,
            }
            for e in self._entries
        ]
        self._path.write_text(json.dumps(data, indent=2))

    def remember(self, content: str, source: str = "", importance: float = 0.5, tags: list[str] | None = None, ttl_days: float = 30.0) -> MemoryEntry:
        self._expire()
        entry = MemoryEntry(
            id=f"mem_{int(time.time() * 1000000)}",
            content=content,
            source=source,
            importance=importance,
            tags=tags or [],
            created_at=time.time(),
            accessed_at=time.time(),
            ttl_days=ttl_days,
        )
        self._entries.append(entry)
        self._trim()
        self._save()
        return entry

    def recall(self, query: str = "", limit: int = 0) -> list[MemoryEntry]:
        limit = limit or self._policy.recall_limit
        results = self._entries
        if query:
            q = query.lower()
            results = [
                e for e in results
                if q in e.content.lower() or any(q in t.lower() for t in e.tags)
            ]
        results.sort(key=lambda e: (e.importance, e.accessed_at), reverse=True)
        for e in results[:limit]:
            e.accessed_at = time.time()
        self._save()
        return results[:limit]

    def forget(self, memory_id: str) -> bool:
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.id != memory_id]
        if len(self._entries) < before:
            self._save()
            return True
        return False

    def update_importance(self, memory_id: str, importance: float) -> bool:
        for e in self._entries:
            if e.id == memory_id:
                e.importance = importance
                self._save()
                return True
        return False

    def summarize(self, limit: int = 5) -> str:
        top = self.recall(limit=limit)
        if not top:
            return "No memories stored."
        lines = ["Key memories:"]
        for e in top:
            lines.append(f"  [{e.importance:.1f}] {e.content[:150]}")
        return "\n".join(lines)

    def _expire(self) -> None:
        now = time.time()
        self._entries = [
            e for e in self._entries
            if (now - e.created_at) < e.ttl_days * 86400
        ]

    def _trim(self) -> None:
        if len(self._entries) <= self._policy.max_entries:
            return
        self._entries.sort(key=lambda e: (e.importance, e.created_at))
        self._entries = self._entries[-self._policy.max_entries:]

    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()
        self._save()
