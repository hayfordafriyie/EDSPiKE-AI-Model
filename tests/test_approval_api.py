from __future__ import annotations

import pytest

pytest.importorskip("dotenv")
pytest.importorskip("fastapi")

import os

from fastapi.testclient import TestClient
from src.deployment.inference_server import app
from src.tools.permissions import ApprovalManager, ApprovalDecision

os.environ.setdefault("EDSPIKE_API_KEY", "test-key-123")
client = TestClient(app)
AUTH = {"Authorization": "Bearer test-key-123"}


def test_approve_invalid_session():
    resp = client.post(
        "/v1/approve",
        json={"session_id": "bad", "action": "approve_one", "index": 0},
        headers=AUTH,
    )
    assert resp.status_code == 400
    assert "not found" in resp.json()["detail"]


def test_approve_invalid_action():
    resp = client.post(
        "/v1/approve",
        json={"session_id": "x", "action": "invalid_action"},
        headers=AUTH,
    )
    assert resp.status_code == 422


class TestApprovalManager:
    def test_approve_one_missing_index(self):
        mgr = ApprovalManager()
        result = mgr.decide("nonexistent", ApprovalDecision.APPROVE_ONE)
        assert "error" in result
        assert "not found" in result["error"]

    def test_approve_one_with_index_no_session(self):
        mgr = ApprovalManager()
        result = mgr.decide("nonexistent", ApprovalDecision.APPROVE_ONE, index=0)
        assert "error" in result
        assert "not found" in result["error"]

    def test_approve_all_no_session(self):
        mgr = ApprovalManager()
        result = mgr.decide("nonexistent", ApprovalDecision.APPROVE_ALL)
        assert "error" in result
