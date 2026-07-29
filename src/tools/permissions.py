from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from .executor import ToolExecutor

logger = logging.getLogger(__name__)


class ApprovalDecision(Enum):
    APPROVE_ONE = "approve_one"
    APPROVE_ALL = "approve_all"
    REJECT = "reject"


@dataclass
class PendingCall:
    index: int
    name: str
    arguments: dict[str, Any]


@dataclass
class ApprovalSession:
    session_id: str
    messages: list[str] = field(default_factory=list)
    pending_calls: list[PendingCall] = field(default_factory=list)
    executor: ToolExecutor | None = None
    generate_fn: Callable | None = None
    max_tokens: int = 4096
    temperature: float = 0.3
    total_tokens: int = 0
    approve_all: bool = False
    finished: bool = False
    final_answer: str = ""


class ApprovalManager:
    def __init__(self):
        self._sessions: dict[str, ApprovalSession] = {}

    def create_session(
        self,
        generate_fn: Callable,
        executor: ToolExecutor,
        messages: list[str],
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        sid = uuid.uuid4().hex[:16]
        self._sessions[sid] = ApprovalSession(
            session_id=sid,
            messages=messages,
            executor=executor,
            generate_fn=generate_fn,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return sid

    def get_pending_calls(self, session_id: str) -> list[dict[str, Any]]:
        session = self._sessions.get(session_id)
        if not session:
            return []
        return [
            {
                "index": pc.index,
                "tool": pc.name,
                "arguments": pc.arguments,
                "description": f"{pc.name}({', '.join(f'{k}={v}' for k, v in pc.arguments.items())})",
            }
            for pc in session.pending_calls
        ]

    def decide(
        self, session_id: str, decision: ApprovalDecision, index: int | None = None
    ) -> dict[str, Any]:
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "Session not found or expired"}
        if session.finished:
            return {"status": "finished", "final_answer": session.final_answer}

        if decision == ApprovalDecision.APPROVE_ALL:
            session.approve_all = True
            return self._execute_all_pending(session)

        if decision == ApprovalDecision.APPROVE_ONE and index is not None:
            approved = [pc for pc in session.pending_calls if pc.index == index]
            if not approved:
                return {"error": f"No pending call with index {index}"}
            rejected = [pc for pc in session.pending_calls if pc.index != index]
            return self._execute_selected(session, approved, rejected)

        if decision == ApprovalDecision.REJECT and index is not None:
            rejected = [pc for pc in session.pending_calls if pc.index == index]
            approved = [pc for pc in session.pending_calls if pc.index != index]
            if not rejected:
                return {"error": f"No pending call with index {index}"}
            return self._execute_selected(session, approved, rejected)

        return {"error": "Invalid decision"}

    def _execute_selected(
        self, session: ApprovalSession, approved: list[PendingCall], rejected: list[PendingCall]
    ) -> dict[str, Any]:
        results: list[str] = []
        for pc in rejected:
            results.append(f"<tool_result>\nUser rejected this operation\n</tool_result>")
        for pc in approved:
            try:
                out = session.executor.execute(pc.name, pc.arguments)
                results.append(f"<tool_result>\n{out}\n</tool_result>")
            except Exception as exc:
                results.append(f"<tool_result>\nError: {exc}\n</tool_result>")
        return self._continue(session, results)

    def _execute_all_pending(self, session: ApprovalSession) -> dict[str, Any]:
        results: list[str] = []
        for pc in session.pending_calls:
            try:
                out = session.executor.execute(pc.name, pc.arguments)
                results.append(f"<tool_result>\n{out}\n</tool_result>")
            except Exception as exc:
                results.append(f"<tool_result>\nError: {exc}\n</tool_result>")
        return self._continue(session, results)

    def _continue(self, session: ApprovalSession, results: list[str]) -> dict[str, Any]:
        if session.messages:
            last = session.messages[-1] if session.messages else ""
            session.messages.append(last)
        session.messages.extend(results)
        session.total_tokens += sum(len(r) for r in results)

        return self._run_next_turn(session)

    def _run_next_turn(self, session: ApprovalSession) -> dict[str, Any]:
        prompt = "\n\n".join(session.messages)
        responses, counts = session.generate_fn(
            [prompt],
            max_tokens=session.max_tokens,
            temperature=session.temperature,
            top_p=0.95,
        )
        response = responses[0].strip()
        session.total_tokens += counts[0]
        session.messages.append(response)

        calls = session.executor.parse_tool_call(response)
        if calls:
            if session.approve_all:
                results: list[str] = []
                for call in calls:
                    try:
                        out = session.executor.execute(call["name"], call["arguments"])
                        results.append(f"<tool_result>\n{out}\n</tool_result>")
                    except Exception as exc:
                        results.append(f"<tool_result>\nError: {exc}\n</tool_result>")
                session.messages.extend(results)
                return self._run_next_turn(session)

            session.pending_calls = [
                PendingCall(index=i, name=c["name"], arguments=c["arguments"])
                for i, c in enumerate(calls)
            ]
            return {
                "status": "awaiting_approval",
                "session_id": session.session_id,
                "pending_calls": [
                    {
                        "index": pc.index,
                        "tool": pc.name,
                        "arguments": pc.arguments,
                        "description": f"{pc.name}({', '.join(f'{k}={v}' for k, v in pc.arguments.items())})",
                    }
                    for pc in session.pending_calls
                ],
            }

        session.finished = True
        session.final_answer = response
        return {
            "status": "completed",
            "session_id": session.session_id,
            "response": response,
            "tokens_generated": session.total_tokens,
        }

    def cleanup(self, session_id: str):
        self._sessions.pop(session_id, None)
