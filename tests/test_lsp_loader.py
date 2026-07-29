from pathlib import Path

import pytest

from src.lsp.loader import auto_detect_lsp


class TestAutoLsp:
    def test_empty_project(self, tmp_path: Path):
        configs = auto_detect_lsp(str(tmp_path))
        assert configs == []

    def test_detect_python(self, tmp_path: Path):
        (tmp_path / "setup.py").write_text("from setuptools import setup")
        configs = auto_detect_lsp(str(tmp_path))
        assert any(c.language == "python" for c in configs)

    def test_detect_typescript(self, tmp_path: Path):
        (tmp_path / "package.json").write_text("{}")
        configs = auto_detect_lsp(str(tmp_path))
        assert any(c.language == "typescript" for c in configs)

    def test_detect_go(self, tmp_path: Path):
        (tmp_path / "go.mod").write_text("module test")
        configs = auto_detect_lsp(str(tmp_path))
        assert any(c.language == "go" for c in configs)

    def test_detect_rust(self, tmp_path: Path):
        (tmp_path / "Cargo.toml").write_text("[package]")
        configs = auto_detect_lsp(str(tmp_path))
        assert any(c.language == "rust" for c in configs)

    def test_detect_ruby(self, tmp_path: Path):
        (tmp_path / "Gemfile").write_text("source 'https://rubygems.org'")
        configs = auto_detect_lsp(str(tmp_path))
        assert any(c.language == "ruby" for c in configs)

    def test_detect_java(self, tmp_path: Path):
        (tmp_path / "pom.xml").write_text("<project></project>")
        configs = auto_detect_lsp(str(tmp_path))
        assert any(c.language == "java" for c in configs)

    def test_multiple_languages(self, tmp_path: Path):
        (tmp_path / "setup.py").write_text("")
        (tmp_path / "package.json").write_text("{}")
        (tmp_path / "go.mod").write_text("")
        configs = auto_detect_lsp(str(tmp_path))
        assert len(configs) >= 3
