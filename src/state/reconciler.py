from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StateDiff:
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    modified: list[tuple[str, Any, Any]] = field(default_factory=list)
    unchanged: int = 0


class StateReconciler:
    def diff(self, current: dict[str, Any], desired: dict[str, Any]) -> StateDiff:
        diff = StateDiff()
        cur_keys = set(current.keys())
        des_keys = set(desired.keys())

        diff.added = sorted(des_keys - cur_keys)
        diff.removed = sorted(cur_keys - des_keys)

        for key in sorted(cur_keys & des_keys):
            if current[key] != desired[key]:
                diff.modified.append((key, current[key], desired[key]))
            else:
                diff.unchanged += 1

        return diff

    def reconcile(self, base: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
        result = dict(base)
        for key, value in target.items():
            result[key] = value
        for key in list(result.keys()):
            if key not in target and key in base:
                del result[key]
        return result

    def merge(self, *states: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for state in states:
            result.update(state)
        return result
