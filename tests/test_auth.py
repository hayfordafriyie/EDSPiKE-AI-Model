from __future__ import annotations

import time

import pytest

from src.auth import OAuthToken, OAuthFlow


class TestOAuthToken:
    def test_defaults(self):
        t = OAuthToken(access_token="abc")
        assert t.token_type == "bearer"
        assert t.refresh_token == ""
        assert t.scope == ""

    def test_not_expired(self):
        t = OAuthToken(access_token="abc", expires_at=time.time() + 3600)
        assert t.expired is False

    def test_expired(self):
        t = OAuthToken(access_token="abc", expires_at=time.time() - 1)
        assert t.expired is True

    def test_no_expiry(self):
        t = OAuthToken(access_token="abc")
        assert t.expired is False

    def test_to_from_dict(self):
        original = OAuthToken(access_token="tok", refresh_token="ref", expires_at=100.0, scope="read")
        data = original.to_dict()
        restored = OAuthToken.from_dict(data)
        assert restored.access_token == "tok"
        assert restored.refresh_token == "ref"
        assert restored.expires_at == 100.0
        assert restored.scope == "read"


class TestOAuthFlow:
    def test_get_authorization_url(self):
        flow = OAuthFlow("cid", "csec", "https://auth.example.com/authorize", "https://auth.example.com/token")
        url = flow.get_authorization_url(state="xyz")
        assert "client_id=cid" in url
        assert "redirect_uri" in url
        assert "state=xyz" in url
        assert url.startswith("https://auth.example.com/authorize")

    def test_authorization_url_with_default_scopes(self):
        flow = OAuthFlow("cid", "csec", "https://auth.example.com/authorize", "https://auth.example.com/token")
        url = flow.get_authorization_url()
        assert "scope=" in url
