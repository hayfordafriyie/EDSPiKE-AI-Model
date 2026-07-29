from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]


BUILTIN_TOOLS: list[ToolSpec] = [
    ToolSpec(
        name="read_file",
        description="Read the contents of a file. Returns lines of text.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to the file",
                },
                "offset": {
                    "type": "integer",
                    "description": "Line number to start from (1-indexed)",
                    "default": 1,
                },
                "limit": {
                    "type": "integer",
                    "description": "Max lines to return (default: all)",
                    "default": None,
                },
            },
            "required": ["path"],
        },
    ),
    ToolSpec(
        name="write_file",
        description="Create or overwrite a file with new content.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute path to the file"},
                "content": {"type": "string", "description": "Full file content"},
            },
            "required": ["path", "content"],
        },
    ),
    ToolSpec(
        name="edit_file",
        description="Replace exact text in a file. Use for targeted edits.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute path to the file"},
                "old_string": {
                    "type": "string",
                    "description": "Exact text to replace (must exist in file)",
                },
                "new_string": {
                    "type": "string",
                    "description": "Replacement text",
                },
            },
            "required": ["path", "old_string", "new_string"],
        },
    ),
    ToolSpec(
        name="grep",
        description="Search file contents with a regex pattern.",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern to search for"},
                "path": {
                    "type": "string",
                    "description": "Directory to search (default: current)",
                    "default": ".",
                },
                "include": {
                    "type": "string",
                    "description": "File glob pattern (e.g. *.py)",
                    "default": None,
                },
            },
            "required": ["pattern"],
        },
    ),
    ToolSpec(
        name="glob",
        description="Find files matching a glob pattern.",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern (e.g. **/*.py)"},
                "path": {
                    "type": "string",
                    "description": "Root directory (default: current)",
                    "default": ".",
                },
            },
            "required": ["pattern"],
        },
    ),
    ToolSpec(
        name="ls",
        description="List files and directories in a path.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path (default: current)",
                    "default": ".",
                },
            },
            "required": [],
        },
    ),
    ToolSpec(
        name="bash",
        description="Run a shell command and return its output.",
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
                "workdir": {
                    "type": "string",
                    "description": "Working directory (default: current)",
                    "default": None,
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in milliseconds",
                    "default": 30000,
                },
            },
            "required": ["command"],
        },
    ),
    ToolSpec(
        name="diagnostics",
        description="Get LSP diagnostics (errors, warnings) for a file. Returns all issues found by the language server.",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Absolute path to the file to check"},
                "language": {"type": "string", "description": "Programming language", "default": ""},
            },
            "required": ["file_path"],
        },
    ),
]


def get_tool_schemas() -> list[dict[str, Any]]:
    return [
        {
            "name": t.name,
            "description": t.description,
            "parameters": t.parameters,
        }
        for t in BUILTIN_TOOLS
    ]
