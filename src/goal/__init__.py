from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4


MAX_OBJECTIVE_LENGTH = 4000
MAX_CRITERION_LENGTH = 4000

GoalStatus = str  # 'active' | 'paused' | 'blocked' | 'complete'
GoalActor = str  # 'user' | 'model' | 'runtime' | 'system'


@dataclass
class GoalBudgetLimits:
    token_budget: int | None = None
    turn_budget: int | None = None
    wall_clock_budget_ms: int | None = None


@dataclass
class GoalSnapshot:
    goal_id: str
    objective: str
    completion_criterion: str = ""
    status: GoalStatus = "active"
    turns_used: int = 0
    tokens_used: int = 0
    wall_clock_ms: float = 0.0
    budget_limits: GoalBudgetLimits = field(default_factory=GoalBudgetLimits)
    terminal_reason: str = ""


@dataclass
class GoalBudgetReport:
    token_budget: int | None = None
    turn_budget: int | None = None
    wall_clock_budget_ms: int | None = None
    remaining_tokens: int | None = None
    remaining_turns: int | None = None
    remaining_wall_clock_ms: float | None = None
    token_budget_reached: bool = False
    turn_budget_reached: bool = False
    wall_clock_budget_reached: bool = False
    over_budget: bool = False


GOAL_CANCELLED_REMINDER = (
    "The user cancelled the current goal. "
    "Ignore earlier active-goal reminders. "
    "Handle the next user request normally."
)

GOAL_FORK_CLEARED_REMINDER = (
    "This fork does not have a current goal. "
    "Ignore earlier active-goal reminders from the source session. "
    "Handle requests normally unless the user starts a new goal."
)


