import pytest

from src.providers.testing import EchoProvider, ScriptedEchoProvider, ChaosProvider


class FakeProvider:
    provider_name = "fake"
    def generate(self, prompt, **kwargs):
        return f"Response to: {prompt[:50]}"


class TestEchoProvider:
    def test_echo(self):
        p = EchoProvider()
        result = p.generate("hello")
        assert "Echo:" in result
        assert "hello" in result

    def test_echo_batch(self):
        p = EchoProvider()
        results, tokens = p.generate_batch(["a", "b"])
        assert len(results) == 2
        assert len(tokens) == 2


class TestScriptedEchoProvider:
    def test_matched_response(self):
        p = ScriptedEchoProvider()
        result = p.generate("hello world")
        assert "Hi there" in result

    def test_default_response(self):
        p = ScriptedEchoProvider()
        result = p.generate("something unknown")
        assert "Default" in result or "No matching" in result

    def test_custom_response(self):
        p = ScriptedEchoProvider()
        p.set_response("custom", "Custom response!")
        result = p.generate("this is custom")
        assert "Custom response" in result


class TestChaosProvider:
    def test_no_error_sometimes(self):
        p = ChaosProvider(FakeProvider(), error_rate=0.0)
        result = p.generate("hello")
        assert "Response to" in result

    def test_always_error(self):
        p = ChaosProvider(FakeProvider(), error_rate=1.0)
        with pytest.raises((ConnectionError, TimeoutError, RuntimeError)):
            p.generate("hello")
