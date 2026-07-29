from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


class FormatterManager:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def format_file(self, file_path: str) -> str:
        if not self.enabled:
            return ""

        path = Path(file_path)
        ext = path.suffix.lower()

        formatter = self._detect_formatter(ext)
        if not formatter:
            return ""

        try:
            result = subprocess.run(
                formatter,
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                return f"Formatted with {' '.join(formatter)}"
            else:
                return f"Formatter warning: {result.stderr.strip()}"
        except FileNotFoundError:
            return f"Formatter not installed: {formatter[0]}"
        except subprocess.TimeoutExpired:
            return "Formatter timed out"
        except Exception as e:
            return f"Formatter error: {e}"

    def _detect_formatter(self, ext: str) -> list[str] | None:
        formatters = {
            ".py": self._find_python_formatter(),
            ".js": ["npx", "--yes", "prettier", "--write", "--stdin-filepath"],
            ".jsx": ["npx", "--yes", "prettier", "--write", "--stdin-filepath"],
            ".ts": ["npx", "--yes", "prettier", "--write", "--stdin-filepath"],
            ".tsx": ["npx", "--yes", "prettier", "--write", "--stdin-filepath"],
            ".json": ["npx", "--yes", "prettier", "--write", "--stdin-filepath"],
            ".css": ["npx", "--yes", "prettier", "--write", "--stdin-filepath"],
            ".html": ["npx", "--yes", "prettier", "--write", "--stdin-filepath"],
            ".md": ["npx", "--yes", "prettier", "--write", "--stdin-filepath"],
            ".yaml": ["npx", "--yes", "prettier", "--write", "--stdin-filepath"],
            ".yml": ["npx", "--yes", "prettier", "--write", "--stdin-filepath"],
            ".go": ["gofmt"],
            ".rs": ["rustfmt"],
            ".java": ["google-java-format"],
        }
        return formatters.get(ext)

    def _find_python_formatter(self) -> list[str]:
        for candidate in ["ruff", "black", "autopep8", "yapf"]:
            try:
                subprocess.run(
                    [candidate, "--version"],
                    capture_output=True, timeout=5,
                )
                if candidate == "ruff":
                    return [candidate, "format"]
                return [candidate]
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return ["ruff", "format"]
