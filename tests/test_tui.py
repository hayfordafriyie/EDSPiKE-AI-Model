import pytest

from src.tui import _show_help, _handle_command


class MockConsole:
    def __init__(self):
        self.output = []

    def print(self, *args, **kwargs):
        self.output.append(("print", args, kwargs))

    def clear(self):
        self.output.append(("clear",))


class MockModeManager:
    def __init__(self):
        self._mode = "build"
        self._modes = {"build": "Build", "plan": "Plan"}

    def get_current(self):
        from src.modes import Mode
        return Mode(id=self._mode, name=self._modes[self._mode], description="")

    def set_mode(self, mode_id):
        if mode_id not in self._modes:
            raise KeyError(f"Unknown mode: {mode_id}")
        self._mode = mode_id
        return self.get_current()

    def list_modes(self):
        from src.modes import Mode
        return [Mode(id=k, name=v, description="") for k, v in self._modes.items()]


class MockMutationTracker:
    def __init__(self):
        self._history = []

    def undo_last(self):
        if self._history:
            return self._history.pop()
        return None

    def detect_changes(self):
        return []


class TestTUICommands:
    def test_help(self):
        console = MockConsole()
        _show_help(console)
        assert len(console.output) > 0

    def test_mode_switch(self):
        console = MockConsole()
        mgr = MockModeManager()
        _handle_command("/plan", console, mgr, MockMutationTracker(), ".")
        assert mgr._mode == "plan"

        _handle_command("/build", console, mgr, MockMutationTracker(), ".")
        assert mgr._mode == "build"

    def test_mode_show(self):
        console = MockConsole()
        mgr = MockModeManager()
        _handle_command("/mode", console, mgr, MockMutationTracker(), ".")
        prints = [o for o in console.output if o[0] == "print"]
        assert len(prints) > 0

    def test_undo_no_changes(self):
        console = MockConsole()
        tracker = MockMutationTracker()
        _handle_command("/undo", console, MockModeManager(), tracker, ".")
        prints = [o for o in console.output if o[0] == "print"]
        assert any("Nothing" in str(o[1]) for o in prints)

    def test_diff_no_changes(self):
        console = MockConsole()
        _handle_command("/diff", console, MockModeManager(), MockMutationTracker(), ".")
        prints = [o for o in console.output if o[0] == "print"]
        assert any("no" in str(o[1][0]).lower() for o in prints)

    def test_unknown_command(self):
        console = MockConsole()
        _handle_command("/foobar", console, MockModeManager(), MockMutationTracker(), ".")
        prints = [o for o in console.output if o[0] == "print"]
        assert any("unknown" in str(o[1][0]).lower() for o in prints)
