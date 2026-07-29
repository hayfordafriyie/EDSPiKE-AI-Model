from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Mode:
    id: str
    name: str
    description: str
    permissions: dict[str, str] = field(default_factory=dict)
    agent_id: str = ""


BUILTIN_MODES: dict[str, Mode] = {
    "build": Mode(
        id="build", name="Build",
        description="Full-access development mode. All tools enabled.",
        agent_id="build",
    ),
    "plan": Mode(
        id="plan", name="Plan",
        description="Read-only planning mode. No file modifications, bash requires approval.",
        permissions={
            "write_file": "deny",
            "edit_file": "deny",
            "apply_patch": "deny",
            "bash": "ask",
        },
        agent_id="plan",
    ),
}


class ModeManager:
    def __init__(self):
        self._modes: dict[str, Mode] = dict(BUILTIN_MODES)
        self._current: str = "build"

    def get_current(self) -> Mode:
        return self._modes[self._current]

    def set_mode(self, mode_id: str) -> Mode:
        if mode_id not in self._modes:
            raise KeyError(f"Unknown mode: {mode_id}. Available: {list(self._modes)}")
        self._current = mode_id
        return self._modes[mode_id]

    def list_modes(self) -> list[Mode]:
        return list(self._modes.values())

    def get_permissions(self) -> dict[str, str]:
        return dict(self._modes[self._current].permissions)

    def can(self, tool_name: str) -> str:
        perms = self.get_permissions()
        return perms.get(tool_name, "allow")

    def register(self, mode: Mode) -> None:
        self._modes[mode.id] = mode
