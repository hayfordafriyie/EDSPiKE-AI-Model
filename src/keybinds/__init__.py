from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class Keybind:
    key: str
    action: str
    description: str = ""
    args: dict[str, Any] = field(default_factory=dict)


KeybindHandlerFn = Callable[[str, dict[str, Any]], None]


DEFAULT_KEYBINDS: list[Keybind] = [
    Keybind(key="tab", action="switch_mode", description="Switch between Plan and Build mode"),
    Keybind(key="ctrl+c", action="exit", description="Exit the application"),
    Keybind(key="ctrl+l", action="clear", description="Clear screen"),
    Keybind(key="ctrl+z", action="undo", description="Undo last change"),
    Keybind(key="ctrl+y", action="redo", description="Redo last undo"),
    Keybind(key="alt+h", action="help", description="Show help"),
    Keybind(key="alt+d", action="diff", description="Show recent changes"),
]


class KeybindManager:
    def __init__(self, data_dir: str = ""):
        self._keybinds: dict[str, Keybind] = {kb.key: kb for kb in DEFAULT_KEYBINDS}
        self._handlers: dict[str, KeybindHandlerFn] = {}
        self._data_dir = data_dir
        if data_dir:
            self._load()

    def _path(self) -> Path:
        return Path(self._data_dir) / "keybinds.json"

    def _load(self) -> None:
        path = self._path()
        if path.exists():
            try:
                data = json.loads(path.read_text())
                for item in data:
                    kb = Keybind(**item)
                    self._keybinds[kb.key] = kb
            except Exception:
                pass

    def _save(self) -> None:
        if not self._data_dir:
            return
        self._path().parent.mkdir(parents=True, exist_ok=True)
        data = [kb.__dict__ for kb in self._keybinds.values()]
        self._path().write_text(json.dumps(data, indent=2))

    def get(self, key: str) -> Keybind | None:
        return self._keybinds.get(key)

    def bind(self, key: str, action: str, description: str = "", handler: KeybindHandlerFn | None = None) -> Keybind:
        kb = Keybind(key=key, action=action, description=description)
        self._keybinds[key] = kb
        if handler:
            self._handlers[key] = handler
        self._save()
        return kb

    def handle(self, key: str) -> str:
        kb = self.get(key)
        if not kb:
            return f"no_action:{key}"
        handler = self._handlers.get(key)
        if handler:
            handler(kb.action, kb.args)
        return kb.action

    def list(self) -> list[Keybind]:
        return list(self._keybinds.values())

    def unbind(self, key: str) -> bool:
        if key in self._keybinds:
            del self._keybinds[key]
            self._handlers.pop(key, None)
            self._save()
            return True
        return False
