import pytest

from src.tools.dedup import ToolDeduplicator


class TestToolDedup:
    def test_first_call_not_duplicate(self):
        dd = ToolDeduplicator()
        is_dup, result, reminder = dd.check("bash", {"cmd": "ls"})
        assert is_dup is False
        assert result == ""
        assert reminder is None

    def test_same_step_dedup(self):
        dd = ToolDeduplicator()
        dd.check("bash", {"cmd": "ls"})
        dd.record("bash", {"cmd": "ls"}, "output")
        is_dup, result, reminder = dd.check("bash", {"cmd": "ls"})
        assert is_dup is True
        assert result == "output"

    def test_different_step_not_dup(self):
        dd = ToolDeduplicator()
        dd.new_step()
        dd.check("bash", {"cmd": "ls"})
        dd.record("bash", {"cmd": "ls"}, "output1")
        dd.new_step()
        is_dup, result, reminder = dd.check("bash", {"cmd": "ls"})
        # Different step, not a duplicate of current step
        assert is_dup is False

    def test_repetition_reminder_at_3(self):
        dd = ToolDeduplicator()
        for i in range(2):
            dd.check("bash", {"cmd": "ls"})
        is_dup, result, reminder = dd.check("bash", {"cmd": "ls"})
        assert reminder is not None
        assert "repeating" in reminder

    def test_repetition_reminder_at_5(self):
        dd = ToolDeduplicator()
        for i in range(4):
            dd.check("bash", {"cmd": "ls"})
        is_dup, result, reminder = dd.check("bash", {"cmd": "ls"})
        assert "many times" in (reminder or "")

    def test_force_stop_at_12(self):
        dd = ToolDeduplicator()
        for i in range(11):
            dd.check("bash", {"cmd": "ls"})
        is_dup, result, reminder = dd.check("bash", {"cmd": "ls"})
        assert reminder == "force_stop"

    def test_different_args_not_dup(self):
        dd = ToolDeduplicator()
        dd.new_step()
        dd.check("bash", {"cmd": "ls"})
        dd.record("bash", {"cmd": "ls"}, "out")
        is_dup, _, _ = dd.check("bash", {"cmd": "pwd"})
        assert is_dup is False

    def test_reset(self):
        dd = ToolDeduplicator()
        dd.check("bash", {"cmd": "ls"})
        dd.reset()
        is_dup, _, _ = dd.check("bash", {"cmd": "ls"})
        assert is_dup is False
