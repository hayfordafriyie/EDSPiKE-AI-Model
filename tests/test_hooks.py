import pytest

from src.hooks import LifecycleHookManager, LifecycleHook


class TestHooks:
    def test_register_and_run(self):
        mgr = LifecycleHookManager()
        results = []

        def my_handler(ctx):
            results.append(ctx["tool"])
            return "handled"

        mgr.register_handler("test", "before_tool", my_handler)
        mgr.run("before_tool", {"tool": "bash"})
        assert results == ["bash"]

    def test_event_filtering(self):
        mgr = LifecycleHookManager()
        calls = []

        mgr.register_handler("h1", "before_tool", lambda ctx: calls.append("tool"))
        mgr.register_handler("h2", "after_turn", lambda ctx: calls.append("turn"))

        mgr.run("before_tool", {})
        assert calls == ["tool"]

    def test_disabled_hook(self):
        mgr = LifecycleHookManager()
        calls = []

        mgr.register_handler("test", "before_tool", lambda ctx: calls.append("x"))
        mgr.disable("test")
        mgr.run("before_tool", {})
        assert calls == []

    def test_enable_disable(self):
        mgr = LifecycleHookManager()
        mgr.register_handler("test", "before_tool", lambda ctx: "ok")
        assert mgr.disable("test") is True
        assert mgr.disable("nonexistent") is False
        assert mgr.enable("test") is True
        assert mgr.enable("nonexistent") is False

    def test_list(self):
        mgr = LifecycleHookManager()
        mgr.register_handler("a", "before_tool", lambda ctx: None)
        mgr.register_handler("b", "after_tool", lambda ctx: None)
        hooks = mgr.list()
        assert len(hooks) == 2

    def test_clear(self):
        mgr = LifecycleHookManager()
        mgr.register_handler("test", "before_tool", lambda ctx: None)
        mgr.clear()
        assert mgr.list() == []

    def test_command_hook(self):
        mgr = LifecycleHookManager()
        mgr.register(LifecycleHook(name="echo", event="before_turn", command="echo hello"))
        results = mgr.run("before_turn", {})
        assert len(results) == 1
        assert "hello" in results[0]
