import tempfile
from pathlib import Path

import pytest

from src.session.fork import SessionForker


class TestSessionFork:
    def test_fork_creates_entry(self, tmp_path: Path):
        forker = SessionForker(str(tmp_path / "sessions"))
        fork = forker.fork("orig_sess", 0)
        assert fork.fork_id.startswith("fork_")
        assert fork.original_session_id == "orig_sess"

    def test_get_fork(self, tmp_path: Path):
        forker = SessionForker(str(tmp_path / "sessions"))
        fork = forker.fork("s1", 2)
        assert forker.get(fork.fork_id) is not None
        assert forker.get("nonexistent") is None

    def test_list_forks(self, tmp_path: Path):
        forker = SessionForker(str(tmp_path / "sessions"))
        forker.fork("s1", 0)
        forker.fork("s1", 1)
        forker.fork("s2", 0)
        assert len(forker.list("s1")) == 2
        assert len(forker.list()) == 3

    def test_delete_fork(self, tmp_path: Path):
        forker = SessionForker(str(tmp_path / "sessions"))
        fork = forker.fork("s1", 0)
        assert forker.delete(fork.fork_id) is True
        assert forker.get(fork.fork_id) is None
        assert forker.delete("nonexistent") is False

    def test_fork_preserves_wire(self, tmp_path: Path):
        sessions_dir = tmp_path / "sessions"
        (sessions_dir / "orig").mkdir(parents=True)
        (sessions_dir / "orig" / "wire.jsonl").write_text("line1\nline2\nline3\nline4\n")
        forker = SessionForker(str(sessions_dir))
        fork = forker.fork("orig", 1)
        fork_wire = sessions_dir / fork.fork_id / "wire.jsonl"
        assert fork_wire.exists()
        assert fork_wire.read_text().count("\n") < 4
