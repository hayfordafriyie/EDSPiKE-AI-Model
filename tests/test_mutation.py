from __future__ import annotations

from pathlib import Path

import pytest

from src.mutation import FileMutationTracker, MutationType


class TestFileMutation:
    def test_detect_creation(self, tmp_path: Path):
        tracker = FileMutationTracker(str(tmp_path))
        tracker.snapshot()
        (tmp_path / "new.txt").write_text("hello")
        changes = tracker.detect_changes()
        assert len(changes) == 1
        assert changes[0].type == MutationType.CREATED
        assert changes[0].path == "new.txt"

    def test_detect_edit(self, tmp_path: Path):
        f = tmp_path / "edit.txt"
        f.write_text("original")
        tracker = FileMutationTracker(str(tmp_path))
        tracker.snapshot()
        f.write_text("modified")
        changes = tracker.detect_changes()
        assert len(changes) == 1
        assert changes[0].type == MutationType.EDITED
        assert "original" in changes[0].old_content
        assert "modified" in changes[0].new_content

    def test_detect_deletion(self, tmp_path: Path):
        f = tmp_path / "del.txt"
        f.write_text("to delete")
        tracker = FileMutationTracker(str(tmp_path))
        tracker.snapshot()
        f.unlink()
        changes = tracker.detect_changes()
        assert len(changes) == 1
        assert changes[0].type == MutationType.DELETED
        assert changes[0].path == "del.txt"

    def test_undo_creation(self, tmp_path: Path):
        (tmp_path / "undo.txt").write_text("undo me")
        tracker = FileMutationTracker(str(tmp_path))
        tracker.snapshot()
        (tmp_path / "new.txt").write_text("created")
        tracker.detect_changes()
        undone = tracker.undo_last()
        assert undone is not None
        assert undone.type == MutationType.CREATED
        assert not (tmp_path / "new.txt").exists()

    def test_undo_edit(self, tmp_path: Path):
        f = tmp_path / "revert.txt"
        f.write_text("original")
        tracker = FileMutationTracker(str(tmp_path))
        tracker.snapshot()
        f.write_text("changed")
        tracker.detect_changes()
        tracker.undo_last()
        assert f.read_text() == "original"

    def test_get_history(self, tmp_path: Path):
        tracker = FileMutationTracker(str(tmp_path))
        tracker.snapshot()
        (tmp_path / "a.txt").write_text("a")
        tracker.detect_changes()
        (tmp_path / "b.txt").write_text("b")
        tracker.detect_changes()
        assert len(tracker.get_history()) == 2

    def test_clear(self, tmp_path: Path):
        tracker = FileMutationTracker(str(tmp_path))
        tracker.snapshot()
        (tmp_path / "x.txt").write_text("x")
        tracker.detect_changes()
        tracker.clear()
        assert tracker.get_history() == []

    def test_diff_generated(self, tmp_path: Path):
        f = tmp_path / "diff.txt"
        f.write_text("old line")
        tracker = FileMutationTracker(str(tmp_path))
        tracker.snapshot()
        f.write_text("new line")
        changes = tracker.detect_changes()
        assert changes[0].diff
        assert "-old line" in changes[0].diff
        assert "+new line" in changes[0].diff

    def test_multiple_changes(self, tmp_path: Path):
        tracker = FileMutationTracker(str(tmp_path))
        tracker.snapshot()
        (tmp_path / "c1.txt").write_text("1")
        (tmp_path / "c2.txt").write_text("2")
        changes = tracker.detect_changes()
        assert len(changes) == 2
