from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.database import Database, Table, Column, ColumnType, Migration


@pytest.fixture
def db():
    with tempfile.TemporaryDirectory() as tmp:
        yield Database(str(Path(tmp) / "test.db"))


class TestDatabase:
    def test_create_table(self, db):
        table = Table("users", columns=[
            Column("id", ColumnType.INTEGER, primary_key=True),
            Column("name", ColumnType.TEXT, nullable=False),
            Column("email", ColumnType.TEXT, unique=True),
        ])
        db.create_table(table)
        # verify by inserting
        db.insert("users", {"id": 1, "name": "Alice", "email": "alice@test.com"})
        rows = db.select("users")
        assert len(rows) == 1
        assert rows[0]["name"] == "Alice"

    def test_insert_and_get(self, db):
        table = Table("items", columns=[
            Column("id", ColumnType.INTEGER, primary_key=True),
            Column("value", ColumnType.TEXT),
        ])
        db.create_table(table)
        db.insert("items", {"id": 1, "value": "hello"})
        row = db.get("items", 1)
        assert row is not None
        assert row["value"] == "hello"

    def test_get_nonexistent(self, db):
        table = Table("empty", columns=[Column("id", ColumnType.INTEGER, primary_key=True)])
        db.create_table(table)
        assert db.get("empty", 999) is None

    def test_update(self, db):
        table = Table("cfg", columns=[
            Column("key", ColumnType.TEXT, primary_key=True),
            Column("val", ColumnType.TEXT),
        ])
        db.create_table(table)
        db.insert("cfg", {"key": "k1", "val": "v1"})
        db.update("cfg", {"val": "v2"}, {"key": "k1"})
        row = db.get("cfg", "k1", pk_name="key")
        assert row["val"] == "v2"

    def test_delete(self, db):
        table = Table("tmp", columns=[Column("id", ColumnType.INTEGER, primary_key=True)])
        db.create_table(table)
        db.insert("tmp", {"id": 1})
        db.insert("tmp", {"id": 2})
        db.delete("tmp", {"id": 1})
        rows = db.select("tmp")
        assert len(rows) == 1
        assert rows[0]["id"] == 2

    def test_select_with_where(self, db):
        table = Table("fruits", columns=[
            Column("id", ColumnType.INTEGER, primary_key=True),
            Column("name", ColumnType.TEXT),
        ])
        db.create_table(table)
        db.insert("fruits", {"id": 1, "name": "apple"})
        db.insert("fruits", {"id": 2, "name": "banana"})
        db.insert("fruits", {"id": 3, "name": "apple"})
        rows = db.select("fruits", where={"name": "apple"})
        assert len(rows) == 2

    def test_select_order_limit_offset(self, db):
        table = Table("nums", columns=[
            Column("id", ColumnType.INTEGER, primary_key=True),
            Column("val", ColumnType.INTEGER),
        ])
        db.create_table(table)
        for i in range(10):
            db.insert("nums", {"id": i, "val": i})
        rows = db.select("nums", order_by="val DESC", limit=3, offset=2)
        assert len(rows) == 3
        assert rows[0]["val"] == 7  # 9, 8, 7

    def test_json_column(self, db):
        table = Table("data", columns=[
            Column("id", ColumnType.INTEGER, primary_key=True),
            Column("payload", ColumnType.JSON),
        ])
        db.create_table(table)
        db.insert("data", {"id": 1, "payload": {"key": "value", "nested": [1, 2, 3]}})
        row = db.get("data", 1)
        assert row["payload"] == {"key": "value", "nested": [1, 2, 3]}

    def test_migration(self, db):
        m = Migration(1, "create test table", "CREATE TABLE IF NOT EXISTS migrated (id INTEGER PRIMARY KEY, name TEXT);")
        assert db.run_migration(m) is True
        assert db.run_migration(m) is False  # already applied
        applied = db.get_applied_migrations()
        assert len(applied) == 1
        assert applied[0]["version"] == 1

    def test_foreign_key(self, db):
        parent = Table("parent", columns=[
            Column("id", ColumnType.INTEGER, primary_key=True),
        ])
        child = Table("child", columns=[
            Column("id", ColumnType.INTEGER, primary_key=True),
            Column("parent_id", ColumnType.INTEGER, foreign_key="parent(id)"),
        ])
        db.create_table(parent)
        db.create_table(child)
        db.insert("parent", {"id": 1})
        db.insert("child", {"id": 1, "parent_id": 1})
        row = db.get("child", 1)
        assert row["parent_id"] == 1
