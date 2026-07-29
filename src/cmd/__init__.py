from __future__ import annotations

from typing import Any

from .cmd_init import cmd_init
from .cmd_connect import cmd_connect
from .cmd_share import cmd_share, cmd_share_list
from .cmd_agent import cmd_agent_create

COMMAND_MAP: dict[str, Any] = {
    "init": cmd_init,
    "connect": cmd_connect,
    "share": cmd_share,
    "share_list": cmd_share_list,
    "agent_create": cmd_agent_create,
}


def run_command(name: str, args: list[str] | None = None) -> int:
    cmd = COMMAND_MAP.get(name)
    if cmd is None:
        print(f"Unknown command: {name}")
        return 1
    return cmd(args or [])
