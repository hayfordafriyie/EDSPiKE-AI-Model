from __future__ import annotations

import logging
import os
from typing import Any

from .base import AIProvider

logger = logging.getLogger(__name__)


class GoogleProvider(AIProvider):
    provider_name = "google"

    def __init__(self, api_key: str | None = None, model: str = "gemini-1.5-pro"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self.model_name = model

    def generate_batch(
        self, prompts: list[str], max_tokens: int, temperature: float, top_p: float,
    ) -> tuple[list[str], list[int]]:
        import httpx
        responses_list: list[str] = []
        counts_list: list[int] = []
        with httpx.Client(timeout=120) as client:
            for prompt in prompts:
                url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{self.model_name}:generateContent?key={self.api_key}"
                )
                payload: dict[str, Any] = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "maxOutputTokens": max_tokens,
                        "temperature": temperature,
                        "topP": top_p,
                    },
                }
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                candidate = data["candidates"][0]
                text = candidate["content"]["parts"][0]["text"]
                responses_list.append(text)
                counts_list.append(0)
        return responses_list, counts_list
