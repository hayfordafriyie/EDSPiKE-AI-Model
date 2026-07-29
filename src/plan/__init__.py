from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


PLAN_MODE_REMINDER = "You are in PLAN mode. Analyze and suggest changes but do NOT modify any files. You may NOT use write_file, edit_file, apply_patch, or bash."

DENIED_TOOLS_IN_PLAN_MODE = {"write_file", "edit_file", "apply_patch", "bash"}


class PlanMode:
    def __init__(self):
        self._active = False

    @property
    def active(self) -> bool:
        return self._active

    def activate(self) -> None:
        self._active = True

    def deactivate(self) -> None:
        self._active = False

    def toggle(self) -> bool:
        self._active = not self._active
        return self._active

    def check_tool_allowed(self, tool_name: str) -> bool:
        if not self._active:
            return True
        return tool_name not in DENIED_TOOLS_IN_PLAN_MODE

    def get_reminder(self) -> str:
        return PLAN_MODE_REMINDER if self._active else ""

    def get_status(self) -> dict[str, Any]:
        return {"active": self._active, "denied_tools": list(DENIED_TOOLS_IN_PLAN_MODE) if self._active else []}
