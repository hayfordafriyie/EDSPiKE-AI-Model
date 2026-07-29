from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class PolicyDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


@dataclass
class Policy:
    name: str
    action_pattern: str
    resource_pattern: str
    decision: PolicyDecision = PolicyDecision.DENY
    priority: int = 0
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


PolicyCheckFn = Callable[[str, str, dict[str, Any]], PolicyDecision | None]


class PolicyEngine:
    def __init__(self):
        self._policies: list[Policy] = []
        self._checks: list[PolicyCheckFn] = []

    def add(self, policy: Policy) -> None:
        self._policies.append(policy)
        self._policies.sort(key=lambda p: p.priority, reverse=True)

    def add_check(self, fn: PolicyCheckFn) -> None:
        self._checks.append(fn)

    def evaluate(self, action: str, resource: str, context: dict[str, Any] | None = None) -> tuple[PolicyDecision, str]:
        ctx = context or {}

        for fn in self._checks:
            result = fn(action, resource, ctx)
            if result is not None:
                return result, f"Check: {fn.__name__}"

        for policy in self._policies:
            if re.match(policy.action_pattern, action) and re.match(policy.resource_pattern, resource):
                return policy.decision, policy.reason or f"Policy: {policy.name}"

        return PolicyDecision.ALLOW, "Default allow"

    def can(self, action: str, resource: str, context: dict | None = None) -> bool:
        decision, _ = self.evaluate(action, resource, context)
        return decision == PolicyDecision.ALLOW

    def list_policies(self) -> list[dict[str, Any]]:
        return [
            {
                "name": p.name,
                "action_pattern": p.action_pattern,
                "resource_pattern": p.resource_pattern,
                "decision": p.decision.value,
                "priority": p.priority,
                "reason": p.reason,
            }
            for p in self._policies
        ]

    def clear(self) -> None:
        self._policies.clear()
        self._checks.clear()
