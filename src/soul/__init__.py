from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from src.wire import Wire, send_wire_event, WireEventType


@dataclass
class SoulStatus:
    context_usage: float = 0.0
    plan_mode: bool = False
    afk_enabled: bool = False
    yolo_enabled: bool = False
    context_tokens: int = 0
    max_context_tokens: int = 0
    steps_taken: int = 0


class Soul(Protocol):
    @property
    def name(self) -> str:
        ...

    @property
    def status(self) -> SoulStatus:
        ...

    async def run(self, user_input: str, wire: Wire | None = None) -> str:
        ...


@dataclass
class SoulConfig:
    model: str = ""
    provider: str = ""
    temperature: float = 0.5
    max_tokens: int = 4096
    max_steps: int = 25
    system_prompt: str = ""
    plan_mode: bool = False
    tools_enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
