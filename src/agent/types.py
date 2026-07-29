from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Step:
    index: int
    description: str
    action: str
    status: StepStatus = StepStatus.PENDING
    result: str = ""
    error: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Plan:
    goal: str
    steps: list[Step] = field(default_factory=list)
    current_step: int = 0


@dataclass
class AgentState:
    plan: Plan = field(default_factory=lambda: Plan(goal=""))
    messages: list[dict[str, Any]] = field(default_factory=list)
    total_tokens: int = 0
    max_steps: int = 20
    finished: bool = False
    final_answer: str = ""
