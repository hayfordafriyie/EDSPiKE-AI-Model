from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from typing import Any


class ExecutionError(Exception):
    pass


class ExecutionResult:
    def __init__(self, stdout: str = "", stderr: str = "", exit_code: int = 0, duration_ms: float = 0.0):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.duration_ms = duration_ms

    def ok(self) -> bool:
        return self.exit_code == 0

    def __repr__(self) -> str:
        return f"Result(exit={self.exit_code}, stdout={len(self.stdout)}b, stderr={len(self.stderr)}b)"


class ExecutionEnvironment:
    def __init__(self, cwd: str | None = None):
        self._cwd = Path(cwd).resolve() if cwd else Path.cwd()

    def with_cwd(self, path: str) -> ExecutionEnvironment:
        return ExecutionEnvironment(str(Path(path).resolve()))

    def with_env(self, **env: str) -> ExecutionEnvironment:
        new = ExecutionEnvironment(str(self._cwd))
        new._env_overrides = env
        return new

    # --- Path operations ---

    def normpath(self, path: str) -> str:
        return str(Path(path).resolve())

    def gethome(self) -> str:
        return str(Path.home())

    def getcwd(self) -> str:
        return str(self._cwd)

    def chdir(self, path: str) -> None:
        self._cwd = Path(path).resolve()

    def iterdir(self, path: str = "") -> list[str]:
        target = self._resolve(path)
        if not target.is_dir():
            raise ExecutionError(f"Not a directory: {target}")
        return sorted(str(p.relative_to(target)) for p in target.iterdir())

    def glob(self, pattern: str, root: str = "") -> list[str]:
        target = self._resolve(root)
        return [str(p.relative_to(target)) for p in target.glob(pattern)]

    def mkdir(self, path: str, parents: bool = True) -> None:
        self._resolve(path).mkdir(parents=parents, exist_ok=True)

    def stat(self, path: str) -> dict[str, Any]:
        p = self._resolve(path)
        if not p.exists():
            raise ExecutionError(f"Path not found: {p}")
        s = p.stat()
        return {
            "size": s.st_size,
            "mode": s.st_mode,
            "mtime": s.st_mtime,
            "is_dir": p.is_dir(),
            "is_file": p.is_file(),
        }

    # --- File operations ---

    def read_bytes(self, path: str) -> bytes:
        return self._resolve(path).read_bytes()

    def read_text(self, path: str) -> str:
        return self._resolve(path).read_text()

    def read_lines(self, path: str) -> list[str]:
        return self._resolve(path).read_text().splitlines()

    def write_bytes(self, path: str, data: bytes) -> None:
        p = self._resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def write_text(self, path: str, text: str) -> None:
        p = self._resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def unlink(self, path: str) -> None:
        self._resolve(path).unlink()

    # --- Process execution ---

    def exec(self, command: str, timeout: float = 30.0) -> ExecutionResult:
        import time
        start = time.time()
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(self._cwd),
                timeout=timeout,
            )
            duration = (time.time() - start) * 1000
            return ExecutionResult(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                duration_ms=duration,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(stderr=f"Timed out after {timeout}s", exit_code=-1, duration_ms=timeout * 1000)
        except Exception as e:
            return ExecutionResult(stderr=str(e), exit_code=-1)

    def exec_with_env(self, command: str, env: dict[str, str] | None = None, timeout: float = 30.0) -> ExecutionResult:
        merged = os.environ.copy()
        if env:
            merged.update(env)
        import time
        start = time.time()
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(self._cwd),
                env=merged,
                timeout=timeout,
            )
            duration = (time.time() - start) * 1000
            return ExecutionResult(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                duration_ms=duration,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(stderr=f"Timed out after {timeout}s", exit_code=-1, duration_ms=timeout * 1000)
        except Exception as e:
            return ExecutionResult(stderr=str(e), exit_code=-1)

    # --- Helpers ---

    def _resolve(self, path: str = "") -> Path:
        if not path:
            return self._cwd
        p = Path(path)
        if p.is_absolute():
            return p.resolve()
        return (self._cwd / p).resolve()

    @staticmethod
    def detect_os() -> str:
        import platform
        system = platform.system().lower()
        if system == "linux":
            return "posix"
        if system == "darwin":
            return "posix"
        if system == "windows":
            return "win32"
        return system

    @staticmethod
    def detect_shell() -> str:
        return os.environ.get("SHELL", "/bin/bash")
