from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AgentSpec:
    id: str
    name: str = ""
    system_prompt_path: str = ""
    system_prompt: str = ""
    description: str = ""
    model: str = ""
    temperature: float = 0.5
    tools: list[str] = field(default_factory=list)
    permissions: dict[str, str] = field(default_factory=dict)
    extends: str = ""  # parent spec id
    subagents: dict[str, str] = field(default_factory=dict)  # name -> spec path


class AgentSpecLoader:
    def __init__(self, search_paths: list[str] | None = None):
        self._search_paths = [Path(p) for p in (search_paths or [])]
        self._specs: dict[str, AgentSpec] = {}

    def add_search_path(self, path: str) -> None:
        self._search_paths.append(Path(path))

    def load(self, spec_id: str) -> AgentSpec | None:
        if spec_id in self._specs:
            return self._resolve(spec_id)

        for base in self._search_paths:
            spec_path = base / spec_id / "agent.yaml"
            if spec_path.exists():
                return self._load_file(spec_id, spec_path)
        return None

    def _load_file(self, spec_id: str, path: Path) -> AgentSpec:
        import yaml
        data = yaml.safe_load(path.read_text()) or {}
        agent_data = data.get("agent", data)
        parent_path = path.parent / "system.md"

        spec = AgentSpec(
            id=spec_id,
            name=agent_data.get("name", spec_id),
            system_prompt_path=str(agent_data.get("system_prompt_path", "")),
            system_prompt=agent_data.get("system_prompt", parent_path.read_text() if parent_path.exists() else ""),
            description=agent_data.get("description", ""),
            model=agent_data.get("model", ""),
            temperature=float(agent_data.get("temperature", 0.5)),
            tools=agent_data.get("tools", []),
            permissions=agent_data.get("permissions", agent_data.get("permission", {})),
            extends=agent_data.get("extend", ""),
            subagents=agent_data.get("subagents", {}),
        )

        # Resolve extends
        if spec.extends:
            parent = self.load(spec.extends)
            if parent:
                spec.system_prompt = spec.system_prompt or parent.system_prompt
                spec.tools = spec.tools or parent.tools
                spec.permissions = {**parent.permissions, **spec.permissions}

        self._specs[spec_id] = spec
        return spec

    def _resolve(self, spec_id: str) -> AgentSpec:
        spec = self._specs.get(spec_id)
        if spec and spec.extends:
            if spec.extends not in self._specs:
                self.load(spec.extends)
            parent = self._specs.get(spec.extends)
            if parent:
                spec.system_prompt = spec.system_prompt or parent.system_prompt
                spec.tools = spec.tools or parent.tools
        return spec

    def list_specs(self) -> list[str]:
        return list(self._specs.keys())

    def get_spec_dir(self, spec_id: str) -> str:
        for base in self._search_paths:
            p = base / spec_id
            if p.exists():
                return str(p)
        return ""
