from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.location import LocationManager


class TestLocation:
    def test_register_and_get(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = LocationManager(str(Path(tmp) / "locations"))
            mgr.register("workspace", str(Path(tmp) / "ws"),
                         description="Main workspace", services=["git", "shell"])
            loc = mgr.get("workspace")
            assert loc is not None
            assert loc.name == "workspace"
            assert "git" in loc.services

    def test_get_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = LocationManager(str(Path(tmp) / "locations"))
            assert mgr.get("nonexistent") is None

    def test_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = LocationManager(str(Path(tmp) / "locations"))
            mgr.register("a", "/tmp/a")
            mgr.register("b", "/tmp/b")
            locs = mgr.list()
            assert len(locs) == 2

    def test_remove(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = LocationManager(str(Path(tmp) / "locations"))
            mgr.register("temp", "/tmp/temp")
            assert mgr.remove("temp") is True
            assert mgr.remove("temp") is False

    def test_add_service(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = LocationManager(str(Path(tmp) / "locations"))
            mgr.register("ws", "/tmp/ws")
            assert mgr.add_service("ws", "docker") is True
            assert mgr.add_service("ws", "docker") is True  # idempotent
            loc = mgr.get("ws")
            assert loc.services == ["docker"]

    def test_add_service_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = LocationManager(str(Path(tmp) / "locations"))
            assert mgr.add_service("nope", "x") is False

    def test_resolve_by_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = LocationManager(str(Path(tmp) / "locations"))
            mgr.register("home", str(Path(tmp)))
            assert mgr.resolve("home") == str(Path(tmp).resolve())

    def test_resolve_by_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = LocationManager(str(Path(tmp) / "locations"))
            assert mgr.resolve(str(Path(tmp))) == str(Path(tmp).resolve())
            assert mgr.resolve("/nonexistent_path_xyz") is None

    def test_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "locations"
            mgr1 = LocationManager(str(data_dir))
            mgr1.register("p", "/tmp/p", services=["git"])
            mgr2 = LocationManager(str(data_dir))
            loc = mgr2.get("p")
            assert loc is not None
            assert loc.path == "/tmp/p"
            assert "git" in loc.services