class GoalMode:
    def __init__(self, data_dir: str = ""):
        self._data_dir = Path(data_dir) if data_dir else Path.cwd() / ".edspike" / "goals"
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._state: dict[str, Any] | None = None
        self._wall_clock_resumed_at: float | None = None
        self._budget_limits: GoalBudgetLimits = GoalBudgetLimits()
        self._load()

    def _path(self) -> Path:
        return self._data_dir / "active_goal.json"

    def _load(self) -> None:
        path = self._path()
        if path.exists():
            try:
                data = json.loads(path.read_text())
                self._state = data
                self._budget_limits = GoalBudgetLimits(**data.get("budget_limits", {}))
                self._wall_clock_resumed_at = data.get("wall_clock_resumed_at")
                if self._state and self._state.get("status") == "active":
                    self._normalize_after_replay()
            except Exception:
                self._state = None

    def _save(self) -> None:
        if self._state is None:
            if self._path().exists():
                self._path().unlink()
            return
        data = dict(self._state)
        data["budget_limits"] = {
            "token_budget": self._budget_limits.token_budget,
            "turn_budget": self._budget_limits.turn_budget,
            "wall_clock_budget_ms": self._budget_limits.wall_clock_budget_ms,
        }
        data["wall_clock_resumed_at"] = self._wall_clock_resumed_at
        self._path().write_text(json.dumps(data, indent=2))

    def _normalize_after_replay(self) -> None:
        if self._state is None:
            return
        self._wall_clock_resumed_at = None
        if self._state["status"] == "active":
            self._state["status"] = "paused"
            self._state["terminal_reason"] = "Paused after agent resume"
            self._save()

    # --- Public API ---

    def get_goal(self) -> GoalSnapshot | None:
        if self._state is None:
            return None
        return self._to_snapshot()

    def get_active_goal(self) -> GoalSnapshot | None:
        if self._state is None or self._state.get("status") != "active":
            return None
        return self._to_snapshot()

    def create_goal(self, objective: str, completion_criterion: str = "", replace: bool = False, actor: str = "user") -> GoalSnapshot:
        objective = objective.strip()
        if not objective:
            raise ValueError("Goal objective cannot be empty")
        if len(objective) > MAX_OBJECTIVE_LENGTH:
            raise ValueError(f"Goal objective cannot exceed {MAX_OBJECTIVE_LENGTH} characters")

        if self._state is not None:
            if not replace:
                raise ValueError("A goal already exists; use replace=True to start a new one")

        if completion_criterion and len(completion_criterion) > MAX_CRITERION_LENGTH:
            completion_criterion = completion_criterion[:MAX_CRITERION_LENGTH]

        self._state = {
            "goal_id": str(uuid4()),
            "objective": objective,
            "completion_criterion": completion_criterion,
            "status": "active",
            "turns_used": 0,
            "tokens_used": 0,
            "wall_clock_ms": 0.0,
            "terminal_reason": "",
        }
        self._wall_clock_resumed_at = time.time()
        self._budget_limits = GoalBudgetLimits()
        self._save()
        return self._to_snapshot()

    def pause_goal(self, reason: str = "", actor: str = "user") -> GoalSnapshot:
        state = self._require_state()
        if state["status"] == "paused":
            return self._to_snapshot()
        if state["status"] != "active":
            raise ValueError(f'Cannot pause a goal in status "{state["status"]}"')
        self._apply_status("paused", reason)
        self._save()
        return self._to_snapshot()

    def resume_goal(self, reason: str = "", actor: str = "user") -> GoalSnapshot:
        state = self._require_state()
        if state["status"] == "active":
            return self._to_snapshot()
        if state["status"] not in ("paused", "blocked"):
            raise ValueError(f'Cannot resume a goal in status "{state["status"]}"')
        state["terminal_reason"] = ""
        self._apply_status("active")
        self._save()
        return self._to_snapshot()

    def cancel_goal(self, actor: str = "user") -> GoalSnapshot | None:
        if self._state is None:
            return None
        snapshot = self._to_snapshot()
        self._state = None
        self._wall_clock_resumed_at = None
        self._save()
        return snapshot

    def mark_blocked(self, reason: str = "", actor: str = "runtime") -> GoalSnapshot | None:
        if self._state is None or self._state["status"] != "active":
            return None
        self._apply_status("blocked", reason)
        self._save()
        return self._to_snapshot()

    def mark_complete(self, reason: str = "", actor: str = "model") -> GoalSnapshot | None:
        if self._state is None or self._state["status"] != "active":
            return None
        self._state["terminal_reason"] = reason
        snapshot = self._to_snapshot_with_status("complete")
        self._state = None
        self._wall_clock_resumed_at = None
        self._save()
        return snapshot

    def record_token_usage(self, token_delta: int) -> GoalSnapshot | None:
        if self._state is None or self._state["status"] != "active":
            return None
        self._state["tokens_used"] += max(0, token_delta)
        self._save()
        return self._to_snapshot()

    def increment_turn(self) -> GoalSnapshot | None:
        if self._state is None or self._state["status"] != "active":
            return None
        self._state["turns_used"] += 1
        self._save()
        return self._to_snapshot()

    def set_budget_limits(self, limits: GoalBudgetLimits) -> GoalSnapshot:
        self._require_state()
        self._budget_limits = limits
        self._save()
        return self._to_snapshot()

    def get_budget_report(self) -> GoalBudgetReport:
        if self._state is None or self._state["status"] != "active":
            return GoalBudgetReport()

        wall_clock_ms = self._live_wall_clock_ms()
        tokens_used = self._state["tokens_used"]
        turns_used = self._state["turns_used"]

        token_reached = self._budget_limits.token_budget is not None and tokens_used >= self._budget_limits.token_budget
        turn_reached = self._budget_limits.turn_budget is not None and turns_used >= self._budget_limits.turn_budget
        wall_reached = self._budget_limits.wall_clock_budget_ms is not None and wall_clock_ms >= self._budget_limits.wall_clock_budget_ms

        return GoalBudgetReport(
            token_budget=self._budget_limits.token_budget,
            turn_budget=self._budget_limits.turn_budget,
            wall_clock_budget_ms=self._budget_limits.wall_clock_budget_ms,
            remaining_tokens=None if self._budget_limits.token_budget is None else max(0, self._budget_limits.token_budget - tokens_used),
            remaining_turns=None if self._budget_limits.turn_budget is None else max(0, self._budget_limits.turn_budget - turns_used),
            remaining_wall_clock_ms=None if self._budget_limits.wall_clock_budget_ms is None else max(0, self._budget_limits.wall_clock_budget_ms - wall_clock_ms),
            token_budget_reached=token_reached,
            turn_budget_reached=turn_reached,
            wall_clock_budget_reached=wall_reached,
            over_budget=token_reached or turn_reached or wall_reached,
        )

    # --- Internals ---

    def _require_state(self) -> dict[str, Any]:
        if self._state is None:
            raise ValueError("No current goal")
        return self._state

    def _apply_status(self, status: str, reason: str = "") -> None:
        now = time.time()
        if self._state["status"] == "active" and self._wall_clock_resumed_at is not None:
            self._state["wall_clock_ms"] += max(0, now - self._wall_clock_resumed_at)
            self._wall_clock_resumed_at = None
        if status == "active":
            self._wall_clock_resumed_at = now
        self._state["status"] = status
        if reason:
            self._state["terminal_reason"] = reason

    def _live_wall_clock_ms(self) -> float:
        if self._state is not None and self._state["status"] == "active" and self._wall_clock_resumed_at is not None:
            return self._state["wall_clock_ms"] + max(0, time.time() - self._wall_clock_resumed_at) * 1000
        return self._state["wall_clock_ms"] * 1000 if self._state else 0.0

    def _to_snapshot(self) -> GoalSnapshot:
        return self._to_snapshot_with_status(self._state["status"])

    def _to_snapshot_with_status(self, status: str) -> GoalSnapshot:
        return GoalSnapshot(
            goal_id=self._state["goal_id"],
            objective=self._state["objective"],
            completion_criterion=self._state.get("completion_criterion", ""),
            status=status,
            turns_used=self._state["turns_used"],
            tokens_used=self._state["tokens_used"],
            wall_clock_ms=self._live_wall_clock_ms(),
            budget_limits=self._budget_limits,
            terminal_reason=self._state.get("terminal_reason", ""),
        )
