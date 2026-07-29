from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


TOKEN_ESTIMATE = 0.25  # ~4 chars per token


@dataclass
class CompactResult:
    summary: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float


class ContextCompressor:
    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens

    def estimate_tokens(self, text: str) -> int:
        return int(len(text) * TOKEN_ESTIMATE) + 1

    def needs_compression(self, text: str, threshold: float = 0.9) -> bool:
        return self.estimate_tokens(text) >= self.max_tokens * threshold

    def compress(self, conversations: list[dict[str, Any]]) -> CompactResult:
        full_text = self._format_conversations(conversations)
        original_tokens = self.estimate_tokens(full_text)

        if not self.needs_compression(full_text):
            return CompactResult(
                summary=full_text,
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                compression_ratio=1.0,
            )

        summary_parts: list[str] = []
        for conv in conversations:
            role = conv.get("role", "unknown")
            content = conv.get("content", "")
            if not content:
                continue
            compressed = self._compress_content(content)
            summary_parts.append(f"[{role}] {compressed}")

        summary = "\n".join(summary_parts)
        compressed_tokens = self.estimate_tokens(summary)
        ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0

        return CompactResult(
            summary=summary,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=round(ratio, 2),
        )

    def _format_conversations(self, conversations: list[dict[str, Any]]) -> str:
        parts: list[str] = []
        for conv in conversations:
            role = conv.get("role", "")
            content = conv.get("content", "")
            parts.append(f"{role}: {content}")
        return "\n".join(parts)

    def _compress_content(self, content: str) -> str:
        content = content.strip()
        lines = content.splitlines()
        if len(lines) > 20:
            lines = lines[:10] + ["..."] + lines[-10:]
        content = "\n".join(lines)

        if self.estimate_tokens(content) > self.max_tokens // 4:
            words = content.split()
            max_words = self.max_tokens // 2
            if max_words < 1:
                max_words = 1
            if len(words) > max_words:
                content = " ".join(words[:max_words])
            elif len(content) > self.max_tokens * 2:
                content = content[:self.max_tokens * 2] + "..."

        return content

    def summarize_session(self, messages: list[dict[str, Any]]) -> str:
        result = self.compress(messages)
        return result.summary

    def generate_title(self, messages: list[dict[str, Any]]) -> str:
        if not messages:
            return "New Session"
        first = messages[0].get("content", "")
        words = first.split()[:8]
        title = " ".join(words)
        if len(title) > 60:
            title = title[:57] + "..."
        return title or "Untitled"
