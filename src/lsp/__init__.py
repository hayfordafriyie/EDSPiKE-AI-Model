from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class LspPosition:
    line: int
    character: int


@dataclass
class LspRange:
    start: LspPosition
    end: LspPosition


@dataclass
class LspDiagnostic:
    range: LspRange
    severity: int
    message: str
    source: str = ""


@dataclass
class LspCompletionItem:
    label: str
    kind: int = 0
    detail: str = ""
    insert_text: str = ""


@dataclass
class LspLocation:
    uri: str
    range: LspRange


@dataclass
class LspHover:
    contents: str
    range: LspRange | None = None


class LspClient:
    def __init__(self, language: str, server_command: list[str], root_uri: str):
        self.language = language
        self.server_command = server_command
        self.root_uri = root_uri
        self._process: subprocess.Popen | None = None
        self._request_id = 0
        self._capabilities: dict[str, Any] = {}

    def start(self) -> None:
        self._process = subprocess.Popen(
            self.server_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._send("initialize", {
            "processId": None,
            "rootUri": self.root_uri,
            "capabilities": {},
        })
        resp = self._recv()
        self._capabilities = resp.get("result", {}).get("capabilities", {})
        self._send("initialized", {})

    def shutdown(self) -> None:
        if self._process:
            self._send("shutdown", {})
            self._recv()
            self._send("exit", {})
            self._process.wait(timeout=5)
            self._process = None

    def open_document(self, uri: str, language_id: str, version: int, text: str) -> None:
        self._send("textDocument/didOpen", {
            "textDocument": {
                "uri": uri, "languageId": language_id,
                "version": version, "text": text,
            }
        })

    def close_document(self, uri: str) -> None:
        self._send("textDocument/didClose", {
            "textDocument": {"uri": uri}
        })

    def change_document(self, uri: str, version: int, text: str) -> None:
        self._send("textDocument/didChange", {
            "textDocument": {"uri": uri, "version": version},
            "contentChanges": [{"text": text}],
        })

    def get_diagnostics(self, uri: str) -> list[dict[str, Any]]:
        self._send("textDocument/diagnostic", {
            "textDocument": {"uri": uri}
        })
        resp = self._recv()
        result = resp.get("result") or {}
        kind = result.get("kind", "full")
        if kind == "full":
            return result.get("items", [])
        return []

    def goto_definition(self, uri: str, line: int, character: int) -> list[LspLocation]:
        self._send("textDocument/definition", {
            "textDocument": {"uri": uri},
            "position": {"line": line, "character": character},
        })
        resp = self._recv()
        result = resp.get("result") or []
        if isinstance(result, dict):
            result = [result]
        return [LspLocation(
            uri=loc["uri"],
            range=LspRange(
                start=LspPosition(**loc["range"]["start"]),
                end=LspPosition(**loc["range"]["end"]),
            )
        ) for loc in result]

    def find_references(self, uri: str, line: int, character: int) -> list[LspLocation]:
        self._send("textDocument/references", {
            "textDocument": {"uri": uri},
            "position": {"line": line, "character": character},
            "context": {"includeDeclaration": True},
        })
        resp = self._recv()
        result = resp.get("result") or []
        return [LspLocation(
            uri=loc["uri"],
            range=LspRange(
                start=LspPosition(**loc["range"]["start"]),
                end=LspPosition(**loc["range"]["end"]),
            )
        ) for loc in result]

    def hover(self, uri: str, line: int, character: int) -> LspHover | None:
        self._send("textDocument/hover", {
            "textDocument": {"uri": uri},
            "position": {"line": line, "character": character},
        })
        resp = self._recv()
        result = resp.get("result")
        if not result:
            return None
        contents = result.get("contents", "")
        if isinstance(contents, dict):
            contents = contents.get("value", "")
        elif isinstance(contents, list):
            contents = "\n".join(
                c.get("value", str(c)) if isinstance(c, dict) else str(c)
                for c in contents
            )
        range_ = result.get("range")
        if range_:
            range_obj = LspRange(
                start=LspPosition(**range_["start"]),
                end=LspPosition(**range_["end"]),
            )
        else:
            range_obj = None
        return LspHover(contents=str(contents), range=range_obj)

    def complete(self, uri: str, line: int, character: int) -> list[LspCompletionItem]:
        self._send("textDocument/completion", {
            "textDocument": {"uri": uri},
            "position": {"line": line, "character": character},
        })
        resp = self._recv()
        result = resp.get("result") or {}
        items = result if isinstance(result, list) else result.get("items", [])
        return [LspCompletionItem(
            label=item.get("label", ""),
            kind=item.get("kind", 0),
            detail=item.get("detail", ""),
            insert_text=item.get("insertText", ""),
        ) for item in items]

    def _send(self, method: str, params: dict[str, Any]) -> None:
        self._request_id += 1
        msg = json.dumps({
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        })
        header = f"Content-Length: {len(msg.encode())}\r\n\r\n"
        if self._process and self._process.stdin:
            self._process.stdin.write((header + msg).encode())
            self._process.stdin.flush()

    def _recv(self) -> dict[str, Any]:
        if not self._process or not self._process.stdout:
            return {}
        raw = b""
        while True:
            line = self._process.stdout.readline()
            if not line:
                break
            raw += line
            if line.strip() == b"":
                break
        content_length = 0
        for hdr in raw.decode().split("\r\n"):
            if hdr.lower().startswith("content-length:"):
                content_length = int(hdr.split(":")[1].strip())
        body = self._process.stdout.read(content_length) if content_length else b"{}"
        try:
            return json.loads(body.decode())
        except json.JSONDecodeError:
            return {}
