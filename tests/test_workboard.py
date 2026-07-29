import tempfile
from pathlib import Path

import pytest

from src.workboard import Workboard


class TestWorkboard:
    def test_add(self, tmp_path: Path):
        wb = Workboard(str(tmp_path))
        item = wb.add("Fix bug", "The login form crashes", priority="high")
        assert item.title == "Fix bug"
        assert item.status == "todo"

    def test_move(self, tmp_path: Path):
        wb = Workboard(str(tmp_path))
        item = wb.add("Task")
        assert wb.move(item.id, "in_progress") is True
        assert wb.get(item.id).status == "in_progress"
        assert wb.move("nonexistent", "done") is False

    def test_list(self, tmp_path: Path):
        wb = Workboard(str(tmp_path))
        wb.add("A")
        wb.add("B")
        assert len(wb.list()) == 2

    def test_board_view(self, tmp_path: Path):
        wb = Workboard(str(tmp_path))
        wb.add("Task")
        view = wb.board_view()
        assert "todo" in view
        assert "done" in view

    def test_delete(self, tmp_path: Path):
        wb = Workboard(str(tmp_path))
        item = wb.add("Task")
        assert wb.delete(item.id) is True
        assert wb.delete("nonexistent") is False
