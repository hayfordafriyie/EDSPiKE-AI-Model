from __future__ import annotations

import json
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class CustomCommand:
    name: str
    prompt_template: str
    description: str = ""
    named_args: list[str] = field(default_factory=list)
    enabled: bool = True


CommandHandlerFn = Callable[[str, dict[str, str]], str]


class CommandRegistry:
    def __init__(self, data_dir: str = ""):
        self._commands: dict[str, CustomCommand] = {}
        self._handlers: dict[str, CommandHandlerFn] = {}
        self._data_dir = data_dir
        if data_dir:
            Path(data_dir).mkdir(parents=True, exist_ok=True)
            self._load()

    def _path(self) -> Path:
        return Path(self._data_dir) / "commands.json"

    def _load(self) -> None:
        path = self._path()
        if path.exists():
            data = json.loads(path.read_text())
            for item in data:
                cmd = CustomCommand(**item)
                self._commands[cmd.name] = cmd

    def _save(self) -> None:
        if not self._data_dir:
            return
        data = [c.__dict__ for c in self._commands.values()]
        self._path().write_text(json.dumps(data, indent=2))

    def register(self, name: str, prompt_template: str, description: str = "", named_args: list[str] | None = None, handler: CommandHandlerFn | None = None) -> CustomCommand:
        cmd = CustomCommand(
            name=name, prompt_template=prompt_template,
            description=description, named_args=named_args or [],
        )
        self._commands[name] = cmd
        if handler:
            self._handlers[name] = handler
        self._save()
        return cmd

    def get(self, name: str) -> CustomCommand | None:
        return self._commands.get(name)

    def execute(self, name: str, args: dict[str, str] | None = None) -> str:
        cmd = self.get(name)
        if not cmd:
            raise KeyError(f"Command not found: {name}")

        resolved_args = args or {}
        template = cmd.prompt_template

        for arg_name in cmd.named_args:
            value = resolved_args.get(arg_name, f"{{{{{arg_name}}}}}")
            template = template.replace(f"{{{{{arg_name}}}}}", value)

        handler = self._handlers.get(name)
        if handler:
            return handler(name, resolved_args)

        return template

    def parse_args(self, text: str) -> tuple[str, dict[str, str]]:
        parts = shlex.split(text)
        if not parts:
            return "", {}
        name = parts[0].lstrip("/")
        args: dict[str, str] = {}
        i = 1
        while i < len(parts):
            if parts[i].startswith("--"):
                key = parts[i].lstrip("-")
                if i + 1 < len(parts) and not parts[i + 1].startswith("--"):
                    args[key] = parts[i + 1]
                    i += 2
                else:
                    args[key] = ""
                    i += 1
            elif "=" in parts[i]:
                key, val = parts[i].split("=", 1)
                args[key] = val
                i += 1
            else:
                args.setdefault("_", parts[i])
                i += 1
        return name, args

    def list(self) -> list[CustomCommand]:
        return list(self._commands.values())

    def remove(self, name: str) -> bool:
        if name in self._commands:
            del self._commands[name]
            self._handlers.pop(name, None)
            self._save()
            return True
        return False
