"""EDSPiKE Python SDK — programmatic access to the EDSPiKE AI Agent API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx


class EDSPiKEClient:
    """Client for the EDSPiKE AI Agent API.

    Usage:
        client = EDSPiKEClient("http://localhost:8000", api_key="your-key")
        response = client.generate("What is the capital of France?")
        print(response)
    """

    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.Client(headers=self._headers(), timeout=60)

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def generate(self, prompt: str, model: str = "", max_tokens: int = 1024, temperature: float = 0.5, session_id: str = "") -> str:
        """Send a prompt and get a response."""
        payload: dict[str, Any] = {"prompt": prompt, "max_tokens": max_tokens, "temperature": temperature}
        if model:
            payload["model"] = model
        if session_id:
            payload["session_id"] = session_id
        resp = self._client.post(f"{self.base_url}/v1/generate", json=payload)
        resp.raise_for_status()
        return resp.json().get("response", "")

    def generate_stream(self, prompt: str, model: str = "", max_tokens: int = 1024):
        """Stream a response token by token."""
        payload: dict[str, Any] = {"prompt": prompt, "max_tokens": max_tokens}
        if model:
            payload["model"] = model
        with self._client.stream("POST", f"{self.base_url}/v1/generate/stream", json=payload) as resp:
            for line in resp.iter_lines():
                if line.startswith("data: "):
                    yield line[6:]

    def generate_batch(self, prompts: list[str], model: str = "", max_tokens: int = 1024) -> list[str]:
        """Send multiple prompts and get responses."""
        payload: dict[str, Any] = {"prompts": prompts, "max_tokens": max_tokens}
        if model:
            payload["model"] = model
        resp = self._client.post(f"{self.base_url}/v1/generate", json=payload)
        resp.raise_for_status()
        return resp.json().get("responses", [])

    def list_agents(self) -> list[dict[str, Any]]:
        """List all available agents."""
        resp = self._client.get(f"{self.base_url}/v1/agents")
        resp.raise_for_status()
        return resp.json().get("agents", [])

    def get_agent(self, agent_id: str) -> dict[str, Any]:
        """Get details for a specific agent."""
        resp = self._client.get(f"{self.base_url}/v1/agents/{agent_id}")
        resp.raise_for_status()
        return resp.json()

    def list_sessions(self, limit: int = 20) -> list[dict[str, Any]]:
        """List recent sessions."""
        resp = self._client.get(f"{self.base_url}/v1/sessions?limit={limit}")
        resp.raise_for_status()
        return resp.json().get("sessions", [])

    def get_session(self, session_id: str) -> dict[str, Any]:
        """Get a session by ID."""
        resp = self._client.get(f"{self.base_url}/v1/sessions/{session_id}")
        resp.raise_for_status()
        return resp.json()

    def list_providers(self) -> list[dict[str, Any]]:
        """List configured AI providers."""
        resp = self._client.get(f"{self.base_url}/v1/providers")
        resp.raise_for_status()
        return resp.json().get("providers", [])

    def list_models(self) -> list[dict[str, Any]]:
        """List available models."""
        resp = self._client.get(f"{self.base_url}/v1/models")
        resp.raise_for_status()
        return resp.json().get("models", [])

    def read_file(self, path: str) -> str:
        """Read a file from the workspace."""
        resp = self._client.get(f"{self.base_url}/v1/fs/read", params={"path": path})
        resp.raise_for_status()
        return resp.text

    def write_file(self, path: str, content: str) -> dict[str, Any]:
        """Write content to a file in the workspace."""
        resp = self._client.post(f"{self.base_url}/v1/fs/write", json={"path": path, "content": content})
        resp.raise_for_status()
        return resp.json()

    def execute_code(self, code: str, language: str = "python") -> dict[str, Any]:
        """Execute code in the sandbox."""
        resp = self._client.post(f"{self.base_url}/v1/codemode/execute", json={"code": code, "language": language})
        resp.raise_for_status()
        return resp.json()

    def health(self) -> dict[str, Any]:
        """Check API health."""
        resp = self._client.get(f"{self.base_url}/health")
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        self._client.close()
