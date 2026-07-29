import pytest

from src.lobster import LobsterEngine


class TestLobster:
    def test_parse_pipeline(self):
        eng = LobsterEngine()
        steps = eng.parse_pipeline("tool1 | tool2 | tool3")
        assert steps == ["tool1", "tool2", "tool3"]

    def test_run_simple(self):
        eng = LobsterEngine()
        eng.register("upper", lambda inp: {"result": inp.get("text", "").upper()})
        result = eng.run("upper", {"text": "hello"})
        assert result.final_output["result"] == "HELLO"

    def test_run_multi_step(self):
        eng = LobsterEngine()
        eng.register("add", lambda inp: {"value": inp.get("value", 0) + 1})
        eng.register("double", lambda inp: {"value": inp.get("value", 0) * 2})
        result = eng.run("add | double", {"value": 5})
        assert result.final_output["value"] == 12

    def test_unknown_step(self):
        eng = LobsterEngine()
        result = eng.run("nonexistent", {})
        assert len(result.steps) == 1
        assert "Unknown" in result.steps[0]["error"]

    def test_step_error(self):
        eng = LobsterEngine()
        eng.register("fail", lambda inp: 1 / 0)
        result = eng.run("fail", {})
        assert "division" in str(result.steps[0]["error"])
