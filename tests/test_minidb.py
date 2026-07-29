import tempfile
from pathlib import Path

import pytest

from src.minidb import MiniDB


class TestMiniDB:
    def test_set_and_get(self, tmp_path: Path):
        db = MiniDB(str(tmp_path / "db"))
        db.set("doc1", {"title": "Hello", "body": "World"})
        doc = db.get("doc1")
        assert doc is not None
        assert doc["title"] == "Hello"

    def test_get_nonexistent(self, tmp_path: Path):
        db = MiniDB(str(tmp_path / "db"))
        assert db.get("nonexistent") is None

    def test_delete(self, tmp_path: Path):
        db = MiniDB(str(tmp_path / "db"))
        db.set("doc1", {"x": 1})
        assert db.delete("doc1") is True
        assert db.delete("doc1") is False

    def test_search(self, tmp_path: Path):
        db = MiniDB(str(tmp_path / "db"))
        db.set("doc1", {"title": "Python programming"})
        db.set("doc2", {"title": "Java programming"})
        db.set("doc3", {"title": "Cooking recipes"})
        results = db.search("python")
        assert len(results) == 1
        assert results[0]["title"] == "Python programming"

    def test_search_multiple_words(self, tmp_path: Path):
        db = MiniDB(str(tmp_path / "db"))
        db.set("doc1", {"title": "Python programming guide"})
        db.set("doc2", {"title": "Python programming tutorial"})
        db.set("doc3", {"title": "Java tutorial"})
        results = db.search("python programming")
        assert len(results) == 2

    def test_list(self, tmp_path: Path):
        db = MiniDB(str(tmp_path / "db"))
        db.set("a", {"n": 1})
        db.set("b", {"n": 2})
        assert len(db.list()) == 2

    def test_count(self, tmp_path: Path):
        db = MiniDB(str(tmp_path / "db"))
        assert db.count() == 0
        db.set("x", {})
        assert db.count() == 1

    def test_persistence(self, tmp_path: Path):
        data_dir = str(tmp_path / "db")
        db1 = MiniDB(data_dir)
        db1.set("persist", {"key": "value"})
        db2 = MiniDB(data_dir)
        assert db2.get("persist")["key"] == "value"

    def test_compact(self, tmp_path: Path):
        db = MiniDB(str(tmp_path / "db"))
        db.set("a", {"x": 1})
        db.set("b", {"y": 2})
        db.compact()
        assert db.count() == 2

    def test_clear(self, tmp_path: Path):
        db = MiniDB(str(tmp_path / "db"))
        db.set("a", {})
        db.clear()
        assert db.count() == 0
