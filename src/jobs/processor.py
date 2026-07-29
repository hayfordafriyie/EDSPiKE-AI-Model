from __future__ import annotations

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    id: str = ""
    name: str = ""
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    result: Any = None
    error: str = ""
    created_at: float = 0.0
    started_at: float = 0.0
    completed_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


JobHandler = Callable[[Job], Any]


class BackgroundJobProcessor:
    def __init__(self, max_workers: int = 4):
        self._max_workers = max_workers
        self._jobs: dict[str, Job] = {}
        self._handlers: dict[str, JobHandler] = {}
        self._lock = threading.Lock()
        self._running = True
        self._threads: list[threading.Thread] = []
        self._queue: list[str] = []

    def register(self, name: str, handler: JobHandler) -> None:
        self._handlers[name] = handler

    def enqueue(self, name: str, metadata: dict[str, Any] | None = None) -> str:
        job = Job(
            id=uuid.uuid4().hex[:16],
            name=name,
            status=JobStatus.PENDING,
            created_at=time.time(),
            metadata=metadata or {},
        )
        with self._lock:
            self._jobs[job.id] = job
            self._queue.append(job.id)
        self._maybe_process()
        return job.id

    def _maybe_process(self) -> None:
        active = sum(1 for j in self._jobs.values() if j.status == JobStatus.RUNNING)
        if active < self._max_workers:
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self._threads.append(t)

    def _worker(self) -> None:
        while self._running:
            job_id = None
            with self._lock:
                if self._queue:
                    job_id = self._queue.pop(0)
                    if job_id in self._jobs:
                        self._jobs[job_id].status = JobStatus.RUNNING
                        self._jobs[job_id].started_at = time.time()
            if not job_id:
                break
            self._process_job(job_id)

    def _process_job(self, job_id: str) -> None:
        job = self._jobs.get(job_id)
        if not job:
            return
        handler = self._handlers.get(job.name)
        if not handler:
            self._fail(job, f"No handler registered for job type: {job.name}")
            return
        try:
            result = handler(job)
            with self._lock:
                job.status = JobStatus.COMPLETED
                job.result = result
                job.completed_at = time.time()
                job.progress = 1.0
            logger.info("Job %s completed", job_id)
        except Exception as exc:
            self._fail(job, str(exc))

    def _fail(self, job: Job, error: str) -> None:
        with self._lock:
            job.status = JobStatus.FAILED
            job.error = error
            job.completed_at = time.time()
        logger.error("Job %s failed: %s", job.id, error)

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if job and job.status in (JobStatus.PENDING, JobStatus.RUNNING):
                job.status = JobStatus.CANCELLED
                return True
            return False

    def list(self, status: JobStatus | None = None) -> list[Job]:
        jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    def shutdown(self) -> None:
        self._running = False
