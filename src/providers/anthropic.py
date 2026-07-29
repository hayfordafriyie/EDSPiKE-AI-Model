from __future__ import annotations

import logging
import os
from typing import Any

from .base import AIProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(AIProvider):
    provider_name = "anthropic"

    def __init__(self, api_key: str | None = None, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.model_name = model

    def generate_batch(
        self, prompts: list[str], max_tokens: int, temperature: float, top_p: float,
    ) -> tuple[list[str], list[int]]:
        import httpx
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
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
                    "messages": [{"role": "user", "content": prompt}],
                }
                resp = client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                content = data["content"][0]["text"]
                responses_list.append(content)
                counts_list.append(data.get("usage", {}).get("output_tokens", 0))
        return responses_list, counts_list
