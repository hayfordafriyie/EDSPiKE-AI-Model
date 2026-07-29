import pytest

from src.session.urls import parse_session_url, build_session_url, is_valid_session_id


class TestSessionURL:
    def test_parse_valid(self):
        link = parse_session_url("https://edspike.ai/share/abc123")
        assert link is not None
        assert link.session_id == "abc123"
        assert link.host == "edspike.ai"

    def test_parse_with_turn(self):
        link = parse_session_url("https://edspike.ai/share/abc123/5")
        assert link is not None
        assert link.turn_index == 5

    def test_parse_invalid(self):
        link = parse_session_url("not-a-url")
        assert link is None

    def test_build(self):
        url = build_session_url("xyz789")
        assert "xyz789" in url
        assert "edspike.ai" in url

    def test_build_with_turn(self):
        url = build_session_url("xyz789", turn_index=3)
        assert "/3" in url

    def test_is_valid(self):
        assert is_valid_session_id("abc123_def-456") is True
        assert is_valid_session_id("short") is False
