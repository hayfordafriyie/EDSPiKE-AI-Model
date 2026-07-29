from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolOutput:
    id: str = ""
    session_id: str = ""
    tool_name: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    result: str = ""
    error: str = ""
    duration_ms: float = 0.0
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class ToolOutputStore:
    def __init__(self):
        self._outputs: list[ToolOutput] = []
        self._index: dict[str, list[int]] = {}  # session_id → indices

    def record(self, session_id: str, tool_name: str, arguments: dict[str, Any], result: str = "", error: str = "", duration_ms: float = 0.0) -> ToolOutput:
        output = ToolOutput(
            id=f"to_{int(time.time() * 1000)}_{len(self._outputs)}",
            session_id=session_id,
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            error=error,
            duration_ms=duration_ms,
            timestamp=time.time(),
        )
        idx = len(self._outputs)
        self._outputs.append(output)
        if session_id not in self._index:
            self._index[session_id] = []
        self._index[session_id].append(idx)
        return output

    def get_session_outputs(self, session_id: str) -> list[ToolOutput]:
        indices = self._index.get(session_id, [])
        return [self._outputs[i] for i in indices]

    def get_last(self, session_id: str, tool_name: str | None = None) -> ToolOutput | None:
        indices = self._index.get(session_id, [])
        for i in reversed(indices):
            out = self._outputs[i]
            if tool_name is None or out.tool_name == tool_name:
                return out
        return None

    def get_all(self, limit: int = 100) -> list[ToolOutput]:
        return self._outputs[-limit:]

    def clear_session(self, session_id: str) -> None:
        indices = self._index.pop(session_id, [])
        self._outputs = [o for i, o in enumerate(self._outputs) if i not in indices]

    def count(self) -> int:
        return len(self._outputs)
