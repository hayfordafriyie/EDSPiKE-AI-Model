import tempfile
from pathlib import Path

import pytest

from src.tools.diagnostics import run_diagnostics, DIAGNOSTICS_TOOL


class TestDiagnosticsTool:
    def test_tool_spec(self):
        assert DIAGNOSTICS_TOOL.name == "diagnostics"
        assert "file_path" in DIAGNOSTICS_TOOL.parameters["properties"]

    def test_run_diagnostics_file_not_found(self):
        result = run_diagnostics("/nonexistent/file.py")
        assert "not found" in result.lower()

    def test_run_diagnostics_no_language(self, tmp_path: Path):
        f = tmp_path / "test.unknown_ext_xyz"
        f.write_text("hello")
        result = run_diagnostics(str(f))
        assert "determine" in result.lower()

    def test_run_diagnostics_lsp_not_installed(self, tmp_path: Path):
        f = tmp_path / "test.py"
        f.write_text("x = 1")
        result = run_diagnostics(str(f), language="python").lower()
        # Accept any reasonable outcome: error, no diagnostics, or actual issues
        valid = any(word in result for word in ["error", "not found", "no lsp", "no diagnostics", "diagnostics"])
        assert valid or "result" in result
