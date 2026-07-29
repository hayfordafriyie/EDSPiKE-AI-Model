import tempfile
from pathlib import Path

import pytest

from src.database.store import SQLiteStore


class TestSQLiteStore:
    def test_set_and_get(self, tmp_path: Path):
        db = SQLiteStore(str(tmp_path / "test.db"))
        db.set("key1", "value1")
        assert db.get("key1") == "value1"

    def test_get_nonexistent(self, tmp_path: Path):
        db = SQLiteStore(str(tmp_path / "test.db"))
        assert db.get("nonexistent") is None

    def test_delete(self, tmp_path: Path):
        db = SQLiteStore(str(tmp_path / "test.db"))
        db.set("k", "v")
        assert db.delete("k") is True
        assert db.delete("k") is False

    def test_namespace_isolation(self, tmp_path: Path):
        db = SQLiteStore(str(tmp_path / "test.db"))
        db.set("k", "ns1_val", "ns1")
        db.set("k", "ns2_val", "ns2")
        assert db.get("k", "ns1") == "ns1_val"
        assert db.get("k", "ns2") == "ns2_val"

    def test_json(self, tmp_path: Path):
        db = SQLiteStore(str(tmp_path / "test.db"))
        db.set_json("config", {"key": "val", "num": 42})
        data = db.get_json("config")
        assert data["key"] == "val"
        assert data["num"] == 42

    def test_list_namespace(self, tmp_path: Path):
        db = SQLiteStore(str(tmp_path / "test.db"))
        db.set("a", "1", "ns")
        db.set("b", "2", "ns")
        items = db.list_namespace("ns")
        assert len(items) == 2

    def test_count(self, tmp_path: Path):
        db = SQLiteStore(str(tmp_path / "test.db"))
        assert db.count() == 0
        db.set("k", "v")
        assert db.count() == 1
