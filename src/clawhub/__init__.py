from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HubListing:
    name: str
    type: str  # plugin, skill, tool, agent
    description: str
    version: str = "1.0.0"
    author: str = ""
    downloads: int = 0
    rating: float = 0.0
    tags: list[str] = field(default_factory=list)
    verified: bool = False
    install_url: str = ""


BUILTIN_LISTINGS: list[HubListing] = [
    HubListing(name="TokenJuice", type="tool", description="Compress noisy tool outputs to save context window", version="1.0.0", author="EDSPiKE", downloads=3400, rating=4.8, tags=["context", "optimization"], verified=True),
    HubListing(name="Active Memory", type="plugin", description="Policy-driven memory with importance scoring and TTL", version="1.0.0", author="EDSPiKE", downloads=2800, rating=4.7, tags=["memory", "persistence"], verified=True),
    HubListing(name="Lobster Workflows", type="tool", description="Pipeline-style multi-step automation with approval gates", version="1.0.0", author="EDSPiKE", downloads=2100, rating=4.6, tags=["automation", "pipeline"], verified=True),
    HubListing(name="Browser Automation", type="tool", description="Headless browser control for web testing and scraping", version="1.0.0", author="EDSPiKE", downloads=1800, rating=4.5, tags=["browser", "web"], verified=True),
    HubListing(name="Code Review Agent", type="agent", description="Automated code review for PR quality checks", version="1.0.0", author="EDSPiKE", downloads=4500, rating=4.9, tags=["review", "quality"], verified=True),
    HubListing(name="SQLite Store", type="plugin", description="Thread-safe KV store with WAL mode and JSON support", version="1.0.0", author="EDSPiKE", downloads=1500, rating=4.4, tags=["database", "storage"], verified=True),
    HubListing(name="Workboard", type="plugin", description="Kanban task board for tracking work items", version="1.0.0", author="EDSPiKE", downloads=1200, rating=4.3, tags=["kanban", "tasks"], verified=True),
    HubListing(name="Webhook Gateway", type="plugin", description="Incoming and outgoing webhook triggers for automation", version="1.0.0", author="EDSPiKE", downloads=900, rating=4.2, tags=["webhooks", "automation"], verified=True),
]


class ClawHub:
    def __init__(self):
        self._listings: dict[str, HubListing] = {l.name: l for l in BUILTIN_LISTINGS}

    def search(self, query: str = "", type_: str = "", tag: str = "") -> list[HubListing]:
        results = list(self._listings.values())
        if query:
            q = query.lower()
            results = [l for l in results if q in l.name.lower() or q in l.description.lower()]
        if type_:
            results = [l for l in results if l.type == type_]
        if tag:
            results = [l for l in results if tag in l.tags]
        return results

    def get(self, name: str) -> HubListing | None:
        return self._listings.get(name)

    def register(self, listing: HubListing) -> None:
        self._listings[listing.name] = listing

    def trending(self, limit: int = 5) -> list[HubListing]:
        return sorted(self._listings.values(), key=lambda l: l.downloads, reverse=True)[:limit]

    def top_rated(self, limit: int = 5) -> list[HubListing]:
        return sorted(self._listings.values(), key=lambda l: l.rating, reverse=True)[:limit]

    def list_categories(self) -> list[str]:
        return sorted({l.type for l in self._listings.values()})
