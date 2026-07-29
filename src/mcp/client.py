from __future__ import annotations

import json
import logging
import subprocess
from typing import Any

from .types import McpResult, McpTool

logger = logging.getLogger(__name__)


class McpClient:
    def __init__(self, command: str | None = None, args: list[str] | None = None):
        self._command = command
        self._args = args or []
        self._process: subprocess.Popen | None = None
        self._tools: list[dict[str, Any]] = []
        self._server_info: dict[str, Any] = {}

    def connect(self) -> None:
        if not self._command:
            raise RuntimeError("No MCP server command configured")
        self._process = subprocess.Popen(
            [self._command] + self._args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        # Send initialize
        self._send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        resp = self._recv()
        if resp and "result" in resp:
            self._server_info = resp["result"].get("serverInfo", {})
        # List tools
        self._send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        resp = self._recv()
        if resp and "result" in resp:
            self._tools = resp["result"].get("tools", [])

    def _send(self, msg: dict[str, Any]) -> None:
        if not self._process or not self._process.stdin:
            raise RuntimeError("Not connected")
        self._process.stdin.write(json.dumps(msg) + "\n")
        self._process.stdin.flush()

    def _recv(self) -> dict[str, Any] | None:
        if not self._process or not self._process.stdout:
            return None
        import select
        import time
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            r, _, _ = select.select([self._process.stdout], [], [], 0.5)
            if r:
                line = self._process.stdout.readline()
                if line:
                    return json.loads(line.strip())
            else:
                break
        return None

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> McpResult:
        self._send({
            "jsonrpc": "2.0", "id": 3,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        })
        resp = self._recv()
        if not resp:
            return McpResult(success=False, error="No response from server")
        if "error" in resp:
            return McpResult(success=False, error=resp["error"].get("message", str(resp["error"])))
        content = resp.get("result", {}).get("content", [])
        texts = [c.get("text", "") for c in content if c.get("type") == "text"]
        return McpResult(success=True, data="\n".join(texts))

    def list_tools(self) -> list[dict[str, Any]]:
        return self._tools

    def close(self) -> None:
        if self._process:
            self._process.terminate()
            self._process.wait(timeout=5)
            self._process = None
