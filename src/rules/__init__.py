from __future__ import annotations

import glob as glob_module
import os
from pathlib import Path
from typing import Any


class RulesLoader:
    def __init__(self, project_root: str = ""):
        self.project_root = Path(project_root or ".").resolve()
        self._instructions: list[str] = []

    def load_all(self) -> str:
        parts: list[str] = []

        project_rules = self._load_project_rules()
        if project_rules:
            parts.append(project_rules)

        global_rules = self._load_global_rules()
        if global_rules:
            parts.append(global_rules)

        return "\n\n".join(parts)

    def load_instructions(self, patterns: list[str]) -> str:
        parts: list[str] = []
        for pattern in patterns:
            if pattern.startswith("http://") or pattern.startswith("https://"):
                try:
                    import urllib.request
                    resp = urllib.request.urlopen(pattern, timeout=5)
                    parts.append(resp.read().decode())
                except Exception as e:
                    parts.append(f"[Failed to load {pattern}: {e}]")
            else:
                matched = list(self.project_root.glob(pattern))
                for mp in sorted(matched):
                    if mp.is_file():
                        parts.append(mp.read_text())
        return "\n\n".join(parts)

    def _load_project_rules(self) -> str:
        candidates = [
            self.project_root / "AGENTS.md",
            self.project_root / "CLAUDE.md",
        ]
        for path in candidates:
            if path.exists():
                return path.read_text()
        return ""

    def _load_global_rules(self) -> str:
        candidates = [
            Path.home() / ".config" / "opencode" / "AGENTS.md",
            Path.home() / ".claude" / "CLAUDE.md",
        ]
        for path in candidates:
            if path.exists():
                return path.read_text()
        return ""
