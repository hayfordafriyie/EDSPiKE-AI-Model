import tempfile
from pathlib import Path

import pytest

from src.transcript import TranscriptStore


class TestTranscript:
    def test_append(self, tmp_path: Path):
        ts = TranscriptStore(str(tmp_path / "transcript"))
        entry = ts.append("agent1", "user", "hello")
        assert entry.role == "user"
        assert entry.content == "hello"
        assert ts.count() == 1

    def test_get_entries(self, tmp_path: Path):
        ts = TranscriptStore(str(tmp_path / "transcript"))
        ts.append("agent1", "user", "q1")
        ts.append("agent1", "assistant", "a1")
        entries = ts.get_entries(agent_id="agent1")
        assert len(entries) == 2

    def test_get_entries_limit(self, tmp_path: Path):
        ts = TranscriptStore(str(tmp_path / "transcript"))
        for i in range(10):
            ts.append("a1", "user", f"q{i}")
        entries = ts.get_entries(limit=3)
        assert len(entries) == 3

    def test_get_turns(self, tmp_path: Path):
        ts = TranscriptStore(str(tmp_path / "transcript"))
        ts.append("a1", "user", "q1")
        ts.append("a1", "assistant", "a1")
        ts.append("a1", "user", "q2")
        ts.append("a1", "assistant", "a2")
        turns = ts.get_turns()
        assert len(turns) >= 2

    def test_get_agent_ids(self, tmp_path: Path):
        ts = TranscriptStore(str(tmp_path / "transcript"))
        ts.append("agent1", "user", "hi")
        ts.append("agent2", "user", "hi")
        ids = ts.get_agent_ids()
        assert "agent1" in ids
        assert "agent2" in ids

    def test_persistence(self, tmp_path: Path):
        data_dir = str(tmp_path / "transcript")
        ts1 = TranscriptStore(data_dir)
        ts1.append("a1", "user", "hello")
        ts2 = TranscriptStore(data_dir)
        assert ts2.count() == 1

    def test_subscribe(self, tmp_path: Path):
        ts = TranscriptStore(str(tmp_path / "transcript"))
        received = []
        ts.subscribe("test", 1, lambda e, d: received.append(d))
        ts.append("a1", "user", "test")
        assert len(received) == 1

    def test_unsubscribe(self, tmp_path: Path):
        ts = TranscriptStore(str(tmp_path / "transcript"))
        received = []
        ts.subscribe("test", 1, lambda e, d: received.append(d))
        ts.unsubscribe("test")
        ts.append("a1", "user", "test")
        assert len(received) == 0
