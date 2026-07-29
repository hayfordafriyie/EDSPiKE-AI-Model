from __future__ import annotations

import hashlib
import json
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

REMINDER_LEVELS = [
    (3, "You are repeating the same tool call. Consider a different approach."),
    (5, "You have repeated this call many times. Try something else."),
    (8, "Stop repeating and report your progress to the user."),
    (12, "Force stopping this turn due to excessive repetition."),
]


@dataclass
class DedupRecord:
    tool_name: str
    arguments: dict[str, Any]
    result: str = ""
    step: int = 0
    count: int = 1


class ToolDeduplicator:
    def __init__(self, max_history: int = 50):
        self._history: deque[DedupRecord] = deque(maxlen=max_history)
        self._step_counts: dict[str, int] = defaultdict(int)
        self._current_step = 0

    def new_step(self) -> None:
        self._current_step += 1

    def fingerprint(self, tool_name: str, arguments: dict[str, Any]) -> str:
        return hashlib.md5(
            json.dumps([tool_name, arguments], sort_keys=True, default=str).encode()
        ).hexdigest()

    def check(self, tool_name: str, arguments: dict[str, Any]) -> tuple[bool, str, str | None]:
        fp = self.fingerprint(tool_name, arguments)
        self._step_counts[fp] += 1
        count = self._step_counts[fp]

        # Check if this exact call was already made in this step
        for record in self._history:
            if record.step == self._current_step and self.fingerprint(record.tool_name, record.arguments) == fp:
                return True, record.result, None

        # Check repetition level and return reminder
        for threshold, reminder in REMINDER_LEVELS:
            if count == threshold:
                if threshold >= 12:
                    return True, "", "force_stop"
                return False, "", reminder

        return False, "", None

    def record(self, tool_name: str, arguments: dict[str, Any], result: str) -> None:
        fp = self.fingerprint(tool_name, arguments)
        record = DedupRecord(
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            step=self._current_step,
            count=self._step_counts[fp],
        )
        self._history.append(record)

    def reset(self) -> None:
        self._history.clear()
        self._step_counts.clear()
        self._current_step = 0

    def get_repetition_count(self, tool_name: str, arguments: dict[str, Any]) -> int:
        fp = self.fingerprint(tool_name, arguments)
        return self._step_counts.get(fp, 0)
