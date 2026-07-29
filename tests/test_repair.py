import pytest

from src.repair import repair_tool_call, extract_tool_call, validate_tool_call


class TestRepair:
    def test_valid_call(self):
        result, repairs = repair_tool_call('{"name": "bash", "arguments": {"cmd": "ls"}}')
        assert result is not None
        assert result["name"] == "bash"
        assert repairs == []

    def test_missing_braces(self):
        text = '{"name": "bash", "arguments": {"cmd": "ls"}'
        result, repairs = repair_tool_call(text)
        assert result is not None
        assert any("braces" in r for r in repairs)

    def test_trailing_comma(self):
        text = '{"name": "bash", "arguments": {"cmd": "ls",}}'
        result, repairs = repair_tool_call(text)
        assert result is not None

    def test_empty(self):
        result, repairs = repair_tool_call("")
        assert result is None

    def test_extract_from_tags(self):
        text = 'some text <tool_call>{"name": "bash", "arguments": {"cmd": "ls"}}</tool_call> more text'
        result = extract_tool_call(text)
        assert result is not None
        assert result["name"] == "bash"

    def test_validate_valid(self):
        valid, errors = validate_tool_call({"name": "bash", "arguments": {"cmd": "ls"}})
        assert valid is True

    def test_validate_missing_name(self):
        valid, errors = validate_tool_call({"arguments": {}})
        assert valid is False
        assert any("name" in e for e in errors)

    def test_validate_missing_arguments(self):
        valid, errors = validate_tool_call({"name": "bash"})
        assert valid is False
        assert any("arguments" in e for e in errors)
