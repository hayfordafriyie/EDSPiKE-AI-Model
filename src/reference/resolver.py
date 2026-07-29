from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Reference:
    raw: str
    source: str  # e.g. "file", "session", "tool", "variable"
    path: str
    metadata: dict[str, Any] = field(default_factory=dict)


ReferenceResolverFn = Callable[[Reference], str | None]


class ReferenceResolver:
    PATTERN = re.compile(r"\{\{([A-Za-z_][A-Za-z0-9_.]*)\}\}")

    def __init__(self):
        self._resolvers: dict[str, ReferenceResolverFn] = {}

    def register(self, source: str, resolver: ReferenceResolverFn) -> None:
        self._resolvers[source] = resolver

    def resolve(self, text: str, context: dict[str, Any] | None = None) -> str:
        def _replacer(match: re.Match) -> str:
            raw = match.group(1)
            ref = self._parse(raw, context or {})
            resolver_fn = self._resolvers.get(ref.source)
            if resolver_fn:
                result = resolver_fn(ref)
                if result is not None:
                    return result
            return match.group(0)  # leave unresolved

        return self.PATTERN.sub(_replacer, text)

    def _parse(self, raw: str, context: dict[str, Any]) -> Reference:
        parts = raw.split(".", 1)
        source = parts[0]
        path = parts[1] if len(parts) > 1 else ""
        metadata = {}
        if source in context:
            metadata["context_value"] = context[source]
        return Reference(raw=raw, source=source, path=path, metadata=metadata)

    def extract_references(self, text: str) -> list[str]:
        return self.PATTERN.findall(text)
