from __future__ import annotations

import random
import time
from typing import Any


class EchoProvider:
    provider_name = "echo"

    def generate(self, prompt: str, **kwargs: Any) -> str:
        return f"Echo: {prompt[:500]}"

    def generate_batch(self, prompts: list[str], **kwargs: Any) -> tuple[list[str], list[int]]:
        return ([f"Echo: {p[:500]}" for p in prompts], [len(p) for p in prompts])


class ScriptedEchoProvider:
    provider_name = "scripted_echo"

    def __init__(self, responses: dict[str, str] | None = None):
        self._responses = responses or {
            "default": "Default scripted response.",
            "hello": "Hi there! I'm a scripted echo provider.",
            "test": "Test completed successfully.",
        }

    def set_response(self, prompt_pattern: str, response: str) -> None:
        self._responses[prompt_pattern] = response

    def generate(self, prompt: str, **kwargs: Any) -> str:
        for pattern, response in self._responses.items():
            if pattern in prompt.lower():
                return response
        return self._responses.get("default", "No matching response.")

    def generate_batch(self, prompts: list[str], **kwargs: Any) -> tuple[list[str], list[int]]:
        responses = [self.generate(p) for p in prompts]
        return (responses, [len(r) for r in responses])


class ChaosProvider:
    provider_name = "chaos"

    def __init__(self, wrapped_provider: Any, error_rate: float = 0.3):
        self._wrapped = wrapped_provider
        self._error_rate = error_rate
        self._error_types = ["api_connection", "api_timeout", "rate_limit", "server_error", "quota_exhausted"]

    def generate(self, prompt: str, **kwargs: Any) -> str:
        if random.random() < self._error_rate:
            error_type = random.choice(self._error_types)
            time.sleep(random.uniform(0.1, 0.5))
            if error_type == "api_connection":
                raise ConnectionError("Chaos: API connection failed")
            elif error_type == "api_timeout":
                raise TimeoutError("Chaos: API request timed out")
            elif error_type == "rate_limit":
                raise RuntimeError("Chaos: 429 Too Many Requests")
            elif error_type == "server_error":
                raise RuntimeError("Chaos: 500 Internal Server Error")
            elif error_type == "quota_exhausted":
                raise RuntimeError("Chaos: 402 Quota Exhausted")
        return self._wrapped.generate(prompt, **kwargs)

    def generate_batch(self, prompts: list[str], **kwargs: Any) -> tuple[list[str], list[int]]:
        results = []
        tokens = []
        for p in prompts:
            try:
                r = self.generate(p, **kwargs)
                results.append(r)
                tokens.append(len(r))
            except Exception as e:
                results.append(f"[Chaos Error: {e}]")
                tokens.append(0)
        return results, tokens
