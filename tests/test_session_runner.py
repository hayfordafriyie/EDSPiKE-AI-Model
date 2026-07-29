from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.session import SessionStore, SessionRunner


@pytest.fixture
def store():
    with tempfile.TemporaryDirectory() as tmp:
        yield SessionStore(str(Path(tmp) / "test.db"))


class TestSessionRunner:
    def test_create_and_run(self, store):
        def fake_gen(prompts, max_tokens, temperature, top_p):
            return ["Task complete: done"], [10]

        runner = SessionRunner(store)
        result = runner.create_and_run(
            task="test task",
            generate_fn=fake_gen,
            agent_id="coding",
            provider="openai",
            metadata={"env": "test"},
        )
        assert result.session_id
        assert result.final_answer == "done"
        assert result.finished is True
        assert result.total_tokens > 0
        assert result.duration_ms > 0

        # session should be persisted
        session = store.get_session(result.session_id)
        assert session is not None
        assert session.status.value == "finished"
        assert len(session.messages) >= 1

    def test_run_existing_session(self, store):
        def fake_gen(prompts, max_tokens, temperature, top_p):
            return ["Task complete: ok"], [5]

        session = store.create_session(agent_id="test")
        runner = SessionRunner(store)
        result = runner.run(session.id, "do something", fake_gen)
        assert result.finished is True
        assert result.final_answer == "ok"

    def test_run_nonexistent_session(self, store):
        runner = SessionRunner(store)
        with pytest.raises(ValueError, match="Session not found"):
            runner.run("bad-id", "task", lambda: None)

    def test_run_with_error(self, store):
        def broken_gen(prompts, max_tokens, temperature, top_p):
            raise RuntimeError("model failure")

        session = store.create_session()
        runner = SessionRunner(store)
        result = runner.run(session.id, "test", broken_gen)
        assert result.finished is False
        assert "model failure" in result.error

        updated = store.get_session(session.id)
        assert updated.status.value == "error"

    def test_replay(self, store):
        def fake_gen(prompts, max_tokens, temperature, top_p):
            return ["Task complete: replay"], [5]

        runner = SessionRunner(store)
        result = runner.create_and_run("replay test", fake_gen)
        steps = runner.replay(result.session_id)
        assert len(steps) > 0
        assert steps[0]["type"].startswith("session.")

    def test_replay_nonexistent(self, store):
        runner = SessionRunner(store)
        with pytest.raises(ValueError, match="Session not found"):
            runner.replay("bad")

    def test_list_runs(self, store):
        def fake_gen(prompts, max_tokens, temperature, top_p):
            return ["done"], [3]

        runner = SessionRunner(store)
        runner.create_and_run("task1", fake_gen, agent_id="a")
        runner.create_and_run("task2", fake_gen, agent_id="b")

        runs = runner.list_runs()
        assert len(runs) >= 2
        assert runs[0]["agent_id"] in ("a", "b")
