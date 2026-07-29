from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class Integration:
    name: str
    version: str = "0.1.0"
    description: str = ""
    actions: dict[str, Callable] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)


class IntegrationFramework:
    def __init__(self):
        self._integrations: dict[str, Integration] = {}

    def register(self, integration: Integration) -> None:
        self._integrations[integration.name] = integration
        logger.info("Registered integration: %s", integration.name)

    def get(self, name: str) -> Integration | None:
        return self._integrations.get(name)

    def execute(self, integration_name: str, action: str, **kwargs: Any) -> Any:
        integration = self._integrations.get(integration_name)
        if not integration:
            raise KeyError(f"Integration not found: {integration_name}")
        handler = integration.actions.get(action)
        if not handler:
            raise KeyError(f"Action '{action}' not found in integration '{integration_name}'")
        try:
            return handler(**kwargs)
        except Exception as exc:
            logger.error("Integration %s action %s failed: %s", integration_name, action, exc)
            raise

    def list(self) -> list[dict[str, Any]]:
        return [
            {
                "name": i.name,
                "version": i.version,
                "description": i.description,
                "actions": list(i.actions.keys()),
            }
            for i in self._integrations.values()
        ]

    def unregister(self, name: str) -> bool:
        if name in self._integrations:
            del self._integrations[name]
            return True
        return False
