import tempfile
from pathlib import Path

import pytest

from src.session.state import SessionStateManager, SessionState


class TestSessionState:
    def test_default_state(self, tmp_path: Path):
        mgr = SessionStateManager(str(tmp_path / "sessions" / "s1"))
        assert mgr.state.plan_mode is False
        assert mgr.state.approval.yolo is False

    def test_set_plan_mode(self, tmp_path: Path):
        mgr = SessionStateManager(str(tmp_path / "sessions" / "s1"))
        mgr.set_plan_mode(True, "plan1", "fix-login")
        assert mgr.state.plan_mode is True
        assert mgr.state.plan_session_id == "plan1"

    def test_set_yolo(self, tmp_path: Path):
        mgr = SessionStateManager(str(tmp_path / "sessions" / "s1"))
        mgr.set_yolo(True)
        assert mgr.state.approval.yolo is True

    def test_set_afk(self, tmp_path: Path):
        mgr = SessionStateManager(str(tmp_path / "sessions" / "s1"))
        mgr.set_afk(True)
        assert mgr.state.approval.afk is True

    def test_add_auto_approve(self, tmp_path: Path):
        mgr = SessionStateManager(str(tmp_path / "sessions" / "s1"))
        mgr.add_auto_approve("bash")
        assert "bash" in mgr.state.approval.auto_approve_actions

    def test_todos(self, tmp_path: Path):
        mgr = SessionStateManager(str(tmp_path / "sessions" / "s1"))
        mgr.add_todo("Fix the bug")
        mgr.add_todo("Write tests")
        assert len(mgr.state.todos) == 2
        assert mgr.update_todo(0, "done") is True
        assert mgr.state.todos[0].status == "done"

    def test_persistence(self, tmp_path: Path):
        data_dir = str(tmp_path / "sessions" / "s1")
        mgr1 = SessionStateManager(data_dir)
        mgr1.set_plan_mode(True, "pid", "slug")
        mgr2 = SessionStateManager(data_dir)
        assert mgr2.state.plan_mode is True
        assert mgr2.state.plan_session_id == "pid"

    def test_clear(self, tmp_path: Path):
        mgr = SessionStateManager(str(tmp_path / "sessions" / "s1"))
        mgr.set_yolo(True)
        mgr.clear()
        assert mgr.state.approval.yolo is False
