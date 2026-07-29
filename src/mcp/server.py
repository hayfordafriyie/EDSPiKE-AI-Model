from __future__ import annotations

import json
import logging
from typing import Any

from .types import McpResult, McpTool

logger = logging.getLogger(__name__)


class McpServer:
    def __init__(self, name: str = "edspike-mcp", version: str = "0.1.0"):
        self.name = name
        self.version = version
        self._tools: dict[str, McpTool] = {}

    def register_tool(self, tool: McpTool) -> None:
        self._tools[tool.name] = tool
        logger.debug("Registered MCP tool: %s", tool.name)

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": {
                    "type": "object",
                    "properties": t.parameters,
                },
            }
            for t in self._tools.values()
        ]

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> McpResult:
        tool = self._tools.get(name)
        if not tool:
            return McpResult(success=False, error=f"Tool not found: {name}")
        if not tool.handler:
            return McpResult(success=False, error=f"Tool {name} has no handler")
        try:
            result = tool.handler(**(arguments or {}))
            return McpResult(success=True, data=result)
        except Exception as exc:
            logger.error("MCP tool %s failed: %s", name, exc)
            return McpResult(success=False, error=str(exc))

    def handle_jsonrpc(self, raw: str) -> str:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError as exc:
            return json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": str(exc)}, "id": None})

        msg_id = msg.get("id", None)
        method = msg.get("method", "")

        if method == "initialize":
            return json.dumps({
                "jsonrpc": "2.0", "id": msg_id,
                "result": {
                    "protocolVersion": "0.1.0",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": self.name, "version": self.version},
                },
            })
        elif method == "tools/list":
            return json.dumps({
                "jsonrpc": "2.0", "id": msg_id,
                "result": {"tools": self.list_tools()},
            })
        elif method == "tools/call":
            params = msg.get("params", {})
            result = self.call_tool(params.get("name", ""), params.get("arguments", {}))
            if result.success:
                return json.dumps({
                    "jsonrpc": "2.0", "id": msg_id,
                    "result": {"content": [{"type": "text", "text": str(result.data)}]},
                })
            else:
                return json.dumps({
                    "jsonrpc": "2.0", "id": msg_id,
                    "error": {"code": -32000, "message": result.error},
                })
        else:
            return json.dumps({
                "jsonrpc": "2.0", "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            })
