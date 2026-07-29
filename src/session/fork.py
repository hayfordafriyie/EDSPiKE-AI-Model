from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ForkedSession:
    fork_id: str
    original_session_id: str
    title: str
    turn_index: int
    created_at: float = 0.0
    turn_count: int = 0


class SessionForker:
    def __init__(self, sessions_dir: str):
        self._sessions_dir = Path(sessions_dir)
        self._sessions_dir.mkdir(parents=True, exist_ok=True)
        self._forks: dict[str, ForkedSession] = {}

    def fork(self, original_session_id: str, turn_index: int, title_prefix: str = "Fork") -> ForkedSession:
        fork_id = f"fork_{original_session_id}_{turn_index}_{int(time.time())}"
        fork = ForkedSession(
            fork_id=fork_id,
            original_session_id=original_session_id,
            title=f"{title_prefix}: {original_session_id}",
            turn_index=turn_index,
            created_at=time.time(),
        )

        # Copy wire file up to the turn index
        wire_path = self._sessions_dir / original_session_id / "wire.jsonl"
        if wire_path.exists():
            lines = wire_path.read_text().splitlines()
            truncated = lines[:turn_index * 2]  # approximate: 2 entries per turn
            fork_dir = self._sessions_dir / fork_id
            fork_dir.mkdir(parents=True, exist_ok=True)
            (fork_dir / "wire.jsonl").write_text("\n".join(truncated))
            fork.turn_count = len(truncated) // 2

        self._forks[fork_id] = fork
        return fork

    def get(self, fork_id: str) -> ForkedSession | None:
        return self._forks.get(fork_id)

    def list(self, original_session_id: str = "") -> list[ForkedSession]:
        forks = list(self._forks.values())
        if original_session_id:
            forks = [f for f in forks if f.original_session_id == original_session_id]
        return sorted(forks, key=lambda f: f.created_at, reverse=True)

    def delete(self, fork_id: str) -> bool:
        if fork_id not in self._forks:
            return False
        fork_dir = self._sessions_dir / fork_id
        if fork_dir.exists():
            shutil.rmtree(fork_dir)
        del self._forks[fork_id]
        return True
