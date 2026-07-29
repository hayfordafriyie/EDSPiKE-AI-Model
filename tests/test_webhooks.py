import pytest

from src.webhooks import WebhookManager


class TestWebhooks:
    def test_register(self):
        mgr = WebhookManager()
        wh = mgr.register("test", "tool_executed")
        assert wh.name == "test"
        assert wh.event == "tool_executed"

    def test_trigger_handler(self):
        mgr = WebhookManager()
        results = []
        mgr.register("test", "tool_executed", handler=lambda p: results.append(p) or {"status": "ok"})
        mgr.trigger("tool_executed", {"tool": "bash"})
        assert len(results) == 1

    def test_trigger_no_match(self):
        mgr = WebhookManager()
        mgr.register("test", "event_a", handler=lambda p: "handled")
        results = mgr.trigger("event_b", {})
        assert len(results) == 0

    def test_list(self):
        mgr = WebhookManager()
        mgr.register("a", "e1")
        mgr.register("b", "e2")
        assert len(mgr.list()) == 2

    def test_delete(self):
        mgr = WebhookManager()
        wh = mgr.register("test", "e")
        assert mgr.delete(wh.id) is True
        assert mgr.delete("nonexistent") is False
