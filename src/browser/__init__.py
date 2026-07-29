from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BrowserSession:
    url: str = ""
    title: str = ""
    html: str = ""
    screenshot: bytes = b""


class BrowserAutomation:
    def __init__(self):
        self._session = BrowserSession()
        self._available = self._check_available()

    def _check_available(self) -> bool:
        try:
            import selenium
            import webdriver_manager
            return True
        except ImportError:
            pass
        try:
            subprocess.run(["which", "chromium", "google-chrome", "firefox"], capture_output=True, shell=True)
            return True
        except Exception:
            return False
        return False

    def navigate(self, url: str) -> str:
        if not self._available:
            return "Browser automation not available. Install selenium: pip install selenium webdriver-manager"
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            opts = Options()
            opts.add_argument("--headless=new")
            opts.add_argument("--no-sandbox")
            driver = webdriver.Chrome(options=opts)
            driver.get(url)
            self._session.url = url
            self._session.title = driver.title
            self._session.html = driver.page_source
            driver.quit()
            return f"Navigated to {url}. Title: {driver.title}. Page size: {len(self._session.html)} chars"
        except Exception as e:
            return f"Browser error: {e}"

    def get_html(self) -> str:
        return self._session.html

    def get_title(self) -> str:
        return self._session.title

    def search(self, query: str) -> str:
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        return self.navigate(search_url)

    def is_available(self) -> bool:
        return self._available
