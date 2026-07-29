from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BtwResult:
    question: str
    answer: str
    tokens_used: int = 0
    duration_ms: float = 0.0


class DenyAllToolset:
    """Toolset that denies all tool calls - used for /btw questions."""

    @staticmethod
    def handle(tool_name: str, args: dict[str, Any]) -> str:
        return f"Error: Tool '{tool_name}' is not available. Please answer without using tools."


class BtwEngine:
    def __init__(self, max_retries: int = 2):
        self._max_retries = max_retries
        self._history: list[BtwResult] = []

    def ask(self, question: str, system_prompt: str, generate_fn: Any) -> BtwResult:
        import time
        start = time.time()

        enhanced_prompt = (
            f"[Side Question - Answer without using any tools]\n"
            f"System context: {system_prompt[:500]}\n"
            f"Question: {question}\n\n"
            f"Important: You must answer using text only. Do NOT call any tools."
        )

        retries = 0
        while retries <= self._max_retries:
            try:
                response = generate_fn(enhanced_prompt)
                duration = (time.time() - start) * 1000
                result = BtwResult(question=question, answer=str(response), duration_ms=duration)
                self._history.append(result)
                return result
            except Exception:
                retries += 1
                if retries > self._max_retries:
                    raise

        raise RuntimeError(f"Failed to get answer after {self._max_retries + 1} attempts")

    def get_history(self) -> list[BtwResult]:
        return list(self._history)

    def clear(self) -> None:
        self._history.clear()
