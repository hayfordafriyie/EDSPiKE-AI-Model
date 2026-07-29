from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

from src.agents.definitions import AgentDefinition, AGENT_DEFINITIONS


def cmd_agent_create(args: list[str]) -> int:
    print("=== Create Agent ===")
    print()

    try:
        name = input("Agent name [my-agent]: ").strip() or "my-agent"
    except (EOFError, KeyboardInterrupt):
        print()
        return 1

    try:
        description = input("Description: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return 1

    try:
        mode = input("Mode [subagent] (primary/subagent/all): ").strip() or "subagent"
    except (EOFError, KeyboardInterrupt):
        print()
        return 1

    print(f"\nCreating agent '{name}'...")

    prompt = f"You are a {name.replace('-', ' ')} agent. {description}" if description else f"You are a {name.replace('-', ' ')} agent."

    if mode == "primary":
        # Add to JSON config
        config_dir = Path.cwd() / ".edspike"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "edspike.json"

        config = {}
        if config_path.exists():
            import json
            try:
                config = json.loads(config_path.read_text())
            except Exception:
                pass

        if "agent" not in config:
            config["agent"] = {}
        config["agent"][name] = {
            "description": description,
            "mode": mode,
            "prompt": prompt,
        }

        import json
        config_path.write_text(json.dumps(config, indent=2))
        print(f"Added to {config_path}")

    else:
        # Add as Markdown file
        agents_dir = Path.cwd() / ".edspike" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        md_path = agents_dir / f"{name}.md"

        md_content = f"""---
description: {description}
mode: {mode}
permission:
  edit: deny
---

{prompt}
"""
        md_path.write_text(md_content)
        print(f"Created {md_path}")

    print(f"Agent '{name}' created. Available via @{name}.")
    return 0
