from pathlib import Path

import pytest

from src.rules.scoped import ScopedRulesLoader


class TestScopedRules:
    def test_load_tree_root(self, tmp_path: Path):
        (tmp_path / "AGENTS.md").write_text("# Root rules")
        loader = ScopedRulesLoader(str(tmp_path))
        rules = loader.load_tree(str(tmp_path))
        assert "." in rules
        assert "Root" in rules["."]

    def test_load_tree_subdir(self, tmp_path: Path):
        (tmp_path / "AGENTS.md").write_text("# Root")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "AGENTS.md").write_text("# Sub rules")
        loader = ScopedRulesLoader(str(tmp_path))
        rules = loader.load_tree(str(tmp_path), max_depth=2)
        assert "subdir" in rules
        assert "Sub" in rules["subdir"]

    def test_build_combined(self, tmp_path: Path):
        (tmp_path / "AGENTS.md").write_text("# Root")
        loader = ScopedRulesLoader(str(tmp_path))
        ctx = loader.build_combined_context(str(tmp_path))
        assert "Project Rules" in ctx

    def test_empty_dir(self, tmp_path: Path):
        loader = ScopedRulesLoader(str(tmp_path))
        rules = loader.load_tree(str(tmp_path))
        assert rules == {}
