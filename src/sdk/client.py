from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx


class EDSPiKEClient:
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.Client(headers=self._headers())

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def generate(self, prompt: str, model: str = "", max_tokens: int = 1024, temperature: float = 0.5) -> str:
        payload: dict[str, Any] = {"prompt": prompt, "max_tokens": max_tokens, "temperature": temperature}
        if model:
            payload["model"] = model
        resp = self._client.post(f"{self.base_url}/v1/generate", json=payload)
        resp.raise_for_status()
        return resp.json().get("response", "")

    def generate_stream(self, prompt: str, model: str = "", max_tokens: int = 1024):
        payload: dict[str, Any] = {"prompt": prompt, "max_tokens": max_tokens}
        if model:
            payload["model"] = model
        with self._client.stream("POST", f"{self.base_url}/v1/generate/stream", json=payload) as resp:
            for line in resp.iter_lines():
                if line.startswith("data: "):
                    yield line[6:]

    def list_agents(self) -> list[dict[str, Any]]:
        resp = self._client.get(f"{self.base_url}/v1/agents")
        resp.raise_for_status()
        return resp.json().get("agents", [])

    def list_sessions(self) -> list[dict[str, Any]]:
        resp = self._client.get(f"{self.base_url}/v1/sessions")
        resp.raise_for_status()
        return resp.json().get("sessions", [])

    def health(self) -> dict[str, Any]:
        resp = self._client.get(f"{self.base_url}/health")
        resp.raise_for_status()
        return resp.json()
