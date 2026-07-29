import json
from pathlib import Path

import pytest

from src.project import ProjectScanner


class TestProject:
    def test_scan_name(self, tmp_path: Path):
        scanner = ProjectScanner(str(tmp_path))
        info = scanner.scan()
        assert info.name == tmp_path.name

    def test_detect_python(self, tmp_path: Path):
        (tmp_path / "main.py").write_text("print('hello')")
        scanner = ProjectScanner(str(tmp_path))
        info = scanner.scan()
        assert info.language == "Python"

    def test_detect_build_system(self, tmp_path: Path):
        (tmp_path / "setup.py").write_text("from setuptools import setup")
        scanner = ProjectScanner(str(tmp_path))
        info = scanner.scan()
        assert info.build_system == "setuptools"

    def test_detect_dependencies_requirements(self, tmp_path: Path):
        (tmp_path / "requirements.txt").write_text("flask==2.0\npytest")
        scanner = ProjectScanner(str(tmp_path))
        info = scanner.scan()
        assert "flask==2.0" in info.dependencies

    def test_detect_frameworks(self, tmp_path: Path):
        (tmp_path / "requirements.txt").write_text("fastapi\nflask")
        scanner = ProjectScanner(str(tmp_path))
        info = scanner.scan()
        assert "fastapi" in info.frameworks or "flask" in info.frameworks

    def test_generate_agents_md(self, tmp_path: Path):
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "utils.py").write_text("def util(): pass")
        scanner = ProjectScanner(str(tmp_path))
        md = scanner.generate_agents_md()
        assert tmp_path.name in md
        assert "Python" in md
        assert "Development" in md

    def test_empty_dir(self, tmp_path: Path):
        scanner = ProjectScanner(str(tmp_path))
        info = scanner.scan()
        assert info.language == ""
        assert info.build_system == ""

    def test_detect_package_json(self, tmp_path: Path):
        pkg = {"dependencies": {"express": "^4.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        scanner = ProjectScanner(str(tmp_path))
        info = scanner.scan()
        assert any("express" in d for d in info.dependencies)
