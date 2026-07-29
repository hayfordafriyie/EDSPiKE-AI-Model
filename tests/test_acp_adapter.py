import json
import pytest

from src.acp.adapter import AcpAdapter, AcpSlashCommand


class TestAcpAdapter:
    def test_ping_pong(self):
        adapter = AcpAdapter("test-agent")
        resp = adapter._handle_message({"type": "ping"})
        assert resp["type"] == "pong"
        assert resp["agent_id"] == "test-agent"

    def test_list_slash_commands(self):
        adapter = AcpAdapter()
        resp = adapter._handle_message({"type": "list_slash_commands"})
        assert resp["type"] == "slash_commands"
        names = [c["name"] for c in resp["commands"]]
        assert "help" in names
        assert "status" in names

    def test_execute_unknown_slash(self):
        adapter = AcpAdapter()
        resp = adapter._handle_message({"type": "execute_slash", "command": "nonexistent"})
        assert "error" in resp

    def test_register_slash(self):
        adapter = AcpAdapter()
        results = []
        adapter.register_slash("ping", "Ping test", lambda args: results.append(args) or "pong")
        resp = adapter._handle_message({"type": "execute_slash", "command": "ping", "args": "hello"})
        assert resp["result"] == "pong"

    def test_generate_message(self):
        adapter = AcpAdapter()
        resp = adapter._handle_message({"type": "generate", "prompt": "hello"})
        assert resp["type"] == "generating"

    def test_unknown_message(self):
        adapter = AcpAdapter()
        resp = adapter._handle_message({"type": "unknown"})
        assert resp is None

    def test_format_for_editor(self):
        adapter = AcpAdapter()
        md = adapter.format_for_editor("**bold** `code`", style="markdown")
        assert "**bold**" in md
        plain = adapter.format_for_editor("**bold** `code`", style="plain")
        assert "bold" in plain
        assert "**" not in plain

    def test_build_status_panel(self):
        adapter = AcpAdapter()
        panel = adapter.build_status_panel(mode="build")
        assert "Mode: build" in panel
        panel_with_goal = adapter.build_status_panel({"objective": "Fix bug", "status": "active"}, "plan")
        assert "Fix bug" in panel_with_goal
        assert "plan" in panel_with_goal.lower()
