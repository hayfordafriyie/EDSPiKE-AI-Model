from __future__ import annotations

import json

import pytest

from src.mcp import McpServer, McpTool, McpResult


class TestMcpServer:
    def test_register_tool(self):
        server = McpServer()
        server.register_tool(McpTool(name="hello", handler=lambda: "world"))
        tools = server.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "hello"

    def test_call_tool(self):
        server = McpServer()
        server.register_tool(McpTool(name="add", handler=lambda a, b: a + b, parameters={"a": {}, "b": {}}))
        result = server.call_tool("add", {"a": 2, "b": 3})
        assert result.success is True
        assert result.data == 5

    def test_call_nonexistent_tool(self):
        server = McpServer()
        result = server.call_tool("nonexistent")
        assert result.success is False
        assert "not found" in result.error

    def test_initialize(self):
        server = McpServer(name="test-mcp", version="0.1.0")
        resp = server.handle_jsonrpc(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"}))
        data = json.loads(resp)
        assert data["result"]["serverInfo"]["name"] == "test-mcp"

    def test_tools_list(self):
        server = McpServer()
        server.register_tool(McpTool(name="ping", handler=lambda: "pong"))
        resp = server.handle_jsonrpc(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}))
        data = json.loads(resp)
        assert len(data["result"]["tools"]) == 1
        assert data["result"]["tools"][0]["name"] == "ping"

    def test_tools_call(self):
        server = McpServer()
        server.register_tool(McpTool(name="echo", handler=lambda text: text))
        resp = server.handle_jsonrpc(json.dumps({
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "echo", "arguments": {"text": "hello"}},
        }))
        data = json.loads(resp)
        assert data["result"]["content"][0]["text"] == "hello"

    def test_tools_call_error(self):
        server = McpServer()
        server.register_tool(McpTool(name="fail", handler=lambda: (_ for _ in ()).throw(RuntimeError("boom"))))
        resp = server.handle_jsonrpc(json.dumps({
            "jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": "fail", "arguments": {}},
        }))
        data = json.loads(resp)
        assert "error" in data

    def test_method_not_found(self):
        server = McpServer()
        resp = server.handle_jsonrpc(json.dumps({"jsonrpc": "2.0", "id": 5, "method": "unknown"}))
        data = json.loads(resp)
        assert data["error"]["code"] == -32601

    def test_invalid_json(self):
        server = McpServer()
        resp = server.handle_jsonrpc("not json")
        data = json.loads(resp)
        assert data["error"]["code"] == -32700
