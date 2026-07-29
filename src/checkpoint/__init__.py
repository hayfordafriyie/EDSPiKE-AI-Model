from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field
from typing import Any


class BackToTheFuture(Exception):
    def __init__(self, save_id: str, message: str):
        self.save_id = save_id
        self.message = message
        super().__init__(f"DMail: revert to {save_id}: {message}")


@dataclass
class Checkpoint:
    save_id: str
    step: int
    context: list[dict[str, Any]]
    state: dict[str, Any]
    timestamp: float = 0.0


class CheckpointManager:
    def __init__(self):
        self._checkpoints: list[Checkpoint] = []
        self._step = 0

    def save(self, context: list[dict[str, Any]], state: dict[str, Any] | None = None) -> str:
        self._step += 1
        save_id = f"cp_{self._step}_{int(time.time())}"
        checkpoint = Checkpoint(
            save_id=save_id,
            step=self._step,
            context=copy.deepcopy(context),
            state=copy.deepcopy(state or {}),
            timestamp=time.time(),
        )
        self._checkpoints.append(checkpoint)
        return save_id

    def revert(self, save_id: str) -> Checkpoint | None:
        for i, cp in enumerate(self._checkpoints):
            if cp.save_id == save_id:
                result = copy.deepcopy(cp)
                self._checkpoints = self._checkpoints[:i]
                self._step = cp.step
                return result
        return None

    def revert_to_step(self, step: int) -> Checkpoint | None:
        for i, cp in enumerate(reversed(self._checkpoints)):
            if cp.step <= step:
                return self.revert(cp.save_id)
        return None

    def send_dmail(self, save_id: str, message: str) -> None:
        raise BackToTheFuture(save_id, message)

    def latest(self) -> Checkpoint | None:
        return self._checkpoints[-1] if self._checkpoints else None

    def count(self) -> int:
        return len(self._checkpoints)

    def clear(self) -> None:
        self._checkpoints.clear()
        self._step = 0
