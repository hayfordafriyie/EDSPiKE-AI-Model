from __future__ import annotations

import logging
import os
from typing import Any

from .base import AIProvider

logger = logging.getLogger(__name__)


class DeepSeekProvider(AIProvider):
    provider_name = "deepseek"

    def __init__(self, api_key: str | None = None, model: str = "deepseek-chat"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.model_name = model

    def generate_batch(
        self, prompts: list[str], max_tokens: int, temperature: float, top_p: float,
    ) -> tuple[list[str], list[int]]:
        import httpx
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        responses_list: list[str] = []
        counts_list: list[int] = []
        with httpx.Client(timeout=120) as client:
            for prompt in prompts:
                payload: dict[str, Any] = {
                    "model": self.model_name,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "messages": [{"role": "user", "content": prompt}],
                }
                resp = client.post("https://api.deepseek.com/v1/chat/completions", json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                choice = data["choices"][0]
                responses_list.append(choice["message"]["content"])
                counts_list.append(choice.get("usage", {}).get("completion_tokens", 0))
        return responses_list, counts_list
