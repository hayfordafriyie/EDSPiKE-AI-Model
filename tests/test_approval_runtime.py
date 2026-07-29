import pytest

from src.approval_runtime import ApprovalRuntime


class TestApprovalRuntime:
    def test_request(self):
        ar = ApprovalRuntime()
        req = ar.request("sess1", "bash", {"cmd": "ls"})
        assert req.status == "pending"
        assert req.tool_name == "bash"

    def test_approve(self):
        ar = ApprovalRuntime()
        req = ar.request("s1", "bash", {})
        approved = ar.approve(req.id, "OK")
        assert approved is not None
        assert approved.status == "approved"

    def test_approve_for_session(self):
        ar = ApprovalRuntime()
        req = ar.request("s1", "read_file", {"path": "/x"})
        ar.approve_for_session(req.id)
        assert ar.is_approved("s1", "read_file") is True

    def test_reject(self):
        ar = ApprovalRuntime()
        req = ar.request("s1", "bash", {})
        rejected = ar.reject(req.id, "Not now")
        assert rejected.status == "rejected"

    def test_get_pending(self):
        ar = ApprovalRuntime()
        ar.request("s1", "bash", {})
        ar.request("s1", "write_file", {})
        ar.request("s2", "bash", {})
        assert len(ar.get_pending("s1")) == 2
        assert len(ar.get_pending("s2")) == 1

    def test_clear_session(self):
        ar = ApprovalRuntime()
        req = ar.request("s1", "bash", {})
        ar.approve_for_session(req.id)
        ar.clear_session("s1")
        assert ar.is_approved("s1", "bash") is False
