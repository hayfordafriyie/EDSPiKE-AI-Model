import pytest

from src.tui import run_tui, _fallback_repl, _show_help, _process_prompt


class MockConsole:
    def __init__(self):
        self.output = []

    def print(self, *args, **kwargs):
        self.output.append(("print", args, kwargs))

    def clear(self):
        self.output.append(("clear",))

    def status(self, *args, **kwargs):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_, **__):
        pass


class TestTUI:
    def test_show_help(self):
        console = MockConsole()
        _show_help(console)
        assert len(console.output) > 0

    def test_process_prompt_no_provider(self):
        console = MockConsole()
        _process_prompt("hello", console, ".")
        assert len(console.output) > 0

    def test_fallback_repl_exit(self, capsys):
        pass  # interactive only, skip
