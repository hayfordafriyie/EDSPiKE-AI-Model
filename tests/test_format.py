from pathlib import Path

import pytest

from src.format import FormatterManager


class TestFormatter:
    def test_disabled(self):
        mgr = FormatterManager(enabled=False)
        result = mgr.format_file("/tmp/test.py")
        assert result == ""

    def test_unknown_extension(self, tmp_path: Path):
        f = tmp_path / "test.xyz"
        f.write_text("hello")
        mgr = FormatterManager(enabled=True)
        result = mgr.format_file(str(f))
        assert result == ""

    def test_python_formatter_detection(self):
        mgr = FormatterManager(enabled=True)
        formatter = mgr._detect_formatter(".py")
        assert formatter is not None
        assert formatter[0] in ("ruff", "black", "autopep8", "yapf")

    def test_prettier_formats(self):
        mgr = FormatterManager(enabled=True)
        formatter = mgr._detect_formatter(".ts")
        assert formatter is not None
        assert "prettier" in formatter

    def test_go_formatter(self):
        mgr = FormatterManager(enabled=True)
        formatter = mgr._detect_formatter(".go")
        assert formatter == ["gofmt"]

    def test_rust_formatter(self):
        mgr = FormatterManager(enabled=True)
        formatter = mgr._detect_formatter(".rs")
        assert formatter == ["rustfmt"]
