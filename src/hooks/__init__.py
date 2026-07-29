from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Any, Callable

HookFn = Callable[[dict[str, Any]], str | None]


@dataclass
class LifecycleHook:
    name: str
    event: str  # before_tool, after_tool, before_turn, after_turn, on_error
    command: str = ""
    handler: HookFn | None = None
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class LifecycleHookManager:
    def __init__(self):
        self._hooks: list[LifecycleHook] = []

    def register(self, hook: LifecycleHook) -> None:
        self._hooks.append(hook)

    def register_handler(self, name: str, event: str, handler: HookFn) -> None:
        self._hooks.append(LifecycleHook(name=name, event=event, handler=handler))

    def run(self, event: str, context: dict[str, Any]) -> list[str]:
        results: list[str] = []
        for hook in self._hooks:
            if hook.event != event or not hook.enabled:
                continue
            result = self._execute(hook, context)
            if result:
                results.append(f"[{hook.name}] {result}")
        return results

    def _execute(self, hook: LifecycleHook, context: dict[str, Any]) -> str | None:
        if hook.handler:
            try:
                return hook.handler(context)
            except Exception as e:
                return f"Handler error: {e}"

        if hook.command:
            try:
                result = subprocess.run(
                    hook.command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                output = result.stdout.strip()
                if result.stderr:
                    output += f"\n[stderr] {result.stderr.strip()}"
                return output or "(no output)"
            except subprocess.TimeoutExpired:
                return "Command timed out"
            except Exception as e:
                return f"Command error: {e}"

        return None

    def disable(self, name: str) -> bool:
        for hook in self._hooks:
            if hook.name == name:
                hook.enabled = False
                return True
        return False

    def enable(self, name: str) -> bool:
        for hook in self._hooks:
            if hook.name == name:
                hook.enabled = True
                return True
        return False

    def list(self) -> list[LifecycleHook]:
        return list(self._hooks)

    def clear(self) -> None:
        self._hooks.clear()
