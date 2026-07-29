from __future__ import annotations

import pytest

pytest.importorskip("dotenv")
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient
from src.deployment.inference_server import app

client = TestClient(app)


def test_approve_invalid_session():
    resp = client.post(
        "/v1/approve",
        json={"session_id": "bad", "action": "approve_one", "index": 0},
    )
    assert resp.status_code == 400
    assert "error" in resp.json()["detail"]


def test_approve_invalid_action():
    resp = client.post(
        "/v1/approve",
        json={"session_id": "x", "action": "invalid_action"},
    )
    assert resp.status_code == 422


def test_approve_missing_index():
    resp = client.post(
        "/v1/approve",
        json={"session_id": "x", "action": "approve_one"},
    )
    assert resp.status_code == 200
