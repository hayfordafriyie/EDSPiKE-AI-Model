from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.snapshot import SnapshotManager


class TestSnapshot:
    def test_create_and_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            src.mkdir()
            (src / "a.txt").write_text("content a")
            (src / "b.txt").write_text("content b")
            snap_dir = Path(tmp) / "snapshots"
            mgr = SnapshotManager(str(snap_dir))
            snap = mgr.create(str(src), name="test-snap")
            assert snap.file_count == 2
            assert snap.size_bytes > 0
            snaps = mgr.list()
            assert len(snaps) == 1
            assert snaps[0]["name"] == "test-snap"

    def test_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            src.mkdir()
            (src / "data.txt").write_text("important data")
            snap_dir = Path(tmp) / "snapshots"
            mgr = SnapshotManager(str(snap_dir))
            snap = mgr.create(str(src))

            restore_dir = Path(tmp) / "restored"
            mgr.restore(snap.id, str(restore_dir))
            assert (restore_dir / "data.txt").exists()
            assert (restore_dir / "data.txt").read_text() == "important data"

    def test_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            src.mkdir()
            (src / "f.txt").write_text("x")
            mgr = SnapshotManager(str(Path(tmp) / "snapshots"))
            snap = mgr.create(str(src))
            assert mgr.delete(snap.id) is True
            assert mgr.get(snap.id) is None
            assert mgr.delete("nonexistent") is False

    def test_get(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            src.mkdir()
            (src / "f.txt").write_text("x")
            mgr = SnapshotManager(str(Path(tmp) / "snapshots"))
            snap = mgr.create(str(src))
            data = mgr.get(snap.id)
            assert data is not None
            assert data["file_count"] == 1
