import pytest

from src.output import ToolOutputStore


class TestToolOutputStore:
    def test_record_and_get(self):
        store = ToolOutputStore()
        out = store.record("sess1", "read_file", {"path": "/tmp/x"}, result="content")
        assert out.tool_name == "read_file"
        assert out.session_id == "sess1"

    def test_get_session_outputs(self):
        store = ToolOutputStore()
        store.record("s1", "tool_a", {})
        store.record("s1", "tool_b", {})
        store.record("s2", "tool_a", {})
        assert len(store.get_session_outputs("s1")) == 2
        assert len(store.get_session_outputs("s2")) == 1

    def test_get_last(self):
        store = ToolOutputStore()
        store.record("s1", "bash", {"cmd": "echo 1"}, result="1")
        store.record("s1", "bash", {"cmd": "echo 2"}, result="2")
        last = store.get_last("s1", "bash")
        assert last is not None
        assert last.result == "2"

    def test_get_last_any_tool(self):
        store = ToolOutputStore()
        store.record("s1", "bash", {"cmd": "echo 1"}, result="1")
        store.record("s1", "read_file", {"path": "x"}, result="x")
        last = store.get_last("s1")
        assert last is not None
        assert last.tool_name == "read_file"

    def test_get_last_nonexistent(self):
        store = ToolOutputStore()
        assert store.get_last("no_session") is None

    def test_get_all(self):
        store = ToolOutputStore()
        for i in range(5):
            store.record("s1", f"tool_{i}", {})
        assert len(store.get_all(limit=3)) == 3
        assert len(store.get_all(limit=100)) == 5

    def test_clear_session(self):
        store = ToolOutputStore()
        store.record("s1", "tool_a", {})
        store.record("s1", "tool_b", {})
        store.clear_session("s1")
        assert store.get_session_outputs("s1") == []
        assert store.count() == 0

    def test_count(self):
        store = ToolOutputStore()
        assert store.count() == 0
        store.record("s1", "t", {})
        assert store.count() == 1
