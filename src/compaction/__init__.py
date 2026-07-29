from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from src.wire import Wire, send_compaction_begin, send_compaction_end, send_text

TOKEN_ESTIMATE = 0.25


@dataclass
class CompactResult:
    summary: str
    original_tokens: int
    compressed_tokens: int
    ratio: float
    preserved_turns: int = 0


CompactionProvider = Callable[[list[dict[str, Any]]], str]


class DefaultCompactor:
    def __init__(self, max_context_tokens: int = 8000, reserve_tokens: int = 2000, threshold: float = 0.85):
        self.max_context_tokens = max_context_tokens
        self.reserve_tokens = reserve_tokens
        self.threshold = threshold
        self._provider: CompactionProvider | None = None

    def set_provider(self, provider: CompactionProvider) -> None:
        self._provider = provider

    def estimate_tokens(self, text: str) -> int:
        return int(len(text) * TOKEN_ESTIMATE) + 1

    def should_compact(self, token_count: int) -> bool:
        return token_count >= self.max_context_tokens * self.threshold or token_count + self.reserve_tokens >= self.max_context_tokens

    def compact(self, turns: list[dict[str, Any]], wire: Wire | None = None) -> CompactResult:
        full_text = self._format_turns(turns)
        original_tokens = self.estimate_tokens(full_text)

        if not self.should_compact(original_tokens):
            return CompactResult(summary=full_text, original_tokens=original_tokens, compressed_tokens=original_tokens, ratio=1.0)

        send_compaction_begin(wire)

        preserve_count = min(max(1, len(turns) // 4), len(turns) - 1) if len(turns) > 1 else 0
        to_compact = turns[:-preserve_count] if preserve_count > 0 else turns
        to_preserve = turns[-preserve_count:] if preserve_count > 0 else []

        if self._provider and to_compact:
            compact_text = self._format_turns(to_compact)
            summary = self._provider([{"role": "system", "content": f"Compress this conversation history preserving key facts, decisions, and context:\n\n{compact_text}"}])
        else:
            summary = self._simple_compress(to_compact)

        preserved_text = self._format_turns(to_preserve)
        result_text = f"[Compressed History]\n{summary}\n\n[Recent Messages]\n{preserved_text}"

        compressed_tokens = self.estimate_tokens(result_text)
        ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0

        send_text(wire, f"_Context compacted: {original_tokens} → {compressed_tokens} tokens ({ratio:.0%})_")
        send_compaction_end(wire)

        return CompactResult(summary=result_text, original_tokens=original_tokens, compressed_tokens=compressed_tokens, ratio=ratio, preserved_turns=preserve_count)

    def _format_turns(self, turns: list[dict[str, Any]]) -> str:
        parts: list[str] = []
        for t in turns:
            role = t.get("role", "unknown")
            content = t.get("content", "")
            parts.append(f"{role}: {content}")
        return "\n".join(parts)

    def _simple_compress(self, turns: list[dict[str, Any]]) -> str:
        lines: list[str] = []
        for t in turns:
            role = t.get("role", "?")
            content = t.get("content", "")
            content = content[:200] if len(content) > 200 else content
            lines.append(f"[{role}] {content}")
        return "\n".join(lines[-20:])
