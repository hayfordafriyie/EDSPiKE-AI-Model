from __future__ import annotations

import json
import logging
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class OAuthToken:
    access_token: str
    token_type: str = "bearer"
    refresh_token: str = ""
    expires_at: float = 0.0
    scope: str = ""

    @property
    def expired(self) -> bool:
        return self.expires_at > 0 and time.time() >= self.expires_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "scope": self.scope,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OAuthToken:
        return cls(
            access_token=data.get("access_token", ""),
            token_type=data.get("token_type", "bearer"),
            refresh_token=data.get("refresh_token", ""),
            expires_at=data.get("expires_at", 0.0),
            scope=data.get("scope", ""),
        )


class OAuthFlow:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        authorize_url: str,
        token_url: str,
        redirect_uri: str = "http://localhost:8000/auth/callback",
        scopes: list[str] | None = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorize_url = authorize_url
        self.token_url = token_url
        self.redirect_uri = redirect_uri
        self.scopes = scopes or ["openid", "email"]

    def get_authorization_url(self, state: str = "") -> str:
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state or "",
        }
        return f"{self.authorize_url}?{urllib.parse.urlencode(params)}"

    def exchange_code(self, code: str) -> OAuthToken:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        resp = self._post(self.token_url, data)
        return self._parse_token(resp)

    def refresh_token(self, token: OAuthToken) -> OAuthToken:
        if not token.refresh_token:
            raise ValueError("No refresh token available")
        data = {
            "grant_type": "refresh_token",
            "refresh_token": token.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        resp = self._post(self.token_url, data)
        return self._parse_token(resp)

    def _post(self, url: str, data: dict[str, str]) -> dict[str, Any]:
        body = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode()
            logger.error("OAuth error %s: %s", exc.code, error_body)
            raise RuntimeError(f"OAuth failed: {exc.code} {error_body}")

    def _parse_token(self, data: dict[str, Any]) -> OAuthToken:
        expires_in = data.get("expires_in", 0)
        return OAuthToken(
            access_token=data.get("access_token", ""),
            token_type=data.get("token_type", "bearer"),
            refresh_token=data.get("refresh_token", ""),
            expires_at=time.time() + expires_in if expires_in else 0,
            scope=data.get("scope", ""),
        )
