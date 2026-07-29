from __future__ import annotations

import os
import logging
import subprocess
from typing import Any

from .pty import PtyProcess, PtyResult

logger = logging.getLogger(__name__)


class ShellExecutor:
    def __init__(self, work_dir: str = "."):
        self._work_dir = work_dir

    def run(
        self,
        command: str,
        timeout: float = 30.0,
        shell: str = "/bin/bash",
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess:
        run_env = os.environ.copy()
        if env:
            run_env.update(env)

        return subprocess.run(
            [shell, "-c", command],
            cwd=self._work_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=run_env,
        )

    def run_interactive(
        self,
        command: str,
        timeout: float = 30.0,
        shell: str = "/bin/bash",
    ) -> PtyResult:
        return PtyProcess.run_command(command, timeout=timeout, shell=shell)

    def get_tool_specs(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "shell_run",
                "description": "Run a shell command and capture output (non-interactive)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Shell command to run"},
                        "timeout": {"type": "number", "description": "Timeout in seconds"},
                    },
                    "required": ["command"],
                },
            },
            {
                "name": "shell_interactive",
                "description": "Run an interactive shell command (preserves PTY, handles prompts)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Shell command to run"},
                        "timeout": {"type": "number", "description": "Timeout in seconds"},
                    },
                    "required": ["command"],
                },
            },
        ]
