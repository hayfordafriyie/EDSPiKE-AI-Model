import pytest

from src.loop import DoomLoopDetector, MaxStepsLimiter


class TestDoomLoop:
    def test_no_loop_empty(self):
        d = DoomLoopDetector()
        assert d.is_looping() is False

    def test_no_loop_few_actions(self):
        d = DoomLoopDetector(window_size=5, threshold=3)
        d.record("read_file", {"path": "/a"})
        d.record("read_file", {"path": "/b"})
        assert d.is_looping() is False

    def test_detect_loop(self):
        d = DoomLoopDetector(window_size=5, threshold=3)
        args = {"path": "/tmp/x"}
        d.record("read_file", args)
        d.record("read_file", args)
        d.record("read_file", args)
        assert d.is_looping() is True

    def test_different_actions_no_loop(self):
        d = DoomLoopDetector(window_size=5, threshold=3)
        d.record("read_file", {"path": "/a"})
        d.record("read_file", {"path": "/b"})
        d.record("read_file", {"path": "/c"})
        assert d.is_looping() is False

    def test_recovery_prompt(self):
        d = DoomLoopDetector()
        prompt = d.get_recovery_prompt()
        assert "repeating" in prompt.lower()

    def test_clear(self):
        d = DoomLoopDetector(window_size=5, threshold=3)
        d.record("bash", {"cmd": "ls"})
        d.record("bash", {"cmd": "ls"})
        d.record("bash", {"cmd": "ls"})
        assert d.is_looping() is True
        d.clear()
        assert d.is_looping() is False

    def test_last_actions(self):
        d = DoomLoopDetector()
        d.record("a", {})
        d.record("b", {})
        d.record("c", {})
        actions = d.last_actions(2)
        assert len(actions) == 2
        assert actions[0].tool == "b"
        assert actions[1].tool == "c"


class TestMaxSteps:
    def test_not_exhausted(self):
        m = MaxStepsLimiter(max_steps=5)
        assert m.is_exhausted() is False

    def test_exhausted(self):
        m = MaxStepsLimiter(max_steps=3)
        m.record_step()
        m.record_step()
        m.record_step()
        assert m.is_exhausted() is True

    def test_remaining(self):
        m = MaxStepsLimiter(max_steps=10)
        m.record_step()
        m.record_step()
        assert m.remaining() == 8

    def test_reset(self):
        m = MaxStepsLimiter(max_steps=2)
        m.record_step()
        m.record_step()
        assert m.is_exhausted() is True
        m.reset()
        assert m.is_exhausted() is False

    def test_limit_prompt(self):
        m = MaxStepsLimiter()
        prompt = m.get_limit_prompt()
        assert "maximum" in prompt.lower()
