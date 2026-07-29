from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


class ApprovalError(Exception):
    pass


@dataclass
class ApprovalRequest:
    id: str
    session_id: str
    tool_name: str
    arguments: dict[str, Any]
    source: str = "agent"  # agent, subagent
    status: str = "pending"  # pending, approved, rejected, approved_for_session
    feedback: str = ""
    created_at: float = 0.0
    resolved_at: float = 0.0


class ApprovalRuntime:
    def __init__(self):
        self._requests: dict[str, ApprovalRequest] = {}
        self._session_approvals: dict[str, set[str]] = {}  # session_id -> set of tool names

    def request(self, session_id: str, tool_name: str, arguments: dict[str, Any], source: str = "agent") -> ApprovalRequest:
        req = ApprovalRequest(
            id=f"apr_{int(time.time() * 1000000)}",
            session_id=session_id,
            tool_name=tool_name,
            arguments=arguments,
            source=source,
            created_at=time.time(),
        )
        self._requests[req.id] = req
        return req

    def approve(self, request_id: str, feedback: str = "") -> ApprovalRequest | None:
        req = self._requests.get(request_id)
        if req is None or req.status != "pending":
            return None
        req.status = "approved"
        req.feedback = feedback
        req.resolved_at = time.time()
        return req

    def approve_for_session(self, request_id: str, feedback: str = "") -> ApprovalRequest | None:
        req = self.approve(request_id, feedback)
        if req is None:
            return None
        req.status = "approved_for_session"
        if req.session_id not in self._session_approvals:
            self._session_approvals[req.session_id] = set()
        self._session_approvals[req.session_id].add(req.tool_name)
        return req

    def reject(self, request_id: str, feedback: str = "") -> ApprovalRequest | None:
        req = self._requests.get(request_id)
        if req is None or req.status != "pending":
            return None
        req.status = "rejected"
        req.feedback = feedback
        req.resolved_at = time.time()
        return req

    def is_approved(self, session_id: str, tool_name: str) -> bool:
        session_approvals = self._session_approvals.get(session_id, set())
        return tool_name in session_approvals

    def get_pending(self, session_id: str = "") -> list[ApprovalRequest]:
        reqs = [r for r in self._requests.values() if r.status == "pending"]
        if session_id:
            reqs = [r for r in reqs if r.session_id == session_id]
        return sorted(reqs, key=lambda r: r.created_at)

    def get_history(self, session_id: str = "", limit: int = 20) -> list[ApprovalRequest]:
        reqs = list(self._requests.values())
        if session_id:
            reqs = [r for r in reqs if r.session_id == session_id]
        return sorted(reqs, key=lambda r: r.created_at, reverse=True)[:limit]

    def clear_session(self, session_id: str) -> None:
        self._session_approvals.pop(session_id, None)
        self._requests = {k: v for k, v in self._requests.items() if v.session_id != session_id}
