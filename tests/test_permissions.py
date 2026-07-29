from __future__ import annotations

from src.tools.permissions import ApprovalDecision, ApprovalManager, PendingCall
from src.tools.executor import ToolExecutor


def test_approval_decision_enum_values():
    assert ApprovalDecision.APPROVE_ONE.value == "approve_one"
    assert ApprovalDecision.APPROVE_ALL.value == "approve_all"
    assert ApprovalDecision.REJECT.value == "reject"


def test_pending_call_fields():
    pc = PendingCall(index=0, name="read_file", arguments={"path": "/test"})
    assert pc.index == 0
    assert pc.name == "read_file"
    assert pc.arguments == {"path": "/test"}


def test_approval_manager_create_and_cleanup():
    mgr = ApprovalManager()
    sid = mgr.create_session(
        generate_fn=lambda prompts, **kw: (["test"], [1]),
        executor=ToolExecutor(),
        messages=["system", "user"],
    )
    assert sid in mgr._sessions
    mgr.cleanup(sid)
    assert sid not in mgr._sessions


def test_get_pending_calls_empty():
    mgr = ApprovalManager()
    assert mgr.get_pending_calls("nonexistent") == []


def test_decide_without_session_returns_error():
    mgr = ApprovalManager()
    result = mgr.decide("bad_session", ApprovalDecision.APPROVE_ONE, index=0)
    assert "error" in result
