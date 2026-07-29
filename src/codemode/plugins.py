from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class PluginHook(str, Enum):
    PRE_EXEC = "pre_exec"
    POST_EXEC = "post_exec"
    VALIDATE = "validate"


@dataclass
class PluginContext:
    code: str = ""
    language: str = ""
    work_dir: str = ""
    env: dict[str, str] = field(default_factory=dict)
    result: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


PluginHandler = Callable[[PluginContext], PluginContext | None]


class PluginRegistry:
    def __init__(self):
        self._hooks: dict[PluginHook, list[PluginHandler]] = {
            hook: [] for hook in PluginHook
        }

    def register(self, hook: PluginHook, handler: PluginHandler):
        self._hooks[hook].append(handler)
        logger.debug("Registered plugin for hook %s: %s", hook, handler.__name__)

    def unregister(self, hook: PluginHook, handler: PluginHandler):
        self._hooks[hook] = [h for h in self._hooks[hook] if h is not handler]

    def run(self, hook: PluginHook, ctx: PluginContext) -> PluginContext:
        for handler in self._hooks[hook]:
            try:
                result = handler(ctx)
                if result is not None:
                    ctx = result
            except Exception as exc:
                logger.error("Plugin %s failed on hook %s: %s", handler.__name__, hook, exc)
                ctx.errors.append(f"{handler.__name__}: {exc}")
        return ctx

    def clear(self):
        for hook in PluginHook:
            self._hooks[hook].clear()


_global_registry = PluginRegistry()


def get_plugin_registry() -> PluginRegistry:
    return _global_registry


def code_plugin(hook: PluginHook):
    """Decorator to register a plugin handler."""
    def decorator(fn: PluginHandler) -> PluginHandler:
        _global_registry.register(hook, fn)
        return fn
    return decorator
