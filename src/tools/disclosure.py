from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolGroup:
    name: str
    description: str
    tool_names: list[str] = field(default_factory=list)
    loaded: bool = False


DEFAULT_TOOL_GROUPS: list[ToolGroup] = [
    ToolGroup(name="file_ops", description="File read/write/edit operations", tool_names=["read_file", "write_file", "edit_file", "apply_patch"]),
    ToolGroup(name="search", description="Code search and navigation", tool_names=["grep", "glob", "ls", "diagnostics"]),
    ToolGroup(name="execution", description="Command execution", tool_names=["bash"]),
    ToolGroup(name="web", description="Web access", tool_names=["webfetch", "websearch"]),
    ToolGroup(name="agent", description="Agent and session management", tool_names=["question", "skill", "todowrite"]),
]


class ToolDisclosureManager:
    def __init__(self, groups: list[ToolGroup] | None = None):
        self._groups = {g.name: copy.deepcopy(g) for g in (groups or DEFAULT_TOOL_GROUPS)}
        self._loaded_tools: set[str] = set()

    def load_group(self, group_name: str) -> list[str]:
        group = self._groups.get(group_name)
        if not group:
            return []
        if group.loaded:
            return []
        group.loaded = True
        for tool in group.tool_names:
            self._loaded_tools.add(tool)
        return group.tool_names

    def load_tool(self, tool_name: str) -> bool:
        if tool_name in self._loaded_tools:
            return False
        self._loaded_tools.add(tool_name)
        return True

    def is_loaded(self, tool_name: str) -> bool:
        return tool_name in self._loaded_tools

    def get_loaded_tools(self) -> list[str]:
        return list(self._loaded_tools)

    def get_available_groups(self) -> list[ToolGroup]:
        return [g for g in self._groups.values() if not g.loaded]

    def get_available_tools(self) -> list[str]:
        tools: list[str] = []
        for group in self._groups.values():
            if group.loaded:
                tools.extend(group.tool_names)
        return tools

    def describe_available(self) -> str:
        groups = self.get_available_groups()
        if not groups:
            return "All tool groups are loaded."
        parts: list[str] = ["Available tool groups (use select_tools to load):"]
        for g in groups:
            parts.append(f"  - {g.name}: {g.description} ({', '.join(g.tool_names)})")
        return "\n".join(parts)

    def reset(self) -> None:
        for group in self._groups.values():
            group.loaded = False
        self._loaded_tools.clear()
