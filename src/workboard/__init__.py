from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class WorkItem:
    id: str
    title: str
    description: str = ""
    status: str = "todo"  # todo, in_progress, review, done
    priority: str = "medium"  # low, medium, high, critical
    assignee: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: float = 0.0
    updated_at: float = 0.0


BOARD_COLUMNS = ["todo", "in_progress", "review", "done"]


class Workboard:
    def __init__(self, data_dir: str = ""):
        self._items: dict[str, WorkItem] = {}
        self._path = Path(data_dir) / "workboard.json" if data_dir else None
        if self._path:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._load()

    def _load(self) -> None:
        if self._path and self._path.exists():
            try:
                data = json.loads(self._path.read_text())
                self._items = {d["id"]: WorkItem(**d) for d in data}
            except Exception:
                pass

    def _save(self) -> None:
        if self._path is None:
            return
        data = [
            {
                "id": w.id, "title": w.title, "description": w.description,
                "status": w.status, "priority": w.priority, "assignee": w.assignee,
                "tags": w.tags, "created_at": w.created_at, "updated_at": w.updated_at,
            }
            for w in self._items.values()
        ]
        self._path.write_text(json.dumps(data, indent=2))

    def add(self, title: str, description: str = "", priority: str = "medium", assignee: str = "", tags: list[str] | None = None) -> WorkItem:
        item = WorkItem(
            id=f"wi_{int(time.time() * 1000000)}",
            title=title,
            description=description,
            priority=priority,
            assignee=assignee,
            tags=tags or [],
            created_at=time.time(),
            updated_at=time.time(),
        )
        self._items[item.id] = item
        self._save()
        return item

    def move(self, item_id: str, status: str) -> bool:
        if item_id not in self._items:
            return False
        if status not in BOARD_COLUMNS:
            return False
        self._items[item_id].status = status
        self._items[item_id].updated_at = time.time()
        self._save()
        return True

    def get(self, item_id: str) -> WorkItem | None:
        return self._items.get(item_id)

    def list(self, status: str = "") -> list[WorkItem]:
        items = list(self._items.values())
        if status:
            items = [i for i in items if i.status == status]
        return sorted(items, key=lambda i: i.created_at, reverse=True)

    def board_view(self) -> dict[str, list[WorkItem]]:
        return {col: self.list(col) for col in BOARD_COLUMNS}

    def delete(self, item_id: str) -> bool:
        if item_id not in self._items:
            return False
        del self._items[item_id]
        self._save()
        return True

    def count(self) -> int:
        return len(self._items)
