from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from ..agent import AgentLoop, AgentState, Plan, Planner, Step, StepStatus

from .store import SessionStore, SessionStatus

logger = logging.getLogger(__name__)


@dataclass
class RunResult:
    session_id: str
    final_answer: str
    total_tokens: int
    total_steps: int
    duration_ms: float
    finished: bool
    error: str = ""


class SessionRunner:
    def __init__(self, session_store: SessionStore):
        self._store = session_store

    def create_and_run(
        self,
        task: str,
        generate_fn: Callable,
        agent_id: str = "default",
        provider: str = "local",
        model: str = "",
        metadata: dict | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.3,
    ) -> RunResult:
        session = self._store.create_session(
            agent_id=agent_id,
            provider=provider,
            model=model,
            metadata=metadata,
        )
        return self.run(session.id, task, generate_fn, max_tokens, temperature)

    def run(
        self,
        session_id: str,
        task: str,
        generate_fn: Callable,
        max_tokens: int = 2048,
        temperature: float = 0.3,
    ) -> RunResult:
        session = self._store.get_session(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        past_events = self._store.get_events(session_id)
        start = time.perf_counter()

        planner = Planner(generate_fn)
        loop = AgentLoop(generate_fn=generate_fn, planner=planner)

        try:
            state = loop.run(task, max_tokens=max_tokens, temperature=temperature)

            for msg in state.messages:
                role = "assistant" if msg.startswith("<tool") else "user"
                self._store.append_message(session_id, role, msg)

            self._store.append_message(session_id, "assistant", state.final_answer)

            final_status = SessionStatus.FINISHED if state.finished else SessionStatus.INTERRUPTED
            self._store.update_status(session_id, final_status)

            duration = (time.perf_counter() - start) * 1000
            return RunResult(
                session_id=session_id,
                final_answer=state.final_answer,
                total_tokens=state.total_tokens,
                total_steps=state.plan.current_step,
                duration_ms=round(duration, 1),
                finished=state.finished,
            )
        except Exception as exc:
            self._store.update_status(session_id, SessionStatus.ERROR)
            self._store.append_message(session_id, "assistant", f"[Error: {exc}]")
            duration = (time.perf_counter() - start) * 1000
            return RunResult(
                session_id=session_id,
                final_answer="",
                total_tokens=0,
                total_steps=0,
                duration_ms=round(duration, 1),
                finished=False,
                error=str(exc),
            )

    def replay(self, session_id: str, generate_fn: Callable | None = None) -> list[dict[str, Any]]:
        session = self._store.get_session(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")
        events = self._store.get_events(session_id)
        steps = []
        for e in reversed(events):
            steps.append({
                "event_id": e.id,
                "type": e.event_type,
                "data": e.data,
                "timestamp": e.created_at,
            })
        return steps

    def list_runs(self, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
        sessions = self._store.list_sessions(limit=limit, offset=offset)
        return [
            {
                "session_id": s.id,
                "agent_id": s.agent_id,
                "status": s.status.value,
                "message_count": len(s.messages),
                "created_at": s.created_at,
                "updated_at": s.updated_at,
            }
            for s in sessions
        ]
