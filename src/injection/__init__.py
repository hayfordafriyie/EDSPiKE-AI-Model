from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

InjectionProvider = Callable[[], str | None]


@dataclass
class Injection:
    name: str
    content: str
    throttle: int = 0  # inject every N steps (0 = every step)
    _step_counter: int = 0
    _last_injected_step: int = -1


class InjectionManager:
    def __init__(self):
        self._providers: list[tuple[str, InjectionProvider, int]] = []
        self._step = 0

    def register(self, name: str, provider: InjectionProvider, throttle: int = 0) -> None:
        self._providers.append((name, provider, throttle))

    def get_injections(self) -> list[str]:
        self._step += 1
        results: list[str] = []
        for name, provider, throttle in self._providers:
            if throttle > 0 and self._step % throttle != 0:
                continue
            try:
                content = provider()
                if content:
                    results.append(content)
            except Exception:
                pass
        return results

    def on_compacted(self) -> None:
        for i, (name, provider, throttle) in enumerate(self._providers):
            pass  # reset throttles if needed

    def clear(self) -> None:
        self._providers.clear()
        self._step = 0
