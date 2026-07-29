from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.tools.registry import BUILTIN_TOOLS, get_tool_schemas
from src.tools.executor import ToolExecutor, ToolError


def test_builtin_tools_have_required_fields():
    for t in BUILTIN_TOOLS:
        assert t.name
        assert t.description
        assert "type" in t.parameters


def test_get_tool_schemas_format():
    schemas = get_tool_schemas()
    assert len(schemas) == len(BUILTIN_TOOLS)
    for s in schemas:
        assert "name" in s
        assert "description" in s
        assert "parameters" in s


def test_parse_tool_call():
    exec_ = ToolExecutor()
    text = 'Some text <tool_call>{"name": "read_file", "arguments": {"path": "/x"}}</tool_call> more'
    calls = exec_.parse_tool_call(text)
    assert calls is not None
    assert len(calls) == 1
    assert calls[0]["name"] == "read_file"


def test_parse_tool_call_no_match():
    exec_ = ToolExecutor()
    calls = exec_.parse_tool_call("Just a normal response")
    assert calls is None


def test_parse_multiple_tool_calls():
    exec_ = ToolExecutor()
    text = (
        '<tool_call>{"name": "read_file", "arguments": {"path": "/a"}}</tool_call>'
        '<tool_call>{"name": "ls", "arguments": {}}</tool_call>'
    )
    calls = exec_.parse_tool_call(text)
    assert calls is not None
    assert len(calls) == 2


def test_write_and_read_file():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        exec_ = ToolExecutor(allowed_roots=[str(root)])
        test_file = root / "hello.txt"

        result = exec_.execute("write_file", {"path": str(test_file), "content": "Hello, World!"})
        assert "Wrote" in result

        result = exec_.execute("read_file", {"path": str(test_file)})
        assert "Hello, World!" in result


def test_edit_file():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        exec_ = ToolExecutor(allowed_roots=[str(root)])
        test_file = root / "edit.txt"
        test_file.write_text("foo bar baz")

        result = exec_.execute("edit_file", {
            "path": str(test_file), "old_string": "bar", "new_string": "qux",
        })
        assert "Edited" in result
        assert test_file.read_text() == "foo qux baz"


def test_edit_file_not_found_error():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        exec_ = ToolExecutor(allowed_roots=[str(root)])
        test_file = root / "edit.txt"
        test_file.write_text("foo bar baz")

        with pytest.raises(ToolError, match="old_string not found"):
            exec_.execute("edit_file", {
                "path": str(test_file), "old_string": "nonexistent", "new_string": "x",
            })


def test_ls():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a.py").touch()
        (root / "b.txt").touch()
        exec_ = ToolExecutor(allowed_roots=[str(root)])
        result = exec_.execute("ls", {"path": str(root)})
        assert "a.py" in result
        assert "b.txt" in result


def test_glob():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "foo.py").touch()
        (root / "bar.py").touch()
        (root / "data.json").touch()
        exec_ = ToolExecutor(allowed_roots=[str(root)])
        result = exec_.execute("glob", {"pattern": "*.py", "path": str(root)})
        assert "foo.py" in result
        assert "bar.py" in result
        assert "data.json" not in result


def test_grep():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "test.py").write_text("def hello():\n    pass\n")
        exec_ = ToolExecutor(allowed_roots=[str(root)])
        result = exec_.execute("grep", {"pattern": "def hello", "path": str(root)})
        assert "test.py" in result


def test_bash():
    exec_ = ToolExecutor()
    result = exec_.execute("bash", {"command": "echo hello"})
    assert "hello" in result


def test_path_access_denied():
    exec_ = ToolExecutor(allowed_roots=["/tmp"])
    with pytest.raises(ToolError, match="Access denied"):
        exec_.execute("read_file", {"path": "/etc/passwd"})
