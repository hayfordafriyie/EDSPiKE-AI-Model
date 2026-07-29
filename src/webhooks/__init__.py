from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable

WebhookHandler = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass
class Webhook:
    id: str
    name: str
    event: str  # tool_executed, session_started, session_ended, goal_completed, etc.
    url: str = ""
    handler: Any = None
    enabled: bool = True
    created_at: float = 0.0


class WebhookManager:
    def __init__(self):
        self._webhooks: dict[str, Webhook] = {}
        self._handlers: dict[str, WebhookHandler] = {}

    def register(self, name: str, event: str, url: str = "", handler: WebhookHandler | None = None) -> Webhook:
        wh = Webhook(id=f"wh_{int(time.time() * 1000000)}", name=name, event=event, url=url, handler=handler, created_at=time.time())
        self._webhooks[wh.id] = wh
        if handler:
            self._handlers[wh.id] = handler
        return wh

    def trigger(self, event: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for wh in self._webhooks.values():
            if wh.event != event or not wh.enabled:
                continue
            result = self._execute(wh, payload)
            results.append({"webhook": wh.name, "result": result})
        return results

    def _execute(self, wh: Webhook, payload: dict[str, Any]) -> Any:
        if wh.handler:
            try:
                return wh.handler(payload)
            except Exception as e:
                return {"error": str(e)}
        if wh.url:
            try:
                import httpx
                resp = httpx.post(wh.url, json=payload, timeout=10)
                return {"status": resp.status_code, "body": resp.text[:500]}
            except Exception as e:
                return {"error": str(e)}
        return {"error": "No handler or URL configured"}

    def list(self) -> list[Webhook]:
        return list(self._webhooks.values())

    def delete(self, webhook_id: str) -> bool:
        if webhook_id in self._webhooks:
            del self._webhooks[webhook_id]
            self._handlers.pop(webhook_id, None)
            return True
        return False
