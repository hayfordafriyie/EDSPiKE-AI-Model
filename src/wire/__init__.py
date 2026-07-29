from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue
from typing import Any


class WireEventType(Enum):
    TURN_BEGIN = "turn_begin"
    TURN_END = "turn_end"
    STEP_BEGIN = "step_begin"
    STEP_END = "step_end"
    STEP_INTERRUPTED = "step_interrupted"
    COMPACTION_BEGIN = "compaction_begin"
    COMPACTION_END = "compaction_end"
    TEXT_PART = "text_part"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    STATUS_UPDATE = "status_update"
    APPROVAL_REQUEST = "approval_request"
    QUESTION_REQUEST = "question_request"
    BTW_BEGIN = "btw_begin"
    BTW_END = "btw_end"
    PLAN_DISPLAY = "plan_display"
    SUBAGENT_EVENT = "subagent_event"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class WireMessage:
    type: WireEventType
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0


class WireChannel:
    def __init__(self):
        self._queue: Queue = Queue()
        self._shutdown = False

    def send(self, msg: WireMessage) -> None:
        if self._shutdown:
            return
        msg.timestamp = time.time()
        self._queue.put(msg)

    def receive(self, block: bool = True, timeout: float | None = None) -> WireMessage | None:
        try:
            return self._queue.get(block=block, timeout=timeout)
        except Exception:
            return None

    def shutdown(self) -> None:
        self._shutdown = True
        self._queue.put(WireMessage(type=WireEventType.SHUTDOWN))

    @property
    def is_shutdown(self) -> bool:
        return self._shutdown


class Wire:
    def __init__(self):
        self.soul_side = WireChannel()
        self.ui_side = WireChannel()

    def shutdown(self) -> None:
        self.soul_side.shutdown()
        self.ui_side.shutdown()


def send_wire_event(wire: Wire | None, event_type: WireEventType, data: dict[str, Any] | None = None) -> None:
    if wire is None:
        return
    wire.soul_side.send(WireMessage(type=event_type, data=data or {}))


def turn_begin(wire: Wire | None, user_input: str) -> None:
    send_wire_event(wire, WireEventType.TURN_BEGIN, {"user_input": user_input})


def turn_end(wire: Wire | None) -> None:
    send_wire_event(wire, WireEventType.TURN_END)


def step_begin(wire: Wire | None, n: int) -> None:
    send_wire_event(wire, WireEventType.STEP_BEGIN, {"n": n})


def step_end(wire: Wire | None) -> None:
    send_wire_event(wire, WireEventType.STEP_END)


def send_text(wire: Wire | None, text: str) -> None:
    send_wire_event(wire, WireEventType.TEXT_PART, {"text": text})


def send_status(wire: Wire | None, context_usage: float = 0.0, plan_mode: bool = False, afk: bool = False) -> None:
    send_wire_event(wire, WireEventType.STATUS_UPDATE, {
        "context_usage": context_usage,
        "plan_mode": plan_mode,
        "afk_enabled": afk,
    })


def send_approval_request(wire: Wire | None, tool: str, args: dict[str, Any]) -> None:
    send_wire_event(wire, WireEventType.APPROVAL_REQUEST, {"tool": tool, "arguments": args})


def send_compaction_begin(wire: Wire | None) -> None:
    send_wire_event(wire, WireEventType.COMPACTION_BEGIN)


def send_compaction_end(wire: Wire | None) -> None:
    send_wire_event(wire, WireEventType.COMPACTION_END)
