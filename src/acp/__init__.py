from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AcpMessage:
    type: str  # request, response, broadcast
    sender: str
    receiver: str = ""
    method: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: str = ""
    id: str = ""
    timestamp: float = 0.0


class AcpChannel:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self._inbox: list[AcpMessage] = []
        self._handlers: dict[str, callable] = {}

    def send(self, message: AcpMessage) -> None:
        message.timestamp = time.time()
        self._inbox.append(message)

    def receive(self) -> list[AcpMessage]:
        msgs = list(self._inbox)
        self._inbox.clear()
        return msgs

    def register_handler(self, method: str, handler: callable) -> None:
        self._handlers[method] = handler

    def handle(self, message: AcpMessage) -> AcpMessage | None:
        handler = self._handlers.get(message.method)
        if handler:
            try:
                result = handler(message.params)
                return AcpMessage(
                    type="response",
                    sender=self.agent_id,
                    receiver=message.sender,
                    id=message.id,
                    result=result,
                )
            except Exception as e:
                return AcpMessage(
                    type="response",
                    sender=self.agent_id,
                    receiver=message.sender,
                    id=message.id,
                    error=str(e),
                )
        return None

    def request(self, receiver: str, method: str, params: dict[str, Any] | None = None) -> str:
        msg_id = f"acp_{int(time.time() * 1000000)}"
        msg = AcpMessage(
            type="request",
            sender=self.agent_id,
            receiver=receiver,
            method=method,
            params=params or {},
            id=msg_id,
        )
        self.send(msg)
        return msg_id

    def respond(self, request: AcpMessage, result: Any = None, error: str = "") -> None:
        msg = AcpMessage(
            type="response",
            sender=self.agent_id,
            receiver=request.sender,
            id=request.id,
            result=result,
            error=error,
        )
        self.send(msg)

    def broadcast(self, method: str, params: dict[str, Any] | None = None) -> None:
        msg = AcpMessage(
            type="broadcast",
            sender=self.agent_id,
            method=method,
            params=params or {},
            id=f"acp_{int(time.time() * 1000000)}",
        )
        self.send(msg)
