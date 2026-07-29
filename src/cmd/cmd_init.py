from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from src.project import ProjectScanner


def cmd_init(args: list[str]) -> int:
    root = args[0] if args else "."
    path = Path(root).resolve()
    if not path.exists():
        print(f"Error: Directory not found: {path}", file=sys.stderr)
        return 1

    print(f"Scanning {path}...")
    scanner = ProjectScanner(str(path))
    md_content = scanner.generate_agents_md()

    agents_path = path / "AGENTS.md"
    if agents_path.exists():
        print(f"Updating existing {agents_path}")
    else:
        print(f"Creating {agents_path}")

    agents_path.write_text(md_content)
    print(f"Done. Generated {len(md_content)} bytes of project context.")
    return 0
