from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.deployment.inference_server import app, _session_store


@pytest.fixture(autouse=True)
def isolate_session_store():
    """Use a temp DB for every test so tests don't leak into each other."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        with patch("src.deployment.inference_server._session_store") as mock_store:
            from src.session import SessionStore
            real = SessionStore(str(db_path))
            mock_store.create_session = real.create_session
            mock_store.get_session = real.get_session
            mock_store.list_sessions = real.list_sessions
            mock_store.append_message = real.append_message
            mock_store.update_status = real.update_status
            mock_store.delete_session = real.delete_session
            mock_store.get_event_stream = real.get_event_stream
            mock_store.get_events = real.get_events
            yield


@pytest.fixture(autouse=True)
def set_api_key():
    os.environ["EDSPIKE_API_KEY"] = "test-key-123"
    yield
    os.environ.pop("EDSPIKE_API_KEY", None)


@pytest.fixture
def client():
    return TestClient(app)


def _api_key_header():
    return {"Authorization": "Bearer test-key-123"}


# ── Sessions ──────────────────────────────────────────────────────────────

class TestSessionsAPI:
    def test_create_session(self, client):
        resp = client.post("/v1/sessions", json={"agent_id": "coding"}, headers=_api_key_header())
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert data["status"] == "active"

    def test_create_session_with_provider(self, client):
        resp = client.post("/v1/sessions", json={
            "agent_id": "default", "provider": "openai", "model": "gpt-4o",
        }, headers=_api_key_header())
        assert resp.status_code == 200

    def test_list_sessions(self, client):
        client.post("/v1/sessions", json={}, headers=_api_key_header())
        client.post("/v1/sessions", json={}, headers=_api_key_header())
        resp = client.get("/v1/sessions", headers=_api_key_header())
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["sessions"]) >= 2

    def test_get_session(self, client):
        created = client.post("/v1/sessions", json={"agent_id": "coding"}, headers=_api_key_header()).json()
        sid = created["session_id"]
        resp = client.get(f"/v1/sessions/{sid}", headers=_api_key_header())
        assert resp.status_code == 200
        assert resp.json()["id"] == sid
        assert resp.json()["agent_id"] == "coding"

    def test_get_session_not_found(self, client):
        resp = client.get("/v1/sessions/nonexistent", headers=_api_key_header())
        assert resp.status_code == 404

    def test_append_message(self, client):
        created = client.post("/v1/sessions", json={}, headers=_api_key_header()).json()
        sid = created["session_id"]
        resp = client.post(f"/v1/sessions/{sid}/messages", json={
            "role": "user", "content": "hello",
        }, headers=_api_key_header())
        assert resp.status_code == 200
        assert resp.json()["message_count"] == 1

    def test_get_events(self, client):
        created = client.post("/v1/sessions", json={}, headers=_api_key_header()).json()
        sid = created["session_id"]
        client.post(f"/v1/sessions/{sid}/messages", json={"role": "user", "content": "hi"}, headers=_api_key_header())
        resp = client.get(f"/v1/sessions/{sid}/events", headers=_api_key_header())
        assert resp.status_code == 200
        assert len(resp.json()["events"]) >= 2  # created + message.added

    def test_interrupt_session(self, client):
        created = client.post("/v1/sessions", json={}, headers=_api_key_header()).json()
        sid = created["session_id"]
        resp = client.post(f"/v1/sessions/{sid}/interrupt", headers=_api_key_header())
        assert resp.status_code == 200
        assert resp.json()["status"] == "interrupted"

    def test_delete_session(self, client):
        created = client.post("/v1/sessions", json={}, headers=_api_key_header()).json()
        sid = created["session_id"]
        resp = client.delete(f"/v1/sessions/{sid}", headers=_api_key_header())
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"
        # should be gone
        resp2 = client.get(f"/v1/sessions/{sid}", headers=_api_key_header())
        assert resp2.status_code == 404


# ── Agents ────────────────────────────────────────────────────────────────

class TestAgentsAPI:
    def test_list_agents(self, client):
        resp = client.get("/v1/agents", headers=_api_key_header())
        assert resp.status_code == 200
        agents = resp.json()["agents"]
        assert len(agents) >= 7
        ids = [a["id"] for a in agents]
        assert "coding" in ids
        assert "default" in ids

    def test_get_agent(self, client):
        resp = client.get("/v1/agents/coding", headers=_api_key_header())
        assert resp.status_code == 200
        assert resp.json()["name"] == "Software Engineer"
        assert resp.json()["tools_enabled"] is True

    def test_get_agent_not_found(self, client):
        resp = client.get("/v1/agents/nonexistent", headers=_api_key_header())
        assert resp.status_code == 404


# ── Providers ─────────────────────────────────────────────────────────────

class TestProvidersAPI:
    def test_list_providers(self, client):
        resp = client.get("/v1/providers", headers=_api_key_header())
        assert resp.status_code == 200
        providers = resp.json()["providers"]
        assert "local" in providers
        assert resp.json()["default"] == "local"


# ── Models ────────────────────────────────────────────────────────────────

class TestModelsAPI:
    def test_list_models(self, client):
        resp = client.get("/v1/models", headers=_api_key_header())
        assert resp.status_code == 200
        models = resp.json()["models"]
        assert len(models) >= 8
        ids = [m["id"] for m in models]
        assert "local" in ids
        assert "gpt-4o" in ids

    def test_list_models_filtered(self, client):
        resp = client.get("/v1/models?provider=openai", headers=_api_key_header())
        assert resp.status_code == 200
        models = resp.json()["models"]
        assert all(m["provider"] == "openai" for m in models)


# ── Filesystem ────────────────────────────────────────────────────────────

class TestFilesystemAPI:
    def test_fs_read(self, client, tmp_path: Path):
        f = tmp_path / "hello.txt"
        f.write_text("hello world")
        resp = client.post("/v1/fs/read", json={"path": str(f)}, headers=_api_key_header())
        assert resp.status_code == 200
        assert "hello world" in resp.json()["content"]

    def test_fs_write(self, client, tmp_path: Path):
        target = tmp_path / "written.txt"
        resp = client.post("/v1/fs/write", json={"path": str(target), "content": "new content"}, headers=_api_key_header())
        assert resp.status_code == 200
        assert target.read_text() == "new content"

    def test_fs_edit(self, client, tmp_path: Path):
        f = tmp_path / "edit.txt"
        f.write_text("old text")
        resp = client.post("/v1/fs/edit", json={"path": str(f), "old_string": "old text", "new_string": "new text"}, headers=_api_key_header())
        assert resp.status_code == 200
        assert f.read_text() == "new text"

    def test_fs_ls(self, client, tmp_path: Path):
        (tmp_path / "a.txt").touch()
        (tmp_path / "b.txt").touch()
        resp = client.get(f"/v1/fs/ls?path={tmp_path}", headers=_api_key_header())
        assert resp.status_code == 200
        entries = resp.json()["entries"]
        assert "a.txt" in entries
        assert "b.txt" in entries

    def test_fs_glob(self, client, tmp_path: Path):
        (tmp_path / "data.csv").touch()
        (tmp_path / "data.json").touch()
        resp = client.get(f"/v1/fs/glob?pattern=*.csv&path={tmp_path}", headers=_api_key_header())
        assert resp.status_code == 200
        assert any("data.csv" in f for f in resp.json()["files"])

    def test_fs_grep(self, client, tmp_path: Path):
        f = tmp_path / "search.txt"
        f.write_text("apple\nbanana\napple pie")
        resp = client.post("/v1/fs/grep", json={"pattern": "apple", "path": str(f)}, headers=_api_key_header())
        assert resp.status_code == 200
        matches = resp.json()["matches"]
        assert any("apple" in m for m in matches)

    def test_fs_error_handling(self, client):
        resp = client.post("/v1/fs/read", json={"path": "/nonexistent/file.txt"}, headers=_api_key_header())
        assert resp.status_code == 400


# ── Auth ──────────────────────────────────────────────────────────────────

class TestAuth:
    def test_missing_api_key(self, client):
        resp = client.post("/v1/sessions", json={})
        assert resp.status_code == 401

    def test_wrong_api_key(self, client):
        resp = client.post("/v1/sessions", json={}, headers={"Authorization": "Bearer wrong"})
        assert resp.status_code == 401
