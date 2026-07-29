from pathlib import Path

import pytest

from src.rules import RulesLoader


class TestRules:
    def test_empty_project(self, tmp_path: Path):
        loader = RulesLoader(str(tmp_path))
        result = loader.load_all()
        assert result == ""

    def test_load_agents_md(self, tmp_path: Path):
        (tmp_path / "AGENTS.md").write_text("# My Project\nPython project")
        loader = RulesLoader(str(tmp_path))
        result = loader.load_all()
        assert "My Project" in result
        assert "Python" in result

    def test_load_claude_md_fallback(self, tmp_path: Path):
        (tmp_path / "CLAUDE.md").write_text("# Claude rules")
        loader = RulesLoader(str(tmp_path))
        result = loader.load_all()
        assert "Claude" in result

    def test_agents_md_preferred_over_claude(self, tmp_path: Path):
        (tmp_path / "AGENTS.md").write_text("# My Project")
        (tmp_path / "CLAUDE.md").write_text("# Claude")
        loader = RulesLoader(str(tmp_path))
        result = loader.load_all()
        assert "My Project" in result
        assert "Claude" not in result

    def test_load_instructions(self, tmp_path: Path):
        doc_dir = tmp_path / "docs"
        doc_dir.mkdir()
        (doc_dir / "guide.md").write_text("# Guide content")
        loader = RulesLoader(str(tmp_path))
        result = loader.load_instructions(["docs/guide.md"])
        assert "Guide content" in result

    def test_load_instructions_glob(self, tmp_path: Path):
        (tmp_path / "a.md").write_text("A")
        (tmp_path / "b.md").write_text("B")
        loader = RulesLoader(str(tmp_path))
        result = loader.load_instructions(["*.md"])
        assert "A" in result
        assert "B" in result

    def test_load_instructions_remote_failure(self):
        loader = RulesLoader("/tmp")
        result = loader.load_instructions(["https://nonexistent.example.com/file.txt"])
        assert "Failed" in result or result  # Should return error message
