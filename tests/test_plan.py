import pytest

from src.plan import PlanMode


class TestPlanMode:
    def test_default_inactive(self):
        pm = PlanMode()
        assert pm.active is False

    def test_activate(self):
        pm = PlanMode()
        pm.activate()
        assert pm.active is True

    def test_deactivate(self):
        pm = PlanMode()
        pm.activate()
        pm.deactivate()
        assert pm.active is False

    def test_toggle(self):
        pm = PlanMode()
        assert pm.toggle() is True
        assert pm.toggle() is False

    def test_tool_allowed_in_build(self):
        pm = PlanMode()
        assert pm.check_tool_allowed("bash") is True

    def test_tool_denied_in_plan(self):
        pm = PlanMode()
        pm.activate()
        assert pm.check_tool_allowed("write_file") is False
        assert pm.check_tool_allowed("edit_file") is False
        assert pm.check_tool_allowed("bash") is False
        assert pm.check_tool_allowed("read_file") is True

    def test_reminder(self):
        pm = PlanMode()
        assert pm.get_reminder() == ""
        pm.activate()
        assert "PLAN mode" in pm.get_reminder()

    def test_status(self):
        pm = PlanMode()
        status = pm.get_status()
        assert status["active"] is False
        pm.activate()
        status = pm.get_status()
        assert status["active"] is True
        assert "write_file" in status["denied_tools"]
