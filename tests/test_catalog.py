import tempfile
from pathlib import Path

import pytest

from src.catalog import CatalogSystem


class TestCatalog:
    def test_register_and_get(self):
        with tempfile.TemporaryDirectory() as tmp:
            cat = CatalogSystem(str(Path(tmp) / "catalog"))
            cat.register("file_read", "Read File", "tool", description="Read a file", tags=["fs", "read"])
            entry = cat.get("file_read")
            assert entry is not None
            assert entry.name == "Read File"
            assert entry.type == "tool"
            assert "fs" in entry.tags

    def test_get_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmp:
            cat = CatalogSystem(str(Path(tmp) / "catalog"))
            assert cat.get("nonexistent") is None

    def test_find_by_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            cat = CatalogSystem(str(Path(tmp) / "catalog"))
            cat.register("t1", "Tool 1", "tool")
            cat.register("t2", "Tool 2", "tool")
            cat.register("a1", "Agent 1", "agent")
            assert len(cat.find(type_="tool")) == 2
            assert len(cat.find(type_="agent")) == 1

    def test_find_by_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            cat = CatalogSystem(str(Path(tmp) / "catalog"))
            cat.register("t1", "Tool 1", "tool", tags=["fs"])
            cat.register("t2", "Tool 2", "tool", tags=["net"])
            assert len(cat.find(tag="fs")) == 1
            assert len(cat.find(tag="net")) == 1
            assert len(cat.find(tag="unknown")) == 0

    def test_find_by_query(self):
        with tempfile.TemporaryDirectory() as tmp:
            cat = CatalogSystem(str(Path(tmp) / "catalog"))
            cat.register("fr", "File Reader", "tool", description="Reads files from disk")
            cat.register("nr", "Network Reader", "tool")
            assert len(cat.find(query="file")) == 1
            assert len(cat.find(query="reader")) == 2

    def test_enable_disable(self):
        with tempfile.TemporaryDirectory() as tmp:
            cat = CatalogSystem(str(Path(tmp) / "catalog"))
            cat.register("t1", "Tool 1", "tool")
            assert cat.get("t1").enabled is True
            assert cat.disable("t1") is True
            assert cat.get("t1").enabled is False
            assert cat.enable("t1") is True
            assert cat.get("t1").enabled is True

    def test_remove(self):
        with tempfile.TemporaryDirectory() as tmp:
            cat = CatalogSystem(str(Path(tmp) / "catalog"))
            cat.register("t1", "Tool 1", "tool")
            assert cat.remove("t1") is True
            assert cat.get("t1") is None
            assert cat.remove("nonexistent") is False

    def test_list_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            cat = CatalogSystem(str(Path(tmp) / "catalog"))
            cat.register("t1", "Tool 1", "tool")
            cat.register("a1", "Agent 1", "agent")
            types = cat.list_types()
            assert "tool" in types
            assert "agent" in types

    def test_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = str(Path(tmp) / "catalog")
            c1 = CatalogSystem(data_dir)
            c1.register("k1", "Key 1", "tool")
            c2 = CatalogSystem(data_dir)
            assert c2.count() == 1
            assert c2.get("k1").name == "Key 1"
