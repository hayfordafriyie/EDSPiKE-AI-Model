import pytest

from src.btw import BtwEngine, DenyAllToolset


class TestBtw:
    def test_deny_all_toolset(self):
        result = DenyAllToolset.handle("bash", {"cmd": "ls"})
        assert "not available" in result

    def test_ask_with_mock(self):
        engine = BtwEngine()

        def mock_generate(prompt):
            return "42"

        result = engine.ask("What is 2+2?", "System: you are helpful", mock_generate)
        assert result.answer == "42"
        assert "2+2" in result.question

    def test_get_history(self):
        engine = BtwEngine()

        def mock_generate(prompt):
            return "yes"

        engine.ask("test?", "system", mock_generate)
        assert len(engine.get_history()) == 1

    def test_clear(self):
        engine = BtwEngine()

        def mock_generate(prompt):
            return "ok"

        engine.ask("q?", "system", mock_generate)
        engine.clear()
        assert engine.get_history() == []

    def test_retry_on_failure(self):
        calls = [0]

        def failing_generate(prompt):
            calls[0] += 1
            if calls[0] < 2:
                raise RuntimeError("fail")
            return "success"

        engine = BtwEngine(max_retries=2)
        result = engine.ask("q?", "system", failing_generate)
        assert result.answer == "success"
        assert calls[0] == 2
