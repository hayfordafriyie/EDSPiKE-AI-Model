from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(Enum):
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    KILLED = "killed"
    LOST = "lost"


@dataclass
class BackgroundTask:
    id: str
    type: str  # bash, agent
    command: str = ""
    status: TaskStatus = TaskStatus.CREATED
    process: subprocess.Popen | None = None
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    created_at: float = 0.0
    completed_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class BackgroundTaskManager:
    def __init__(self):
        self._tasks: dict[str, BackgroundTask] = {}
        self._lock = threading.Lock()

    def start_bash(self, task_id: str, command: str, timeout: float | None = None, workdir: str | None = None) -> BackgroundTask:
        task = BackgroundTask(id=task_id, type="bash", command=command, status=TaskStatus.STARTING, created_at=time.time())
        with self._lock:
            self._tasks[task_id] = task

        def _run():
            task.status = TaskStatus.RUNNING
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=workdir,
                    timeout=timeout,
                )
                task.stdout = result.stdout
                task.stderr = result.stderr
                task.exit_code = result.returncode
                task.status = TaskStatus.COMPLETED if result.returncode == 0 else TaskStatus.FAILED
            except subprocess.TimeoutExpired:
                task.status = TaskStatus.KILLED
                task.stderr = f"Timed out after {timeout}s"
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.stderr = str(e)
            task.completed_at = time.time()

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return task

    def get(self, task_id: str) -> BackgroundTask | None:
        with self._lock:
            return self._tasks.get(task_id)

    def kill(self, task_id: str) -> bool:
        task = self.get(task_id)
        if task is None or task.process is None:
            return False
        try:
            if os.name == "posix":
                os.killpg(os.getpgid(task.process.pid), signal.SIGTERM)
            else:
                task.process.terminate()
            task.status = TaskStatus.KILLED
            return True
        except Exception:
            return False

    def list(self, status: TaskStatus | None = None) -> list[BackgroundTask]:
        with self._lock:
            tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    def reconcile(self) -> None:
        now = time.time()
        with self._lock:
            for task in list(self._tasks.values()):
                if task.status == TaskStatus.RUNNING and task.process and task.process.poll() is not None:
                    task.exit_code = task.process.returncode
                    task.status = TaskStatus.COMPLETED if task.process.returncode == 0 else TaskStatus.FAILED
                    task.completed_at = now

    def count(self) -> int:
        return len(self._tasks)

    def clear_completed(self) -> None:
        with self._lock:
            self._tasks = {k: v for k, v in self._tasks.items() if v.status in (TaskStatus.RUNNING, TaskStatus.STARTING)}
