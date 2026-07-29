import tempfile
from pathlib import Path

import pytest

from src.review import DiffReviewer


class TestDiffReviewer:
    def test_auto_approve(self):
        reviewer = DiffReviewer(auto_approve=True)
        assert reviewer.review_write("/tmp/test.txt", "new content") is True

    def test_review_write_new_file(self, tmp_path: Path):
        f = tmp_path / "new.txt"
        reviewer = DiffReviewer(auto_approve=True)
        assert reviewer.review_write(str(f), "hello") is True

    def test_review_write_existing_file(self, tmp_path: Path):
        f = tmp_path / "existing.txt"
        f.write_text("old content")
        reviewer = DiffReviewer(auto_approve=True)
        assert reviewer.review_write(str(f), "new content") is True

    def test_review_edit_no_change(self, tmp_path: Path):
        f = tmp_path / "edit.txt"
        f.write_text("hello world")
        reviewer = DiffReviewer(auto_approve=True)
        # old_string not found -> no change, so auto-approve
        assert reviewer.review_edit(str(f), "nonexistent", "new") is True

    def test_review_patch(self, tmp_path: Path):
        f = tmp_path / "patch.txt"
        f.write_text("original")
        reviewer = DiffReviewer(auto_approve=True)
        assert reviewer.review_patch(str(f), "diff content") is True

    def test_review_with_auto_approve_skip_input(self):
        reviewer = DiffReviewer(auto_approve=True)
        # Should not block on input
        assert reviewer._ask_approval("test?") is True
