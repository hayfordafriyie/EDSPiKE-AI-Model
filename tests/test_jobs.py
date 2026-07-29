from __future__ import annotations

import time

import pytest

from src.jobs import BackgroundJobProcessor, JobStatus


class TestBackgroundJobs:
    def test_enqueue_and_complete(self):
        proc = BackgroundJobProcessor(max_workers=2)
        proc.register("echo", lambda j: j.metadata.get("msg", ""))
        job_id = proc.enqueue("echo", {"msg": "hello"})
        time.sleep(0.2)
        job = proc.get(job_id)
        assert job is not None
        assert job.status == JobStatus.COMPLETED
        assert job.result == "hello"

    def test_enqueue_fails(self):
        proc = BackgroundJobProcessor(max_workers=1)

        def fail(job):
            raise RuntimeError("boom")

        proc.register("fail", fail)
        job_id = proc.enqueue("fail")
        time.sleep(0.2)
        job = proc.get(job_id)
        assert job.status == JobStatus.FAILED
        assert "boom" in job.error

    def test_unregistered_handler(self):
        proc = BackgroundJobProcessor()
        job_id = proc.enqueue("unknown")
        time.sleep(0.1)
        job = proc.get(job_id)
        assert job.status == JobStatus.FAILED
        assert "No handler" in job.error

    def test_cancel_pending(self):
        proc = BackgroundJobProcessor()

        def slow(job):
            time.sleep(10)

        proc.register("slow", slow)
        job_id = proc.enqueue("slow")
        assert proc.cancel(job_id) is True
        assert proc.get(job_id).status == JobStatus.CANCELLED

    def test_cancel_completed(self):
        proc = BackgroundJobProcessor(max_workers=1)
        proc.register("fast", lambda j: 42)
        job_id = proc.enqueue("fast")
        time.sleep(0.2)
        assert proc.cancel(job_id) is False

    def test_list(self):
        proc = BackgroundJobProcessor(max_workers=2)
        proc.register("a", lambda j: 1)
        proc.register("b", lambda j: 2)
        id1 = proc.enqueue("a")
        id2 = proc.enqueue("b")
        time.sleep(0.3)
        jobs = proc.list()
        assert len(jobs) >= 2

    def test_list_filtered(self):
        proc = BackgroundJobProcessor(max_workers=1)
        proc.register("x", lambda j: 0)
        proc.enqueue("x")
        time.sleep(0.2)
        pending = proc.list(JobStatus.PENDING)
        completed = proc.list(JobStatus.COMPLETED)
        assert len(completed) >= 1
