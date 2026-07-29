from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.telemetry import TelemetryExporter


class TestTelemetry:
    def test_start_and_end_span(self):
        with tempfile.TemporaryDirectory() as tmp:
            exp = TelemetryExporter(str(tmp), enabled=True)
            span = exp.start_span("test-op", attributes={"key": "val"})
            assert span.name == "test-op"
            assert span.span_id
            assert span.trace_id
            assert span.attributes["key"] == "val"
            exp.end_span(span)
            assert span.duration_ms >= 0
            assert span.status == "ok"

    def test_span_with_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            exp = TelemetryExporter(str(tmp), enabled=True)
            span = exp.start_span("failing")
            exp.end_span(span, status="error", error="something broke")
            assert span.status == "error"
            assert span.error == "something broke"

    def test_add_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            exp = TelemetryExporter(str(tmp), enabled=True)
            span = exp.start_span("with-events")
            exp.add_event(span, "cache_hit", {"key": "xyz"})
            assert len(span.events) == 1
            assert span.events[0]["name"] == "cache_hit"

    def test_export_creates_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            exp = TelemetryExporter(str(tmp), enabled=True)
            span = exp.start_span("export-test")
            exp.end_span(span)
            spans = exp.export(flush=True)
            assert len(spans) > 0
            files = list(Path(tmp).iterdir())
            assert len(files) >= 1

    def test_disabled_exporter(self):
        exp = TelemetryExporter(enabled=False)
        span = exp.start_span("nope")
        exp.end_span(span)
        assert exp.export() == []

    def test_add_attribute(self):
        with tempfile.TemporaryDirectory() as tmp:
            exp = TelemetryExporter(str(tmp), enabled=True)
            span = exp.start_span("attr-test")
            exp.add_attribute(span, "cpu", 42)
            assert span.attributes["cpu"] == 42
