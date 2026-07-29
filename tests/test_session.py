from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.session import SessionStore, SessionStatus


@pytest.fixture
def store():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        yield SessionStore(str(db))


class TestSessionStore:
    def test_create_and_get(self, store):
        session = store.create_session(agent_id="coding", provider="openai", model="gpt-4o", metadata={"env": "test"})
        assert session.id
        assert session.agent_id == "coding"
        assert session.provider == "openai"
        assert session.model == "gpt-4o"
        assert session.status == SessionStatus.ACTIVE
        assert session.messages == []

        got = store.get_session(session.id)
        assert got is not None
        assert got.id == session.id
        assert got.agent_id == "coding"

    def test_get_nonexistent(self, store):
        assert store.get_session("nonexistent") is None

    def test_list_sessions(self, store):
        s1 = store.create_session(agent_id="a")
        s2 = store.create_session(agent_id="b")
        sessions = store.list_sessions()
        assert len(sessions) >= 2
        ids = [s.id for s in sessions]
        assert s1.id in ids
        assert s2.id in ids

    def test_append_message(self, store):
        session = store.create_session()
        updated = store.append_message(session.id, "user", "hello")
        assert updated is not None
        assert len(updated.messages) == 1
        assert updated.messages[0]["role"] == "user"
        assert updated.messages[0]["content"] == "hello"

        updated2 = store.append_message(session.id, "assistant", "world")
        assert len(updated2.messages) == 2

    def test_append_message_nonexistent(self, store):
        assert store.append_message("nope", "user", "x") is None

    def test_update_status(self, store):
        session = store.create_session()
        assert store.update_status(session.id, SessionStatus.FINISHED) is True
        got = store.get_session(session.id)
        assert got.status == SessionStatus.FINISHED

    def test_update_status_nonexistent(self, store):
        assert store.update_status("nope", SessionStatus.ERROR) is False

    def test_delete_session(self, store):
        session = store.create_session()
        store.append_message(session.id, "user", "keep")
        store.update_status(session.id, SessionStatus.FINISHED)
        assert store.delete_session(session.id) is True
        assert store.get_session(session.id) is None
        # events should also be deleted
        assert store.get_events(session.id) == []

    def test_delete_nonexistent(self, store):
        assert store.delete_session("nope") is False

    def test_event_emission(self, store):
        session = store.create_session()
        store.append_message(session.id, "user", "hi")
        store.update_status(session.id, SessionStatus.FINISHED)
        events = store.get_events(session.id)
        assert len(events) >= 3
        types = [e.event_type for e in events]
        assert "session.created" in types
        assert "message.added" in types
        assert "session.status_changed" in types

    def test_event_stream(self, store):
        session = store.create_session()
        store.append_message(session.id, "user", "m1")
        store.append_message(session.id, "assistant", "m2")
        events = store.get_event_stream(session.id)
        assert len(events) == 3  # created + m1 + m2

    def test_event_stream_after_id(self, store):
        session = store.create_session()
        store.append_message(session.id, "user", "m1")
        events_before = store.get_events(session.id)
        # get_events returns DESC; [0] is the newest = last message.added
        after_id = events_before[0].id
        store.append_message(session.id, "assistant", "m2")
        events_after = store.get_event_stream(session.id, after_id=after_id)
        assert len(events_after) == 1
        assert events_after[0].data.get("role") == "assistant"

    def test_list_sessions_pagination(self, store):
        for i in range(10):
            store.create_session(agent_id=str(i))
        page1 = store.list_sessions(limit=3, offset=0)
        assert len(page1) <= 3
        page2 = store.list_sessions(limit=3, offset=3)
        assert len(page2) <= 3
        all_ids = {s.id for s in page1} | {s.id for s in page2}
        assert len(all_ids) == len(page1) + len(page2)
