from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PluginListing:
    name: str
    description: str
    version: str
    author: str
    repo: str
    type: str = "plugin"  # plugin, tool, agent, skill
    downloads: int = 0
    tags: list[str] = field(default_factory=list)


BUILTIN_PLUGINS: list[PluginListing] = [
    PluginListing(
        name="code-formatter",
        description="Auto-format code on write using black, prettier, ruff",
        version="1.0.0", author="EDSPiKE", repo="edspike/code-formatter",
        type="plugin", downloads=1200, tags=["format", "code"],
    ),
    PluginListing(
        name="lsp-integration",
        description="Language Server Protocol integration for code intelligence",
        version="1.0.0", author="EDSPiKE", repo="edspike/lsp-integration",
        type="plugin", downloads=980, tags=["lsp", "code-intel"],
    ),
    PluginListing(
        name="docker-tools",
        description="Docker and container management tools for the agent",
        version="1.0.0", author="EDSPiKE", repo="edspike/docker-tools",
        type="tool", downloads=750, tags=["docker", "containers"],
    ),
    PluginListing(
        name="web-scraper",
        description="Advanced web scraping and data extraction tools",
        version="1.0.0", author="EDSPiKE", repo="edspike/web-scraper",
        type="tool", downloads=620, tags=["web", "scraping"],
    ),
    PluginListing(
        name="code-reviewer",
        description="Automated code review agent for PR quality checks",
        version="1.0.0", author="EDSPiKE", repo="edspike/code-reviewer",
        type="agent", downloads=890, tags=["review", "quality"],
    ),
    PluginListing(
        name="test-writer",
        description="Automated test generation and maintenance agent",
        version="1.0.0", author="EDSPiKE", repo="edspike/test-writer",
        type="agent", downloads=670, tags=["test", "coverage"],
    ),
]


class PluginMarketplace:
    def __init__(self, data_dir: str = ""):
        self._plugins: dict[str, PluginListing] = {p.name: p for p in BUILTIN_PLUGINS}
        self._data_dir = data_dir
        if data_dir:
            Path(data_dir).mkdir(parents=True, exist_ok=True)
            self._load()

    def _path(self) -> Path:
        return Path(self._data_dir) / "marketplace.json"

    def _load(self) -> None:
        path = self._path()
        if path.exists():
            try:
                data = json.loads(path.read_text())
                for item in data:
                    plugin = PluginListing(**item)
                    self._plugins[plugin.name] = plugin
            except Exception:
                pass

    def _save(self) -> None:
        if not self._data_dir:
            return
        data = [p.__dict__ for p in self._plugins.values()]
        self._path().write_text(json.dumps(data, indent=2))

    def search(self, query: str = "", type_: str = "", tag: str = "") -> list[PluginListing]:
        results = list(self._plugins.values())
        if query:
            q = query.lower()
            results = [p for p in results if q in p.name.lower() or q in p.description.lower()]
        if type_:
            results = [p for p in results if p.type == type_]
        if tag:
            results = [p for p in results if tag in p.tags]
        return results

    def get(self, name: str) -> PluginListing | None:
        return self._plugins.get(name)

    def register(self, listing: PluginListing) -> None:
        self._plugins[listing.name] = listing
        self._save()

    def install(self, name: str, target_dir: str) -> str:
        listing = self.get(name)
        if not listing:
            return f"Plugin '{name}' not found in marketplace"

        target = Path(target_dir) / name
        if target.exists():
            return f"Plugin '{name}' already installed at {target}"

        target.mkdir(parents=True, exist_ok=True)
        readme = target / "README.md"
        readme.write_text(f"# {listing.name}\n\n{listing.description}\n\nInstalled from marketplace.\n")
        return f"Installed '{name}' to {target}"

    def list_categories(self) -> list[str]:
        return list({p.type for p in self._plugins.values()})

    def trending(self, limit: int = 5) -> list[PluginListing]:
        return sorted(self._plugins.values(), key=lambda p: p.downloads, reverse=True)[:limit]
