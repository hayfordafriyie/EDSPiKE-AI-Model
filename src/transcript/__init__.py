from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

SubscriptionFn = Callable[[str, dict[str, Any]], None]

SUB_GRANULARITY_OFF = 0
SUB_GRANULARITY_TURN = 1
SUB_GRANULARITY_BLOCK = 2
SUB_GRANULARITY_DELTA = 3


@dataclass
class TranscriptEntry:
    turn_id: str
    agent_id: str
    role: str
    content: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    batch: int = 0


class TranscriptStore:
    def __init__(self, data_dir: str):
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._wire_path = self._data_dir / "wire.jsonl"
        self._entries: list[TranscriptEntry] = []
        self._batch = 0
        self._subscriptions: dict[str, tuple[int, SubscriptionFn]] = {}
        self._load()

    def _load(self) -> None:
        if self._wire_path.exists():
            try:
                for line in self._wire_path.read_text().splitlines():
                    if line.strip():
                        data = json.loads(line)
                        entry = TranscriptEntry(**data)
                        self._entries.append(entry)
                        self._batch = max(self._batch, entry.batch)
            except Exception:
                pass

    def _append_wire(self, entry: TranscriptEntry) -> None:
        with self._wire_path.open("a") as f:
            f.write(json.dumps({
                "turn_id": entry.turn_id,
                "agent_id": entry.agent_id,
                "role": entry.role,
                "content": entry.content,
                "tool_calls": entry.tool_calls,
                "tool_results": entry.tool_results,
                "metadata": entry.metadata,
                "timestamp": entry.timestamp,
                "batch": entry.batch,
            }) + "\n")

    def append(self, agent_id: str, role: str, content: str, tool_calls: list | None = None, tool_results: list | None = None) -> TranscriptEntry:
        self._batch += 1
        entry = TranscriptEntry(
            turn_id=f"t_{int(time.time() * 1000000)}",
            agent_id=agent_id,
            role=role,
            content=content,
            tool_calls=tool_calls or [],
            tool_results=tool_results or [],
            timestamp=time.time(),
            batch=self._batch,
        )
        self._entries.append(entry)
        self._append_wire(entry)
        self._notify("append", {"entry": entry, "agent_id": agent_id})
        return entry

    def get_entries(self, agent_id: str = "", limit: int = 100, offset: int = 0) -> list[TranscriptEntry]:
        entries = [e for e in self._entries if not agent_id or e.agent_id == agent_id]
        return entries[offset:offset + limit]

    def get_turns(self, agent_id: str = "", limit: int = 50) -> list[list[TranscriptEntry]]:
        entries = self.get_entries(agent_id=agent_id, limit=limit * 10)
        turns: list[list[TranscriptEntry]] = []
        current_turn: list[TranscriptEntry] = []
        for entry in entries:
            if entry.role == "user" and current_turn:
                turns.append(current_turn)
                current_turn = []
            current_turn.append(entry)
        if current_turn:
            turns.append(current_turn)
        return turns[-limit:]

    def cold_rebuild(self) -> None:
        if self._wire_path.exists():
            self._entries.clear()
            self._load()

    def subscribe(self, key: str, granularity: int, fn: SubscriptionFn) -> None:
        self._subscriptions[key] = (granularity, fn)

    def unsubscribe(self, key: str) -> None:
        self._subscriptions.pop(key, None)

    def _notify(self, event: str, data: dict[str, Any]) -> None:
        for key, (granularity, fn) in self._subscriptions.items():
            try:
                fn(event, data)
            except Exception:
                pass

    def count(self) -> int:
        return len(self._entries)

    def get_agent_ids(self) -> list[str]:
        return list({e.agent_id for e in self._entries})

    def latest_batch(self) -> int:
        return self._batch
