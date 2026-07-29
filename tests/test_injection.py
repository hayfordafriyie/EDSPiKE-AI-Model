import pytest

from src.injection import InjectionManager


class TestInjection:
    def test_no_providers(self):
        mgr = InjectionManager()
        assert mgr.get_injections() == []

    def test_simple_provider(self):
        mgr = InjectionManager()
        mgr.register("reminder", lambda: "Remember to check tests")
        results = mgr.get_injections()
        assert "Remember to check tests" in results

    def test_throttle(self):
        mgr = InjectionManager()
        calls = []
        mgr.register("counter", lambda: f"step {len(calls)}", throttle=2)
        r1 = mgr.get_injections()  # step 1, throttle 2 -> skip
        r2 = mgr.get_injections()  # step 2 -> inject
        r3 = mgr.get_injections()  # step 3 -> skip
        r4 = mgr.get_injections()  # step 4 -> inject
        assert len(r2) == 1
        assert len(r4) == 1

    def test_multiple_providers(self):
        mgr = InjectionManager()
        mgr.register("a", lambda: "A")
        mgr.register("b", lambda: "B")
        results = mgr.get_injections()
        assert len(results) == 2

    def test_provider_returns_none(self):
        mgr = InjectionManager()
        mgr.register("null", lambda: None)
        results = mgr.get_injections()
        assert results == []

    def test_clear(self):
        mgr = InjectionManager()
        mgr.register("test", lambda: "hello")
        mgr.clear()
        assert mgr.get_injections() == []
