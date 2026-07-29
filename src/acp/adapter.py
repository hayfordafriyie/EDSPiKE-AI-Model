from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AcpSlashCommand:
    name: str
    description: str
    handler: Any = None


class AcpAdapter:
    def __init__(self, agent_id: str = "edspike"):
        self.agent_id = agent_id
        self._slash_commands: dict[str, AcpSlashCommand] = {}
        self._version = "0.1.0"
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register_slash("help", "Show available slash commands")
        self.register_slash("status", "Show agent status and current goal")
        self.register_slash("mode", "Switch between Build and Plan mode")

    def register_slash(self, name: str, description: str, handler: Any = None) -> None:
        self._slash_commands[name] = AcpSlashCommand(name=name, description=description, handler=handler)

    def handle_stdin(self) -> None:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                response = self._handle_message(msg)
                if response:
                    print(json.dumps(response), flush=True)
            except json.JSONDecodeError:
                print(json.dumps({"error": "Invalid JSON", "type": "error"}), flush=True)

    def _handle_message(self, msg: dict[str, Any]) -> dict[str, Any] | None:
        msg_type = msg.get("type", "")
        if msg_type == "ping":
            return {"type": "pong", "version": self._version, "agent_id": self.agent_id}

        if msg_type == "list_slash_commands":
            return {
                "type": "slash_commands",
                "commands": [
                    {"name": c.name, "description": c.description}
                    for c in self._slash_commands.values()
                ],
            }

        if msg_type == "execute_slash":
            name = msg.get("command", "")
            cmd = self._slash_commands.get(name)
            if cmd and cmd.handler:
                try:
                    result = cmd.handler(msg.get("args", ""))
                    return {"type": "slash_result", "command": name, "result": str(result)}
                except Exception as e:
                    return {"type": "slash_result", "command": name, "error": str(e)}
            return {"type": "slash_result", "command": name, "error": f"Unknown command: {name}"}

        if msg_type == "generate":
            prompt = msg.get("prompt", "")
            return {"type": "generating", "prompt": prompt, "agent_id": self.agent_id}

        return None

    def format_for_editor(self, text: str, style: str = "markdown") -> str:
        if style == "markdown":
            return text
        if style == "plain":
            import re
            return re.sub(r"\*{1,3}|`{1,3}|#{1,6}\s", "", text)
        return text

    def build_status_panel(self, goal: dict[str, Any] | None = None, mode: str = "build") -> str:
        lines = [f"Agent: {self.agent_id}", f"Mode: {mode}"]
        if goal:
            lines.append(f"Goal: {goal.get('objective', 'N/A')} ({goal.get('status', 'N/A')})")
        return "\n".join(lines)
