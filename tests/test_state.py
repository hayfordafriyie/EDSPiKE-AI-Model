from __future__ import annotations

import pytest

from src.state import StateReconciler


class TestStateReconciler:
    def test_diff_added(self):
        r = StateReconciler()
        diff = r.diff({"a": 1}, {"a": 1, "b": 2})
        assert diff.added == ["b"]
        assert diff.removed == []
        assert diff.modified == []

    def test_diff_removed(self):
        r = StateReconciler()
        diff = r.diff({"a": 1, "b": 2}, {"a": 1})
        assert diff.removed == ["b"]

    def test_diff_modified(self):
        r = StateReconciler()
        diff = r.diff({"a": 1}, {"a": 2})
        assert len(diff.modified) == 1
        assert diff.modified[0] == ("a", 1, 2)

    def test_diff_unchanged(self):
        r = StateReconciler()
        diff = r.diff({"a": 1, "b": 2}, {"a": 1, "b": 2})
        assert diff.unchanged == 2
        assert diff.added == []
        assert diff.removed == []
        assert diff.modified == []

    def test_reconcile(self):
        r = StateReconciler()
        result = r.reconcile({"a": 1, "b": 2}, {"a": 10, "c": 3})
        assert result == {"a": 10, "c": 3}

    def test_merge(self):
        r = StateReconciler()
        result = r.merge({"a": 1}, {"b": 2}, {"c": 3})
        assert result == {"a": 1, "b": 2, "c": 3}
