from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


NotificationCategory = str  # "task" | "agent" | "system"
NotificationSeverity = str  # "info" | "success" | "warning" | "error"
NotificationSink = str  # "llm" | "wire" | "shell"
NotificationDeliveryStatus = str  # "pending" | "claimed" | "acked"


@dataclass
class NotificationEvent:
    id: str
    category: NotificationCategory
    type: str
    source_kind: str
    source_id: str
    title: str
    body: str
    severity: NotificationSeverity = "info"
    created_at: float = 0.0
    payload: dict[str, Any] = field(default_factory=dict)
    targets: list[str] = field(default_factory=lambda: ["llm", "wire", "shell"])
    dedupe_key: str | None = None


@dataclass
class NotificationView:
    event: NotificationEvent
    status: NotificationDeliveryStatus = "pending"


class NotificationStore:
    def __init__(self, data_dir: str = ""):
        self._notifications: list[NotificationView] = []
        self._data_path = Path(data_dir) / "notifications.json" if data_dir else None

    def add(self, event: NotificationEvent) -> NotificationView:
        view = NotificationView(event=event, status="pending")
        self._notifications.append(view)
        self._save()
        return view

    def claim(self, sink: str, limit: int = 10) -> list[NotificationView]:
        claimed: list[NotificationView] = []
        for n in self._notifications:
            if n.status == "pending" and sink in n.event.targets:
                n.status = "claimed"
                claimed.append(n)
                if len(claimed) >= limit:
                    break
        self._save()
        return claimed

    def ack(self, notification_id: str) -> bool:
        for n in self._notifications:
            if n.event.id == notification_id and n.status == "claimed":
                n.status = "acked"
                self._save()
                return True
        return False

    def get_pending(self, sink: str = "") -> list[NotificationView]:
        return [n for n in self._notifications if n.status == "pending" and (not sink or sink in n.event.targets)]

    def get_all(self, limit: int = 50) -> list[NotificationView]:
        return self._notifications[-limit:]

    def _save(self) -> None:
        if self._data_path is None:
            return
        self._data_path.parent.mkdir(parents=True, exist_ok=True)
        data = [
            {
                "event": {
                    "id": n.event.id, "category": n.event.category, "type": n.event.type,
                    "source_kind": n.event.source_kind, "source_id": n.event.source_id,
                    "title": n.event.title, "body": n.event.body, "severity": n.event.severity,
                    "created_at": n.event.created_at, "payload": n.event.payload,
                    "targets": n.event.targets, "dedupe_key": n.event.dedupe_key,
                },
                "status": n.status,
            }
            for n in self._notifications
        ]
        self._data_path.write_text(json.dumps(data, indent=2))


class NotificationManager:
    def __init__(self, store: NotificationStore | None = None):
        self.store = store or NotificationStore()

    def notify(self, category: str, type_: str, source_kind: str, source_id: str, title: str, body: str, severity: str = "info", targets: list[str] | None = None) -> NotificationView:
        event = NotificationEvent(
            id=f"notif_{int(time.time() * 1000000)}",
            category=category,
            type=type_,
            source_kind=source_kind,
            source_id=source_id,
            title=title,
            body=body,
            severity=severity,
            created_at=time.time(),
            targets=targets or ["llm", "wire", "shell"],
        )
        return self.store.add(event)

    def notify_task(self, source_id: str, title: str, body: str, severity: str = "info") -> NotificationView:
        return self.notify("task", "task_update", "background", source_id, title, body, severity)

    def notify_agent(self, source_id: str, title: str, body: str, severity: str = "info") -> NotificationView:
        return self.notify("agent", "agent_event", "agent", source_id, title, body, severity)

    def notify_system(self, title: str, body: str, severity: str = "info") -> NotificationView:
        return self.notify("system", "system_event", "system", "system", title, body, severity)

    def build_llm_message(self, limit: int = 5) -> str:
        pending = self.store.get_pending("llm")[:limit]
        if not pending:
            return ""
        lines = ["Notifications:"]
        for n in pending:
            sev = {"info": "ℹ", "success": "✅", "warning": "⚠", "error": "❌"}.get(n.event.severity, "•")
            lines.append(f"  {sev} {n.event.title}: {n.event.body[:200]}")
            self.store.ack(n.event.id)
        return "\n".join(lines)
