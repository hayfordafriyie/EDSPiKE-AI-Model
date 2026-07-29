from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class McpTool:
    name: str
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    handler: Any = None


@dataclass
class McpResource:
    uri: str
    name: str
    description: str = ""
    mime_type: str = "text/plain"


@dataclass
class McpResult:
    success: bool = True
    data: Any = None
    error: str = ""
