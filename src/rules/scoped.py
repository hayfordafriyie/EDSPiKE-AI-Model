from __future__ import annotations

from pathlib import Path
from typing import Any

from src.rules import RulesLoader


class ScopedRulesLoader(RulesLoader):
    def load_tree(self, root_dir: str, max_depth: int = 3) -> dict[str, str]:
        root = Path(root_dir).resolve()
        rules: dict[str, str] = {}

        # Root-level rules
        root_rules = self._load_project_rules()
        if root_rules:
            rules["."] = root_rules

        # Walk directory tree for AGENTS.md files
        for depth in range(1, max_depth + 1):
            for subdir in self._get_dirs_at_depth(root, depth):
                agents_file = subdir / "AGENTS.md"
                claude_file = subdir / "CLAUDE.md"
                if agents_file.exists():
                    rel = str(subdir.relative_to(root))
                    rules[rel] = agents_file.read_text()
                elif claude_file.exists():
                    rel = str(subdir.relative_to(root))
                    rules[rel] = claude_file.read_text()

        return rules

    def build_combined_context(self, root_dir: str, current_dir: str | None = None) -> str:
        rules = self.load_tree(root_dir)
        if not rules:
            return ""

        parts: list[str] = []
        for path, content in sorted(rules.items()):
            if path == ".":
                parts.append(f"# Project Rules\n{content}")
            else:
                label = f"[{path}]" if current_dir and path != current_dir else path
                parts.append(f"# Rules for {label}\n{content}")

        return "\n\n".join(parts)

    def _get_dirs_at_depth(self, root: Path, depth: int) -> list[Path]:
        if depth == 1:
            return [d for d in root.iterdir() if d.is_dir() and not d.name.startswith((".", "__", "node_modules", ".venv"))]
        result: list[Path] = []
        for d in root.rglob("*"):
            if d.is_dir() and len(d.relative_to(root).parts) == depth and not d.name.startswith((".", "__", "node_modules", ".venv")):
                result.append(d)
        return result
