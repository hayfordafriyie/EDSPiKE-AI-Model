from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from src.agents.definitions import AgentDefinition, AGENT_DEFINITIONS


PROMPT_FILE_RE = re.compile(r"\{file:([^}]+)\}")


def resolve_prompt_ref(text: str, base_dir: str) -> str:
    def _replacer(match: re.Match) -> str:
        path = match.group(1).strip()
        full_path = Path(base_dir) / path
        if full_path.exists():
            return full_path.read_text()
        alt = Path(path)
        if alt.exists():
            return alt.read_text()
        return match.group(0)
    return PROMPT_FILE_RE.sub(_replacer, text)


def load_agents_from_json(config_path: str) -> list[AgentDefinition]:
    path = Path(config_path)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return []

    agents_config = data.get("agent", data.get("agents", {}))
    if not isinstance(agents_config, dict):
        return []

    base_dir = str(path.parent)
    loaded: list[AgentDefinition] = []

    for agent_id, cfg in agents_config.items():
        if not isinstance(cfg, dict):
            continue

        system_prompt = cfg.get("prompt", "")
        if isinstance(system_prompt, str) and "{file:" in system_prompt:
            system_prompt = resolve_prompt_ref(system_prompt, base_dir)

        permissions = cfg.get("permission", cfg.get("tool_permissions", {}))
        if isinstance(permissions, dict):
            resolved_perms: dict[str, Any] = {}
            for key, val in permissions.items():
                if isinstance(val, dict):
                    resolved_perms[key] = val
                else:
                    resolved_perms[key] = val
        else:
            resolved_perms = {}

        agent = AgentDefinition(
            id=agent_id,
            name=cfg.get("name", agent_id),
            system_prompt=system_prompt,
            description=cfg.get("description", ""),
            temperature=float(cfg.get("temperature", 0.5)),
            top_p=float(cfg.get("top_p", 0.9)),
            max_tokens=int(cfg.get("max_tokens", cfg.get("maxTokens", 2048))),
            tools_enabled=True,
            tool_permissions=resolved_perms,
            mode=cfg.get("mode", "all"),
            color=cfg.get("color", ""),
            hidden=cfg.get("hidden", False),
            steps=int(cfg.get("steps", cfg.get("maxSteps", 0))),
            prompt_file=cfg.get("prompt_file", ""),
            task_permissions=cfg.get("task_permission", cfg.get("taskPermissions", {})),
            model=cfg.get("model", ""),
        )
        loaded.append(agent)

    return loaded


def load_agents_from_markdown(agents_dir: str) -> list[AgentDefinition]:
    path = Path(agents_dir)
    if not path.exists():
        return []

    loaded: list[AgentDefinition] = []

    for md_file in sorted(path.glob("*.md")):
        content = md_file.read_text()
        if not content.startswith("---\n"):
            continue
        _, _, rest = content.partition("---\n")
        frontmatter, _, body = rest.partition("---\n")
        if not frontmatter.strip():
            continue
        try:
            import yaml
            meta = yaml.safe_load(frontmatter) or {}
        except Exception:
            meta = {}

        agent_id = md_file.stem
        permissions = meta.get("permission", {})
        if isinstance(permissions, dict):
            resolved_perms: dict[str, Any] = {}
            for key, val in permissions.items():
                if isinstance(val, dict):
                    resolved_perms[key] = val
                else:
                    resolved_perms[key] = val
        else:
            resolved_perms = {}

        agent = AgentDefinition(
            id=agent_id,
            name=meta.get("name", agent_id),
            system_prompt=body.strip() or meta.get("prompt", ""),
            description=meta.get("description", ""),
            temperature=float(meta.get("temperature", 0.5)),
            top_p=float(meta.get("top_p", 0.9)),
            max_tokens=int(meta.get("max_tokens", 2048)),
            tools_enabled=True,
            tool_permissions=resolved_perms,
            mode=meta.get("mode", "subagent"),
            color=meta.get("color", ""),
            hidden=meta.get("hidden", False),
            steps=int(meta.get("steps", 0)),
            prompt_file=meta.get("prompt_file", ""),
            task_permissions=meta.get("task_permission", {}),
            model=meta.get("model", ""),
        )
        loaded.append(agent)

    return loaded


def load_all_agents(project_root: str = "") -> dict[str, AgentDefinition]:
    agents: dict[str, AgentDefinition] = dict(AGENT_DEFINITIONS)

    # Load global agents from ~/.config/edspike/agents/
    global_agents_dir = Path.home() / ".config" / "edspike" / "agents"
    for agent in load_agents_from_markdown(str(global_agents_dir)):
        agents[agent.id] = agent

    # Load project agents from .edspike/agents/
    if project_root:
        project_dir = Path(project_root)
        project_agents_dir = project_dir / ".edspike" / "agents"
        for agent in load_agents_from_markdown(str(project_agents_dir)):
            agents[agent.id] = agent

        # Load from project config file (edspike.json / opencode.json)
        for cfg_name in ("edspike.json", "opencode.json"):
            cfg_path = project_dir / cfg_name
            if cfg_path.exists():
                for agent in load_agents_from_json(str(cfg_path)):
                    agents[agent.id] = agent

    return agents
