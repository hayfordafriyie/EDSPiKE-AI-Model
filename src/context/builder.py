from __future__ import annotations

import json
import os
import platform
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


@dataclass
class SystemContext:
    os_info: str = ""
    python_version: str = ""
    working_directory: str = ""
    environment: str = ""
    current_time: str = ""
    tools_available: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    custom: dict[str, Any] = field(default_factory=dict)

    def to_prompt(self) -> str:
        parts = [
            f"## System Context",
            f"OS: {self.os_info}",
            f"Python: {self.python_version}",
            f"Working directory: {self.working_directory}",
            f"Environment: {self.environment}",
            f"Current time: {self.current_time}",
        ]
        if self.tools_available:
            parts.append(f"Available tools: {', '.join(self.tools_available)}")
        if self.capabilities:
            parts.append(f"Capabilities: {', '.join(self.capabilities)}")
        if self.custom:
            parts.append(f"Additional context:\n{json.dumps(self.custom, indent=2)}")
        return "\n".join(parts)


ContextProvider = Callable[[], dict[str, Any]]


class SystemContextBuilder:
    def __init__(self):
        self._providers: list[tuple[str, ContextProvider]] = []

    def register(self, name: str, provider: ContextProvider) -> None:
        self._providers.append((name, provider))

    def build(self, tool_names: list[str] | None = None, capabilities: list[str] | None = None) -> SystemContext:
        ctx = SystemContext(
            os_info=f"{platform.system()} {platform.release()}",
            python_version=platform.python_version(),
            working_directory=str(Path.cwd()),
            environment=os.getenv("EDSPIKE_ENV", "development"),
            current_time=datetime.now(timezone.utc).isoformat(),
            tools_available=tool_names or [],
            capabilities=capabilities or [],
        )

        for name, provider in self._providers:
            try:
                data = provider()
                if isinstance(data, dict):
                    ctx.custom[name] = data
            except Exception:
                ctx.custom[name] = {"error": f"Provider {name} failed"}

        return ctx
