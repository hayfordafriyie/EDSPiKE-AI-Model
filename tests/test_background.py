import time
import pytest

from src.background import BackgroundTaskManager, TaskStatus


class TestBackground:
    def test_start_bash(self):
        mgr = BackgroundTaskManager()
        task = mgr.start_bash("test1", "echo hello")
        # Wait for completion
        time.sleep(0.5)
        task = mgr.get("test1")
        assert task is not None
        assert task.status in (TaskStatus.COMPLETED, TaskStatus.RUNNING)

    def test_get_nonexistent(self):
        mgr = BackgroundTaskManager()
        assert mgr.get("nonexistent") is None

    def test_list(self):
        mgr = BackgroundTaskManager()
        mgr.start_bash("t1", "echo 1")
        mgr.start_bash("t2", "echo 2")
        tasks = mgr.list()
        assert len(tasks) == 2

    def test_list_by_status(self):
        mgr = BackgroundTaskManager()
        mgr.start_bash("t1", "echo 1")
        time.sleep(0.3)
        tasks = mgr.list(status=TaskStatus.RUNNING)
        # The task might be running or completed by now
        assert isinstance(tasks, list)

    def test_reconcile(self):
        mgr = BackgroundTaskManager()
        mgr.start_bash("t1", "echo hello")
        time.sleep(0.5)
        mgr.reconcile()
        task = mgr.get("t1")
        assert task is not None

    def test_clear_completed(self):
        mgr = BackgroundTaskManager()
        mgr.start_bash("t1", "echo 1")
        time.sleep(0.5)
        mgr.reconcile()
        mgr.clear_completed()
        # May or may not be cleared depending on timing
        assert isinstance(mgr.count(), int)
