from __future__ import annotations

from abc import ABC, abstractmethod


class AIProvider(ABC):
    provider_name: str
    model_name: str

    @abstractmethod
    def generate_batch(
        self, prompts: list[str], max_tokens: int, temperature: float, top_p: float,
    ) -> tuple[list[str], list[int]]:
        raise NotImplementedError
