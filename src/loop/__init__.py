from __future__ import annotations

import hashlib
import json
from collections import deque
from dataclasses import dataclass, field
from typing import Any


RECOVERY_PROMPT = """You appear to be repeating the same actions. Take a step back and consider:
1. What are you trying to accomplish?
2. What has already been tried?
3. Is there a different approach?
Please summarize what you've done so far and explain a new approach."""


@dataclass
class LoopAction:
    tool: str
    args: dict[str, Any] = field(default_factory=dict)

    def fingerprint(self) -> str:
        return hashlib.md5(
            json.dumps([self.tool, self.args], sort_keys=True).encode()
        ).hexdigest()


class DoomLoopDetector:
    def __init__(self, window_size: int = 5, threshold: int = 3):
        self.window_size = window_size
        self.threshold = threshold
        self._history: deque[LoopAction] = deque(maxlen=window_size)

    def record(self, tool: str, args: dict[str, Any]) -> None:
        self._history.append(LoopAction(tool=tool, args=args))

    def is_looping(self) -> bool:
        if len(self._history) < self.threshold:
            return False

        fingerprints = [a.fingerprint() for a in self._history]
        recent = fingerprints[-self.threshold:]

        return len(set(recent)) == 1

    def get_recovery_prompt(self) -> str:
        return RECOVERY_PROMPT

    def clear(self) -> None:
        self._history.clear()

    def last_actions(self, n: int = 3) -> list[LoopAction]:
        return list(self._history)[-n:]


MAX_STEPS_REACHED_PROMPT = """You have reached the maximum number of steps allowed. Please provide a summary of what you've accomplished and any remaining work that needs to be done."""


class MaxStepsLimiter:
    def __init__(self, max_steps: int = 25):
        self.max_steps = max_steps
        self._count = 0

    def record_step(self) -> None:
        self._count += 1

    def is_exhausted(self) -> bool:
        return self._count >= self.max_steps

    def remaining(self) -> int:
        return max(0, self.max_steps - self._count)

    def reset(self) -> None:
        self._count = 0

    def get_limit_prompt(self) -> str:
        return MAX_STEPS_REACHED_PROMPT
