from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool = False
    duration_ms: float = 0.0


class Sandbox:
    def __init__(self, work_dir: str | None = None, cleanup: bool = True):
        self._work_dir = work_dir
        self._cleanup = cleanup
        self._dir: str | None = None

    def __enter__(self):
        if self._work_dir:
            self._dir = self._work_dir
            Path(self._dir).mkdir(parents=True, exist_ok=True)
        else:
            self._dir = tempfile.mkdtemp(prefix="codemode_")
        return self

    def __exit__(self, *args: Any):
        if self._cleanup and self._dir and not self._work_dir:
            shutil.rmtree(self._dir, ignore_errors=True)

    @property
    def work_dir(self) -> str:
        if self._dir is None:
            raise RuntimeError("Sandbox not entered")
        return self._dir

    def write_file(self, path: str, content: str) -> str:
        full = os.path.join(self.work_dir, path)
        os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
        with open(full, "w") as f:
            f.write(content)
        return full

    def read_file(self, path: str) -> str:
        with open(os.path.join(self.work_dir, path)) as f:
            return f.read()

    def execute(
        self,
        command: list[str],
        stdin: str = "",
        timeout: float = 30.0,
        env: dict[str, str] | None = None,
        script_path: str = "",
    ) -> SandboxResult:
        import time

        file_path = script_path if script_path else self.work_dir
        resolved = [c.replace("{file}", file_path) for c in command]

        run_env = os.environ.copy()
        run_env["PYTHONUNBUFFERED"] = "1"
        if env:
            run_env.update(env)

        start = time.perf_counter()
        timed_out = False

        proc = subprocess.Popen(
            resolved,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.work_dir,
            env=run_env,
            text=True,
        )

        try:
            stdout, stderr = proc.communicate(input=stdin, timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            timed_out = True

        duration = (time.perf_counter() - start) * 1000

        return SandboxResult(
            stdout=stdout or "",
            stderr=stderr or "",
            exit_code=-1 if timed_out else (proc.returncode or 0),
            timed_out=timed_out,
            duration_ms=round(duration, 1),
        )
