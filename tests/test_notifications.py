import time
from pathlib import Path

import pytest

from src.notifications import NotificationManager, NotificationStore, NotificationEvent


class TestNotifications:
    def test_notify(self):
        mgr = NotificationManager()
        view = mgr.notify("task", "complete", "bg", "task1", "Done", "Task completed", "success")
        assert view.event.title == "Done"
        assert view.status == "pending"

    def test_store_claim(self):
        store = NotificationStore()
        store.add(NotificationEvent(id="n1", category="task", type="done", source_kind="bg", source_id="t1", title="Done", body="ok", targets=["llm", "shell"]))
        claimed = store.claim("llm")
        assert len(claimed) == 1
        assert store.get_pending("llm") == []

    def test_ack(self):
        store = NotificationStore()
        store.add(NotificationEvent(id="n1", category="task", type="done", source_kind="bg", source_id="t1", title="Done", body="ok"))
        store.claim("llm")
        assert store.ack("n1") is True
        assert store.ack("nonexistent") is False

    def test_get_pending_filter(self):
        store = NotificationStore()
        store.add(NotificationEvent(id="n1", category="task", type="a", source_kind="bg", source_id="t1", title="A", body="", targets=["llm"]))
        store.add(NotificationEvent(id="n2", category="task", type="b", source_kind="bg", source_id="t2", title="B", body="", targets=["shell"]))
        assert len(store.get_pending("llm")) == 1
        assert len(store.get_pending("shell")) == 1

    def test_build_llm_message(self, tmp_path: Path):
        store = NotificationStore(str(tmp_path))
        mgr = NotificationManager(store)
        mgr.notify_task("t1", "Background task done", "Task completed as expected")
        msg = mgr.build_llm_message()
        assert "Background task done" in msg

    def test_notify_task(self):
        mgr = NotificationManager()
        v = mgr.notify_task("bg1", "Task done", "Completed")
        assert v.event.category == "task"

    def test_notify_system(self):
        mgr = NotificationManager()
        v = mgr.notify_system("System ready", "All systems operational")
        assert v.event.category == "system"
