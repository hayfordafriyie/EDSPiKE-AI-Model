import json
from pathlib import Path

import pytest

from src.scout import ScoutAgent


class TestScout:
    def test_analyze_local(self, tmp_path: Path):
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "requirements.txt").write_text("flask==2.0\nrequests")
        scout = ScoutAgent()
        result = scout.analyze_local("local://test", str(tmp_path))
        assert result.files_analyzed >= 1
        assert ".py" in result.languages
        assert len(result.dependencies) == 2
        assert result.dependencies[0]["name"] == "flask"

    def test_analyze_with_entry_points(self, tmp_path: Path):
        (tmp_path / "setup.py").write_text("from setuptools import setup")
        scout = ScoutAgent()
        result = scout.analyze_local("local://test2", str(tmp_path))
        assert "setup.py" in result.entry_points

    def test_analyze_package_json(self, tmp_path: Path):
        pkg = {"dependencies": {"express": "^4.0", "react": "^18.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        (tmp_path / "index.js").write_text("console.log('hi')")
        scout = ScoutAgent()
        result = scout.analyze_local("local://pkg", str(tmp_path))
        assert ".js" in result.languages or ".json" in result.languages
        assert len(result.dependencies) == 2

    def test_analyze_empty_dir(self, tmp_path: Path):
        scout = ScoutAgent()
        result = scout.analyze_local("local://empty", str(tmp_path))
        assert result.files_analyzed == 0

    def test_get_and_list(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("a")
        scout = ScoutAgent()
        scout.analyze_local("url1", str(tmp_path))
        assert scout.get("url1") is not None
        assert scout.get("nonexistent") is None
        assert len(scout.list()) == 1
