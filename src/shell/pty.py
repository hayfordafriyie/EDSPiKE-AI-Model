from __future__ import annotations

import logging
import os
import pty
import select
import signal
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PtyResult:
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    timed_out: bool = False
    duration_ms: float = 0.0


class PtyProcess:
    def __init__(self, shell: str = "/bin/bash", env: dict[str, str] | None = None):
        self._shell = shell
        self._env = env
        self._child_fd: int | None = None
        self._child_pid: int | None = None
        self._running = False

    def spawn(self, cols: int = 80, rows: int = 24) -> None:
        if self._running:
            raise RuntimeError("PTY already running")

        pid, fd = pty.fork()
        if pid == 0:
            os.environ["TERM"] = "xterm-256color"
            os.environ["COLUMNS"] = str(cols)
            os.environ["LINES"] = str(rows)
            if self._env:
                os.environ.update(self._env)
            os.execve(self._shell, [self._shell, "-i"], os.environ)
        else:
            self._child_pid = pid
            self._child_fd = fd
            self._running = True

    def write(self, data: str) -> int:
        if not self._running or self._child_fd is None:
            raise RuntimeError("PTY not running")
        return os.write(self._child_fd, data.encode())

    def read(self, timeout: float = 1.0, max_bytes: int = 65536) -> str:
        if not self._running or self._child_fd is None:
            raise RuntimeError("PTY not running")

        output = []
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            r, _, _ = select.select([self._child_fd], [], [], max(0, deadline - time.monotonic()))
            if r:
                try:
                    data = os.read(self._child_fd, max_bytes)
                    if not data:
                        break
                    output.append(data.decode(errors="replace"))
                except OSError:
                    break
            else:
                break

        return "".join(output)

    def execute(
        self,
        command: str,
        timeout: float = 30.0,
        strip_prompt: bool = True,
    ) -> PtyResult:
        """Run a single command through the PTY and return output."""
        if not self._running:
            self.spawn()
            time.sleep(0.1)

        start = time.perf_counter()
        self.write(command + "\n")
        time.sleep(0.05)

        output = ""
        deadline = time.monotonic() + timeout
        timed_out = False

        # Read until we see the shell prompt again or timeout
        prompt_markers = ["$ ", "# ", "❯ "]
        while time.monotonic() < deadline:
            chunk = self.read(timeout=0.5)
            if chunk:
                output += chunk
                if strip_prompt and any(line.strip().endswith(m) for line in output.split("\n") for m in prompt_markers):
                    time.sleep(0.1)
                    extra = self.read(timeout=0.2)
                    if extra:
                        output += extra
                    break
                if command.strip() in output and "not found" in output.lower():
                    break
            else:
                break
        else:
            timed_out = True

        duration = (time.perf_counter() - start) * 1000

        cleaned = self._clean_output(output, command, strip_prompt)
        return PtyResult(
            stdout=cleaned,
            exit_code=1 if timed_out else 0,
            timed_out=timed_out,
            duration_ms=round(duration, 1),
        )

    def _clean_output(self, output: str, command: str, strip_prompt: bool) -> str:
        lines = output.split("\n")
        cleaned = []
        for line in lines:
            if strip_prompt and any(line.strip().endswith(m) for m in ["$ ", "# ", "❯ "]):
                continue
            if line.strip() == command.strip():
                continue
            cleaned.append(line)
        result = "\n".join(cleaned).strip()
        return result

    def close(self) -> None:
        if self._child_pid:
            try:
                os.kill(self._child_pid, signal.SIGHUP)
            except ProcessLookupError:
                pass
            os.waitpid(self._child_pid, 0)
        if self._child_fd:
            try:
                os.close(self._child_fd)
            except OSError:
                pass
        self._running = False
        self._child_fd = None
        self._child_pid = None

    def __enter__(self):
        self.spawn()
        return self

    def __exit__(self, *args: Any):
        self.close()

    @property
    def is_running(self) -> bool:
        return self._running

    @staticmethod
    def run_command(command: str, timeout: float = 30.0, shell: str = "/bin/bash") -> PtyResult:
        """Convenience: spawn PTY, run command, close, return result."""
        with PtyProcess(shell=shell) as pty:
            return pty.execute(command, timeout=timeout)
