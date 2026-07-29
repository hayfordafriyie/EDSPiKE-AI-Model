from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TelemetrySpan:
    name: str
    span_id: str = ""
    trace_id: str = ""
    parent_id: str = ""
    start_time: str = ""
    end_time: str = ""
    duration_ms: float = 0.0
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    status: str = "ok"
    error: str = ""


class TelemetryExporter:
    def __init__(self, output_dir: str | None = None, enabled: bool = True):
        if output_dir is None:
            output_dir = str(Path(os.getenv("EDSPIKE_DATA_DIR", "~/.edspike")).expanduser() / "traces")
        self._dir = Path(output_dir)
        self._enabled = enabled
        self._spans: list[TelemetrySpan] = []
        if enabled:
            self._dir.mkdir(parents=True, exist_ok=True)

    def start_span(
        self,
        name: str,
        trace_id: str = "",
        parent_id: str = "",
        attributes: dict | None = None,
    ) -> TelemetrySpan:
        span = TelemetrySpan(
            name=name,
            span_id=uuid.uuid4().hex[:16],
            trace_id=trace_id or uuid.uuid4().hex[:16],
            parent_id=parent_id,
            start_time=datetime.now(timezone.utc).isoformat(),
            attributes=attributes or {},
        )
        self._spans.append(span)
        return span

    def end_span(self, span: TelemetrySpan, status: str = "ok", error: str = "") -> None:
        span.end_time = datetime.now(timezone.utc).isoformat()
        span.duration_ms = self._compute_duration(span.start_time, span.end_time)
        span.status = status
        span.error = error

    def add_event(self, span: TelemetrySpan, name: str, attributes: dict | None = None) -> None:
        span.events.append({
            "name": name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attributes": attributes or {},
        })

    def add_attribute(self, span: TelemetrySpan, key: str, value: Any) -> None:
        span.attributes[key] = value

    def export(self, flush: bool = True) -> list[dict[str, Any]]:
        if not self._enabled:
            return []
        serialized = []
        for span in self._spans:
            data = {
                "name": span.name,
                "span_id": span.span_id,
                "trace_id": span.trace_id,
                "parent_id": span.parent_id,
                "start_time": span.start_time,
                "end_time": span.end_time,
                "duration_ms": span.duration_ms,
                "attributes": span.attributes,
                "events": span.events,
                "status": span.status,
                "error": span.error,
            }
            serialized.append(data)

        if flush:
            trace_file = self._dir / f"trace_{int(time.time())}_{uuid.uuid4().hex[:8]}.json"
            trace_file.write_text(json.dumps(serialized, indent=2))
            self._spans.clear()

        return serialized

    @staticmethod
    def _compute_duration(start: str, end: str) -> float:
        try:
            s = datetime.fromisoformat(start)
            e = datetime.fromisoformat(end)
            return (e - s).total_seconds() * 1000
        except (ValueError, TypeError):
            return 0.0

    def flush(self) -> None:
        self.export(flush=True)
