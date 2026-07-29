from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


@dataclass
class ApprovalState:
    yolo: bool = False
    afk: bool = False
    auto_approve_actions: set[str] = field(default_factory=set)


@dataclass
class TodoItem:
    title: str
    status: Literal["pending", "in_progress", "done"] = "pending"


@dataclass
class SessionState:
    version: int = 1
    approval: ApprovalState = field(default_factory=ApprovalState)
    plan_mode: bool = False
    plan_session_id: str = ""
    plan_slug: str = ""
    custom_title: str = ""
    title_generated: bool = False
    todos: list[TodoItem] = field(default_factory=list)
    additional_dirs: list[str] = field(default_factory=list)


class SessionStateManager:
    def __init__(self, data_dir: str):
        self._path = Path(data_dir) / "session_state.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._state = SessionState()
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text())
                self._state = SessionState(
                    version=data.get("version", 1),
                    approval=ApprovalState(**data.get("approval", {})),
                    plan_mode=data.get("plan_mode", False),
                    plan_session_id=data.get("plan_session_id", ""),
                    plan_slug=data.get("plan_slug", ""),
                    custom_title=data.get("custom_title", ""),
                    title_generated=data.get("title_generated", False),
                    todos=[TodoItem(**t) for t in data.get("todos", [])],
                    additional_dirs=data.get("additional_dirs", []),
                )
                if self._state.approval.auto_approve_actions:
                    self._state.approval.auto_approve_actions = set(self._state.approval.auto_approve_actions)
            except Exception:
                self._state = SessionState()

    def _save(self) -> None:
        data = {
            "version": self._state.version,
            "approval": {
                "yolo": self._state.approval.yolo,
                "afk": self._state.approval.afk,
                "auto_approve_actions": list(self._state.approval.auto_approve_actions),
            },
            "plan_mode": self._state.plan_mode,
            "plan_session_id": self._state.plan_session_id,
            "plan_slug": self._state.plan_slug,
            "custom_title": self._state.custom_title,
            "title_generated": self._state.title_generated,
            "todos": [{"title": t.title, "status": t.status} for t in self._state.todos],
            "additional_dirs": self._state.additional_dirs,
        }
        self._path.write_text(json.dumps(data, indent=2))

    @property
    def state(self) -> SessionState:
        return self._state

    def set_plan_mode(self, active: bool, session_id: str = "", slug: str = "") -> None:
        self._state.plan_mode = active
        self._state.plan_session_id = session_id
        self._state.plan_slug = slug
        self._save()

    def set_yolo(self, enabled: bool) -> None:
        self._state.approval.yolo = enabled
        self._save()

    def set_afk(self, enabled: bool) -> None:
        self._state.approval.afk = enabled
        self._save()

    def add_auto_approve(self, action: str) -> None:
        self._state.approval.auto_approve_actions.add(action)
        self._save()

    def set_title(self, title: str, generated: bool = False) -> None:
        self._state.custom_title = title
        self._state.title_generated = generated
        self._save()

    def add_todo(self, title: str) -> None:
        self._state.todos.append(TodoItem(title=title))
        self._save()

    def update_todo(self, index: int, status: str) -> bool:
        if 0 <= index < len(self._state.todos):
            self._state.todos[index].status = status  # type: ignore
            self._save()
            return True
        return False

    def clear(self) -> None:
        self._state = SessionState()
        self._save()
