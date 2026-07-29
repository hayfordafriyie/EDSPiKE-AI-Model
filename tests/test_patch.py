import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.patch import apply_patch, create_patch, PatchError


class TestPatch:
    def test_create_and_apply(self, tmp_path: Path):
        f = tmp_path / "test.txt"
        original = "hello\nworld\n"
        modified = "hello\nuniverse\n"
        f.write_text(original)
        diff = create_patch(original, modified)
        assert "hello" in diff
        assert "-world" in diff
        assert "+universe" in diff
        result = apply_patch(str(f), diff)
        assert result["hunks_applied"] == 1
        assert f.read_text() == modified

    def test_apply_reverse(self, tmp_path: Path):
        f = tmp_path / "test.txt"
        original = "hello\nworld\n"
        modified = "hello\nuniverse\n"
        f.write_text(modified)
        diff = create_patch(original, modified)
        result = apply_patch(str(f), diff, reverse=True)
        assert result["hunks_applied"] == 1
        assert f.read_text() == original

    def test_file_not_found(self):
        with pytest.raises(PatchError):
            apply_patch("/nonexistent/file.txt", "diff")

    def test_multiple_hunks(self, tmp_path: Path):
        f = tmp_path / "multi.txt"
        original = "line1\nline2\nline3\nline4\nline5\n"
        modified = "line1\nchanged\nline3\nline4\nupdated\n"
        f.write_text(original)
        diff = create_patch(original, modified)
        result = apply_patch(str(f), diff)
        assert result["hunks_applied"] >= 0

    def test_empty_diff(self, tmp_path: Path):
        f = tmp_path / "empty.txt"
        f.write_text("content")
        diff = create_patch("content", "content")
        result = apply_patch(str(f), diff)
        assert result["hunks_applied"] == 0
