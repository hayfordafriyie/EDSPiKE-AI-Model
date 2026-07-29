from __future__ import annotations

from pathlib import Path

import pytest

from src.vfs import VirtualFileSystem, FsWatcher


class TestVirtualFileSystem:
    def test_read_write(self, tmp_path: Path):
        vfs = VirtualFileSystem(allowed_roots=[str(tmp_path)])
        vfs.write(str(tmp_path / "test.txt"), "hello world")
        assert vfs.read(str(tmp_path / "test.txt")) == "hello world"

    def test_read_outside_root(self, tmp_path: Path):
        vfs = VirtualFileSystem(allowed_roots=[str(tmp_path)])
        with pytest.raises(PermissionError):
            vfs.read("/etc/passwd")

    def test_read_nonexistent(self, tmp_path: Path):
        vfs = VirtualFileSystem(allowed_roots=[str(tmp_path)])
        with pytest.raises(FileNotFoundError):
            vfs.read(str(tmp_path / "nonexistent.txt"))

    def test_edit(self, tmp_path: Path):
        vfs = VirtualFileSystem(allowed_roots=[str(tmp_path)])
        f = tmp_path / "edit.txt"
        f.write_text("old content")
        vfs.edit(str(f), "old", "new")
        assert f.read_text() == "new content"

    def test_edit_not_found(self, tmp_path: Path):
        vfs = VirtualFileSystem(allowed_roots=[str(tmp_path)])
        f = tmp_path / "edit.txt"
        f.write_text("content")
        with pytest.raises(ValueError):
            vfs.edit(str(f), "nonexistent", "replacement")

    def test_list(self, tmp_path: Path):
        vfs = VirtualFileSystem(allowed_roots=[str(tmp_path)])
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.txt").write_text("b")
        (tmp_path / "sub").mkdir()
        entries = vfs.list(str(tmp_path))
        names = [e.path.split("/")[-1] for e in entries]
        assert "a.txt" in names
        assert "b.txt" in names
        assert "sub" in names

    def test_glob(self, tmp_path: Path):
        vfs = VirtualFileSystem(allowed_roots=[str(tmp_path)])
        (tmp_path / "data.csv").write_text("a")
        (tmp_path / "data.json").write_text("b")
        csvs = vfs.glob("*.csv", str(tmp_path))
        assert len(csvs) == 1
        assert csvs[0] == "data.csv"

    def test_grep(self, tmp_path: Path):
        vfs = VirtualFileSystem(allowed_roots=[str(tmp_path)])
        f = tmp_path / "search.txt"
        f.write_text("apple\nbanana\napple pie")
        matches = vfs.grep("apple", str(tmp_path))
        assert len(matches) == 2
        assert all(m["file"] == "search.txt" for m in matches)

    def test_hash(self, tmp_path: Path):
        vfs = VirtualFileSystem(allowed_roots=[str(tmp_path)])
        f = tmp_path / "h.txt"
        f.write_text("content")
        h = vfs.hash(str(f))
        assert len(h) == 64
        assert vfs.hash(str(tmp_path / "nonexistent")) == ""

    def test_exists(self, tmp_path: Path):
        vfs = VirtualFileSystem(allowed_roots=[str(tmp_path)])
        f = tmp_path / "e.txt"
        assert vfs.exists(str(f)) is False
        f.write_text("x")
        assert vfs.exists(str(f)) is True

    def test_tool_specs(self, tmp_path: Path):
        vfs = VirtualFileSystem(allowed_roots=[str(tmp_path)])
        specs = vfs.get_tool_specs()
        names = [s["name"] for s in specs]
        assert "vfs_read" in names
        assert "vfs_write" in names
        assert "vfs_edit" in names
        assert "vfs_list" in names
        assert "vfs_glob" in names
        assert "vfs_grep" in names


class TestFsWatcher:
    def test_snapshot(self, tmp_path: Path):
        watcher = FsWatcher()
        (tmp_path / "a.txt").write_text("a")
        snap = watcher.snapshot(str(tmp_path))
        assert "a.txt" in snap

    def test_poll_detects_creation(self, tmp_path: Path):
        watcher = FsWatcher()
        changes = watcher.poll(str(tmp_path))
        assert changes == []  # first poll stores baseline

        (tmp_path / "new.txt").write_text("new")
        changes = watcher.poll(str(tmp_path))
        assert ("new.txt", "created") in changes

    def test_poll_detects_modification(self, tmp_path: Path):
        f = tmp_path / "mod.txt"
        f.write_text("v1")
        watcher = FsWatcher()
        watcher.poll(str(tmp_path))  # baseline
        f.write_text("v2")
        changes = watcher.poll(str(tmp_path))
        assert ("mod.txt", "modified") in changes

    def test_poll_detects_deletion(self, tmp_path: Path):
        f = tmp_path / "del.txt"
        f.write_text("x")
        watcher = FsWatcher()
        watcher.poll(str(tmp_path))
        f.unlink()
        changes = watcher.poll(str(tmp_path))
        assert ("del.txt", "deleted") in changes

    def test_callback_invoked(self, tmp_path: Path):
        watcher = FsWatcher()
        recorded = []
        watcher.on_change(lambda p, c: recorded.append((p, c)))
        watcher.poll(str(tmp_path))
        (tmp_path / "cb.txt").write_text("cb")
        watcher.poll(str(tmp_path))
        assert len(recorded) >= 1
