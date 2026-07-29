from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .registry import BUILTIN_TOOLS

logger = logging.getLogger(__name__)


class ToolError(Exception):
    pass


ALLOWED_ROOTS: list[Path] = []
WORKSPACE_ROOT = os.getenv("WORKSPACE_ROOT", "").strip()
if WORKSPACE_ROOT:
    ALLOWED_ROOTS.append(Path(WORKSPACE_ROOT).resolve())


class ToolExecutor:
    def __init__(self, allowed_roots: list[str] | None = None):
        self.allowed_roots = [Path(r).resolve() for r in (allowed_roots or [])]
        if ALLOWED_ROOTS:
            self.allowed_roots.extend(ALLOWED_ROOTS)

    def _resolve(self, path_str: str) -> Path:
        p = Path(path_str).resolve()
        if self.allowed_roots:
            allowed = False
            for root in self.allowed_roots:
                try:
                    p.relative_to(root)
                    allowed = True
                    break
                except ValueError:
                    continue
            if not allowed:
                raise ToolError(
                    f"Access denied: {p} is outside allowed workspace. "
                    f"Allowed roots: {[str(r) for r in self.allowed_roots]}"
                )
        return p

    def _check_path(self, path_str: str) -> Path:
        p = self._resolve(path_str)
        if not p.exists():
            raise ToolError(f"Path does not exist: {p}")
        return p

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> str:
        tool_map = {t.name: t for t in BUILTIN_TOOLS}
        if tool_name not in tool_map:
            raise ToolError(f"Unknown tool: {tool_name}")
        handler = getattr(self, f"_{tool_name}", None)
        if handler is None:
            raise ToolError(f"Tool {tool_name} has no handler")
        try:
            return handler(**arguments)
        except ToolError:
            raise
        except Exception as exc:
            raise ToolError(f"{tool_name} failed: {exc}") from exc

    def _read_file(self, path: str, offset: int = 1, limit: int | None = None) -> str:
        p = self._check_path(path)
        if not p.is_file():
            raise ToolError(f"Not a file: {p}")
        lines = p.read_text().splitlines(keepends=True)
        start = max(0, offset - 1)
        if limit is not None:
            lines = lines[start : start + limit]
        else:
            lines = lines[start:]
        return "".join(lines)

    def _write_file(self, path: str, content: str) -> str:
        p = self._resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"Wrote {len(content)} bytes to {p}"

    def _edit_file(self, path: str, old_string: str, new_string: str) -> str:
        p = self._check_path(path)
        if not p.is_file():
            raise ToolError(f"Not a file: {p}")
        content = p.read_text()
        if old_string not in content:
            raise ToolError(
                f"old_string not found in {p}. "
                f"It appears {content.count(old_string)} time(s). "
                "Use read_file first to see current content."
            )
        if content.count(old_string) > 1:
            raise ToolError(
                f"Found {content.count(old_string)} matches for old_string in {p}. "
                "Provide more surrounding context."
            )
        new_content = content.replace(old_string, new_string, 1)
        p.write_text(new_content)
        return f"Edited {p}: replaced {len(old_string)} -> {len(new_string)} chars"

    def _grep(self, pattern: str, path: str = ".", include: str | None = None) -> str:
        search_path = self._check_path(path)
        matches: list[str] = []
        compiled = re.compile(pattern)
        for fpath in search_path.rglob("*") if not include else search_path.rglob(include):
            if not fpath.is_file():
                continue
            try:
                text = fpath.read_text(errors="replace")
                for i, line in enumerate(text.splitlines(), 1):
                    if compiled.search(line):
                        matches.append(f"{fpath}:{i}: {line}")
            except Exception:
                continue
        if not matches:
            return f"No matches for pattern: {pattern}"
        return "\n".join(matches[:200])

    def _glob(self, pattern: str, path: str = ".") -> str:
        search_path = self._check_path(path)
        results = [str(p.relative_to(search_path)) for p in search_path.glob(pattern)]
        if not results:
            return f"No files matching: {pattern}"
        return "\n".join(sorted(results))

    def _ls(self, path: str = ".") -> str:
        p = self._check_path(path)
        if not p.is_dir():
            raise ToolError(f"Not a directory: {p}")
        entries = []
        for entry in sorted(p.iterdir()):
            suffix = "/" if entry.is_dir() else ""
            entries.append(f"{entry.name}{suffix}")
        return "\n".join(entries) if entries else "(empty directory)"

    def _bash(self, command: str, workdir: str | None = None, timeout: int = 30000) -> str:
        cwd = None
        if workdir:
            cwd = self._check_path(workdir)
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=timeout / 1000,
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"
            if result.returncode != 0:
                output += f"\n[exit code: {result.returncode}]"
            return output.strip() or "(no output)"
        except subprocess.TimeoutExpired:
            return f"[Command timed out after {timeout}ms]"
        except Exception as exc:
            return f"[Command failed: {exc}]"

    def parse_tool_call(self, text: str) -> list[dict[str, Any]] | None:
        calls = []
        pattern = r"<tool_call>\s*(\{.*?\})\s*</tool_call>"
        for match in re.finditer(pattern, text, re.DOTALL):
            try:
                call = json.loads(match.group(1))
                if "name" in call and "arguments" in call:
                    calls.append(call)
            except json.JSONDecodeError:
                continue
        return calls if calls else None
