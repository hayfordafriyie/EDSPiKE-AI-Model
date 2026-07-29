import pytest

from src.browser import BrowserAutomation


class TestBrowser:
    def test_init(self):
        b = BrowserAutomation()
        assert hasattr(b, "_available")

    def test_no_browser(self):
        b = BrowserAutomation()
        b._available = False
        result = b.navigate("https://example.com")
        assert "available" in result.lower()
